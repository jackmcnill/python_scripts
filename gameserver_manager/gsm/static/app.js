"use strict";
// --- Hilfen ------------------------------------------------------------------
const $ = (sel, root = document) => root.querySelector(sel);
function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k === "class") el.className = v;
    else if (v === true) el.setAttribute(k, "");
    else if (v !== false && v != null) el.setAttribute(k, v);
  }
  for (const c of children.flat()) if (c != null && c !== false) el.append(c.nodeType ? c : document.createTextNode(c));
  return el;
}
async function api(path, opts = {}) {
  const init = { method: opts.method || "GET", headers: {}, credentials: "same-origin" };
  if (opts.json !== undefined) { init.headers["Content-Type"] = "application/json"; init.body = JSON.stringify(opts.json); }
  if (opts.form) init.body = opts.form;
  const res = await fetch("/api" + path, init);
  if (res.status === 401 && path !== "/login") { state.authed = false; render(); throw new Error("Nicht angemeldet"); }
  const data = res.headers.get("content-type")?.includes("json") ? await res.json() : null;
  if (!res.ok) throw new Error(data?.error || res.statusText);
  return data;
}
const fmtSize = b => b > 1e9 ? (b / 1e9).toFixed(1) + " GB" : b > 1e6 ? (b / 1e6).toFixed(1) + " MB" : Math.ceil(b / 1e3) + " KB";
const state = { authed: null, instances: [], sel: null, tab: "overview", system: null, games: [], jobs: [] };
let ws = null, pollTimer = null;

// --- Jobs --------------------------------------------------------------------
function trackJob(id, title, onDone) {
  const job = { id, title, lines: [], state: "running", since: 0 };
  state.jobs.push(job);
  renderJobs();
  const tick = async () => {
    try {
      const d = await api(`/jobs/${id}?since=${job.since}`);
      job.lines.push(...d.lines); job.since = d.total; job.state = d.state; job.error = d.error;
      renderJobs();
      if (d.state === "running") return setTimeout(tick, 1000);
      await refresh();
      onDone && onDone(d);
      if (d.state === "done") setTimeout(() => dismissJob(job), 4000);
    } catch (e) { job.state = "error"; job.error = e.message; renderJobs(); }
  };
  tick();
}
function dismissJob(job) { state.jobs = state.jobs.filter(j => j !== job); renderJobs(); }
function renderJobs() {
  let box = $("#jobs");
  if (!box) { box = h("div", { id: "jobs", class: "jobs" }); document.body.append(box); }
  box.replaceChildren(...state.jobs.map(j => {
    const log = h("pre", { class: "joblog" }, j.lines.join("\n"));
    setTimeout(() => (log.scrollTop = log.scrollHeight));
    return h("div", { class: "job " + (j.state === "error" ? "error" : "") },
      h("div", { class: "row space" }, h("strong", {}, j.title),
        h("span", { class: "row" }, h("span", { class: "badge" }, j.state === "running" ? "läuft …" : j.state === "done" ? "fertig" : "Fehler"),
          j.state !== "running" && h("button", { onclick: () => dismissJob(j) }, "×"))),
      j.error && h("div", { class: "err" }, j.error), log);
  }));
}
const act = (path, title, opts = {}) => api(path, { method: "POST", ...opts }).then(r => trackJob(r.job, title)).catch(e => alert(e.message));

// --- Login -------------------------------------------------------------------
function loginView() {
  const err = h("div", { class: "err" });
  const pw = h("input", { type: "password", placeholder: "Passwort", autofocus: true });
  const submit = async () => {
    try { await api("/login", { method: "POST", json: { password: pw.value } }); state.authed = true; await start(); }
    catch (e) { err.textContent = e.message; }
  };
  pw.addEventListener("keydown", e => e.key === "Enter" && submit());
  return h("div", { class: "card login" }, h("h1", {}, "Game Server Manager"), pw, h("p", {}, h("button", { class: "primary", onclick: submit }, "Anmelden")), err);
}

