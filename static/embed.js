/**
 * Dragon AI — osadzenie na WordPress (bluedragonjet.com itd.)
 * WPCode: <script src="https://asystent-bdj-ai.onrender.com/embed.js" defer></script>
 */
(function () {
  if (window.__bdjAiEmbedLoaded) return;
  window.__bdjAiEmbedLoaded = true;

  var BASE = (document.currentScript && document.currentScript.src)
    ? document.currentScript.src.replace(/\/embed\.js(?:\?.*)?$/, "")
    : "https://asystent-bdj-ai.onrender.com";

  var style = document.createElement("style");
  style.textContent = [
    "#bdj-ai-fab{position:fixed;bottom:28px;right:28px;width:60px;height:60px;border:1px solid rgba(255,255,255,.18);border-radius:50%;",
    "background:linear-gradient(145deg,rgba(15,23,42,.92),rgba(30,41,59,.88));color:#fff;cursor:pointer;z-index:2147483647;",
    "box-shadow:0 12px 32px rgba(15,23,42,.28),inset 0 1px 0 rgba(255,255,255,.18);display:flex;align-items:center;justify-content:center;padding:0;}",
    "#bdj-ai-fab:hover{transform:translateY(-3px) scale(1.02);}",
    "#bdj-ai-fab svg{width:26px;height:26px;pointer-events:none;}",
    "#bdj-ai-fab.is-loading{opacity:.7;pointer-events:none;}",
    "#bdj-ai-tip{display:none;position:fixed;bottom:100px;right:28px;max-width:min(300px,calc(100vw - 100px));z-index:2147483647;",
    "background:rgba(255,255,255,.95);border:1px solid rgba(15,23,42,.08);border-radius:18px;padding:12px 14px;",
    "box-shadow:0 16px 36px rgba(15,23,42,.18);cursor:pointer;font-family:system-ui,-apple-system,sans-serif;}",
    "#bdj-ai-tip strong{display:block;font-size:14px;color:#0f172a;}",
    "#bdj-ai-tip span{display:block;font-size:13px;color:#64748b;line-height:1.35;margin-top:2px;}",
    "#bdj-ai-tip-close{background:none;border:none;font-size:18px;line-height:1;color:#94a3b8;cursor:pointer;padding:0 2px;}",
    "#bdj-ai-embed{display:none;position:fixed;inset:0;z-index:2147483646;background:transparent;}",
    "#bdj-ai-widget{width:100%;height:100%;border:0;background:transparent;}",
  ].join("");
  document.head.appendChild(style);

  var fab = document.createElement("button");
  fab.id = "bdj-ai-fab";
  fab.type = "button";
  fab.setAttribute("aria-label", "Dragon AI");
  fab.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>';

  var tip = document.createElement("div");
  tip.id = "bdj-ai-tip";
  tip.innerHTML = '<div style="display:flex;gap:10px;align-items:flex-start;"><div style="flex:1;min-width:0;"><strong>DRAGON AI</strong><span>Cześć! Chętnie pomogę Ci w doborze części 😊</span></div><button id="bdj-ai-tip-close" type="button" aria-label="Zamknij">&times;</button></div>';

  var wrap = document.createElement("div");
  wrap.id = "bdj-ai-embed";
  var frame = document.createElement("iframe");
  frame.id = "bdj-ai-widget";
  frame.title = "Dragon AI";
  frame.allow = "clipboard-write";
  wrap.appendChild(frame);

  function mount() {
    // Usuń stare atrapy z WPCode (jeśli zostały)
    ["bdj-ai-fab", "bdj-ai-tip", "bdj-ai-embed"].forEach(function (id) {
      var old = document.getElementById(id);
      if (old && old !== fab && old !== tip && old !== wrap) old.remove();
    });
    document.body.appendChild(fab);
    document.body.appendChild(tip);
    document.body.appendChild(wrap);
  }

  if (document.body) mount();
  else document.addEventListener("DOMContentLoaded", mount);

  var ready = false;
  var wantOpen = false;
  var loaded = false;

  function hideTip() { tip.style.display = "none"; }

  function showChat() {
    hideTip();
    fab.style.display = "none";
    fab.classList.remove("is-loading");
    wrap.style.display = "block";
  }

  function hideChat() {
    wrap.style.display = "none";
    fab.style.display = "flex";
    fab.classList.remove("is-loading");
    wantOpen = false;
  }

  function ensureFrame() {
    if (loaded) return;
    loaded = true;
    frame.src = BASE + "/?embed=1";
  }

  function requestOpen() {
    wantOpen = true;
    fab.classList.add("is-loading");
    ensureFrame();
    if (ready) {
      try { frame.contentWindow.postMessage({ type: "bdj-ai-command", action: "open" }, "*"); } catch (e) {}
    }
  }

  // Preload w tle (poza ekranem) — bez białego prostokąta
  setTimeout(function () {
    ensureFrame();
  }, 800);

  setTimeout(function () {
    if (wrap.style.display !== "block") tip.style.display = "block";
  }, 3000);

  fab.addEventListener("click", requestOpen);
  tip.addEventListener("click", function (e) {
    if (e.target && e.target.id === "bdj-ai-tip-close") {
      e.stopPropagation();
      hideTip();
      return;
    }
    requestOpen();
  });

  window.addEventListener("message", function (e) {
    if (!e.data || typeof e.data !== "object") return;
    if (e.data.type === "bdj-ai-ready") {
      ready = true;
      if (wantOpen) {
        try { frame.contentWindow.postMessage({ type: "bdj-ai-command", action: "open" }, "*"); } catch (err) {}
      }
    }
    if (e.data.type === "bdj-ai-resize") {
      if (e.data.open) showChat();
      else hideChat();
    }
  });
})();
