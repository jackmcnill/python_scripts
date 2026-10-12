"use strict";
/* Game Server Manager – Oberfläche (reines JavaScript, ohne Build-Schritt) */

// ============================================================================
// Grundlagen: DOM-Helfer, Icons, Hilfsfunktionen
// ============================================================================
const ICONS = {
  home: '<rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/>',
  server: '<rect width="20" height="8" x="2" y="2" rx="2"/><rect width="20" height="8" x="2" y="14" rx="2"/><line x1="6" x2="6.01" y1="6" y2="6"/><line x1="6" x2="6.01" y1="18" y2="18"/>',
  play: '<polygon points="6 3 20 12 6 21 6 3"/>', stop: '<rect x="5" y="5" width="14" height="14" rx="2"/>',
  refresh: '<path d="M3 12a9 9 0 0 1 15-6.7L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-15 6.7L3 16"/><path d="M8 16H3v5"/>',
  terminal: '<polyline points="4 17 10 11 4 5"/><line x1="12" x2="20" y1="19" y2="19"/>',
  package: '<path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',
  archive: '<rect width="20" height="5" x="2" y="3" rx="1"/><path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8"/><path d="M10 12h4"/>',
  sliders: '<line x1="21" x2="14" y1="4" y2="4"/><line x1="10" x2="3" y1="4" y2="4"/><line x1="21" x2="12" y1="12" y2="12"/><line x1="8" x2="3" y1="12" y2="12"/><line x1="21" x2="16" y1="20" y2="20"/><line x1="12" x2="3" y1="20" y2="20"/><line x1="14" x2="14" y1="2" y2="6"/><line x1="8" x2="8" y1="10" y2="14"/><line x1="16" x2="16" y1="18" y2="22"/>',
  trash: '<path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
  download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/>',
  upload: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/>',
  search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>', plus: '<path d="M5 12h14"/><path d="M12 5v14"/>',
  x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>', check: '<path d="M20 6 9 17l-5-5"/>',
  copy: '<rect width="14" height="14" x="8" y="8" rx="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>',
  moon: '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>',
  logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/>',
  key: '<circle cx="7.5" cy="15.5" r="5.5"/><path d="m21 2-9.6 9.6"/><path d="m15.5 7.5 3 3L22 7l-3-3"/>',
  menu: '<line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/>',
  users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  shield: '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>',
  activity: '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>', clock: '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
  power: '<path d="M18.36 6.64a9 9 0 1 1-12.73 0"/><line x1="12" x2="12" y1="2" y2="12"/>',
  file: '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/>',
  chevron: '<path d="m6 9 6 6 6-6"/>', alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
  edit: '<path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4Z"/>', arrow: '<path d="M19 12H5"/><path d="m12 19-7-7 7-7"/>',
  hdd: '<line x1="22" x2="2" y1="12" y2="12"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/><line x1="6" x2="6.01" y1="16" y2="16"/>',
};
function icon(name, cls = "") {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 24 24"); svg.setAttribute("class", "i " + cls); svg.setAttribute("aria-hidden", "true");
  svg.innerHTML = ICONS[name] || "";
  return svg;
}
function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k === "class") el.className = v;
    else if (k === "html") el.innerHTML = v;
    else if (k === "value") el.value = v;
    else if (v === true) el.setAttribute(k, "");
    else if (v !== false && v != null) el.setAttribute(k, v);
  }
  add(el, ...children);
  return el;
}
function add(parent, ...kids) {
  for (const c of kids.flat(Infinity)) if (c != null && c !== false) parent.append(c.nodeType ? c : document.createTextNode(c));
  return parent;
}
const $ = (sel, root = document) => root.querySelector(sel);
const btn = (label, opts = {}, ...rest) => h("button", { type: "button", class: "btn " + (opts.cls || ""), disabled: opts.disabled, title: opts.title, onclick: opts.onclick, "aria-label": opts.aria },
  opts.icon && icon(opts.icon, opts.small ? "sm" : ""), label, ...rest);
const iconBtn = (name, title, onclick, cls = "") => h("button", { type: "button", class: "btn icon ghost " + cls, title, "aria-label": title, onclick }, icon(name));
const chip = (text, cls = "", ic) => h("span", { class: "chip " + cls }, ic && icon(ic, "sm"), text);

const fmtSize = b => b >= 1e9 ? (b / 1e9).toFixed(1) + " GB" : b >= 1e6 ? (b / 1e6).toFixed(1) + " MB" : Math.max(1, Math.ceil(b / 1e3)) + " KB";
const fmtNum = n => n >= 1e6 ? (n / 1e6).toFixed(1) + " Mio." : n >= 1e3 ? (n / 1e3).toFixed(1) + " Tsd." : String(n);
function ago(iso) {
  const t = new Date(iso).getTime(); if (isNaN(t)) return "";
  const s = Math.max(0, (Date.now() - t) / 1000);
  if (s < 60) return "gerade eben"; if (s < 3600) return `vor ${Math.floor(s / 60)} Min.`;
  if (s < 86400) return `vor ${Math.floor(s / 3600)} Std.`; return `vor ${Math.floor(s / 86400)} Tagen`;
}
const fullDate = iso => new Date(iso).toLocaleString("de-DE", { dateStyle: "medium", timeStyle: "short" });
function copyText(text) {
  const done = () => toast("In die Zwischenablage kopiert");
  if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text).then(done);
  const ta = h("textarea", { style: "position:fixed;opacity:0" }, text); document.body.append(ta); ta.select();
  try { document.execCommand("copy"); done(); } finally { ta.remove(); }
}
function store(key, value) { try { if (value === undefined) return localStorage.getItem(key); localStorage.setItem(key, value); } catch { return null; } }

const KINDS = {
  vanilla: { abbr: "VA", color: "#64748b", desc: "Der originale Mojang-Server ohne Mods." },
  paper: { abbr: "PA", color: "#3b82f6", desc: "Schnell und stabil, erweiterbar mit Plugins." },
  fabric: { abbr: "FA", color: "#c28a3a", desc: "Leichtgewichtiger Mod-Loader, schnell aktuell." },
  forge: { abbr: "FO", color: "#d9552b", desc: "Klassischer Mod-Loader mit großer Auswahl." },
  neoforge: { abbr: "NF", color: "#e08a1e", desc: "Moderne Weiterentwicklung von Forge." },
};
const kindBadge = (kind, size = 40) => h("div", { class: "kind-icon", style: `background:${(KINDS[kind] || KINDS.vanilla).color};width:${size}px;height:${size}px` }, (KINDS[kind] || KINDS.vanilla).abbr);
const PERM = { viewer: "Ansehen", operator: "Bedienen", manager: "Verwalten" };
const RANK = { viewer: 1, operator: 2, manager: 3 };
const AVATAR_COLORS = ["#6366f1", "#0ea5e9", "#10b981", "#f59e0b", "#ef4444", "#a855f7", "#14b8a6", "#ec4899"];
const avatar = name => { let n = 0; for (const c of name) n += c.charCodeAt(0); return h("div", { class: "avatar", style: `background:${AVATAR_COLORS[n % AVATAR_COLORS.length]}` }, name.slice(0, 2)); };

// ============================================================================
// Zustand, API, Toasts, Dialoge
// ============================================================================
const state = { user: null, ready: false, system: null, games: [], instances: [], jobs: [] };
const can = (inst, level) => RANK[inst.permission] >= RANK[level];
const isAdmin = () => state.user?.role === "admin";
const findInst = id => state.instances.find(i => i.id === id);

