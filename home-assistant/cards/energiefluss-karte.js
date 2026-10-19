// Zentrale Energiefluss-Karte (Wrapper um power-flow-card-plus), genutzt im Dashboard "Mutter".
// Aenderungen an DEFAULT_CONFIG wirken in allen Dashboards, die custom:energiefluss-karte nutzen.
const VERSION = "1.0.0";
const DEFAULT_CONFIG = {
  type: "custom:power-flow-card-plus",
  entities: {
    grid: { entity: "sensor.solarnet_power_grid" },
    solar: { entity: "sensor.power_photovoltaics" },
    battery: {
      entity: "sensor.solarnet_power_battery",
      state_of_charge: "sensor.byd_battery_box_premium_hv_state_of_charge"
    },
    individual: [
      { entity: "sensor.shellypro3em_c8f09e8313dc_total_active_power", icon: "mdi:ev-station", name: "Wallbox", display_zero: true },
      { entity: "sensor.ac_aussen_power", icon: "mdi:air-conditioner", name: "Klimaanlage", display_zero: false }
    ],
    home: { entity: "sensor.solarnet_power_grid" }
  },
  kw_decimals: 2,
  w_decimals: 0,
  watt_threshold: 1000,
  clickable_entities: true
};

class EnergieflussKarte extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
    this._build();
  }

  async _build() {
    const helpers = await window.loadCardHelpers();
    const overrides = this._config.overrides || {};
    const cfg = { ...DEFAULT_CONFIG, ...overrides };
    if (this._config.title) cfg.title = this._config.title;
    const el = helpers.createCardElement(cfg);
    if (this._hass) el.hass = this._hass;
    this._el = el;
    this.replaceChildren(el);
  }

  set hass(hass) {
    this._hass = hass;
    if (this._el) this._el.hass = hass;
  }

  getCardSize() {
    return 6;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }
}

if (!customElements.get("energiefluss-karte")) {
  customElements.define("energiefluss-karte", EnergieflussKarte);
}
window.customCards = window.customCards || [];
window.customCards.push({
  type: "energiefluss-karte",
  name: "Energiefluss (zentral)",
  description: "Zentral gepflegte Energiefluss-Karte, Version " + VERSION
});