// --- Layout ------------------------------------------------------------------
function render() {
  const app = $("#app");
  if (state.authed === null) return app.replaceChildren();
  if (!state.authed) return app.replaceChildren(loginView());
  const side = h("div", { class: "side" },
    h("h1", {}, "Game Server Manager"),
    ...state.instances.map(i => h("button", { class: "item" + (i.id === state.sel ? " active" : ""), onclick: () => select(i.id) },
      h("span", { class: "dot " + (i.busy ? "busy" : i.state) }), i.name)),
    h("button", { class: "primary", onclick: createDialog }, "+ Neuer Server"),
    h("button", { onclick: importDialog }, "Modpack importieren"),
    h("div", { class: "muted" }, state.system ? `Runtime: ${state.system.runtime}${state.system.runtime_ok ? "" : " (!)"} · ${state.system.disk_free_gb} GB frei` : ""),
    h("button", { onclick: async () => { await api("/logout", { method: "POST" }); state.authed = false; render(); } }, "Abmelden"));
  const inst = state.instances.find(i => i.id === state.sel);
  const main = h("div", { class: "main" }, inst ? detailView(inst) : h("p", { class: "muted" }, "Wähle links einen Server oder lege einen neuen an."));
  app.replaceChildren(h("div", { class: "layout" }, side, main));
}

function select(id) { state.sel = id; state.tab = "overview"; closeWs(); render(); }
function closeWs() { if (ws) { ws.close(); ws = null; } }

function detailView(inst) {
  const tabs = [["overview", "Übersicht"], ["console", "Konsole"], ["mods", inst.kind === "paper" ? "Plugins" : "Mods"], ["backups", "Backups"]];
  const body = h("div");
  const show = () => {
    closeWs(); body.replaceChildren();
    ({ overview: overviewTab, console: consoleTab, mods: modsTab, backups: backupsTab })[state.tab](inst, body);
  };
  const bar = h("div", { class: "tabs" }, tabs.map(([id, label]) =>
    h("button", { class: state.tab === id ? "active" : "", onclick: () => { state.tab = id; render(); } }, label)));
  setTimeout(show);
  return h("div", {},
    h("div", { class: "row space" }, h("h2", { style: "margin:0" }, inst.name),
      h("span", { class: "badge" }, inst.busy || (inst.state === "running" ? "läuft" : "gestoppt"))),
    h("div", { class: "muted" }, `${inst.kind} ${inst.version}${inst.loader_version ? " · Loader " + inst.loader_version : ""}`),
    bar, body);
}

// --- Tab: Übersicht ------------------------------------------------------------
function overviewTab(inst, body) {
  const running = inst.state === "running", busy = !!inst.busy;
  const mem = h("input", { value: inst.memory, size: 6 }), port = h("input", { type: "number", value: inst.port, style: "width:100px" });
  const auto = h("input", { type: "checkbox", checked: inst.auto_start });
  body.append(
    h("div", { class: "card" },
      h("div", { class: "row" },
        h("button", { class: "primary", disabled: running || busy, onclick: () => act(`/instances/${inst.id}/start`, `${inst.name} starten`) }, "Starten"),
        h("button", { disabled: !running || busy, onclick: () => act(`/instances/${inst.id}/stop`, `${inst.name} stoppen`) }, "Stoppen"),
        h("button", { disabled: !running || busy, onclick: () => act(`/instances/${inst.id}/restart`, `${inst.name} neu starten`) }, "Neustart"),
        h("button", { class: "danger", disabled: !running, onclick: () => confirm("Prozess hart beenden? Ungespeicherte Daten gehen verloren.") && api(`/instances/${inst.id}/kill`, { method: "POST" }).then(refresh) }, "Beenden erzwingen")),
      h("p", { class: "muted" }, `Verbinden mit: <Server-Adresse>:${inst.port}`)),
    h("div", { class: "card" }, h("h3", { style: "margin-top:0" }, "Einstellungen"),
      h("div", { class: "grid2" }, h("div", {}, h("label", {}, "Arbeitsspeicher (z.B. 4G)"), mem), h("div", {}, h("label", {}, "Port"), port)),
      h("label", { class: "inline" }, auto, "Automatisch starten, wenn der Manager startet"),
      h("p", {}, h("button", { onclick: async () => { try { await api(`/instances/${inst.id}`, { method: "PATCH", json: { memory: mem.value, port: +port.value, auto_start: auto.checked } }); await refresh(); alert(running ? "Gespeichert. Gilt nach dem nächsten Neustart." : "Gespeichert."); } catch (e) { alert(e.message); } } }, "Speichern"))),
    h("div", { class: "card" }, h("button", { class: "danger", disabled: running || busy, onclick: () => {
      if (!confirm(`Server "${inst.name}" samt Welt löschen?`)) return;
      const keep = confirm("Auch alle Backups dieses Servers löschen?\nOK = Backups löschen, Abbrechen = Backups behalten");
      api(`/instances/${inst.id}`, { method: "DELETE", json: { delete_backups: keep } }).then(r => { state.sel = null; trackJob(r.job, "Server löschen"); }).catch(e => alert(e.message));
    } }, "Server löschen")));
}

