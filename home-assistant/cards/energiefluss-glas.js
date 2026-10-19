// Energiefluss (Glas): eigene Energiefluss-Karte im Glas-Design (Kreise + Linien frei gestaltet)
const VERSION = "1.1.0";
const R = 34;
const POS = { grid: [11, 50], solar: [44, 17], home: [66, 50], battery: [44, 83], i0: [88, 17], i1: [88, 83] };
const DEFAULTS = {
  grid: { entity: "sensor.solarnet_power_grid", name: "Netz", icon: "mdi:flash", color: "#86b6f6" },
  solar: { entity: "sensor.power_photovoltaics", name: "Photovoltaik", icon: "mdi:white-balance-sunny", color: "#f2c97d" },
  battery: {
    entity: "sensor.solarnet_power_battery",
    soc: "sensor.byd_battery_box_premium_hv_state_of_charge",
    name: "Batterie",
    color: "#e29fc7"
  },
  home: { entity: "sensor.solarnet_leistung_verbrauch", name: "Haus", icon: "mdi:home", color: "#86e0c6" },
  individual: [
    { entity: "sensor.shellypro3em_c8f09e8313dc_total_active_power", name: "Wallbox", icon: "mdi:ev-station", color: "#d9d98c" },
    { entity: "sensor.ac_aussen_power", name: "Klimaanlage", icon: "mdi:snowflake", color: "#c9a0ff" }
  ]
};

const CSS = `
:host { display: block; }
ha-card { position: relative; padding: 12px; overflow: hidden; color: var(--primary-text-color, #f7f9ff); }
ha-card.glass {
  background: linear-gradient(145deg, rgba(19,33,51,calc(.70 * var(--gi-k,1))), rgba(30,41,60,calc(.52 * var(--gi-k,1))));
  backdrop-filter: blur(18px) saturate(148%);
  -webkit-backdrop-filter: blur(18px) saturate(148%);
  border: 1px solid rgba(232,245,255,.29);
  border-radius: 21px;
  color: #f7f9ff;
  box-shadow: inset 0 0 26px 2px rgba(232,243,255,.24), inset 0 0 6px rgba(255,255,255,.16), inset 0 1px 0 rgba(255,255,255,.14), 0 2px 6px rgba(0,0,0,.10);
}
.title { font-size: 15px; font-weight: 650; margin: 2px 4px 6px; }
.stage { position: relative; width: 100%; height: 350px; }
svg { position: absolute; inset: 0; width: 100%; height: 100%; overflow: visible; pointer-events: none; }
.line { fill: none; stroke-width: 2.6; stroke-linecap: round; transition: opacity .4s; }
.dot { transition: opacity .4s; }
.node { position: absolute; width: ${R * 2}px; height: ${R * 2}px; transform: translate(-50%, -50%); cursor: pointer; }
.circle {
  width: 100%; height: 100%; box-sizing: border-box; border-radius: 50%;
  border: 2px solid var(--c);
  background: radial-gradient(circle at 30% 22%, rgba(255,255,255,.20), rgba(255,255,255,.04) 65%);
  box-shadow: inset 0 0 14px color-mix(in srgb, var(--c) 22%, transparent), 0 0 14px color-mix(in srgb, var(--c) 28%, transparent);
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1px;
}
ha-icon { --mdc-icon-size: 18px; color: var(--c); filter: drop-shadow(0 0 4px var(--c)); }
.val { font-size: 13px; font-weight: 800; line-height: 1.1; white-space: nowrap; }
.sub { font-size: 10px; opacity: .8; line-height: 1; }
.lbl { position: absolute; left: 50%; transform: translateX(-50%); font-size: 12px; opacity: .85; white-space: nowrap; }
.lbl.top { bottom: calc(100% + 4px); }
.lbl.bottom { top: calc(100% + 4px); }
.sum { display: grid; grid-template-columns: repeat(4, 1fr); margin-top: 8px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,.18); }
.si { padding: 0 6px; }
.si .n { font-size: 13px; opacity: .75; }
.si .v { font-size: 19px; font-weight: 800; margin-top: 4px; white-space: nowrap; color: var(--c); }
`;

