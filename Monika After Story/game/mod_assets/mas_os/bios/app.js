(function () {
  var PREVIEW = !(window.BiosBridge);

  function $(id) {
    return document.getElementById(id);
  }

  function pad(n) {
    return n < 10 ? "0" + n : String(n);
  }

  function tickClock() {
    var el = $("clock");
    if (!el) {
      return;
    }
    var d = new Date();
    el.textContent = pad(d.getHours()) + ":" + pad(d.getMinutes());
  }

  function queryOpen() {
    var q = "";
    try {
      q = String(window.location.search || "");
    } catch (e) {
      q = "";
    }
    var m = q.match(/[?&]open=([a-z]+)/i);
    if (m) {
      return m[1].toLowerCase();
    }
    var hash = "";
    try {
      hash = String(window.location.hash || "").replace("#", "");
    } catch (e2) {
      hash = "";
    }
    return hash.toLowerCase();
  }

  window.biosLog = function (text) {
    var log = $("log");
    if (!log || text === undefined || text === null) {
      return;
    }
    log.textContent += String(text);
    log.scrollTop = log.scrollHeight;
  };

  window.biosProgress = function (text, pct) {
    var line = $("progressLine");
    var bar = $("bar");
    if (line) {
      line.textContent = text ? String(text) : "";
    }
    if (!bar) {
      return;
    }
    if (pct === undefined || pct === null || pct < 0) {
      bar.style.width = "100%";
      bar.style.opacity = "0.4";
      return;
    }
    var n = pct;
    if (n > 100) {
      n = 100;
    }
    if (n < 0) {
      n = 0;
    }
    bar.style.opacity = "1";
    bar.style.width = n + "%";
  };

  window.biosSetStatus = function (info) {
    info = info || {};
    if (info.path) {
      var path = $("path");
      if (path) {
        path.textContent = String(info.path);
      }
    }
    if (info.version) {
      var ver = $("version");
      if (ver) {
        ver.textContent = String(info.version);
      }
    }
    toggleChip("chipFiles", !!info.filesOk);
    toggleChip("chipEngine", !!info.engineOk);
    toggleChip("chipSkip", !!info.skipBios);
  };

  function toggleChip(id, on) {
    var el = $(id);
    if (!el) {
      return;
    }
    if (on) {
      el.className = "chip on";
    } else {
      el.className = "chip";
    }
  }

  window.biosOpen = function (name) {
    var id = String(name || "play").toLowerCase();
    var known = {
      play: 1, files: 1, submods: 1, saves: 1, update: 1, engine: 1, system: 1
    };
    if (!known[id]) {
      id = "play";
    }
    var secs = document.querySelectorAll(".sec");
    var i;
    for (i = 0; i < secs.length; i++) {
      if (secs[i].getAttribute("data-sec") === id) {
        secs[i].className = "sec on";
      } else {
        secs[i].className = "sec";
      }
    }
    var btns = document.querySelectorAll(".nav-btn");
    for (i = 0; i < btns.length; i++) {
      if (btns[i].getAttribute("data-open") === id) {
        btns[i].className = "nav-btn on";
      } else {
        btns[i].className = "nav-btn";
      }
    }
    try {
      if (window.location.hash.replace("#", "") !== id) {
        window.location.hash = id;
      }
    } catch (e) {}
  };

  window.callBridge = function (name) {
    try {
      if (window.BiosBridge && BiosBridge[name]) {
        BiosBridge[name]();
        return;
      }
    } catch (e) {
      biosLog("\nкнопка не сработала: " + name);
      return;
    }
    biosLog("\n→ " + name);
    if (PREVIEW) {
      biosLog("  (предпросмотр, Java ещё нет)");
    } else {
      biosLog("  мост не готов");
    }
  };

  function bindNav() {
    var nav = $("nav");
    if (!nav) {
      return;
    }
    nav.addEventListener("click", function (ev) {
      var t = ev.target;
      while (t && t !== nav && !t.getAttribute("data-open")) {
        t = t.parentNode;
      }
      if (!t || !t.getAttribute) {
        return;
      }
      var name = t.getAttribute("data-open");
      if (name) {
        biosOpen(name);
      }
    });
  }

  function boot() {
    bindNav();
    tickClock();
    setInterval(tickClock, 10000);
    var open = queryOpen() || "play";
    biosOpen(open);
    if (PREVIEW) {
      var hint = $("hint");
      if (hint) {
        hint.textContent = "предпросмотр в браузере · открой index.html";
      }
      biosSetStatus({
        path: "Documents/Monika_after_story",
        version: "предпросмотр",
        filesOk: false,
        engineOk: false,
        skipBios: false
      });
      biosLog("MAS BIOS\nстраница живая без Java.\nИз MAS OS сюда можно прыгнуть с extra open=submods.\n");
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
