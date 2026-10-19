// Ladeprotokoll (Firmenwagen): Vorgaenge aus dem Kalender lesen, Zeitraum waehlen, als CSV exportieren
const VERSION = "1.0.0";
const CALENDAR = "calendar.ladeprotokoll_firmenwagen";

const CSS = `
:host { display: block; }
ha-card {
  padding: 14px; color: #f7f9ff;
  background: linear-gradient(145deg, rgba(18,27,45,calc(.50 * var(--gi-k,1))), rgba(28,40,60,calc(.28 * var(--gi-k,1))));
  backdrop-filter: blur(24px) saturate(138%);
  -webkit-backdrop-filter: blur(24px) saturate(138%);
  border: 1px solid rgba(240,247,255,.44);
  border-radius: 22px;
  box-shadow: inset 0 0 26px 2px rgba(232,243,255,.38), inset 0 0 6px rgba(255,255,255,.247), inset 0 1px 0 rgba(255,255,255,.14);
}
.row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-bottom: 10px; }
label { font-size: 12px; opacity: .8; display: flex; flex-direction: column; gap: 3px; flex: 1; min-width: 120px; }
input[type=date] {
  background: rgba(255,255,255,.10); color: #f7f9ff; border: 1px solid rgba(255,255,255,.25);
  border-radius: 12px; padding: 8px 10px; font-size: 15px; font-family: inherit; color-scheme: dark;
}
button {
  background: rgba(255,255,255,.12); color: #f7f9ff; border: 1px solid rgba(255,255,255,.28);
  border-radius: 14px; padding: 9px 12px; font-size: 13px; font-family: inherit; cursor: pointer;
}
button.primary { background: rgba(134,224,198,.30); border-color: rgba(134,224,198,.7); font-weight: 700; font-size: 14px; flex: 1; }
button:active { transform: scale(.98); }
table { width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 4px; }
th { text-align: right; font-weight: 600; opacity: .75; padding: 5px 4px; border-bottom: 1px solid rgba(255,255,255,.2); white-space: nowrap; }
td { text-align: right; padding: 6px 4px; border-bottom: 1px solid rgba(255,255,255,.08); white-space: nowrap; }
th:first-child, td:first-child { text-align: left; }
tr.sum td { font-weight: 800; border-top: 1px solid rgba(255,255,255,.3); border-bottom: none; color: #86e0c6; }
.info { font-size: 12px; opacity: .75; margin: 6px 2px 0; }
.empty { padding: 14px 4px; opacity: .75; font-size: 13px; }
textarea { width: 100%; box-sizing: border-box; height: 120px; margin-top: 8px; background: rgba(0,0,0,.25); color: #f7f9ff; border: 1px solid rgba(255,255,255,.25); border-radius: 10px; font-size: 11px; font-family: monospace; }
.tbl { overflow-x: auto; }
`;

const pad = (n) => String(n).padStart(2, "0");
const iso = (d) => d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());

