/**
 * Dragon AI — osadzenie WP (inline / embed.js)
 * Przycisk montowany na document.body — poza stacking context stopki.
 */
(function () {
  if (window.__bdjAiEmbedLoaded) return;
  window.__bdjAiEmbedLoaded = true;

  var BASE = "https://asystent-bdj-ai.onrender.com";
  var EMBED_VERSION = "0.0.8";
  try {
    if (document.currentScript && document.currentScript.src) {
      BASE = document.currentScript.src.replace(/\/embed\.js(?:\?.*)?$/, "");
    }
  } catch (e) {}

  // Usuń stare atrapy z WPCode (w stopce)
  ["bdj-ai-fab", "bdj-ai-tip", "bdj-ai-embed", "bdj-ai-widget"].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.remove();
  });

  var style = document.createElement("style");
  style.textContent = [
    "#bdj-ai-fab{position:fixed!important;bottom:28px!important;right:28px!important;width:60px!important;height:60px!important;",
    "border:1px solid rgba(255,255,255,.18)!important;border-radius:50%!important;padding:0!important;margin:0!important;",
    "background:linear-gradient(145deg,rgba(15,23,42,.92),rgba(30,41,59,.88))!important;color:#fff!important;cursor:pointer!important;",
    "z-index:2147483647!important;box-shadow:0 12px 32px rgba(15,23,42,.28)!important;",
    "display:flex!important;align-items:center!important;justify-content:center!important;pointer-events:auto!important;}",
    "#bdj-ai-fab svg{width:26px;height:26px;pointer-events:none;}",
    "#bdj-ai-tip{position:fixed!important;bottom:100px!important;right:28px!important;max-width:min(300px,calc(100vw - 100px));",
    "z-index:2147483647!important;background:rgba(255,255,255,.95)!important;border:1px solid rgba(15,23,42,.08)!important;",
    "border-radius:18px!important;padding:12px 14px!important;box-shadow:0 16px 36px rgba(15,23,42,.18)!important;",
    "cursor:pointer!important;font-family:system-ui,sans-serif!important;pointer-events:auto!important;display:none;}",
    "#bdj-ai-tip strong{display:block;font-size:14px;color:#0f172a;}",
    "#bdj-ai-tip span{display:block;font-size:13px;color:#64748b;line-height:1.35;margin-top:2px;}",
    "#bdj-ai-tip-close{background:none;border:none;font-size:18px;color:#94a3b8;cursor:pointer;padding:0 2px;pointer-events:auto!important;}",
    "#bdj-ai-embed{display:none;position:fixed!important;bottom:0!important;right:0!important;",
    "width:min(450px,100vw)!important;height:min(780px,100dvh)!important;",
    "z-index:2147483646!important;background:transparent!important;pointer-events:none!important;border:none!important;}",
    "#bdj-ai-embed.is-open{display:block!important;pointer-events:auto!important;}",
    "#bdj-ai-widget{width:100%!important;height:100%!important;border:0!important;background:transparent!important;}",
  ].join("");

  var fab = document.createElement("button");
  fab.id = "bdj-ai-fab";
  fab.type = "button";
  fab.setAttribute("aria-label", "Dragon AI");
  fab.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path><circle cx="8.5" cy="10.5" r="1" fill="currentColor" stroke="none"></circle><circle cx="12" cy="10.5" r="1" fill="currentColor" stroke="none"></circle><circle cx="15.5" cy="10.5" r="1" fill="currentColor" stroke="none"></circle></svg>';

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

  var ready = false;
  var wantOpen = false;
  var loaded = false;

  function hideTip() { tip.style.display = "none"; }

  function showChat() {
    hideTip();
    fab.style.display = "none";
    wrap.classList.add("is-open");
    wrap.style.display = "block";
    wrap.style.pointerEvents = "auto";
  }

  function hideChat() {
    wrap.classList.remove("is-open");
    wrap.style.display = "none";
    wrap.style.pointerEvents = "none";
    fab.style.display = "flex";
    wantOpen = false;
  }

  function sendOpen() {
    if (!frame.contentWindow) return;
    try { frame.contentWindow.postMessage({ type: "bdj-ai-command", action: "open" }, "*"); } catch (e) {}
  }

  function openChat() {
    wantOpen = true;
    showChat();
    ensureFrame();
    sendOpen();
  }

  function ensureFrame() {
    if (loaded) {
      sendOpen();
      return;
    }
    loaded = true;
    frame.src = BASE + "/?embed=1&open=1&v=" + encodeURIComponent(EMBED_VERSION);
  }

  function mount() {
    document.head.appendChild(style);
    document.body.appendChild(fab);
    document.body.appendChild(tip);
    document.body.appendChild(wrap);

    setTimeout(ensureFrame, 500);
    frame.addEventListener("load", function () {
      if (wantOpen) {
        setTimeout(function () { ready = true; sendOpen(); }, 80);
      }
    });
    setTimeout(function () {
      if (!wrap.classList.contains("is-open")) tip.style.display = "block";
    }, 3000);

    fab.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      openChat();
    });
    tip.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      if (e.target && e.target.id === "bdj-ai-tip-close") {
        hideTip();
        return;
      }
      openChat();
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
        if (e.data.open === false) hideChat();
      }
    });
  }

  if (document.body) mount();
  else document.addEventListener("DOMContentLoaded", mount);
})();