async function api(path, opts = {}) {
  const init = { method: opts.method || "GET", headers: {}, credentials: "same-origin" };
  if (opts.json !== undefined) { init.headers["Content-Type"] = "application/json"; init.body = JSON.stringify(opts.json); }
  if (opts.form) init.body = opts.form;
  const res = await fetch("/api" + path, init);
  let data = null;
  if ((res.headers.get("content-type") || "").includes("json")) data = await res.json();
  if (res.status === 401 && path !== "/login") { sessionLost(); throw new Error("Nicht angemeldet"); }
  if (!res.ok) throw new Error(data?.error || res.statusText);
  return data;
}

function toast(message, type = "ok") {
  let box = $("#toasts"); if (!box) { box = h("div", { id: "toasts", class: "toasts", role: "status", "aria-live": "polite" }); document.body.append(box); }
  const el = h("div", { class: "toast " + (type === "error" ? "error" : "") }, icon(type === "error" ? "alert" : "check"), h("div", { class: "grow" }, message));
  box.append(el); setTimeout(() => el.remove(), type === "error" ? 7000 : 3500);
}
const fail = e => toast(e.message || String(e), "error");

function modal({ title, subtitle, body, buttons = [], width }) {
  const dlg = h("dialog", { class: "modal", style: width ? `width:min(${width}px,calc(100vw - 24px))` : "" });
  const close = () => { if (dlg.open) dlg.close(); };
  add(dlg, h("div", { class: "modal-head" }, h("h2", {}, title), subtitle && h("p", { class: "muted", style: "margin-top:4px" }, subtitle)),
    h("div", { class: "modal-body" }, body),
    h("div", { class: "modal-foot" }, btn("Abbrechen", { cls: "ghost", onclick: close }), ...buttons));
  dlg.addEventListener("close", () => dlg.remove());
  dlg.addEventListener("click", e => { if (e.target === dlg) close(); });
  document.body.append(dlg); dlg.showModal();
  return { el: dlg, close };
}
function confirmBox(title, message, { confirmText = "Bestätigen", danger = false } = {}) {
  return new Promise(resolve => {
    let answered = false;
    const answer = v => { answered = true; m.close(); resolve(v); };
    const m = modal({ title, body: h("p", { class: "muted" }, message), width: 460,
      buttons: [btn(confirmText, { cls: danger ? "danger solid" : "primary", onclick: () => answer(true) })] });
    m.el.addEventListener("close", () => !answered && resolve(false));
  });
}
let fieldId = 0;
const field = (label, input, hint) => {
  const lbl = h("label", {}, label);
  if (input.tagName === "INPUT" || input.tagName === "SELECT") { input.id = input.id || `f${++fieldId}`; lbl.htmlFor = input.id; }
  return h("div", { class: "field" }, lbl, input, hint && h("div", { class: "hint" }, hint));
};

// ============================================================================
// Hintergrundaufgaben (Jobs)
// ============================================================================
function trackJob(id, title, onDone) {
  const job = { id, title, lines: [], state: "running", since: 0, open: false };
  state.jobs.push(job); renderTray();
  const tick = async () => {
    try {
      const d = await api(`/jobs/${id}?since=${job.since}`);
      job.lines.push(...d.lines); job.since = d.total; job.state = d.state; job.error = d.error; job.result = d.result;
      renderTray();
      if (d.state === "running") return setTimeout(tick, 1000);
      await refresh(true);
      if (d.state === "done") { toast(`${title}: fertig`); setTimeout(() => dismissJob(job), 5000); } else { toast(`${title}: ${d.error}`, "error"); job.open = true; renderTray(); }
      onDone && onDone(d);
    } catch (e) { job.state = "error"; job.error = e.message; renderTray(); }
  };
  tick();
}
function dismissJob(job) { state.jobs = state.jobs.filter(j => j !== job); renderTray(); }
function renderTray() {
  let tray = $("#tray"); if (!tray) { tray = h("div", { id: "tray", class: "tray" }); document.body.append(tray); }
  tray.replaceChildren(...state.jobs.map(j => {
    const last = j.lines[j.lines.length - 1] || "Wird gestartet …";
    const log = j.open && h("div", { class: "job-log" }, j.lines.join("\n"));
    if (log) setTimeout(() => (log.scrollTop = log.scrollHeight));
    return h("div", { class: "job " + (j.state === "error" ? "error" : "") },
      h("div", { class: "job-head", onclick: () => { j.open = !j.open; renderTray(); } },
        j.state === "running" ? h("div", { class: "spinner" }) : icon(j.state === "done" ? "check" : "alert", ""),
        h("div", { class: "grow" }, h("div", { class: "t" }, j.title), h("div", { class: "small muted", style: "white-space:nowrap;overflow:hidden;text-overflow:ellipsis" }, j.error || last)),
        j.state !== "running" && iconBtn("x", "Schließen", e => { e.stopPropagation(); dismissJob(j); }, "sm")),
      j.state === "running" && h("div", { class: "bar" }, h("i")), log);
  }));
}
const run = (path, title, opts = {}) => api(path, { method: "POST", ...opts }).then(r => trackJob(r.job, title)).catch(fail);

