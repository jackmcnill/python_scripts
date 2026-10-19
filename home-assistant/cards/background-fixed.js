// Zuhause v7: feststehender Hintergrund (auch iOS) fuer das Dashboard design-h-klar.
// Scharfes Bild komplett sichtbar (contain), darunter dieselbe Aufnahme unscharf als Fuellung, Kopfzeile transparent.
(() => {
  const BASE = "/local/glass_island_v3/";
  const PATHS = ["/design-h-klar"];
  const VARS = {
    "--primary-background-color": "transparent",
    "--app-header-background-color": "transparent",
    "--app-header-box-shadow": "none",
    "--app-header-border-bottom": "none"
  };
  const mq = window.matchMedia("(max-width: 767px)");
  const root = document.documentElement;
  const st = document.createElement("style");
  st.textContent = "html.zh-fixed, html.zh-fixed body { background: transparent !important; }";
  document.head.appendChild(st);
  let wrap = null;
  let blur = null;
  let sharp = null;
  let on = false;
  const apply = () => {
    const active = PATHS.some((p) => location.pathname.indexOf(p) === 0);
    const mobile = mq.matches;
    const img = BASE + (mobile ? "background_mobile.jpg" : "background_desktop.jpg");
    if (!active) {
      if (on) {
        on = false;
        root.classList.remove("zh-fixed");
        Object.keys(VARS).forEach((k) => root.style.removeProperty(k));
        if (wrap) wrap.style.display = "none";
      }
      return;
    }
    if (!wrap) {
      wrap = document.createElement("div");
      wrap.id = "zh-fixed-bg";
      wrap.style.cssText = "position:fixed;top:0;left:0;right:0;bottom:0;z-index:-1;pointer-events:none;overflow:hidden;background:#0b1220;";
      blur = document.createElement("div");
      blur.style.cssText = "position:absolute;top:-30px;left:-30px;right:-30px;bottom:-30px;background-size:cover;background-position:center;background-repeat:no-repeat;filter:blur(28px) brightness(.9);";
      sharp = document.createElement("div");
      sharp.style.cssText = "position:absolute;top:0;left:0;right:0;bottom:0;background-size:contain;background-repeat:no-repeat;";
      wrap.appendChild(blur);
      wrap.appendChild(sharp);
      document.body.insertBefore(wrap, document.body.firstChild);
    }
    wrap.style.display = "block";
    sharp.style.backgroundPosition = mobile ? "center top" : "center center";
    const mask = mobile ? "linear-gradient(#000 0,#000 88%,transparent 100%)" : "none";
    sharp.style.webkitMaskImage = mask;
    sharp.style.maskImage = mask;
    const url = "url('" + img + "')";
    if (sharp.style.backgroundImage.indexOf(img) < 0) {
      sharp.style.backgroundImage = url;
      blur.style.backgroundImage = url;
    }
    on = true;
    root.classList.add("zh-fixed");
    Object.keys(VARS).forEach((k) => root.style.setProperty(k, VARS[k]));
  };
  mq.addEventListener("change", apply);
  setInterval(apply, 500);
  apply();
})();
