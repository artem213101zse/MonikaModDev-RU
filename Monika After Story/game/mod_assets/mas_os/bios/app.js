(function () {
  var PREVIEW = !(window.BiosBridge);
  var currentSec = "play";
  var currentView = "classic";

  function $(id) {
    return document.getElementById(id);
  }

  function pad(n) {
    return n < 10 ? "0" + n : String(n);
  }

  function stamp() {
    var d = new Date();
    return pad(d.getHours()) + ":" + pad(d.getMinutes()) + ":" + pad(d.getSeconds());
  }

  var VIEW_CYCLE = ["classic", "island", "deck", "masl"];
  var VIEW_LABEL = {
    classic: "классика",
    island: "остров",
    deck: "колода",
    masl: "MASL"
  };
  var SEC_TITLE = {
    play: "Monika After Story",
    files: "Проводник",
    archives: "Архивы DDLC",
    content: "Доп. контент",
    library: "Библиотека",
    saves: "Сейвы",
    update: "Обновление",
    engine: "Движок шахмат",
    recovery: "Рекавери",
    system: "Параметры",
    more: "Ещё"
  };

  function tickClock() {
    var d = new Date();
    var t = pad(d.getHours()) + ":" + pad(d.getMinutes());
    var el = $("clock");
    if (el) {
      el.textContent = t;
    }
    var masl = $("maslClock");
    if (masl) {
      masl.textContent = t;
    }
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

  function guessLevel(s) {
    var low = s.toLowerCase();
    if (s.indexOf("→ ") >= 0 && s.indexOf("→ ") <= 2) {
      return "CMD";
    }
    if (
      low.indexOf("fail") >= 0
      || low.indexOf("error") >= 0
      || low.indexOf("не ") >= 0
      || low.indexOf("ошиб") >= 0
      || low.indexOf("denied") >= 0
      || low.indexOf("exception") >= 0
    ) {
      return "ERR";
    }
    if (
      low.indexOf("готово") >= 0
      || low.indexOf(" ok") >= 0
      || low.indexOf("успеш") >= 0
      || low.indexOf("постав") >= 0
      || low.indexOf("записан") >= 0
    ) {
      return "OK ";
    }
    return "INF";
  }

  function formatChunk(text) {
    var s = String(text == null ? "" : text);
    var isCmd = s.indexOf("→ ") >= 0 && s.indexOf("→ ") <= 2;
    if (!isCmd && s.indexOf("\n→ ") >= 0) {
      isCmd = true;
    }
    var lines = s.replace(/^\n+/, "").split(/\r?\n/);
    var out = [];
    var i;
    for (i = 0; i < lines.length; i++) {
      var line = lines[i];
      if (!line || !String(line).replace(/\s+/g, "")) {
        continue;
      }
      var lvl = guessLevel(line);
      out.push("[" + stamp() + "] " + lvl + "  " + line);
    }
    if (!out.length) {
      return "";
    }
    var body = out.join("\n") + "\n";
    if (isCmd) {
      return "\n────────\n" + body;
    }
    return body;
  }

  window.biosLog = function (text) {
    var log = $("log");
    if (!log || text === undefined || text === null) {
      return;
    }
    var title = $("logTitle");
    if (title) {
      title.textContent = "Журнал";
    }
    log.textContent += formatChunk(text);
    log.scrollTop = log.scrollHeight;
    syncMaslNotify();
  };

  window.clearBiosLog = function () {
    var log = $("log");
    if (log) {
      log.textContent = "";
    }
    syncMaslNotify();
    var title = $("logTitle");
    if (title) {
      title.textContent = "Журнал";
    }
  };

  window.biosTrace = function (text) {
    var log = $("log");
    if (!log) {
      return;
    }
    var title = $("logTitle");
    if (title) {
      title.textContent = "Traceback";
    }
    log.textContent = text ? String(text) : "traceback.txt нет";
    log.scrollTop = 0;
  };

  function setIsland(text, pct) {
    var island = $("island");
    var title = $("islandTitle");
    var sub = $("islandSub");
    var pctEl = $("islandPct");
    var bar = $("islandBar");
    var head = $("islandHead");
    var line = text ? String(text) : "";
    if (title) {
      title.textContent = line ? "загрузка" : "MAS BIOS";
    }
    if (sub) {
      sub.textContent = line || "готов";
    }
    if (!island) {
      return;
    }
    island.className = "island";
    if (pct === undefined || pct === null || pct < 0) {
      if (line) {
        island.className = "island busy indeterminate";
        if (pctEl) {
          pctEl.textContent = "…";
        }
      } else {
        island.className = "island idle";
        if (pctEl) {
          pctEl.textContent = "";
        }
      }
      if (bar) {
        bar.style.width = line ? "34%" : "0";
      }
      if (head) {
        head.style.left = "0";
      }
      return;
    }
    var n = pct;
    if (n > 100) {
      n = 100;
    }
    if (n < 0) {
      n = 0;
    }
    island.className = n >= 100 ? "island idle" : "island busy";
    if (pctEl) {
      pctEl.textContent = n + "%";
    }
    if (bar) {
      bar.style.width = n + "%";
    }
    if (head) {
      head.style.left = n + "%";
    }
    if (n >= 100 && title) {
      title.textContent = "готово";
    }
  }

  window.biosDlState = function (state) {
    var s = String(state || "idle");
    try {
      document.body.setAttribute("data-dl", s);
    } catch (e) {
    }
    var title = $("islandTitle");
    var sub = $("islandSub");
    if (s === "paused") {
      if (title) {
        title.textContent = "пауза";
      }
      if (sub) {
        sub.textContent = "включи VPN и нажми Продолжить";
      }
    } else if (s === "idle") {
      if (title) {
        title.textContent = "MAS BIOS";
      }
    }
  }

  window.biosProgress = function (text, pct) {
    var line = $("progressLine");
    var bar = $("bar");
    if (line) {
      line.textContent = text ? String(text) : "";
    }
    setIsland(text, pct);
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
    toggleChip("chipArchives", !!info.archivesOk);
    toggleChip("chipTrace", !!info.tracebackOk);
    var gate = $("permGate");
    if (gate) {
      if (PREVIEW || info.filesOk) {
        gate.setAttribute("hidden", "hidden");
      } else {
        gate.removeAttribute("hidden");
      }
    }
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

  function normalizeView(name) {
    if (name === "island" || name === "deck" || name === "masl") {
      return name;
    }
    return "classic";
  }

  function closeMaslMenus() {
    var start = $("maslStart");
    var more = $("maslMore");
    var note = $("maslNotify");
    if (start) {
      start.hidden = true;
    }
    if (more) {
      more.hidden = true;
    }
    document.body.classList.remove("masl-start-on", "masl-more-on", "masl-notify-on");
    if (note) {
      note.hidden = true;
    }
  }

  function syncMaslNotify() {
    var src = $("log");
    var dst = $("maslNotifyLog");
    if (src && dst) {
      dst.textContent = src.textContent || "";
      dst.scrollTop = dst.scrollHeight;
    }
  }

  window.toggleMaslStart = function () {
    var start = $("maslStart");
    if (!start) {
      return;
    }
    var on = start.hidden;
    closeMaslMenus();
    if (on) {
      start.hidden = false;
      document.body.classList.add("masl-start-on");
    }
  };

  window.toggleMaslMore = function () {
    var more = $("maslMore");
    var start = $("maslStart");
    if (!more) {
      return;
    }
    if (more.hidden) {
      more.hidden = false;
      if (start) {
        start.hidden = false;
      }
      document.body.classList.add("masl-start-on", "masl-more-on");
    } else {
      more.hidden = true;
      document.body.classList.remove("masl-more-on");
    }
  };

  window.toggleMaslNotify = function () {
    var note = $("maslNotify");
    if (!note) {
      return;
    }
    var show = note.hidden;
    closeMaslMenus();
    if (show) {
      syncMaslNotify();
      note.hidden = false;
      document.body.classList.add("masl-notify-on");
    }
  };

  function maslOpenWin(sec) {
    closeMaslMenus();
    document.body.classList.add("masl-open");
    document.body.classList.remove("masl-min");
    var title = SEC_TITLE[sec] || "MAS BIOS";
    var tEl = $("maslWinTitle");
    var task = $("maslTaskApp");
    if (tEl) {
      tEl.textContent = title;
    }
    if (task) {
      task.hidden = false;
      task.textContent = title;
    }
  }

  window.maslCloseWin = function () {
    document.body.classList.remove("masl-open", "masl-min");
    var task = $("maslTaskApp");
    if (task) {
      task.hidden = true;
    }
    closeMaslMenus();
  };

  window.maslMinimize = function () {
    document.body.classList.add("masl-min");
    document.body.classList.remove("masl-open");
    closeMaslMenus();
  };

  window.maslRestore = function () {
    document.body.classList.remove("masl-min");
    document.body.classList.add("masl-open");
    closeMaslMenus();
  };

  window.maslAction = function (name) {
    closeMaslMenus();
    if (name === "startGame" || name === "startSafe" || name === "pickImage" || name === "openDocuments" || name === "exportSaves") {
      callBridge(name);
      return;
    }
    biosOpen(name);
  };

  function saveView(name) {
    currentView = normalizeView(name);
    try {
      localStorage.setItem("mas_bios_view", currentView);
    } catch (e) {
    }
    try {
      if (window.BiosBridge && BiosBridge.setBiosView) {
        BiosBridge.setBiosView(currentView);
      }
    } catch (e2) {
    }
  }

  window.applyBiosView = function (name) {
    var id = normalizeView(name);
    currentView = id;
    var keep = [];
    if (document.body.classList.contains("masl-open")) {
      keep.push("masl-open");
    }
    if (document.body.classList.contains("masl-min")) {
      keep.push("masl-min");
    }
    var dl = document.body.getAttribute("data-dl");
    document.body.className = "view-" + id;
    if (dl) {
      document.body.setAttribute("data-dl", dl);
    }
    var k;
    for (k = 0; k < keep.length; k++) {
      if (id === "masl") {
        document.body.classList.add(keep[k]);
      }
    }
    if (id !== "masl") {
      document.body.classList.remove("masl-open", "masl-min", "masl-start-on", "masl-more-on", "masl-notify-on");
    }
    var chrome = $("maslChrome");
    if (chrome) {
      chrome.setAttribute("aria-hidden", id === "masl" ? "false" : "true");
    }
    var btn = $("viewToggle");
    if (btn) {
      btn.textContent = "вид: " + (VIEW_LABEL[id] || id);
    }
    var hint = $("hint");
    if (hint && !PREVIEW) {
      hint.textContent = id === "masl"
        ? "MASL · Пуск · окна поверх рабочего стола"
        : (id === "deck"
          ? "колода · контент снизу · крупные плитки"
          : (id === "island"
            ? "остров · таблица паков · полоска загрузки"
            : "слева действия · справа журнал"));
    }
  };

  window.biosSetView = function (name) {
    applyBiosView(name);
    try {
      localStorage.setItem("mas_bios_view", currentView);
    } catch (e) {
    }
  };

  window.toggleBiosView = function () {
    var i = 0;
    var next = "classic";
    for (i = 0; i < VIEW_CYCLE.length; i++) {
      if (VIEW_CYCLE[i] === currentView) {
        next = VIEW_CYCLE[(i + 1) % VIEW_CYCLE.length];
        break;
      }
    }
    applyBiosView(next);
    saveView(next);
    biosLog("вид BIOS: " + (VIEW_LABEL[next] || next));
  };

  window.biosOpen = function (name) {
    var id = String(name || "play").toLowerCase();
    var known = {
      play: 1, files: 1, archives: 1, submods: 1, sprites: 1, saves: 1,
      update: 1, engine: 1, recovery: 1, system: 1, content: 1, library: 1, more: 1
    };
    if (id === "submods" || id === "sprites") {
      id = "content";
    }
    if (!known[id]) {
      id = "play";
    }
    currentSec = id;
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
    var tabs = document.querySelectorAll(".deck-tab");
    for (i = 0; i < tabs.length; i++) {
      if (tabs[i].getAttribute("data-open") === id) {
        tabs[i].className = "deck-tab on";
      } else {
        tabs[i].className = "deck-tab";
      }
    }
    if (currentView === "masl") {
      maslOpenWin(id);
    }
    var board = document.querySelector(".board");
    if (board) {
      board.scrollTop = 0;
    }
    if (id === "library" || id === "content" || id === "submods" || id === "sprites") {
      try {
        if (window.BiosBridge && BiosBridge.listSubmods) {
          BiosBridge.listSubmods();
        }
      } catch (e3) {
      }
      try {
        if (window.BiosBridge && BiosBridge.listUrlHistory) {
          BiosBridge.listUrlHistory();
        }
      } catch (e4) {
      }
    }
  };

  window.sendUci = function () {
    var el = $("uciCmd");
    var cmd = el && el.value ? String(el.value) : "";
    biosLog("\n→ sendStockfish " + cmd);
    try {
      if (window.BiosBridge && BiosBridge.sendStockfish) {
        BiosBridge.sendStockfish(cmd);
        return;
      }
    } catch (e) {
      biosLog("\nкнопка не сработала: sendStockfish");
      return;
    }
  };

  function sendPackUrl(url) {
    url = String(url || "");
    biosLog("\n→ downloadSubmodUrl " + url);
    try {
      if (window.BiosBridge && BiosBridge.downloadSubmodUrl) {
        BiosBridge.downloadSubmodUrl(url);
        return true;
      }
    } catch (e) {
      biosLog("\nкнопка не сработала: downloadSubmodUrl");
    }
    return false;
  }

  window.downloadContent = function () {
    var el = $("contentUrl");
    sendPackUrl(el && el.value ? el.value : "");
  };

  window.downloadSubmod = window.downloadContent;
  window.downloadSpritepack = window.downloadContent;

  window.useHistoryUrl = function (url) {
    var u = String(url || "");
    var a = $("contentUrl");
    if (a) { a.value = u; }
    biosLog("подставил ссылку из истории");
  };

  window.uninstallSubmod = function (id) {
    biosLog("\n→ uninstallSubmod " + id);
    try {
      if (window.BiosBridge && BiosBridge.uninstallSubmod) {
        BiosBridge.uninstallSubmod(id);
        return;
      }
    } catch (e) {
      biosLog("\nкнопка не сработала: uninstallSubmod");
    }
  };

  function esc(s) {
    return String(s || "").replace(/[<>&]/g, "");
  }

  function fillCards(box, rows, filter) {
    if (!box) {
      return;
    }
    box.innerHTML = "";
    var i;
    var n = 0;
    for (i = 0; i < rows.length; i++) {
      var row = rows[i] || {};
      var kind = String(row.kind || "submod");
      if (filter === "spritepack") {
        if (kind !== "spritepack") {
          continue;
        }
      } else if (kind === "spritepack") {
        continue;
      }
      var id = String(row.id || "");
      var pack = String(row.pack || id || "пак");
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "tile";
      btn.setAttribute("data-id", id);
      var kindLabel = kind === "assetpack" ? " · рескин" : "";
      btn.innerHTML = "<b>Снять «" + esc(pack) + "»</b><span>id=" + esc(id)
        + " · файлов " + (row.files || 0)
        + " · новых " + (row.added || 0)
        + " · замен " + (row.replaced || 0)
        + kindLabel + "</span>";
      btn.onclick = (function (sid) {
        return function () {
          window.uninstallSubmod(sid);
        };
      })(id);
      box.appendChild(btn);
      n++;
    }
    if (n === 0) {
      var empty = document.createElement("div");
      empty.className = "pack-empty";
      empty.textContent = filter === "spritepack" ? "спрайтпаков пока нет" : "сабмодов пока нет";
      box.appendChild(empty);
    }
  }

  function fillTable(tbody, rows, filter) {
    if (!tbody) {
      return;
    }
    tbody.innerHTML = "";
    var i;
    var n = 0;
    for (i = 0; i < rows.length; i++) {
      var row = rows[i] || {};
      var kind = String(row.kind || "submod");
      if (filter === "spritepack") {
        if (kind !== "spritepack") {
          continue;
        }
      } else if (kind === "spritepack") {
        continue;
      }
      var id = String(row.id || "");
      var pack = String(row.pack || id || "пак");
      var kindLabel = kind === "assetpack" ? " · рескин" : "";
      var tr = document.createElement("tr");
      tr.innerHTML = "<td><span class=\"pack-name\">" + esc(pack)
        + "</span><span class=\"pack-id\">" + esc(id) + kindLabel + "</span></td>"
        + "<td class=\"num\">" + (row.files || 0) + "</td>"
        + "<td class=\"num\">" + (row.added || 0) + "</td>"
        + "<td class=\"num\">" + (row.replaced || 0) + "</td>"
        + "<td></td>";
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "pack-del";
      btn.textContent = "удалить";
      btn.onclick = (function (sid) {
        return function () {
          window.uninstallSubmod(sid);
        };
      })(id);
      tr.lastChild.appendChild(btn);
      tbody.appendChild(tr);
      n++;
    }
    if (n === 0) {
      var tr0 = document.createElement("tr");
      tr0.innerHTML = "<td class=\"pack-empty\" colspan=\"5\">"
        + (filter === "spritepack" ? "спрайтпаков пока нет" : "сабмодов пока нет")
        + "</td>";
      tbody.appendChild(tr0);
    }
  }

  window.biosSubmods = function (raw) {
    var rows = [];
    try {
      rows = JSON.parse(raw || "[]");
    } catch (e) {
      rows = [];
    }
    fillCards($("submodCards"), rows, "submod");
    fillCards($("spriteCards"), rows, "spritepack");
    fillTable($("submodTable"), rows, "submod");
    fillTable($("spriteTable"), rows, "spritepack");
    fillLibrary($("allPackTable"), rows);
  };

  function kindName(kind) {
    if (kind === "spritepack") {
      return "спрайт";
    }
    if (kind === "assetpack") {
      return "рескин";
    }
    return "сабмод";
  }

  function kindClass(kind) {
    if (kind === "spritepack") {
      return "sprite";
    }
    if (kind === "assetpack") {
      return "reskin";
    }
    return "sub";
  }

  function fillLibrary(tbody, rows) {
    if (!tbody) {
      return;
    }
    tbody.innerHTML = "";
    var i;
    var n = 0;
    for (i = 0; i < rows.length; i++) {
      var row = rows[i] || {};
      var kind = String(row.kind || "submod");
      var id = String(row.id || "");
      var pack = String(row.pack || id || "пак");
      var tr = document.createElement("tr");
      tr.innerHTML = "<td><span class=\"pack-name\">" + esc(pack)
        + "</span><span class=\"pack-id\">" + esc(id) + "</span></td>"
        + "<td><span class=\"kind-pill " + kindClass(kind) + "\">"
        + esc(kindName(kind)) + "</span></td>"
        + "<td class=\"num\">" + (row.files || 0) + "</td>"
        + "<td></td>";
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "pack-del";
      btn.textContent = "снять";
      btn.onclick = (function (sid) {
        return function () {
          window.uninstallSubmod(sid);
        };
      })(id);
      tr.lastChild.appendChild(btn);
      tbody.appendChild(tr);
      n++;
    }
    if (n === 0) {
      var tr0 = document.createElement("tr");
      tr0.innerHTML = "<td class=\"pack-empty\" colspan=\"4\">пока пусто — добавь zip во вкладке Контент</td>";
      tbody.appendChild(tr0);
    }
  }

  window.biosUrlHistory = function (raw) {
    var box = $("urlHistory");
    if (!box) {
      return;
    }
    var rows = [];
    try {
      rows = JSON.parse(raw || "[]");
    } catch (e) {
      rows = [];
    }
    box.innerHTML = "";
    if (!rows.length) {
      var empty = document.createElement("div");
      empty.className = "hist-empty";
      empty.textContent = "история пустая — ссылки появятся после скачивания";
      box.appendChild(empty);
      return;
    }
    var i;
    for (i = 0; i < rows.length; i++) {
      var row = rows[i] || {};
      var url = String(row.url || row || "");
      if (!url) {
        continue;
      }
      var wrap = document.createElement("div");
      wrap.className = "hist-row";
      var chip = document.createElement("button");
      chip.type = "button";
      chip.className = "hist-chip";
      chip.textContent = url;
      chip.onclick = (function (u) {
        return function () {
          window.useHistoryUrl(u);
        };
      })(url);
      var x = document.createElement("button");
      x.type = "button";
      x.className = "hist-x";
      x.setAttribute("aria-label", "убрать");
      x.textContent = "×";
      x.onclick = (function (u) {
        return function () {
          biosLog("\n→ removeUrlHistory");
          try {
            if (window.BiosBridge && BiosBridge.removeUrlHistory) {
              BiosBridge.removeUrlHistory(u);
            }
          } catch (err) {
          }
        };
      })(url);
      wrap.appendChild(chip);
      wrap.appendChild(x);
      box.appendChild(wrap);
    }
  };

  window.callBridge = function (name) {
    biosLog("\n→ " + name);
    try {
      if (window.BiosBridge && BiosBridge[name]) {
        BiosBridge[name]();
        return;
      }
    } catch (e) {
      biosLog("\nкнопка не сработала: " + name);
      return;
    }
    if (PREVIEW) {
      biosLog("  (предпросмотр, Java ещё нет)");
    } else {
      biosLog("  мост не готов");
    }
  };

  function bindOpeners(root) {
    if (!root) {
      return;
    }
    root.addEventListener("click", function (ev) {
      var t = ev.target;
      while (t && t !== root && !(t.getAttribute && t.getAttribute("data-open"))) {
        t = t.parentNode;
      }
      if (!t || !t.getAttribute) {
        return;
      }
      var name = t.getAttribute("data-open");
      if (name) {
        ev.preventDefault();
        ev.stopPropagation();
        biosOpen(name);
      }
    }, true);
  }

  function bindNav() {
    bindOpeners($("nav"));
    bindOpeners($("deckBar"));
    bindOpeners($("maslChrome"));
    var wall = document.querySelector(".masl-wallpaper");
    if (wall) {
      wall.addEventListener("click", function () {
        closeMaslMenus();
      });
    }
  }

  function boot() {
    bindNav();
    tickClock();
    setInterval(tickClock, 10000);
    var saved = "classic";
    try {
      saved = localStorage.getItem("mas_bios_view") || "classic";
    } catch (e) {
      saved = "classic";
    }
    applyBiosView(saved);
    var open = queryOpen();
    if (open) {
      biosOpen(open);
    } else if (saved !== "masl") {
      biosOpen(currentSec || "play");
    }
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
        skipBios: false,
        tracebackOk: false
      });
      biosLog("MAS BIOS\nслева категории и кнопки, справа журнал.\nвид переключается кнопкой «вид».\n");
      biosSubmods(JSON.stringify([
        { id: "demo", pack: "пример сабмода", files: 12, added: 8, replaced: 4, kind: "submod" },
        { id: "angel", pack: "Fallen Angel", files: 40, added: 40, replaced: 0, kind: "spritepack" },
        { id: "neon", pack: "pong neon", files: 2, added: 0, replaced: 2, kind: "assetpack" }
      ]));
      biosUrlHistory(JSON.stringify([
        { url: "https://github.com/user/mas-submod" },
        { url: "https://example.com/pong-neon.zip" }
      ]));
      biosProgress("пример загрузки 42 МБ", 42);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