class EnergieflussGlas extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._flow = {};
  }

  setConfig(config) {
    const c = config || {};
    this._cfg = {
      title: c.title || "",
      glass: c.glass !== false,
      summary: c.summary !== false,
      min_power: c.min_power ?? 3,
      kw_threshold: c.kw_threshold ?? 1000,
      grid: { ...DEFAULTS.grid, ...(c.grid || {}) },
      solar: { ...DEFAULTS.solar, ...(c.solar || {}) },
      battery: { ...DEFAULTS.battery, ...(c.battery || {}) },
      home: { ...DEFAULTS.home, ...(c.home || {}) },
      individual: (c.individual || DEFAULTS.individual).slice(0, 2)
    };
    this._build();
    if (this._hass) this._update();
  }

  set hass(hass) {
    this._hass = hass;
    if (this._cfg) this._update();
  }

  getCardSize() { return 7; }
  getGridOptions() { return { columns: 12, min_columns: 6, rows: 7 }; }

  _nodes() {
    const c = this._cfg;
    const list = [
      { k: "grid", ...c.grid, pos: POS.grid, label: "bottom" },
      { k: "solar", ...c.solar, pos: POS.solar, label: "top" },
      { k: "home", ...c.home, pos: POS.home, label: "bottom" },
      { k: "battery", ...c.battery, pos: POS.battery, label: "bottom" }
    ];
    c.individual.forEach((ind, i) => {
      list.push({ k: "i" + i, ...ind, pos: POS["i" + i], label: i === 0 ? "top" : "bottom" });
    });
    return list;
  }

  _build() {
    const c = this._cfg;
    const nodes = this._nodes();
    const html = nodes.map((n) => {
      const inner = n.k === "battery"
        ? '<div class="sub"></div><div class="val"></div>'
        : '<ha-icon icon="' + n.icon + '"></ha-icon><div class="val"></div>';
      return '<div class="node" data-k="' + n.k + '" style="left:' + n.pos[0] + '%;top:' + n.pos[1] + '%;--c:' + n.color + '">' +
        '<div class="circle">' + inner + '</div><div class="lbl ' + n.label + '"></div></div>';
    }).join("");
    const sumItems = [["Solar", "solar", c.solar.color], ["Netz", "grid", c.grid.color], ["Akku", "battery", c.battery.color], ["Haus", "home", c.home.color]];
    const sum = c.summary
      ? '<div class="sum">' + sumItems.map((i) => '<div class="si" data-s="' + i[1] + '" style="--c:' + i[2] + '"><div class="n">' + i[0] + '</div><div class="v"></div></div>').join("") + "</div>"
      : "";
    this.shadowRoot.innerHTML =
      "<style>" + CSS + "</style>" +
      '<ha-card class="' + (c.glass ? "glass" : "") + '">' +
      (c.title ? '<div class="title">' + c.title + "</div>" : "") +
      '<div class="stage"><svg></svg>' + html + "</div>" + sum + "</ha-card>";
    this._stage = this.shadowRoot.querySelector(".stage");
    this._svg = this.shadowRoot.querySelector("svg");
    this.shadowRoot.querySelectorAll(".node").forEach((el) => {
      el.addEventListener("click", () => {
        const n = nodes.find((x) => x.k === el.dataset.k);
        const id = n && (n.entity || n.soc);
        if (id) this.dispatchEvent(new CustomEvent("hass-more-info", { detail: { entityId: id }, bubbles: true, composed: true }));
      });
    });
    if (this._ro) this._ro.disconnect();
    this._ro = new ResizeObserver(() => this._draw());
    this._ro.observe(this._stage);
    this._draw();
  }

  _draw() {
    if (!this._stage) return;
    const W = this._stage.clientWidth;
    const H = this._stage.clientHeight;
    if (!W || !H) return;
    const p = {};
    Object.keys(POS).forEach((k) => { p[k] = { x: POS[k][0] * W / 100, y: POS[k][1] * H / 100 }; });
    const h = p.home;
    const cub = (x1, y1, x2, y2) => {
      const dy = y2 - y1, dx = x2 - x1;
      return "M" + x1 + "," + y1 + " C" + x1 + "," + (y1 + dy * 0.55) + " " + (x1 + dx * 0.45) + "," + y2 + " " + x2 + "," + y2;
    };
    const k = 0.97;
    const paths = {
      grid: "M" + (p.grid.x + R) + "," + p.grid.y + " H" + (h.x - R),
      solar: cub(p.solar.x, p.solar.y + R, h.x - R * k, h.y - R * 0.25),
      battery: cub(p.battery.x, p.battery.y - R, h.x - R * k, h.y + R * 0.25),
      i0: cub(p.i0.x, p.i0.y + R, h.x + R * k, h.y - R * 0.25),
      i1: cub(p.i1.x, p.i1.y - R, h.x + R * k, h.y + R * 0.25)
    };
    const colors = {};
    this._nodes().forEach((n) => { colors[n.k] = n.color; });
    let out = "";
    Object.keys(paths).forEach((id) => {
      if (!colors[id]) return;
      const col = colors[id];
      out += '<path class="line" id="l_' + id + '" d="' + paths[id] + '" stroke="' + col + '" style="filter:drop-shadow(0 0 3px ' + col + ')"/>';
      out += '<circle class="dot" id="d_' + id + '" r="4" fill="' + col + '" style="filter:drop-shadow(0 0 4px ' + col + ');opacity:0">' +
        '<animateMotion dur="3s" repeatCount="indefinite" calcMode="linear" keyTimes="0;1" keyPoints="0;1" path="' + paths[id] + '"/></circle>';
    });
    this._svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    this._svg.innerHTML = out;
    this._applyFlows(true);
  }

  _applyFlows(force) {
    if (!this._svg) return;
    Object.keys(this._flow).forEach((id) => {
      const f = this._flow[id];
      const line = this._svg.querySelector("#l_" + id);
      const dot = this._svg.querySelector("#d_" + id);
      if (!line || !dot) return;
      line.style.opacity = f.active ? "1" : "0.28";
      dot.style.opacity = f.active ? "1" : "0";
      const am = dot.querySelector("animateMotion");
      const kp = f.forward ? "0;1" : "1;0";
      const dur = f.dur + "s";
      if (force || am.getAttribute("keyPoints") !== kp) am.setAttribute("keyPoints", kp);
      if (force || am.getAttribute("dur") !== dur) am.setAttribute("dur", dur);
    });
  }

  _num(id) {
    const s = this._hass && id ? this._hass.states[id] : undefined;
    if (!s) return null;
    const n = parseFloat(s.state);
    return Number.isFinite(n) ? n : null;
  }

  _fmt(w) {
    if (w === null) return "—";
    const a = Math.abs(w);
    if (a >= this._cfg.kw_threshold) {
      return (a / 1000).toLocaleString("de-DE", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " kW";
    }
    return Math.round(a).toLocaleString("de-DE") + " W";
  }

  _dur(w) {
    const a = Math.abs(w);
    return a < 500 ? 3 : a < 2000 ? 2 : 1.2;
  }

  _update() {
    if (!this._hass || !this.shadowRoot) return;
    const c = this._cfg;
    const min = c.min_power;
    const g = this._num(c.grid.entity);
    const s = this._num(c.solar.entity);
    const b = this._num(c.battery.entity);
    let home = this._num(c.home.entity);
    if (home === null) home = (g || 0) + (s || 0) + (b || 0);
    const soc = this._num(c.battery.soc);
    const set = (k, sel, text) => {
      const el = this.shadowRoot.querySelector('.node[data-k="' + k + '"] ' + sel);
      if (el && el.textContent !== text) el.textContent = text;
    };
    set("grid", ".val", this._fmt(g));
    set("grid", ".lbl", g !== null && g <= -min ? "Einspeisung" : g !== null && g >= min ? "Netzbezug" : c.grid.name);
    set("solar", ".val", this._fmt(s));
    set("solar", ".lbl", c.solar.name);
    set("home", ".val", this._fmt(Math.abs(home)));
    set("home", ".lbl", c.home.name);
    set("battery", ".sub", soc === null ? "" : Math.round(soc) + " %");
    set("battery", ".val", this._fmt(b));
    set("battery", ".lbl", b !== null && b >= min ? c.battery.name + " entlädt" : b !== null && b <= -min ? c.battery.name + " lädt" : c.battery.name);
    const setS = (k, text) => {
      const el = this.shadowRoot.querySelector('.si[data-s="' + k + '"] .v');
      if (el && el.textContent !== text) el.textContent = text;
    };
    setS("solar", this._fmt(s));
    setS("grid", this._fmt(g));
    setS("battery", soc === null ? "\u2014" : Math.round(soc) + " %");
    setS("home", this._fmt(Math.abs(home)));
    const flow = {
      grid: { active: g !== null && Math.abs(g) >= min, forward: (g || 0) > 0, dur: this._dur(g || 0) },
      solar: { active: s !== null && s >= min, forward: true, dur: this._dur(s || 0) },
      battery: { active: b !== null && Math.abs(b) >= min, forward: (b || 0) > 0, dur: this._dur(b || 0) }
    };
    c.individual.forEach((ind, i) => {
      const w = this._num(ind.entity);
      set("i" + i, ".val", this._fmt(w));
      set("i" + i, ".lbl", ind.name);
      flow["i" + i] = { active: w !== null && Math.abs(w) >= min, forward: false, dur: this._dur(w || 0) };
    });
    this._flow = flow;
    this._applyFlows(false);
  }
}

if (!customElements.get("energiefluss-glas")) {
  customElements.define("energiefluss-glas", EnergieflussGlas);
}
window.customCards = window.customCards || [];
window.customCards.push({
  type: "energiefluss-glas",
  name: "Energiefluss (Glas)",
  description: "Eigene Energiefluss-Karte im Glas-Design, Version " + VERSION
});