// --- Tab: Konsole ---------------------------------------------------------------
function consoleTab(inst, body) {
  const out = h("pre", { class: "console" });
  const input = h("input", { placeholder: "Befehl eingeben (z.B. list, say Hallo, op Name)", style: "width:100%" });
  body.append(out, input);
  const connect = () => {
    ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/api/instances/${inst.id}/console`);
    ws.onmessage = e => { const stick = out.scrollTop + out.clientHeight >= out.scrollHeight - 30; out.append(e.data + "\n"); if (out.textContent.length > 200000) out.textContent = out.textContent.slice(-100000); if (stick) out.scrollTop = out.scrollHeight; };
    ws.onclose = () => { if (ws && state.tab === "console") setTimeout(() => ws && connect(), 3000); };
  };
  connect();
  input.addEventListener("keydown", e => { if (e.key === "Enter" && input.value.trim() && ws?.readyState === 1) { ws.send(input.value); input.value = ""; } });
  input.focus();
}

// --- Tab: Mods / Plugins ------------------------------------------------------------
async function modsTab(inst, body) {
  if (inst.kind === "vanilla") return body.append(h("p", { class: "muted" }, "Vanilla-Server unterstützen keine Mods. Lege einen Fabric-, Forge-, NeoForge- oder Paper-Server an."));
  const list = h("div"), results = h("div");
  const label = inst.kind === "paper" ? "Plugin" : "Mod";
  const loadList = async () => {
    const items = await api(`/instances/${inst.id}/addons`);
    list.replaceChildren(items.length ? h("table", {}, h("tr", {}, h("th", {}, "Name"), h("th", {}, "Datei"), h("th", {}, "Größe"), h("th")),
      items.map(m => h("tr", {}, h("td", {}, m.title, m.version && h("span", { class: "muted" }, " " + m.version)), h("td", { class: "muted" }, m.file), h("td", {}, fmtSize(m.size)),
        h("td", { class: "row" },
          h("button", { onclick: async () => { await api(`/instances/${inst.id}/addons/${encodeURIComponent(m.file)}`, { method: "PATCH", json: { enabled: !m.enabled } }); loadList(); } }, m.enabled ? "Deaktivieren" : "Aktivieren"),
          h("button", { class: "danger", onclick: async () => { if (confirm(`${m.file} löschen?`)) { await api(`/instances/${inst.id}/addons/${encodeURIComponent(m.file)}`, { method: "DELETE" }); loadList(); } } }, "Löschen"))))) : h("p", { class: "muted" }, `Noch keine ${label}s installiert.`));
  };
  const file = h("input", { type: "file", multiple: true, accept: ".jar" });
  const upload = async () => {
    if (!file.files.length) return;
    const form = new FormData(); for (const f of file.files) form.append("files", f);
    try { await api(`/instances/${inst.id}/addons`, { method: "POST", form }); file.value = ""; loadList(); } catch (e) { alert(e.message); }
  };
  const q = h("input", { placeholder: `${label}s auf Modrinth suchen …`, style: "flex:1" });
  const search = async () => {
    results.replaceChildren(h("p", { class: "muted" }, "Suche …"));
    try {
      const r = await api(`/instances/${inst.id}/catalog?q=${encodeURIComponent(q.value)}`);
      results.replaceChildren(h("table", {}, r.hits.map(m => h("tr", {}, h("td", {}, h("strong", {}, m.title), h("div", { class: "muted" }, m.description)),
        h("td", {}, h("button", { class: "primary", onclick: () => api(`/instances/${inst.id}/catalog`, { method: "POST", json: { project: m.id } }).then(r => trackJob(r.job, `${m.title} installieren`, loadList)) }, "Installieren")))),
        h("p", { class: "muted" }, `${r.total} Treffer für ${inst.kind} ${inst.version}`)));
    } catch (e) { results.replaceChildren(h("p", { class: "err" }, e.message)); }
  };
  q.addEventListener("keydown", e => e.key === "Enter" && search());
  body.append(h("div", { class: "card" }, h("h3", { style: "margin-top:0" }, `Installierte ${label}s`), list),
    h("div", { class: "card" }, h("h3", { style: "margin-top:0" }, ".jar-Dateien hochladen"), h("div", { class: "row" }, file, h("button", { onclick: upload }, "Hochladen"))),
    h("div", { class: "card" }, h("h3", { style: "margin-top:0" }, "Modrinth"), h("div", { class: "row" }, q, h("button", { onclick: search }, "Suchen")),
      h("p", { class: "muted" }, "Abhängigkeiten werden automatisch mitinstalliert. Es werden nur Projekte angezeigt, die auf dem Server laufen."), results));
  loadList(); search();
}

// --- Tab: Backups --------------------------------------------------------------------------
async function backupsTab(inst, body) {
  const list = h("div");
  const b = inst.backup;
  const en = h("input", { type: "checkbox", checked: b.enabled }), iv = h("input", { type: "number", min: 1, value: b.interval_hours, style: "width:80px" });
  const keep = h("input", { type: "number", min: 1, value: b.keep, style: "width:80px" });
  const scope = h("select", {}, h("option", { value: "full", selected: b.scope === "full" }, "Kompletter Server"), h("option", { value: "world", selected: b.scope === "world" }, "Nur Welten + Einstellungen"));
  const load = async () => {
    const items = await api(`/instances/${inst.id}/backups`);
    list.replaceChildren(items.length ? h("table", {}, h("tr", {}, h("th", {}, "Backup"), h("th", {}, "Erstellt"), h("th", {}, "Größe"), h("th")),
      items.map(i => h("tr", {}, h("td", {}, i.name), h("td", {}, i.created.replace("T", " ")), h("td", {}, fmtSize(i.size)),
        h("td", { class: "row" },
          h("a", { href: `/api/instances/${inst.id}/backups/${i.name}/download` }, h("button", {}, "Download")),
          h("button", { disabled: inst.state === "running", title: inst.state === "running" ? "Server zuerst stoppen" : "", onclick: () => confirm(`Server auf "${i.name}" zurücksetzen?\nDer aktuelle Stand wird vorher gesichert.`) && act(`/instances/${inst.id}/backups/${i.name}/restore`, "Wiederherstellen") }, "Wiederherstellen"),
          h("button", { class: "danger", onclick: async () => { if (confirm("Backup löschen?")) { await api(`/instances/${inst.id}/backups/${i.name}`, { method: "DELETE" }); load(); } } }, "Löschen"))))) : h("p", { class: "muted" }, "Noch keine Backups."));
  };
  body.append(
    h("div", { class: "card" }, h("div", { class: "row space" }, h("h3", { style: "margin:0" }, "Backups"),
      h("button", { class: "primary", onclick: () => act(`/instances/${inst.id}/backups`, "Backup erstellen", {}) .then(() => setTimeout(load, 3000)) }, "Jetzt sichern")), list),
    h("div", { class: "card" }, h("h3", { style: "margin-top:0" }, "Automatische Backups"),
      h("label", { class: "inline" }, en, "Aktiv"),
      h("div", { class: "row" }, "Alle ", iv, " Stunden, die letzten ", keep, " behalten"),
      h("label", {}, "Umfang"), scope,
      h("p", {}, h("button", { onclick: async () => { try { await api(`/instances/${inst.id}`, { method: "PATCH", json: { backup: { enabled: en.checked, interval_hours: +iv.value, keep: +keep.value, scope: scope.value } } }); await refresh(); alert("Gespeichert."); } catch (e) { alert(e.message); } } }, "Speichern")),
      h("p", { class: "muted" }, "Läuft der Server, wird vor dem Backup die Welt gespeichert und das automatische Speichern kurz angehalten.")));
  load();
}

// --- Dialoge --------------------------------------------------------------------------------
function dialog(title, content, buttons) {
  const d = h("dialog", {}, h("h2", { style: "margin-top:0" }, title), content,
    h("div", { class: "row", style: "margin-top:16px;justify-content:flex-end" }, h("button", { onclick: () => d.close() }, "Abbrechen"), buttons));
  d.addEventListener("close", () => d.remove());
  document.body.append(d); d.showModal(); return d;
}

function createDialog() {
  const game = state.games[0];
  const name = h("input", { placeholder: "z.B. survival", style: "width:100%" });
  const kind = h("select", {}, game.kinds.map(k => h("option", { value: k.id }, k.label)));
  const version = h("select", {}), all = h("input", { type: "checkbox" });
  const mem = h("input", { value: game.defaults.memory, size: 6 }), port = h("input", { type: "number", value: game.defaults.port, style: "width:100px" });
  const terms = h("input", { type: "checkbox" });
  const loadVersions = async () => {
    version.replaceChildren(h("option", {}, "lädt …"));
    try { const v = await api(`/games/${game.id}/versions?kind=${kind.value}&all=${all.checked ? 1 : 0}`); version.replaceChildren(...v.map((x, i) => h("option", { value: x }, i === 0 ? `${x} (neueste)` : x))); }
    catch (e) { version.replaceChildren(h("option", {}, e.message)); }
  };
  kind.addEventListener("change", loadVersions); all.addEventListener("change", loadVersions); loadVersions();
  const d = dialog("Neuer Minecraft-Server", h("div", {},
    h("label", {}, "Name"), name, h("div", { class: "grid2" }, h("div", {}, h("label", {}, "Typ"), kind), h("div", {}, h("label", {}, "Minecraft-Version"), version)),
    h("label", { class: "inline" }, all, "auch Snapshots / alte Betas"),
    h("div", { class: "grid2" }, h("div", {}, h("label", {}, "Arbeitsspeicher"), mem), h("div", {}, h("label", {}, "Port"), port)),
    h("label", { class: "inline" }, terms, h("span", {}, "Ich akzeptiere die ", h("a", { href: game.terms.url, target: "_blank", rel: "noopener" }, game.terms.label)))),
    h("button", { class: "primary", onclick: () => {
      api("/instances", { method: "POST", json: { name: name.value, game: game.id, kind: kind.value, version: version.value, memory: mem.value, port: +port.value, accept_terms: terms.checked } })
        .then(r => { d.close(); trackJob(r.job, `Server erstellen: ${name.value}`, res => res.state === "done" && select(res.result)); }).catch(e => alert(e.message));
    } }, "Erstellen"));
}

function importDialog() {
  const game = state.games[0];
  const file = h("input", { type: "file", accept: ".mrpack" });
  const ref = h("input", { placeholder: "Modrinth-Link oder Slug, z.B. fabulously-optimized", style: "width:100%" });
  const name = h("input", { placeholder: "leer = Name des Modpacks", style: "width:100%" });
  const mem = h("input", { value: "4G", size: 6 }), port = h("input", { type: "number", value: game.defaults.port, style: "width:100px" });
  const terms = h("input", { type: "checkbox" });
  const results = h("div"), q = h("input", { placeholder: "Modpacks auf Modrinth suchen …", style: "flex:1" });
  const search = async () => {
    try { const r = await api(`/modpacks?q=${encodeURIComponent(q.value)}`);
      results.replaceChildren(...r.hits.slice(0, 8).map(m => h("div", { class: "row space" }, h("span", {}, m.title), h("button", { onclick: () => (ref.value = m.slug) }, "Wählen")))); }
    catch (e) { results.replaceChildren(h("span", { class: "err" }, e.message)); }
  };
  q.addEventListener("keydown", e => e.key === "Enter" && search());
  const d = dialog("Modpack als neuen Server importieren", h("div", {},
    h("p", { class: "muted" }, "Unterstützt Modrinth-Modpacks (.mrpack). Mods, die nur für Clients gedacht sind, werden übersprungen."),
    h("div", { class: "row" }, q, h("button", { onclick: search }, "Suchen")), results,
    h("label", {}, "Modrinth-Modpack"), ref, h("label", {}, "… oder .mrpack-Datei"), file,
    h("label", {}, "Servername"), name,
    h("div", { class: "grid2" }, h("div", {}, h("label", {}, "Arbeitsspeicher"), mem), h("div", {}, h("label", {}, "Port"), port)),
    h("label", { class: "inline" }, terms, h("span", {}, "Ich akzeptiere die ", h("a", { href: game.terms.url, target: "_blank", rel: "noopener" }, game.terms.label)))),
    h("button", { class: "primary", onclick: () => {
      const form = new FormData();
      form.append("name", name.value); form.append("memory", mem.value); form.append("port", port.value); form.append("accept_terms", terms.checked ? "1" : "0");
      if (file.files[0]) form.append("file", file.files[0]); else form.append("modrinth", ref.value);
      api("/modpacks/import", { method: "POST", form }).then(r => { d.close(); trackJob(r.job, "Modpack importieren", res => res.state === "done" && select(res.result)); }).catch(e => alert(e.message));
    } }, "Importieren"));
}

// --- Start ------------------------------------------------------------------------------------
async function refresh() {
  if (!state.authed) return;
  try { state.instances = await api("/instances"); } catch { return; }
  // nur neu zeichnen, wenn sich etwas Sichtbares geändert hat (sonst würden Konsole/Formulare zurückgesetzt)
  const sig = JSON.stringify(state.instances.map(i => [i.id, i.state, i.busy, i.name, i.port, i.memory, i.backup]));
  if (sig !== refresh.last) { refresh.last = sig; render(); }
}
async function start() {
  [state.system, state.games] = await Promise.all([api("/system"), api("/games")]);
  await refresh(); render();
  clearInterval(pollTimer); pollTimer = setInterval(refresh, 3000);
}
(async () => {
  const s = await fetch("/api/session").then(r => r.json());
  state.authed = s.authenticated;
  if (state.authed) await start(); else render();
})();