class LadeprotokollExport extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._rows = [];
  }

  setConfig(config) {
    this._cfg = { calendar: CALENDAR, title: "Ladeprotokoll Firmenwagen", ...(config || {}) };
    const now = new Date();
    this._from = iso(new Date(now.getFullYear(), now.getMonth(), 1));
    this._to = iso(now);
    this._build();
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (first && this.shadowRoot.querySelector(".tbl")) this._load();
  }

  getCardSize() { return 6; }
  getGridOptions() { return { columns: 12, min_columns: 6 }; }

  _build() {
    this.shadowRoot.innerHTML =
      "<style>" + CSS + "</style><ha-card>" +
      '<div style="font-size:15px;font-weight:650;margin:0 2px 10px">' + this._cfg.title + "</div>" +
      '<div class="row"><label>Von<input type="date" id="from" value="' + this._from + '"></label>' +
      '<label>Bis<input type="date" id="to" value="' + this._to + '"></label></div>' +
      '<div class="row"><button id="m0">Dieser Monat</button><button id="m1">Letzter Monat</button><button id="y0">Dieses Jahr</button></div>' +
      '<div class="tbl" id="tbl"><div class="empty">Lade …</div></div>' +
      '<div class="row" style="margin-top:12px"><button class="primary" id="dl">CSV herunterladen</button><button id="cp">CSV kopieren</button></div>' +
      '<div class="info" id="info"></div><textarea id="ta" style="display:none" readonly></textarea></ha-card>';
    const $ = (id) => this.shadowRoot.getElementById(id);
    $("from").addEventListener("change", (e) => { this._from = e.target.value; this._load(); });
    $("to").addEventListener("change", (e) => { this._to = e.target.value; this._load(); });
    const setRange = (a, b) => { this._from = iso(a); this._to = iso(b); $("from").value = this._from; $("to").value = this._to; this._load(); };
    $("m0").addEventListener("click", () => { const n = new Date(); setRange(new Date(n.getFullYear(), n.getMonth(), 1), n); });
    $("m1").addEventListener("click", () => { const n = new Date(); setRange(new Date(n.getFullYear(), n.getMonth() - 1, 1), new Date(n.getFullYear(), n.getMonth(), 0)); });
    $("y0").addEventListener("click", () => { const n = new Date(); setRange(new Date(n.getFullYear(), 0, 1), n); });
    $("dl").addEventListener("click", () => this._download());
    $("cp").addEventListener("click", () => this._copy());
    if (this._hass) this._load();
  }

  async _load() {
    const box = this.shadowRoot.getElementById("tbl");
    if (!this._hass || !box) return;
    const a = new Date(this._from + "T00:00:00");
    const b = new Date(this._to + "T00:00:00");
    b.setDate(b.getDate() + 1);
    if (isNaN(a) || isNaN(b) || b <= a) { box.innerHTML = '<div class="empty">Bitte einen gültigen Zeitraum wählen.</div>'; this._rows = []; return; }
    try {
      const ev = await this._hass.callApi("GET", "calendars/" + this._cfg.calendar + "?start=" + encodeURIComponent(a.toISOString()) + "&end=" + encodeURIComponent(b.toISOString()));
      this._rows = ev.map((e) => this._parse(e)).filter((r) => r).sort((x, y) => x.start - y.start);
    } catch (err) {
      box.innerHTML = '<div class="empty">Fehler beim Laden: ' + (err && err.message ? err.message : err) + "</div>";
      this._rows = [];
      return;
    }
    this._render();
  }

  _parse(e) {
    const s = e.start && (e.start.dateTime || e.start.date);
    const en = e.end && (e.end.dateTime || e.end.date);
    if (!s || !en) return null;
    const d = {};
    String(e.description || "").split(";").forEach((p) => { const i = p.indexOf("="); if (i > 0) d[p.slice(0, i).trim()] = p.slice(i + 1).trim(); });
    const num = (k) => { const v = parseFloat(d[k]); return Number.isFinite(v) ? v : null; };
    return {
      start: new Date(s), end: new Date(en),
      kwh: num("kWh"), cost: num("Kosten"), price: num("Preis"), zs: num("ZaehlerStart"), ze: num("ZaehlerEnde"),
      car: d.Fahrzeug || "", mode: d.Modus || ""
    };
  }

  _f(v, dec) { return v === null || v === undefined ? "" : v.toLocaleString("de-DE", { minimumFractionDigits: dec, maximumFractionDigits: dec }); }

  _render() {
    const box = this.shadowRoot.getElementById("tbl");
    const info = this.shadowRoot.getElementById("info");
    if (!this._rows.length) {
      box.innerHTML = '<div class="empty">Keine Ladevorgänge im gewählten Zeitraum.</div>';
      info.textContent = "";
      return;
    }
    let kwh = 0, cost = 0;
    let h = "<table><tr><th>Datum</th><th>Zeit</th><th>kWh</th><th>€/kWh</th><th>Kosten</th></tr>";
    this._rows.forEach((r) => {
      kwh += r.kwh || 0; cost += r.cost || 0;
      h += "<tr><td>" + this._d(r.start) + "</td><td>" + this._t(r.start) + "–" + this._t(r.end) + "</td><td>" + this._f(r.kwh, 2) + "</td><td>" + this._f(r.price, 3) + "</td><td>" + this._f(r.cost, 2) + " €</td></tr>";
    });
    h += '<tr class="sum"><td>Summe (' + this._rows.length + ")</td><td></td><td>" + this._f(kwh, 2) + "</td><td>" + this._f(kwh ? cost / kwh : null, 3) + "</td><td>" + this._f(cost, 2) + " €</td></tr></table>";
    box.innerHTML = h;
    info.textContent = this._rows.length + " Ladevorgänge im Zeitraum, Preis = Tibber-Preis je kWh (Netz und PV gleich bewertet).";
  }

  _d(d) { return pad(d.getDate()) + "." + pad(d.getMonth() + 1) + "." + d.getFullYear(); }

  _t(d) { return pad(d.getHours()) + ":" + pad(d.getMinutes()); }

  _csv() {
    const f = (v, dec) => (v === null || v === undefined ? "" : v.toFixed(dec).replace(".", ","));
    const head = ["Datum", "Start", "Ende", "Dauer_min", "kWh", "Preis_EUR_je_kWh", "Kosten_EUR", "Zaehlerstand_Start_kWh", "Zaehlerstand_Ende_kWh", "Fahrzeug", "Lademodus"];
    const lines = [head.join(";")];
    let kwh = 0, cost = 0;
    this._rows.forEach((r) => {
      kwh += r.kwh || 0; cost += r.cost || 0;
      lines.push([
        this._d(r.start), this._t(r.start), this._t(r.end), Math.round((r.end - r.start) / 60000),
        f(r.kwh, 3), f(r.price, 4), f(r.cost, 2), f(r.zs, 3), f(r.ze, 3), r.car, r.mode
      ].join(";"));
    });
    lines.push(["Summe", "", "", "", f(kwh, 3), f(kwh ? cost / kwh : null, 4), f(cost, 2), "", "", "", ""].join(";"));
    return lines.join("\r\n");
  }

  _name() { return "ladeprotokoll_" + this._from + "_bis_" + this._to + ".csv"; }

  async _download() {
    const info = this.shadowRoot.getElementById("info");
    if (!this._rows.length) { info.textContent = "Nichts zu exportieren: keine Ladevorgänge im Zeitraum."; return; }
    const text = "﻿" + this._csv();
    const file = new File([text], this._name(), { type: "text/csv" });
    try {
      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        await navigator.share({ files: [file], title: this._name() });
        return;
      }
    } catch (e) {
      if (e && e.name === "AbortError") return;
    }
    try {
      const url = URL.createObjectURL(file);
      const a = document.createElement("a");
      a.href = url; a.download = this._name();
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 5000);
      info.textContent = "Download gestartet: " + this._name() + ". Falls nichts passiert, nutze „CSV kopieren“.";
    } catch (e) {
      this._copy();
    }
  }

  async _copy() {
    const info = this.shadowRoot.getElementById("info");
    const ta = this.shadowRoot.getElementById("ta");
    if (!this._rows.length) { info.textContent = "Nichts zu kopieren: keine Ladevorgänge im Zeitraum."; return; }
    const text = this._csv();
    ta.value = text; ta.style.display = "block";
    try { await navigator.clipboard.writeText(text); info.textContent = "CSV in die Zwischenablage kopiert (Semikolon-getrennt, UTF-8)."; }
    catch (e) { ta.select(); info.textContent = "Bitte den Text markieren und manuell kopieren."; }
  }
}

if (!customElements.get("ladeprotokoll-export")) customElements.define("ladeprotokoll-export", LadeprotokollExport);
window.customCards = window.customCards || [];
window.customCards.push({ type: "ladeprotokoll-export", name: "Ladeprotokoll Export", description: "Ladeprotokoll mit Zeitraumauswahl und CSV-Export, Version " + VERSION });