// ============================================================================
// Routing & Shell
// ============================================================================
const route = () => {
  const p = location.hash.replace(/^#\/?/, "").split("/").map(decodeURIComponent);
  if (p[0] === "server" && p[1]) return { view: "server", id: p[1], tab: p[2] || "overview" };
  if (p[0] === "users") return { view: "users" };
  return { view: "home" };
};
const go = path => { location.hash = "#/" + path; };
let shell = null, cleanup = null, pageSig = null;

function sessionLost() { state.user = null; state.ready = true; shell = null; render(); }

function render() {
  const app = $("#app");
  if (!state.ready) return app.replaceChildren();
  if (!state.user) { stopPolling(); return app.replaceChildren(loginView()); }
  if (!shell) buildShell();
  renderSide(); renderTop(); renderPage();
}

function buildShell() {
  const root = h("div", { class: "shell" });
  shell = { root, side: h("aside", { class: "side" }), top: h("header", { class: "topbar" }), page: h("main", { class: "page", id: "page" }) };
  add(root, shell.side, h("div", { class: "scrim", onclick: () => root.classList.remove("open") }), h("div", { class: "main-col" }, shell.top, shell.page));
  $("#app").replaceChildren(root);
}

function renderSide() {
  const r = route(), nav = (label, ic, path, active, extra) => h("button", { class: "nav" + (active ? " active" : ""), onclick: () => { shell.root.classList.remove("open"); go(path); } },
    ic === "dot" ? h("span", { class: "dot " + (extra?.busy ? "busy" : extra?.state || "") }) : icon(ic), h("span", { class: "grow" }, label));
  shell.side.replaceChildren();
  add(shell.side,
    h("div", { class: "brandbar" }, h("div", { class: "logo" }, icon("package", "lg")), "Game Server"),
    nav("Übersicht", "home", "", r.view === "home"),
    h("div", { class: "nav-label" }, "Server"),
    ...state.instances.map(i => nav(i.name, "dot", `server/${i.id}`, r.view === "server" && r.id === i.id, i)),
    !state.instances.length && h("p", { class: "small faint", style: "padding:4px 10px" }, isAdmin() ? "Noch keine Server." : "Dir ist noch kein Server zugewiesen."),
    isAdmin() && [h("div", { class: "nav-label" }, "Verwaltung"), nav("Benutzer & Protokoll", "users", "users", r.view === "users")],
    h("div", { class: "side-foot" },
      state.system?.disk_free_gb != null && h("div", { class: "row nowrap" }, icon("hdd", "sm"), `${state.system.disk_free_gb} GB frei`),
      state.system && h("div", { class: "row nowrap" }, icon("activity", "sm"), `Runtime: ${state.system.runtime}`, !state.system.runtime_ok && chip("Fehler", "danger"))));
}

function renderTop() {
  const r = route(), inst = r.view === "server" ? findInst(r.id) : null;
  const crumbs = h("div", { class: "crumbs" },
    r.view === "home" && "Übersicht", r.view === "users" && "Benutzer & Protokoll",
    r.view === "server" && [h("a", { href: "#/" }, "Server"), h("span", { class: "sep" }, "/"), inst?.name || r.id]);
  const dark = document.documentElement.dataset.theme === "dark";
  const menuWrap = h("div", { class: "menu-wrap" });
  const closeMenu = () => $(".menu", menuWrap)?.remove();
  const toggleMenu = e => {
    e.stopPropagation(); if ($(".menu", menuWrap)) return closeMenu();
    const m = h("div", { class: "menu" },
      h("div", { class: "who" }, h("div", { style: "font-weight:650" }, state.user.username), h("div", { class: "small muted" }, isAdmin() ? "Administrator" : "Benutzer")), h("hr"),
      h("button", { class: "nav", onclick: () => { closeMenu(); accountDialog(); } }, icon("key"), "Passwort ändern"),
      h("button", { class: "nav", onclick: logout }, icon("logout"), "Abmelden"));
    menuWrap.append(m); setTimeout(() => document.addEventListener("click", closeMenu, { once: true }));
  };
  add(menuWrap, h("button", { class: "btn ghost", style: "padding:0 6px 0 4px", onclick: toggleMenu, "aria-label": "Konto" }, avatar(state.user.username), icon("chevron", "sm")));
  shell.top.replaceChildren(
    h("button", { class: "btn icon ghost menu-btn", "aria-label": "Menü", onclick: () => shell.root.classList.toggle("open") }, icon("menu")),
    h("div", { class: "grow" }, crumbs),
    h("button", { class: "btn icon ghost", title: dark ? "Helles Design" : "Dunkles Design", "aria-label": "Design wechseln", onclick: () => { setTheme(dark ? "light" : "dark"); renderTop(); } }, icon(dark ? "sun" : "moon")),
    menuWrap);
}

function setTheme(t) { document.documentElement.dataset.theme = t; store("gsm_theme", t); }
async function logout() { await api("/logout", { method: "POST" }).catch(() => {}); sessionLost(); }

function renderPage() {
  const r = route(), inst = r.view === "server" ? findInst(r.id) : null;
  const sig = JSON.stringify([r, inst && [inst.state, inst.busy, inst.name, inst.permission, inst.port, inst.memory, inst.auto_start, inst.backup, inst.version], r.view === "home" && state.instances.map(i => [i.id, i.state, i.busy, i.name, i.version])]);
  if (sig === pageSig) return;
  pageSig = sig;
  if (cleanup) { cleanup(); cleanup = null; }
  let view;
  if (r.view === "home") view = homeView();
  else if (r.view === "users") view = isAdmin() ? usersView() : h("div", { class: "empty" }, "Kein Zugriff");
  else view = inst ? serverView(inst, r.tab) : notFoundView();
  cleanup = view.cleanup || null;
  shell.page.replaceChildren(view.el || view);
  window.scrollTo(0, 0);
}
const notFoundView = () => h("div", { class: "empty" }, h("div", { class: "big" }, icon("server", "lg")), h("h3", {}, "Server nicht gefunden"), h("p", {}, "Er existiert nicht oder du hast keinen Zugriff."), h("p", { style: "margin-top:14px" }, btn("Zur Übersicht", { onclick: () => go("") })));

// ============================================================================
// Login
// ============================================================================
function loginView() {
  const err = h("div", { class: "err hidden" });
  const user = h("input", { class: "input", placeholder: "Benutzername", autocomplete: "username", autofocus: true });
  const pw = h("input", { class: "input", type: "password", placeholder: "Passwort", autocomplete: "current-password" });
  const submitBtn = btn("Anmelden", { cls: "primary block", onclick: () => submit() });
  const submit = async () => {
    submitBtn.disabled = true; err.classList.add("hidden");
    try { state.user = await api("/login", { method: "POST", json: { username: user.value, password: pw.value } }); await boot(); }
    catch (e) { err.textContent = e.message; err.classList.remove("hidden"); pw.select(); }
    finally { submitBtn.disabled = false; }
  };
  for (const el of [user, pw]) el.addEventListener("keydown", e => e.key === "Enter" && submit());
  return h("div", { class: "login-wrap" }, h("div", { class: "card login stack" },
    h("div", {}, h("div", { class: "logo" }, icon("package", "lg")), h("h1", {}, "Game Server Manager"), h("p", { class: "muted", style: "margin-top:4px" }, "Melde dich an, um deine Server zu verwalten.")),
    field("Benutzername", user), field("Passwort", pw), err, submitBtn));
}

// ============================================================================
// Übersicht (Dashboard)
// ============================================================================
function homeView() {
  const list = state.instances, running = list.filter(i => i.state === "running").length;
  const head = h("div", { class: "page-head" }, h("div", {}, h("h1", {}, "Deine Server"), h("p", { class: "muted", style: "margin-top:4px" }, "Alle Server auf einen Blick.")),
    isAdmin() && h("div", { class: "row" }, btn("Modpack importieren", { icon: "upload", onclick: importDialog }), btn("Neuer Server", { cls: "primary", icon: "plus", onclick: createDialog })));
  const stat = (k, v, ic) => h("div", { class: "card stat" }, h("div", { class: "k" }, k), h("div", { class: "v" }, ic && icon(ic, "lg"), v));
  const stats = h("div", { class: "stats", style: "margin-bottom:22px" }, stat("Server", String(list.length), "server"), stat("Laufen", `${running} von ${list.length}`, "activity"),
    state.system?.disk_free_gb != null && stat("Freier Speicher", `${state.system.disk_free_gb} GB`, "hdd"));
  const body = list.length ? h("div", { class: "cards" }, list.map(serverCard)) : h("div", { class: "card empty" }, h("div", { class: "big" }, icon("server", "lg")),
    h("h3", {}, isAdmin() ? "Noch kein Server vorhanden" : "Dir ist noch kein Server zugewiesen"),
    h("p", {}, isAdmin() ? "Erstelle deinen ersten Minecraft-Server oder importiere ein Modpack." : "Bitte einen Administrator, dir Zugriff zu geben."),
    isAdmin() && h("p", { class: "row", style: "justify-content:center;margin-top:16px" }, btn("Neuer Server", { cls: "primary", icon: "plus", onclick: createDialog }), btn("Modpack importieren", { onclick: importDialog })));
  return h("div", {}, head, list.length ? stats : null, body);
}

function serverCard(i) {
  const running = i.state === "running", busy = !!i.busy;
  return h("div", { class: "card hover srv", onclick: () => go(`server/${i.id}`) },
    h("div", { class: "row nowrap" }, kindBadge(i.kind), h("div", { class: "grow" }, h("h3", {}, i.name), h("div", { class: "small muted" }, `Minecraft ${i.version}`)),
      statusLabel(i)),
    h("div", { class: "chips" }, chip(i.kind, "info"), i.loader_version && chip(`Loader ${i.loader_version}`), chip(`:${i.port}`, "", "server"), chip(i.memory, "", "hdd")),
    h("div", { class: "srv-foot", onclick: e => e.stopPropagation() },
      running ? btn("Stoppen", { small: true, cls: "sm", icon: "stop", disabled: busy || !can(i, "operator"), onclick: () => run(`/instances/${i.id}/stop`, `${i.name} stoppen`) })
        : btn("Starten", { cls: "sm primary", icon: "play", disabled: busy || !can(i, "operator"), onclick: () => run(`/instances/${i.id}/start`, `${i.name} starten`) }),
      h("span", { class: "small faint" }, ago(i.created) && `erstellt ${ago(i.created)}`)));
}
const statusLabel = i => h("span", { class: "status" }, h("span", { class: "dot " + (i.busy ? "busy" : i.state) }), i.busy || (i.state === "running" ? "Läuft" : "Gestoppt"));

// ============================================================================
// Server-Detailseite
// ============================================================================
function serverView(inst, tab) {
  const running = inst.state === "running", busy = !!inst.busy;
  const tabs = [["overview", "Übersicht", "activity"], ["console", "Konsole", "terminal"], ["addons", inst.kind === "paper" ? "Plugins" : "Mods", "package"], ["backups", "Backups", "archive"]];
  if (can(inst, "manager")) tabs.push(["settings", "Einstellungen", "sliders"]);
  if (!tabs.some(t => t[0] === tab)) tab = "overview";
  const tabViews = { overview: overviewTab, console: consoleTab, addons: addonsTab, backups: backupsTab, settings: settingsTab };
  const content = h("div", { style: "margin-top:22px" });
  const sub = tabViews[tab](inst, content);
  add(content, sub.el || sub);
  const head = h("div", { class: "page-head", style: "margin-bottom:18px" },
    h("div", { class: "row nowrap" }, iconBtn("arrow", "Zurück", () => go("")), kindBadge(inst.kind, 46),
      h("div", {}, h("h1", {}, inst.name), h("div", { class: "row", style: "gap:8px;margin-top:4px" }, statusLabel(inst), chip(`${inst.kind} ${inst.version}`, "info")))),
    h("div", { class: "row" },
      running && btn("Neustart", { icon: "refresh", disabled: busy || !can(inst, "operator"), onclick: () => run(`/instances/${inst.id}/restart`, `${inst.name} neu starten`) }),
      running ? btn("Stoppen", { icon: "stop", disabled: busy || !can(inst, "operator"), onclick: () => run(`/instances/${inst.id}/stop`, `${inst.name} stoppen`) })
        : btn("Starten", { cls: "primary", icon: "play", disabled: busy || !can(inst, "operator"), onclick: () => run(`/instances/${inst.id}/start`, `${inst.name} starten`) })));
  const seg = h("div", { class: "seg" }, tabs.map(([id, label, ic]) => h("button", { class: id === tab ? "active" : "", onclick: () => go(`server/${inst.id}/${id}`) }, icon(ic, "sm"), label)));
  return { el: h("div", {}, head, seg, content), cleanup: sub.cleanup };
}

function overviewTab(inst) {
  const running = inst.state === "running";
  const address = `${location.hostname}:${inst.port}`;
  const stat = (k, v, extra) => h("div", { class: "card stat" }, h("div", { class: "k" }, k), h("div", { class: "v" }, v, extra));
  return h("div", { class: "stack" },
    h("div", { class: "stats" },
      stat("Status", statusLabel(inst)),
      stat("Adresse", h("span", { class: "mono", style: "font-size:15px;white-space:nowrap" }, address), iconBtn("copy", "Adresse kopieren", () => copyText(address), "sm")),
      stat("Arbeitsspeicher", inst.memory), stat("Java", inst.java_major ? `Java ${inst.java_major}` : "–"),
      stat("Minecraft", inst.version), stat("Typ", inst.loader_version ? `${inst.kind} ${inst.loader_version}` : inst.kind),
      stat("Autostart", inst.auto_start ? "An" : "Aus"), stat("Erstellt", h("span", { style: "font-size:16px" }, fullDate(inst.created)))),
    h("div", { class: "card pad row spread" }, h("div", {}, h("h3", {}, "Deine Berechtigung: " + (isAdmin() ? "Administrator" : PERM[inst.permission])),
      h("p", { class: "muted small", style: "margin-top:3px" }, can(inst, "manager") ? "Du darfst diesen Server vollständig verwalten." : can(inst, "operator") ? "Du darfst den Server bedienen (starten, stoppen, Konsole, Backups erstellen)." : "Du darfst den Server ansehen und die Konsole lesen.")),
      running && can(inst, "operator") && btn("Beenden erzwingen", { cls: "danger", icon: "power", onclick: async () => {
        if (await confirmBox("Prozess hart beenden?", "Ungespeicherte Änderungen der Welt können verloren gehen. Nutze das nur, wenn der Server nicht mehr reagiert.", { confirmText: "Erzwingen", danger: true }))
          api(`/instances/${inst.id}/kill`, { method: "POST" }).then(() => refresh(true)).catch(fail);
      } })));
}

// --- Konsole -------------------------------------------------------------------
function consoleTab(inst) {
  const out = h("div", { class: "term-out", tabindex: 0, "aria-label": "Server-Ausgabe" });
  const status = h("span", {}, "verbinde …");
  let follow = true, ws = null, closed = false, retry = 1000;
  const history = [], histKey = `gsm_hist_${inst.id}`;
  try { history.push(...JSON.parse(store(histKey) || "[]")); } catch { /* ignorieren */ }
  let hpos = history.length;
  const LINE = /^\[([\d:]{8})\] \[([^\]]*)\/(INFO|WARN|ERROR|DEBUG|FATAL)\](.*)$/;
  const addLine = text => {
    const m = LINE.exec(text), el = h("span", { class: "l " + (m ? m[3] : "") });
    if (m) add(el, h("span", { class: "t" }, `${m[1]} `), m[4].replace(/^:\s?/, "")); else el.textContent = text;
    out.append(el); while (out.childElementCount > 1500) out.firstChild.remove();
    if (follow) out.scrollTop = out.scrollHeight;
  };
  out.addEventListener("scroll", () => { follow = out.scrollTop + out.clientHeight >= out.scrollHeight - 40; followBtn.classList.toggle("hidden", follow); });
  const followBtn = btn("Zum Ende", { cls: "sm hidden", icon: "chevron", onclick: () => { out.scrollTop = out.scrollHeight; } });
  const connect = () => {
    ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/api/instances/${encodeURIComponent(inst.id)}/console`);
    ws.onopen = () => { status.textContent = inst.state === "running" ? "verbunden" : "verbunden – Server gestoppt, zeigt letzte Ausgabe"; retry = 1000; };
    ws.onmessage = e => addLine(e.data);
    ws.onclose = () => { status.textContent = "getrennt – verbinde neu …"; if (!closed) setTimeout(connect, retry = Math.min(retry * 2, 15000)); };
  };
  connect();
  const send = text => {
    if (!text.trim() || ws?.readyState !== 1) return;
    ws.send(text); addLine(`> ${text}`); out.lastChild.classList.add("cmd");
    history.push(text); history.splice(0, history.length - 50); store(histKey, JSON.stringify(history)); hpos = history.length;
  };
  const input = h("input", { placeholder: "Befehl eingeben, z. B. list", autocomplete: "off", spellcheck: "false", "aria-label": "Konsolenbefehl" });
  input.addEventListener("keydown", e => {
    if (e.key === "Enter") { send(input.value); input.value = ""; }
    else if (e.key === "ArrowUp") { e.preventDefault(); hpos = Math.max(0, hpos - 1); input.value = history[hpos] || ""; }
    else if (e.key === "ArrowDown") { e.preventDefault(); hpos = Math.min(history.length, hpos + 1); input.value = history[hpos] || ""; }
  });
  const operator = can(inst, "operator");
  const quick = ["list", "save-all", "whitelist list", "difficulty", "time set day", "weather clear"].map(c => h("button", { type: "button", onclick: () => send(c) }, c));
  const el = h("div", { class: "term" },
    h("div", { class: "term-bar" }, h("span", { class: "dots" }, h("i"), h("i"), h("i")), h("span", { class: "grow mono" }, `${inst.name} – Konsole`), status, followBtn,
      h("button", { class: "term-link", onclick: () => out.replaceChildren(), title: "Ausgabe leeren" }, "leeren")),
    out,
    operator ? h("div", { class: "term-in" }, h("span", {}, "›"), input) : h("div", { class: "term-bar", style: "border-top:1px solid #1c2233;border-bottom:0" }, "Du darfst die Konsole nur lesen."),
    operator && h("div", { class: "quick" }, quick));
  if (operator) setTimeout(() => input.focus());
  return { el, cleanup: () => { closed = true; ws && ws.close(); } };
}

// --- Mods / Plugins --------------------------------------------------------------
function addonsTab(inst) {
  const label = inst.kind === "paper" ? "Plugins" : "Mods";
  if (inst.kind === "vanilla") return h("div", { class: "card empty" }, h("div", { class: "big" }, icon("package", "lg")), h("h3", {}, "Vanilla unterstützt keine Mods"),
    h("p", {}, "Lege einen Fabric-, Forge-, NeoForge- oder Paper-Server an, um Mods oder Plugins zu nutzen."));
  const manager = can(inst, "manager");
  const box = h("div"), listBox = h("div"), discover = h("div");
  let sub = "installed";

  const loadList = async () => {
    listBox.replaceChildren(h("div", { class: "card pad" }, h("div", { class: "skeleton", style: "height:42px" })));
    try {
      const items = await api(`/instances/${inst.id}/addons`);
      const rows = items.length ? items.map(m => h("div", { class: "item" },
        h("div", { class: "thumb" }, icon("file")),
        h("div", { class: "grow" }, h("div", { class: "title" }, m.title, m.version && chip(m.version, "", null)), h("div", { class: "meta" }, `${m.file} · ${fmtSize(m.size)}`)),
        manager && h("label", { class: "switch", title: m.enabled ? "Deaktivieren" : "Aktivieren" }, h("input", { type: "checkbox", checked: m.enabled, "aria-label": `${m.title} aktiv`, onchange: async e => {
          try { await api(`/instances/${inst.id}/addons/${encodeURIComponent(m.file)}`, { method: "PATCH", json: { enabled: e.target.checked } }); toast(`${m.title} ${e.target.checked ? "aktiviert" : "deaktiviert"} – gilt nach Neustart`); loadList(); } catch (err) { fail(err); loadList(); } } }), h("span")),
        manager && iconBtn("trash", "Löschen", async () => { if (await confirmBox(`${m.title} löschen?`, m.file, { confirmText: "Löschen", danger: true })) { try { await api(`/instances/${inst.id}/addons/${encodeURIComponent(m.file)}`, { method: "DELETE" }); loadList(); } catch (err) { fail(err); } } }, "danger"))) : null;
      listBox.replaceChildren(h("div", { class: "card" }, rows ? h("div", { class: "list" }, rows)
        : h("div", { class: "empty" }, h("div", { class: "big" }, icon("package", "lg")), h("h3", {}, `Noch keine ${label}`), h("p", {}, manager ? "Suche auf Modrinth oder lade eigene .jar-Dateien hoch." : ""))));
    } catch (e) { listBox.replaceChildren(h("div", { class: "err" }, e.message)); }
  };

  const upload = async files => {
    const jars = [...files].filter(f => f.name.endsWith(".jar")); if (!jars.length) return toast("Nur .jar-Dateien möglich", "error");
    const form = new FormData(); jars.forEach(f => form.append("files", f));
    try { const r = await api(`/instances/${inst.id}/addons`, { method: "POST", form }); toast(`${r.saved.length} Datei(en) hochgeladen`); loadList(); } catch (e) { fail(e); }
  };
  const fileInput = h("input", { type: "file", multiple: true, accept: ".jar", class: "hidden", onchange: () => { upload(fileInput.files); fileInput.value = ""; } });
  const drop = h("div", { class: "drop", tabindex: 0, role: "button", onclick: () => fileInput.click(), onkeydown: e => e.key === "Enter" && fileInput.click() },
    icon("upload", "lg"), h("div", { style: "font-weight:600;margin-top:6px" }, ".jar-Dateien hierher ziehen oder klicken"), h("div", { class: "small" }, `Eigene ${label} direkt auf den Server laden`));
  ["dragover", "dragenter"].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.add("over"); }));
  ["dragleave", "drop"].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.remove("over"); }));
  drop.addEventListener("drop", e => upload(e.dataTransfer.files));

  // Modrinth-Suche
  let offset = 0;
  const q = h("input", { class: "input", placeholder: `${label} auf Modrinth suchen …`, "aria-label": "Suche" });
  const results = h("div", { class: "results" }), more = h("p", { class: "row", style: "justify-content:center;margin-top:14px" });
  const search = async (reset = true) => {
    if (reset) { offset = 0; results.replaceChildren(h("div", { class: "card result" }, h("div", { class: "skeleton", style: "width:100%;height:46px" }))); }
    try {
      const r = await api(`/instances/${inst.id}/catalog?q=${encodeURIComponent(q.value)}&offset=${offset}`);
      if (reset) results.replaceChildren();
      add(results, r.hits.map(m => h("div", { class: "card result" },
        m.icon ? h("img", { class: "thumb", src: m.icon, alt: "", loading: "lazy" }) : h("div", { class: "thumb" }, icon("package")),
        h("div", { class: "grow" }, h("div", { style: "font-weight:650" }, m.title), h("div", { class: "small faint" }, `von ${m.author} · ${fmtNum(m.downloads)} Downloads`), h("p", {}, m.description)),
        btn("Installieren", { cls: "sm soft", onclick: e => { e.currentTarget.disabled = true; api(`/instances/${inst.id}/catalog`, { method: "POST", json: { project: m.id } }).then(j => trackJob(j.job, `${m.title} installieren`, () => loadList())).catch(err => { fail(err); e.target.disabled = false; }); } }))));
      if (!r.hits.length && reset) results.replaceChildren(h("div", { class: "empty", style: "grid-column:1/-1" }, `Keine Treffer für ${inst.kind} ${inst.version}.`));
      offset += r.hits.length;
      more.replaceChildren(offset < r.total ? btn("Mehr laden", { onclick: () => search(false) }) : h("span", { class: "small faint" }, `${r.total} Treffer für ${inst.kind} ${inst.version}`));
    } catch (e) { results.replaceChildren(h("div", { class: "err", style: "grid-column:1/-1" }, e.message)); }
  };
  q.addEventListener("keydown", e => e.key === "Enter" && search());
  add(discover, h("div", { class: "row nowrap", style: "margin-bottom:16px" }, q, btn("Suchen", { cls: "primary", icon: "search", onclick: () => search() })),
    h("p", { class: "hint", style: "margin-bottom:14px" }, "Zeigt nur Projekte, die auf dem Server laufen. Abhängigkeiten werden automatisch mitinstalliert."), results, more);
  let discovered = false;

  const show = which => {
    sub = which; box.replaceChildren();
    if (which === "installed") add(box, h("div", { class: "stack" }, manager && drop, fileInput, listBox));
    else { add(box, discover); if (!discovered) { discovered = true; search(); } }
    segEl?.querySelectorAll("button").forEach(b => b.classList.toggle("active", b.dataset.k === which));
  };
  const segEl = manager ? h("div", { class: "seg", style: "margin-bottom:16px" }, h("button", { "data-k": "installed", onclick: () => show("installed") }, icon("package", "sm"), "Installiert"),
    h("button", { "data-k": "discover", onclick: () => show("discover") }, icon("search", "sm"), "Auf Modrinth entdecken")) : null;
  const wrap = h("div", {}, segEl, box);
  show("installed"); loadList();
  return wrap;
}

// --- Backups ------------------------------------------------------------------------
function backupsTab(inst) {
  const listBox = h("div");
  const load = async () => {
    try {
      const items = await api(`/instances/${inst.id}/backups`);
      listBox.replaceChildren(h("div", { class: "card" }, items.length ? h("div", { class: "list" }, items.map(i => h("div", { class: "item" },
        h("div", { class: "thumb" }, icon("archive")),
        h("div", { class: "grow" }, h("div", { class: "title", style: "word-break:break-all" }, fullDate(i.created), " ", chip(i.scope === "world" ? "Nur Welten" : "Komplett", i.scope === "world" ? "info" : "brand")),
          h("div", { class: "meta" }, `${ago(i.created)} · ${fmtSize(i.size)} · ${i.name}`)),
        can(inst, "manager") && h("div", { class: "row nowrap" },
          h("a", { href: `/api/instances/${inst.id}/backups/${i.name}/download`, download: i.name }, btn("", { cls: "icon sm ghost", icon: "download", title: "Herunterladen", small: true })),
          btn("Wiederherstellen", { cls: "sm", icon: "refresh", disabled: inst.state === "running", title: inst.state === "running" ? "Server zuerst stoppen" : "", onclick: async () => {
            if (await confirmBox("Backup wiederherstellen?", `Der Server wird auf den Stand vom ${fullDate(i.created)} zurückgesetzt. Der aktuelle Stand wird vorher automatisch gesichert.`, { confirmText: "Wiederherstellen" }))
              run(`/instances/${inst.id}/backups/${i.name}/restore`, "Backup wiederherstellen");
          } }),
          iconBtn("trash", "Löschen", async () => { if (await confirmBox("Backup löschen?", i.name, { confirmText: "Löschen", danger: true })) { try { await api(`/instances/${inst.id}/backups/${i.name}`, { method: "DELETE" }); load(); } catch (e) { fail(e); } } }, "danger sm")))))
        : h("div", { class: "empty" }, h("div", { class: "big" }, icon("archive", "lg")), h("h3", {}, "Noch keine Backups"), h("p", {}, "Sichere deinen Server manuell oder richte automatische Backups ein."))));
    } catch (e) { listBox.replaceChildren(h("div", { class: "err" }, e.message)); }
  };
  const parts = [h("div", { class: "row spread" }, h("h3", {}, "Gesicherte Stände"),
    can(inst, "operator") && btn("Jetzt sichern", { cls: "primary", icon: "archive", onclick: () => run(`/instances/${inst.id}/backups`, "Backup erstellen").then(() => setTimeout(load, 4000)) })), listBox];
  if (can(inst, "manager")) {
    const b = inst.backup;
    const en = h("input", { type: "checkbox", checked: b.enabled }), iv = h("input", { class: "input", type: "number", min: 1, value: b.interval_hours }), keep = h("input", { class: "input", type: "number", min: 1, value: b.keep });
    const scope = h("select", { class: "select" }, h("option", { value: "full", selected: b.scope === "full" }, "Kompletter Server"), h("option", { value: "world", selected: b.scope === "world" }, "Nur Welten + Einstellungen"));
    parts.push(h("div", { class: "card pad stack" },
      h("div", { class: "row spread" }, h("div", {}, h("h3", {}, "Automatische Backups"), h("p", { class: "muted small", style: "margin-top:3px" }, "Läuft der Server, wird die Welt vorher gespeichert.")), h("label", { class: "switch" }, en, h("span"))),
      h("div", { class: "grid3" }, field("Alle … Stunden", iv), field("Aufbewahren (Anzahl)", keep), field("Umfang", scope)),
      h("div", {}, btn("Speichern", { cls: "primary", onclick: async () => { try { await api(`/instances/${inst.id}`, { method: "PATCH", json: { backup: { enabled: en.checked, interval_hours: +iv.value, keep: +keep.value, scope: scope.value } } }); toast("Backup-Zeitplan gespeichert"); await refresh(true); } catch (e) { fail(e); } } }))));
  }
  load();
  return h("div", { class: "stack" }, parts);
}

// --- Einstellungen --------------------------------------------------------------------
function settingsTab(inst) {
  const running = inst.state === "running";
  const mem = h("input", { class: "input", value: inst.memory }), port = h("input", { class: "input", type: "number", value: inst.port });
  const auto = h("input", { type: "checkbox", checked: inst.auto_start });
  const memChips = h("div", { class: "mem-chips" }, ["1G", "2G", "4G", "6G", "8G", "12G"].map(v => h("button", { type: "button", onclick: () => (mem.value = v) }, v)));
  const cards = [h("div", { class: "card pad stack" }, h("h3", {}, "Server-Einstellungen"),
    h("div", { class: "grid2" }, h("div", {}, field("Arbeitsspeicher", mem), memChips), field("Port", port, "Muss in Firewall/Router freigegeben sein")),
    h("label", { class: "check" }, auto, h("span", {}, h("b", {}, "Automatisch starten"), h("div", { class: "small muted" }, "Startet den Server, wenn der Manager startet."))),
    running && h("div", { class: "chip warn" }, icon("alert", "sm"), "Änderungen gelten nach dem nächsten Neustart des Servers"),
    h("div", {}, btn("Speichern", { cls: "primary", onclick: async () => { try { await api(`/instances/${inst.id}`, { method: "PATCH", json: { memory: mem.value, port: +port.value, auto_start: auto.checked } }); toast("Gespeichert"); await refresh(true); } catch (e) { fail(e); } } })))];
  if (isAdmin()) cards.push(h("div", { class: "card pad row spread", style: "border-color:color-mix(in srgb,var(--danger) 35%,var(--border))" },
    h("div", {}, h("h3", {}, "Server löschen"), h("p", { class: "muted small", style: "margin-top:3px" }, "Entfernt den Server samt Welt. Das lässt sich nicht rückgängig machen.")),
    btn("Server löschen", { cls: "danger", icon: "trash", disabled: running || !!inst.busy, title: running ? "Server zuerst stoppen" : "", onclick: () => deleteDialog(inst) })));
  return h("div", { class: "stack" }, cards);
}
function deleteDialog(inst) {
  const keep = h("input", { type: "checkbox", checked: true });
  const name = h("input", { class: "input", placeholder: inst.name });
  const go_ = btn("Endgültig löschen", { cls: "danger solid", disabled: true, onclick: () => api(`/instances/${inst.id}`, { method: "DELETE", json: { delete_backups: !keep.checked } }).then(r => { m.close(); go(""); trackJob(r.job, `${inst.name} löschen`); }).catch(fail) });
  name.addEventListener("input", () => (go_.disabled = name.value !== inst.name));
  const m = modal({ title: `„${inst.name}“ löschen?`, width: 480, body: [h("p", { class: "muted" }, "Welt, Mods und Einstellungen werden unwiderruflich gelöscht."),
    field(`Zur Bestätigung den Servernamen eingeben`, name), h("label", { class: "check" }, keep, h("span", {}, "Backups dieses Servers behalten"))], buttons: [go_] });
}

// ============================================================================
// Server erstellen / Modpack importieren
// ============================================================================
function memoryField(initial) {
  const mem = h("input", { class: "input", value: initial });
  return { input: mem, el: h("div", {}, field("Arbeitsspeicher", mem), h("div", { class: "mem-chips" }, ["2G", "4G", "6G", "8G", "12G"].map(v => h("button", { type: "button", onclick: () => (mem.value = v) }, v)))) };
}
const termsField = game => { const cb = h("input", { type: "checkbox" }); return { input: cb, el: h("label", { class: "check" }, cb, h("span", {}, "Ich akzeptiere die ", h("a", { href: game.terms.url, target: "_blank", rel: "noopener" }, game.terms.label), ".")) }; };

function createDialog() {
  const game = state.games[0]; if (!game) return;
  let kind = "vanilla";
  const name = h("input", { class: "input", placeholder: "z. B. survival", autofocus: true });
  const version = h("select", { class: "select" }), all = h("input", { type: "checkbox" });
  const port = h("input", { class: "input", type: "number", value: game.defaults.port });
  const mem = memoryField(game.defaults.memory), terms = termsField(game);
  const kindsEl = h("div", { class: "kinds" });
  const loadVersions = async () => {
    version.replaceChildren(h("option", {}, "lädt …")); version.disabled = true;
    try { const v = await api(`/games/${game.id}/versions?kind=${kind}&all=${all.checked ? 1 : 0}`); version.replaceChildren(...v.map((x, i) => h("option", { value: x }, i === 0 ? `${x} (neueste)` : x))); }
    catch (e) { version.replaceChildren(h("option", {}, e.message)); } finally { version.disabled = false; }
  };
  const drawKinds = () => kindsEl.replaceChildren(...game.kinds.map(k => h("button", { type: "button", class: "kind" + (k.id === kind ? " sel" : ""), onclick: () => { kind = k.id; drawKinds(); loadVersions(); } },
    kindBadge(k.id, 32), h("b", {}, k.label.replace(/ \(.*\)/, "")), h("span", {}, (KINDS[k.id] || {}).desc || ""))));
  drawKinds(); all.addEventListener("change", loadVersions); loadVersions();
  const create = btn("Server erstellen", { cls: "primary", icon: "plus", onclick: () => {
    if (!name.value.trim()) return toast("Bitte einen Namen eingeben", "error");
    api("/instances", { method: "POST", json: { name: name.value, game: game.id, kind, version: version.value, memory: mem.input.value, port: +port.value, accept_terms: terms.input.checked } })
      .then(r => { m.close(); trackJob(r.job, `Server „${name.value}“ erstellen`, res => res.state === "done" && go(`server/${res.result}`)); }).catch(fail);
  } });
  const m = modal({ title: "Neuer Minecraft-Server", subtitle: "Wähle den Server-Typ und die Version.", width: 760,
    body: [kindsEl, h("div", { class: "grid2" }, field("Name", name), h("div", {}, field("Minecraft-Version", version), h("label", { class: "check hint", style: "margin-top:8px" }, all, "auch Snapshots / alte Betas"))),
      h("div", { class: "grid2" }, mem.el, field("Port", port)), terms.el], buttons: [create] });
}

function importDialog() {
  const game = state.games[0]; if (!game) return;
  let mode = "modrinth", picked = null;
  const q = h("input", { class: "input", placeholder: "Modpacks auf Modrinth suchen …" }), results = h("div", { class: "list card", style: "max-height:260px;overflow:auto" });
  const pickedEl = h("div", { class: "chip brand hidden" });
  const file = h("input", { class: "input", type: "file", accept: ".mrpack", style: "padding-top:6px" });
  const name = h("input", { class: "input", placeholder: "leer = Name des Modpacks" }), port = h("input", { class: "input", type: "number", value: game.defaults.port });
  const mem = memoryField("4G"), terms = termsField(game);
  const search = async () => {
    results.replaceChildren(h("div", { class: "item" }, h("div", { class: "spinner" }), "Suche …"));
    try {
      const r = await api(`/modpacks?q=${encodeURIComponent(q.value)}`);
      results.replaceChildren(...(r.hits.length ? r.hits.map(p => h("div", { class: "item", style: "cursor:pointer", onclick: () => { picked = p; pickedEl.replaceChildren(icon("check", "sm"), p.title); pickedEl.classList.remove("hidden"); } },
        p.icon ? h("img", { class: "thumb", src: p.icon, alt: "" }) : h("div", { class: "thumb" }, icon("package")),
        h("div", { class: "grow" }, h("div", { class: "title" }, p.title), h("div", { class: "meta" }, `${fmtNum(p.downloads)} Downloads`)), btn("Wählen", { cls: "sm" }))) : [h("div", { class: "empty" }, "Keine Treffer")]));
    } catch (e) { results.replaceChildren(h("div", { class: "err" }, e.message)); }
  };
  q.addEventListener("keydown", e => e.key === "Enter" && search());
  const panes = { modrinth: h("div", { class: "stack" }, h("div", { class: "row nowrap" }, q, btn("Suchen", { icon: "search", onclick: search })), results, pickedEl), file: h("div", { class: "stack" }, field(".mrpack-Datei", file, "Modrinth-Modpack (.mrpack), z. B. aus der Modrinth-App exportiert")) };
  const paneBox = h("div"), seg = h("div", { class: "seg" });
  const show = which => { mode = which; paneBox.replaceChildren(panes[which]); seg.querySelectorAll("button").forEach(b => b.classList.toggle("active", b.dataset.k === which)); };
  add(seg, h("button", { "data-k": "modrinth", onclick: () => show("modrinth") }, icon("search", "sm"), "Von Modrinth"), h("button", { "data-k": "file", onclick: () => show("file") }, icon("upload", "sm"), "Datei hochladen"));
  show("modrinth");
  const go_ = btn("Importieren", { cls: "primary", icon: "upload", onclick: () => {
    const form = new FormData(); form.append("name", name.value); form.append("memory", mem.input.value); form.append("port", port.value); form.append("accept_terms", terms.input.checked ? "1" : "0");
    if (mode === "file") { if (!file.files[0]) return toast("Bitte eine .mrpack-Datei wählen", "error"); form.append("file", file.files[0]); }
    else { if (!picked) return toast("Bitte ein Modpack wählen", "error"); form.append("modrinth", picked.slug); }
    api("/modpacks/import", { method: "POST", form }).then(r => { m.close(); trackJob(r.job, "Modpack importieren", res => res.state === "done" && go(`server/${res.result}`)); }).catch(fail);
  } });
  const m = modal({ title: "Modpack importieren", subtitle: "Legt aus einem Modrinth-Modpack einen neuen Server an. Client-only-Mods werden übersprungen.", width: 680,
    body: [seg, paneBox, h("div", { class: "grid2" }, field("Servername", name), field("Port", port)), mem.el, terms.el], buttons: [go_] });
}

// ============================================================================
// Benutzer & Protokoll
// ============================================================================
function usersView() {
  const box = h("div"), logBox = h("div");
  const load = async () => {
    try {
      const users = await api("/users");
      box.replaceChildren(h("div", { class: "table-wrap" }, h("table", { class: "t" }, h("thead", {}, h("tr", {}, h("th", {}, "Benutzer"), h("th", {}, "Rolle"), h("th", {}, "Serverrechte"), h("th"))),
        h("tbody", {}, users.map(u => h("tr", {}, h("td", {}, h("div", { class: "row nowrap" }, avatar(u.username), h("div", {}, h("b", {}, u.username), u.disabled && h("div", {}, chip("gesperrt", "danger"))))),
          h("td", {}, u.role === "admin" ? chip("Administrator", "brand", "shield") : chip("Benutzer")),
          h("td", {}, u.role === "admin" ? h("span", { class: "muted small" }, "alle Server") : Object.keys(u.servers).length ? h("div", { class: "row", style: "gap:6px" }, Object.entries(u.servers).map(([s, l]) => chip(`${s}: ${PERM[l]}`))) : h("span", { class: "faint small" }, "keine")),
          h("td", {}, h("div", { class: "row nowrap", style: "justify-content:flex-end" }, iconBtn("edit", "Bearbeiten", () => userDialog(u, load), "sm"),
            u.username.toLowerCase() !== state.user.username.toLowerCase() && iconBtn("trash", "Löschen", async () => { if (await confirmBox(`Benutzer „${u.username}“ löschen?`, "Der Zugang wird sofort entfernt.", { confirmText: "Löschen", danger: true })) { try { await api(`/users/${encodeURIComponent(u.username)}`, { method: "DELETE" }); load(); } catch (e) { fail(e); } } }, "danger sm")))))))));
    } catch (e) { box.replaceChildren(h("div", { class: "err" }, e.message)); }
  };
  const loadLog = async () => {
    try {
      const entries = await api("/audit?limit=100");
      logBox.replaceChildren(entries.length ? h("div", { class: "list" }, entries.map(e => h("div", { class: "item", style: "padding:10px 20px" }, avatar(e.user || "?"),
        h("div", { class: "grow" }, h("div", {}, h("b", {}, e.user), " ", h("span", { class: "mono small" }, e.action)), h("div", { class: "meta" }, `${fullDate(e.time)}${e.ip ? " · " + e.ip : ""}`)),
        e.status != null && chip(String(e.status), e.status >= 400 ? "danger" : "brand")))) : h("div", { class: "empty" }, "Noch keine Einträge"));
    } catch (e) { logBox.replaceChildren(h("div", { class: "err" }, e.message)); }
  };
  load(); loadLog();
  return h("div", { class: "stack" },
    h("div", { class: "page-head", style: "margin-bottom:0" }, h("div", {}, h("h1", {}, "Benutzer & Protokoll"), h("p", { class: "muted", style: "margin-top:4px" }, "Wer darf was auf welchem Server.")),
      btn("Benutzer hinzufügen", { cls: "primary", icon: "plus", onclick: () => userDialog(null, load) })),
    h("div", { class: "card" }, box),
    h("div", { class: "card pad small muted" }, h("b", { style: "color:var(--text)" }, "Rechte pro Server: "), "Ansehen = Konsole lesen · Bedienen = zusätzlich starten/stoppen, Befehle, Backup erstellen · Verwalten = zusätzlich Mods, Einstellungen, Backups wiederherstellen. Administratoren dürfen alles."),
    h("div", { class: "card" }, h("div", { class: "card-head" }, h("h3", {}, "Protokoll"), iconBtn("refresh", "Aktualisieren", loadLog, "sm")), logBox));
}

function userDialog(user, reload) {
  const name = h("input", { class: "input", value: user?.username || "", disabled: !!user, placeholder: "Benutzername" });
  const pw = h("input", { class: "input", type: "password", placeholder: user ? "leer lassen = unverändert" : "mind. 8 Zeichen", autocomplete: "new-password" });
  const role = h("select", { class: "select" }, h("option", { value: "user", selected: user?.role !== "admin" }, "Benutzer"), h("option", { value: "admin", selected: user?.role === "admin" }, "Administrator"));
  const blocked = h("input", { type: "checkbox", checked: !!user?.disabled });
  const perms = {};
  const permRows = state.instances.map(i => { const sel = h("select", { class: "select", style: "width:150px" }, h("option", { value: "" }, "kein Zugriff"), ...Object.entries(PERM).map(([k, v]) => h("option", { value: k, selected: user?.servers?.[i.id] === k }, v))); perms[i.id] = sel;
    return h("div", { class: "row spread" }, h("div", { class: "row nowrap" }, kindBadge(i.kind, 28), i.name), sel); });
  const permBox = h("div", { class: "stack", style: "gap:10px" }, h("div", { class: "label" }, "Rechte pro Server"), permRows.length ? permRows : h("p", { class: "muted small" }, "Noch keine Server vorhanden."));
  const sync = () => permBox.classList.toggle("hidden", role.value === "admin"); role.addEventListener("change", sync); sync();
  const save = btn("Speichern", { cls: "primary", onclick: async () => {
    const servers = Object.fromEntries(Object.entries(perms).filter(([, el]) => el.value).map(([id, el]) => [id, el.value]));
    try {
      if (user) await api(`/users/${encodeURIComponent(user.username)}`, { method: "PATCH", json: { role: role.value, servers, disabled: blocked.checked, ...(pw.value ? { password: pw.value } : {}) } });
      else await api("/users", { method: "POST", json: { username: name.value, password: pw.value, role: role.value, servers } });
      m.close(); toast("Benutzer gespeichert"); reload();
    } catch (e) { fail(e); }
  } });
  const m = modal({ title: user ? `Benutzer ${user.username}` : "Neuer Benutzer", width: 540,
    body: [field("Benutzername", name), field(user ? "Neues Passwort" : "Passwort", pw), field("Rolle", role), permBox, user && h("label", { class: "check" }, blocked, h("span", {}, h("b", {}, "Konto sperren"), h("div", { class: "small muted" }, "Der Benutzer wird sofort abgemeldet.")))], buttons: [save] });
}

function accountDialog() {
  const cur = h("input", { class: "input", type: "password", autocomplete: "current-password" }), next = h("input", { class: "input", type: "password", autocomplete: "new-password" });
  const save = btn("Passwort ändern", { cls: "primary", onclick: async () => { try { await api("/me/password", { method: "POST", json: { current: cur.value, new: next.value } }); m.close(); toast("Passwort geändert"); } catch (e) { fail(e); } } });
  const m = modal({ title: "Passwort ändern", width: 440, body: [field("Aktuelles Passwort", cur), field("Neues Passwort", next, "Mindestens 8 Zeichen")], buttons: [save] });
}

// ============================================================================
// Start & Aktualisierung
// ============================================================================
let pollTimer = null, instSig = "";
function stopPolling() { clearInterval(pollTimer); pollTimer = null; }
async function refresh(force = false) {
  if (!state.user) return;
  try {
    const [instances, system] = await Promise.all([api("/instances"), force || !state.system ? api("/system") : state.system]);
    state.system = system;
    const sig = JSON.stringify(instances);
    if (!force && sig === instSig) return;
    instSig = sig; state.instances = instances;
    if (shell) { renderSide(); renderTop(); renderPage(); }
  } catch { /* Netzwerkfehler: nächster Versuch folgt */ }
}
async function boot() {
  state.games = isAdmin() ? await api("/games").catch(() => []) : [];
  state.instances = []; instSig = ""; pageSig = null; shell = null;
  await refresh(true); render();
  stopPolling(); pollTimer = setInterval(refresh, 3000);
}
window.addEventListener("hashchange", () => { shell?.root.classList.remove("open"); if (state.user && shell) { renderSide(); renderTop(); renderPage(); } });
(async () => {
  const saved = store("gsm_theme"); if (saved === "dark" || saved === "light") document.documentElement.dataset.theme = saved;
  else if (matchMedia("(prefers-color-scheme: dark)").matches) document.documentElement.dataset.theme = "dark";
  try { const s = await fetch("/api/session").then(r => r.json()); state.user = s.user; } catch { state.user = null; }
  state.ready = true;
  if (state.user) await boot(); else render();
})();
