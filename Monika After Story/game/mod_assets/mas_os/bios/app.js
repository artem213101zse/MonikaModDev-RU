(function () {
  var PREVIEW = !(window.BiosBridge);

  var ICO = {
    play: '<polygon points="6 4 20 12 6 20 6 4"/>',
    package: '<path d="M16.5 9.4 7.5 4.21"/><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.29 7 12 12 20.71 7"/><line x1="12" y1="22" x2="12" y2="12"/>',
    database: '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>',
    download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>',
    settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
    chevronLeft: '<polyline points="15 18 9 12 15 6"/>',
    chevronRight: '<polyline points="9 18 15 12 9 6"/>',
    shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    hardDrive: '<line x1="22" y1="12" x2="2" y2="12"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/><line x1="6" y1="16" x2="6.01" y2="16"/><line x1="10" y1="16" x2="10.01" y2="16"/>',
    folder: '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>',
    archive: '<polyline points="21 8 21 21 3 21 3 8"/><rect x="1" y="3" width="22" height="5"/><line x1="10" y1="12" x2="14" y2="12"/>',
    checkCircle: '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
    file: '<path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/>',
    filePlus: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/>',
    gift: '<polyline points="20 12 20 22 4 22 4 12"/><rect x="2" y="7" width="20" height="5"/><line x1="12" y1="22" x2="12" y2="7"/><path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z"/><path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z"/>',
    music: '<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>',
    image: '<rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>',
    library: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
    trash: '<polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/>',
    save: '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>',
    share: '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>',
    heart: '<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>',
    search: '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
    refresh: '<polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>',
    smartphone: '<rect x="5" y="2" width="14" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12.01" y2="18"/>',
    cpu: '<rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/>',
    terminal: '<polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/>',
    folderOpen: '<path d="m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2v2"/>',
    alert: '<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    moon: '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>',
    sun: '<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>',
    sparkles: '<path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/><path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/>',
    pause: '<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>',
    x: '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
    cloud: '<polyline points="8 17 12 21 16 17"/><line x1="12" y1="12" x2="12" y2="21"/><path d="M20.88 18.09A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.29"/>',
    link: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
    clock: '<circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15 14"/>',
    broom: '<path d="M14 3 4 13"/><path d="m4 13 2 7 5-2 3-5"/><path d="m6 16 3 1"/><path d="m7 19 3 1"/>',
    eraser: '<path d="m7 21-4.3-4.3c-1-1-1-2.5 0-3.4l9.6-9.6c1-1 2.5-1 3.4 0l5.6 5.6c1 1 1 2.5 0 3.4L13 21"/><path d="M22 21H7"/><path d="m5 11 9 9"/>',
    clipboard: '<rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>',
    code: '<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>',
    home: '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',
    layout: '<rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/>',
    wrench: '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',
    dot: '<circle cx="12" cy="12" r="4"/>'
  };

  var CATS = [
    { id: "play", label: "Игра", icon: "play", hint: "Слева запуск и characters. Справа архивы базы DDLC." },
    { id: "content", label: "Контент", icon: "package", hint: "Блок установки пакета и библиотека того, что уже стоит." },
    { id: "data", label: "Данные", icon: "database", hint: "Блок импорта, экспорт и таблица архивов. Поделиться — у строки." },
    { id: "dl", label: "Загрузки", icon: "download", hint: "Обновление порта: проверка, скачивание и установка APK." },
    { id: "set", label: "Настройки", icon: "settings", hint: "Сразу MAS, тема и анимации." },
    { id: "repair", label: "Ремонт", icon: "wrench", hint: "Безопасный режим, Моника и шахматы." }
  ];

  var SEC_TO_CAT = {
    play: "play",
    files: "content", content: "content", library: "content",
    submods: "content", sprites: "content",
    saves: "data", data: "data",
    archives: "dl", update: "dl", dl: "dl",
    engine: "set", system: "set", more: "set", set: "set",
    recovery: "repair", repair: "repair", safe: "repair", chess: "repair"
  };

  var catId = "play";
  var slim = false;
  var logOpen = false;
  var logAlert = false;
  var job = { cmd: "", phase: "idle", text: "" };
  var archFlash = "";
  var archFlashTimer = 0;
  var archNudgeTimer = 0;
  var theme = "dark";
  var anim = true;
  var contentUrl = "";
  var uciCmd = "";
  var enterAnim = true;
  var packRows = [];
  var urlRows = [];
  var exportRows = [];
  var status = {
    path: "Documents/Monika_after_story",
    version: "порт",
    filesOk: false,
    engineOk: false,
    skipBios: false,
    archivesOk: false,
    tracebackOk: false,
    updateNeeded: false,
    safeMode: false,
    charsNew: false,
    charsCount: 0
  };
  var dl = { text: "", pct: -1, state: "idle" };
  var LOG_HUES = [
    "#7ee0d6",
    "#c9b3ff",
    "#7ee0a6",
    "#ffd07a",
    "#7ab8ff",
    "#ff9ec4",
    "#e8d48a",
    "#9ee8ff"
  ];
  var logHue = -1;
  var logColor = LOG_HUES[0];

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

  function esc(s) {
    return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function ico(name) {
    return '<svg xmlns="http://www.w3.org/2000/svg" class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (ICO[name] || ICO.dot) + "</svg>";
  }

  function wrapIco(name) {
    return '<span class="ico-wrap">' + ico(name) + "</span>";
  }

  function lsGet(key, fallback) {
    try {
      var v = localStorage.getItem(key);
      return v == null ? fallback : v;
    } catch (e) {
      return fallback;
    }
  }

  function lsSet(key, value) {
    try {
      localStorage.setItem(key, value);
    } catch (e) {
    }
  }

  function persistPref(key, value) {
    lsSet("mas_bios_" + key, value);
    try {
      if (window.BiosBridge && BiosBridge.setBiosPref) {
        BiosBridge.setBiosPref(key, value);
      }
    } catch (e) {
    }
  }

  function cat() {
    var i;
    for (i = 0; i < CATS.length; i++) {
      if (CATS[i].id === catId) {
        return CATS[i];
      }
    }
    return CATS[0];
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

  function bumpLogColor() {
    logHue = (logHue + 1) % LOG_HUES.length;
    logColor = LOG_HUES[logHue];
    return logColor;
  }

  function formatChunkHtml(text) {
    var s = String(text == null ? "" : text);
    var isCmd = s.indexOf("→ ") >= 0 && s.indexOf("→ ") <= 2;
    if (!isCmd && s.indexOf("\n→ ") >= 0) {
      isCmd = true;
    }
    if (isCmd) {
      bumpLogColor();
    }
    var lines = s.replace(/^\n+/, "").split(/\r?\n/);
    var out = [];
    var i;
    for (i = 0; i < lines.length; i++) {
      var line = lines[i];
      if (!line || !String(line).replace(/\s+/g, "")) {
        continue;
      }
      out.push(
        '<span class="log-op" style="color:' + logColor + '"><span class="log-time">[' +
          stamp() + '] </span><span class="log-msg">' + guessLevel(line) + "  " +
          esc(line) + "</span></span>"
      );
    }
    if (!out.length) {
      return "";
    }
    if (isCmd) {
      return '<span class="log-sep" style="color:' + logColor + '">────────</span>' + out.join("");
    }
    return out.join("");
  }

  function classifyLine(line) {
    var s = String(line || "").toLowerCase();
    if (!s.replace(/\s+/g, "")) {
      return "";
    }
    if (s.indexOf("ошиб") >= 0 || s.indexOf("не удал") >= 0 || s.indexOf("failed") >= 0
        || s.indexOf("не найден") >= 0 || s.indexOf("не проч") >= 0 || s.indexOf("не создан") >= 0
        || s.indexOf("mismatch") >= 0 || s.indexOf("нельзя") >= 0 || s.indexOf("нет ") >= 0
        || s.indexOf("не сработ") >= 0 || s.indexOf("сначала") >= 0
        || s.indexOf("не хватает") >= 0 || s.indexOf("не скач") >= 0
        || s.indexOf("отмен") >= 0) {
      return "err";
    }
    if (s.indexOf("установлен") >= 0 || s.indexOf("готово") >= 0 || s.indexOf("готов.") >= 0
        || s.indexOf("заверш") >= 0 || s.indexOf("записан") >= 0 || s.indexOf("сохран") >= 0
        || s.indexOf("на месте") >= 0 || s.indexOf("открыл") >= 0 || s.indexOf("очищ") >= 0
        || s.indexOf("экспорт") >= 0 || s.indexOf("импорт") >= 0) {
      return "ok";
    }
    if (s.indexOf("распак") >= 0 || s.indexOf("копиру") >= 0 || s.indexOf("ставлю") >= 0
        || s.indexOf("файлов:") >= 0 || s.indexOf("достаю") >= 0 || s.indexOf("из zip") >= 0) {
      return "unpack";
    }
    if (s.indexOf("пауза") >= 0) {
      return "pause";
    }
    return "load";
  }

  function phaseLabel(phase) {
    if (phase === "err") {
      return "Ошибка";
    }
    if (phase === "unpack") {
      return "Распаковка";
    }
    if (phase === "ok") {
      return "Готово";
    }
    if (phase === "pause") {
      return "Пауза";
    }
    return "Загрузка";
  }

  function paintLogBtn() {
    var dot = $("logDot");
    if (!dot) {
      return;
    }
    if (logAlert) {
      dot.removeAttribute("hidden");
    } else {
      dot.setAttribute("hidden", "hidden");
    }
  }

  function paintJobs() {
    var tileCmd = {};
    var marked = document.querySelectorAll(".tile[data-cmd]");
    var n;
    for (n = 0; n < marked.length; n++) {
      tileCmd[marked[n].getAttribute("data-cmd")] = true;
    }
    var nodes = document.querySelectorAll(".tile[data-cmd], .hero-act[data-cmd], .arch-btn[data-cmd], .arch-btn[data-job]");
    var i;
    for (i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      var cmd = el.getAttribute("data-job") || el.getAttribute("data-cmd") || el.id;
      if (el.className.indexOf("hero-act") >= 0 && tileCmd[cmd]) {
        continue;
      }
      var stat = el.querySelector(".jobstat");
      if (stat && stat.parentNode === el) {
        el.removeChild(stat);
      }
      el.className = el.className.replace(/\s*job-run|\s*job-ok|\s*job-err/g, "");
      if (!job.cmd || cmd !== job.cmd || job.phase === "idle") {
        continue;
      }
      var cls = job.phase === "ok" ? "job-ok" : (job.phase === "err" ? "job-err" : "job-run");
      el.className += " " + cls;
      var row = document.createElement("span");
      row.className = "jobstat";
      if (job.cmd === "checkArchives") {
        if (job.phase === "ok") {
          row.className = "jobstat mark ok";
          row.innerHTML = ico("checkCircle");
        } else if (job.phase === "err") {
          row.className = "jobstat mark bad";
          row.innerHTML = ico("x");
        } else {
          row.innerHTML = '<i class="spin"></i>';
        }
      } else {
        row.innerHTML = (job.phase === "ok" || job.phase === "err" || job.phase === "pause" ? "" : '<i class="spin"></i>')
          + "<em>" + esc(job.text || phaseLabel(job.phase)) + "</em>";
      }
      el.appendChild(row);
    }
    paintLogBtn();
  }

  function noteLine(line) {
    var phase = classifyLine(line);
    if (!phase) {
      return;
    }
    if (!job.cmd) {
      return;
    }
    if (phase === "err") {
      logAlert = true;
    }
    if (phase === "err" && archiveJob() && !dlBusy()) {
      endArchiveJob(true);
      paintLogBtn();
      if (catId === "play") {
        quietRender();
      }
      return;
    }
    job.phase = phase;
    if (phase === "load" && dl.pct >= 0 && dl.pct < 100) {
      job.text = "Загрузка " + Math.round(dl.pct) + "%";
    } else {
      job.text = phaseLabel(phase);
    }
    paintJobs();
    paintArchHead();
    var archLine = $("archLine");
    if (archLine && archiveWorking()) {
      archLine.textContent = String(line || "");
    }
  }

  function needsJob(cmd) {
    return cmd === "downloadDdlcMoe" || cmd === "pickArchive" || cmd === "installArchives"
      || cmd === "deleteArchives" || cmd === "checkArchives"
      || cmd === "downloadUpdate" || cmd === "downloadUpdateAgain"
      || cmd === "installLocalApk" || cmd === "downloadSubmodUrl" || cmd === "pickSubmodZip";
  }

  function archiveJob() {
    return job.cmd === "downloadDdlcMoe" || job.cmd === "pickArchive"
      || job.cmd === "installArchives" || job.cmd === "deleteArchives";
  }

  function archiveWorking() {
    return dlBusy() && archiveJob();
  }

  function beginJob(cmd) {
    if (!needsJob(cmd)) {
      return;
    }
    job.cmd = cmd;
    job.phase = "load";
    job.text = "Загрузка";
    if (cmd === "downloadDdlcMoe") {
      dl.state = "running";
      dl.text = "Идёт загрузка базы…";
      dl.pct = -1;
      try {
        document.documentElement.setAttribute("data-dl", "running");
        document.body.setAttribute("data-dl", "running");
      } catch (e1) {
      }
    }
    paintJobs();
    if (cmd === "downloadDdlcMoe" && catId === "play") {
      quietRender();
    }
  }

  function journalPlain() {
    var log = $("log");
    if (!log) {
      return "";
    }
    return String(log.innerText || log.textContent || "");
  }

  function openLog() {
    var modal = $("logModal");
    if (!modal) {
      return;
    }
    logAlert = false;
    modal.removeAttribute("hidden");
    paintLogBtn();
    var log = $("log");
    if (log) {
      log.scrollTop = log.scrollHeight;
    }
  }

  function closeLog() {
    var modal = $("logModal");
    if (modal) {
      modal.setAttribute("hidden", "hidden");
    }
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
    var raw = String(text);
    var bits = raw.split("\n");
    var i;
    var last = "";
    for (i = 0; i < bits.length; i++) {
      if (String(bits[i]).replace(/\s+/g, "")) {
        last = bits[i];
      }
    }
    log.innerHTML += formatChunkHtml(text);
    log.scrollTop = log.scrollHeight;
    if (last) {
      noteLine(last);
    }
  };

  window.clearBiosLog = function () {
    var log = $("log");
    if (log) {
      log.innerHTML = "";
    }
    logHue = -1;
    logColor = LOG_HUES[0];
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

  function paintBusyBars() {
    var on = dlBusy() || (dl.pct >= 0 && dl.pct < 100 && dl.state === "running");
    var arch = $("archBar");
    if (arch) {
      if (on && (archiveJob() || catId === "play")) {
        arch.removeAttribute("hidden");
      } else {
        arch.setAttribute("hidden", "hidden");
      }
    }
    var top = $("topDl");
    var showTop = on && !((archiveJob() || !job.cmd) && catId === "play") && !(catId === "dl" && !archiveJob());
    if (on && archiveJob() && catId !== "play") {
      showTop = true;
    }
    if (on && !archiveJob() && job.cmd && catId !== "dl") {
      showTop = true;
    }
    if (!on) {
      showTop = false;
    }
    if (top) {
      if (showTop) {
        top.removeAttribute("hidden");
      } else {
        top.setAttribute("hidden", "hidden");
      }
    }
    var topText = $("topDlText");
    if (topText) {
      topText.textContent = dl.text || "";
    }
    var archLine = $("archLine");
    if (archLine && dl.text) {
      archLine.textContent = String(dl.text);
    }
    paintArchHead();
    var topBar = $("topDlBar");
    var n = dl.pct;
    if (n === undefined || n === null || n < 0) {
      n = on ? 34 : 0;
    }
    if (n > 100) {
      n = 100;
    }
    if (topBar) {
      topBar.style.width = n + "%";
    }
  }

  function paintArchHead() {
    var title = $("archTitle");
    if (!title || !archiveWorking()) {
      return;
    }
    if (dl.state === "paused" || job.phase === "pause") {
      title.textContent = "Пауза";
    } else if (job.phase === "unpack") {
      title.textContent = "Распаковка";
    } else {
      title.textContent = "Скачивание";
    }
  }

  function endArchiveJob(failed) {
    job.cmd = "";
    job.phase = "idle";
    job.text = "";
    dl.text = "";
    dl.pct = -1;
    if (failed) {
      flashArchFail();
    }
  }

  function paintDlStrip() {
    var strip = $("dlstrip");
    var line = $("progressLine");
    var bar = $("bar");
    var pctEl = $("dlPct");
    var jobBar = $("dlBar");
    var jobPct = $("dlJobPct");
    var n = dl.pct;
    paintBusyBars();
    if (line) {
      line.textContent = dl.text ? String(dl.text) : "";
    }
    if (strip) {
      if (dlBusy() || (dl.text && dl.state !== "idle")) {
        strip.removeAttribute("hidden");
      } else {
        strip.setAttribute("hidden", "hidden");
      }
    }
    if (n === undefined || n === null || n < 0) {
      if (bar) {
        bar.style.width = dl.text ? "34%" : "0";
      }
      if (pctEl) {
        pctEl.textContent = dl.text ? "…" : "";
      }
      if (jobBar) {
        jobBar.style.width = dl.text ? "34%" : "0";
      }
      if (jobPct) {
        jobPct.textContent = dl.text ? "…" : "—";
      }
      return;
    }
    if (n > 100) {
      n = 100;
    }
    if (bar) {
      bar.style.width = n + "%";
    }
    if (pctEl) {
      pctEl.textContent = n + "%";
    }
    if (jobBar) {
      jobBar.style.width = n + "%";
    }
    if (jobPct) {
      jobPct.textContent = n + "%";
    }
  }

  function dlBusy() {
    return dl.state === "running" || dl.state === "paused";
  }

  function dlTitle() {
    if (dl.state === "paused") {
      return "Пауза";
    }
    if (dl.state === "running") {
      return "Идёт загрузка";
    }
    if (status.archivesOk) {
      return "Готово";
    }
    return "Качать недостающее";
  }

  function dlStateLabel() {
    if (dl.state === "paused") {
      return "пауза";
    }
    if (dl.state === "running") {
      return "качается";
    }
    if (status.archivesOk) {
      return "завершено";
    }
    return "ожидание";
  }

  function flashArchFail() {
    archFlash = "bad";
    if (archFlashTimer) {
      clearTimeout(archFlashTimer);
    }
    archFlashTimer = setTimeout(function () {
      archFlash = "";
      archFlashTimer = 0;
      if (catId === "play") {
        quietRender();
      }
    }, 2800);
  }

  function pokeArchives() {
    if (catId !== "play") {
      catId = "play";
      render();
    }
    var panel = document.querySelector(".play-board .arch-panel");
    if (!panel) {
      return;
    }
    if (archNudgeTimer) {
      clearInterval(archNudgeTimer);
      archNudgeTimer = 0;
    }
    var ticks = 0;
    panel.className = panel.className.replace(/\s*nudge/g, "") + " nudge";
    archNudgeTimer = setInterval(function () {
      ticks++;
      var live = document.querySelector(".play-board .arch-panel");
      if (!live || ticks >= 6) {
        clearInterval(archNudgeTimer);
        archNudgeTimer = 0;
        if (live && live.className) {
          live.className = live.className.replace(/\s*nudge/g, "");
        }
        return;
      }
      if (live.className.indexOf("nudge") >= 0) {
        live.className = live.className.replace(/\s*nudge/g, "");
      } else {
        live.className += " nudge";
      }
    }, 380);
  }

  window.biosChars = function (raw) {
    var info = {};
    try {
      info = JSON.parse(raw || "{}");
    } catch (e) {
      info = {};
    }
    var box = $("charsList");
    var path = $("charsPath");
    var files = info.files || [];
    if (path) {
      path.textContent = info.path ? ("Путь: " + info.path) : "Папка characters недоступна.";
    }
    if (box) {
      if (!files.length) {
        box.innerHTML = "<p class=\"arch-note\">Пока пусто. Моника кладёт сюда подарки.</p>";
      } else {
        var html = "";
        var i;
        for (i = 0; i < files.length; i++) {
          html += "<div class=\"chars-row\">" + ico("file") + "<span>" + esc(files[i]) + "</span></div>";
        }
        box.innerHTML = html;
      }
    }
    var modal = $("charsModal");
    if (modal) {
      modal.removeAttribute("hidden");
    }
    var hint = $("charsHint");
    if (hint) {
      hint.textContent = info.path
        ? "Открой «Файлы» на телефоне и зайди: Documents → Monika_after_story → characters."
        : "Папка сейчас недоступна. Сначала разреши доступ к файлам.";
    }
  };

  window.biosDlState = function (state) {
    var s = String(state || "idle");
    var wasArchive = archiveJob();
    dl.state = s;
    if (s === "idle") {
      if (wasArchive) {
        var failed = job.phase === "err" || (job.phase !== "ok" && !status.archivesOk);
        endArchiveJob(failed);
      } else if (status.archivesOk) {
        dl.text = "завершено";
        dl.pct = 100;
      } else if (dl.pct >= 100) {
        dl.text = "";
        dl.pct = -1;
      }
    }
    try {
      document.documentElement.setAttribute("data-dl", s);
      document.body.setAttribute("data-dl", s);
    } catch (e) {
    }
    paintDlStrip();
    rail();
    if (wasArchive && catId === "play") {
      quietRender();
    }
    var titleEl = $("dlHeroTitle");
    if (titleEl) {
      titleEl.textContent = dlTitle();
    }
    var stateEl = $("dlHeroState");
    if (stateEl) {
      stateEl.textContent = dlStateLabel();
    }
    var sub = $("dlHeroSub");
    if (sub && s === "idle") {
      sub.textContent = status.archivesOk ? "архивы готовы" : (dl.text || "images.rpa и audio.rpa");
    }
  };

  window.biosProgress = function (text, pct) {
    dl.text = text ? String(text) : "";
    dl.pct = (pct === undefined || pct === null) ? -1 : pct;
    if (job.cmd) {
      var phase = classifyLine(dl.text);
      if (dl.pct >= 100) {
        job.phase = "ok";
        job.text = "Готово";
      } else if (phase === "err") {
        job.phase = "err";
        job.text = "Ошибка";
        logAlert = true;
      } else if (phase === "unpack") {
        job.phase = "unpack";
        job.text = "Распаковка";
      } else if (dl.pct >= 0) {
        job.phase = "load";
        job.text = "Загрузка " + Math.round(dl.pct) + "%";
      } else if (dl.text) {
        job.phase = "load";
        job.text = "Загрузка";
      }
      paintJobs();
    }
    paintDlStrip();
  };

  function toggleChip(id, on) {
    var el = $(id);
    if (!el) {
      return;
    }
    el.className = on ? "chip on" : "chip";
  }

  window.biosSetStatus = function (info) {
    info = info || {};
    if (info.path) {
      status.path = String(info.path);
      var path = $("path");
      if (path) {
        path.textContent = status.path;
      }
    }
    if (info.version) {
      status.version = String(info.version);
      var ver = $("version");
      if (ver) {
        ver.textContent = status.version;
      }
    }
    if (info.filesOk !== undefined) {
      status.filesOk = !!info.filesOk;
    }
    if (info.engineOk !== undefined) {
      status.engineOk = !!info.engineOk;
    }
    if (info.skipBios !== undefined) {
      status.skipBios = !!info.skipBios;
    }
    var archChanged = false;
    if (info.archivesOk !== undefined) {
      archChanged = status.archivesOk !== !!info.archivesOk;
      status.archivesOk = !!info.archivesOk;
    }
    if (info.tracebackOk !== undefined) {
      status.tracebackOk = !!info.tracebackOk;
    }
    if (info.updateNeeded !== undefined) {
      status.updateNeeded = !!info.updateNeeded;
    }
    var safeChanged = false;
    if (info.safeMode !== undefined) {
      safeChanged = status.safeMode !== !!info.safeMode;
      status.safeMode = !!info.safeMode;
    }
    var charsChanged = false;
    if (info.charsNew !== undefined) {
      charsChanged = status.charsNew !== !!info.charsNew;
      status.charsNew = !!info.charsNew;
    }
    if (info.charsCount !== undefined) {
      var nextCount = Number(info.charsCount) || 0;
      if (status.charsCount !== nextCount) {
        charsChanged = true;
      }
      status.charsCount = nextCount;
    }
    toggleChip("chipFiles", status.filesOk);
    toggleChip("chipEngine", status.engineOk);
    toggleChip("chipSkip", status.skipBios);
    toggleChip("chipArchives", status.archivesOk);
    toggleChip("chipTrace", status.tracebackOk);
    var gate = $("permGate");
    if (gate) {
      if (PREVIEW || status.filesOk) {
        gate.setAttribute("hidden", "hidden");
      } else {
        gate.removeAttribute("hidden");
      }
    }
    var skip = $("skip");
    if (skip) {
      skip.className = status.skipBios ? "tog on" : "tog";
    }
    var safeTog = $("safeTog");
    if (safeTog) {
      safeTog.className = status.safeMode ? "tog on" : "tog";
    }
    rail();
    var arch = $("factArchives");
    if (arch) {
      arch.className = "st " + (status.archivesOk ? "ok" : "bad");
      arch.textContent = status.archivesOk ? "можно входить" : "архивы не полные";
    }
    if (
      (archChanged && (catId === "play" || catId === "dl"))
      || (safeChanged && catId === "repair")
      || (charsChanged && catId === "play")
    ) {
      quietRender();
    }
  };

  window.biosSetPrefs = function (info) {
    info = info || {};
    var changed = false;
    if (info.theme === "light" || info.theme === "dark") {
      if (theme !== info.theme) {
        theme = info.theme;
        changed = true;
      }
    }
    if (info.anim === "on" || info.anim === "off") {
      var nextAnim = info.anim === "on";
      if (anim !== nextAnim) {
        anim = nextAnim;
        changed = true;
      }
    }
    if (info.rail === "slim" || info.rail === "open") {
      var nextSlim = info.rail === "slim";
      if (slim !== nextSlim) {
        slim = nextSlim;
        changed = true;
      }
    }
    if (info.log === "open" || info.log === "slim") {
      var nextLog = info.log === "open";
      if (logOpen !== nextLog) {
        logOpen = nextLog;
        changed = true;
      }
    }
    if (changed) {
      applyChrome();
      quietRender();
    } else {
      applyChrome();
    }
  };

  window.applyBiosView = function () {};
  window.biosSetView = function () {};
  window.toggleBiosView = function () {};

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

  function rememberInputs() {
    var url = $("contentUrl");
    if (url) {
      contentUrl = url.value;
    }
    var uci = $("uciCmd");
    if (uci) {
      uciCmd = uci.value;
    }
  }

  function isCompact() {
    return (window.innerWidth || 0) < 1100 || (window.innerHeight || 0) < 700;
  }

  function applyChrome() {
    var html = document.documentElement;
    html.setAttribute("data-theme", theme);
    if (html.classList) {
      html.classList.toggle("anim", !!anim);
      html.classList.toggle("no-anim", !anim);
      html.classList.toggle("compact", isCompact());
    } else {
      html.className = (anim ? "anim" : "no-anim") + (isCompact() ? " compact" : "");
    }
    try {
      var meta = document.querySelector("meta[name=color-scheme]");
      if (meta) {
        meta.setAttribute("content", theme);
      }
    } catch (e) {
    }
    var app = $("app");
    if (app) {
      app.className = "app" + (slim ? " slim" : "") + (logOpen ? " log-open" : "");
    }
    var fold = $("fold");
    if (fold) {
      fold.innerHTML = ico(slim ? "chevronRight" : "chevronLeft");
      fold.title = slim ? "развернуть меню" : "свернуть меню";
    }
    var logfold = $("logfold");
    if (logfold) {
      logfold.innerHTML = ico(logOpen ? "chevronRight" : "chevronLeft");
      logfold.title = logOpen ? "свернуть журнал" : "развернуть журнал";
    }
    if (dl.state) {
      html.setAttribute("data-dl", dl.state);
    }
  }

  function rail() {
    var i;
    var c;
    var html = "";
    var on;
    var badge;
    var busy = dlBusy();
    for (i = 0; i < CATS.length; i++) {
      c = CATS[i];
      if (c.id === "repair") {
        html += '<div class="rail-gap"></div>';
      }
      on = c.id === catId ? " on" : "";
      badge = "";
      if (c.id === "play" && (status.charsNew || (busy && archiveJob()))) {
        badge = '<em class="dot"></em>';
      } else if (c.id === "dl" && busy && !archiveJob()) {
        badge = '<em class="dot"></em>';
      } else if (c.id === "set" && status.updateNeeded) {
        badge = '<em class="dot"></em>';
      } else if (c.id === "repair" && status.safeMode) {
        badge = '<em class="dot"></em>';
      }
      html += '<button type="button" class="cat' + on + '" data-cat="' + c.id +
        '" title="' + c.label + '">' + ico(c.icon) + "<span>" + c.label + "</span>" + badge + "</button>";
    }
    var el = $("rail");
    if (el) {
      el.innerHTML = html;
    }
  }

  function fact(name, val, cls, id) {
    return '<div class="fact"><span>' + name + '</span><span class="st ' + (cls || "") + '"' +
      (id ? ' id="' + id + '"' : "") + ">" + val + "</span></div>";
  }

  function bar(pct, id) {
    var n = pct;
    if (n < 0) {
      n = 0;
    }
    if (n > 100) {
      n = 100;
    }
    return '<div class="pbar"><i' + (id ? ' id="' + id + '"' : "") + ' style="width:' + n + '%"></i></div>';
  }

  function sm(o) {
    return '<button type="button" class="tile" data-cmd="' + o.cmd + '" data-t="' + esc(o.t) + '">' +
      (o.dot ? '<em class="dot"></em>' : "") +
      '<span class="row">' + wrapIco(o.icon) + '<span class="copy"><b>' + esc(o.t) +
      '</b><span class="s">' + esc(o.s) + "</span></span></span></button>";
  }

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
      btn.setAttribute("data-uninstall", id);
      btn.innerHTML = ico("trash") + '<span class="mini-txt"> снять</span>';
      tr.lastChild.appendChild(btn);
      tbody.appendChild(tr);
      n++;
    }
    if (n === 0) {
      var tr0 = document.createElement("tr");
      tr0.innerHTML = "<td class=\"pack-empty\" colspan=\"4\">пока пусто — поставь zip в Контент</td>";
      tbody.appendChild(tr0);
    }
  }

  function fillHistory(box, rows) {
    if (!box) {
      return;
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
      chip.setAttribute("data-hist", url);
      chip.textContent = url;
      var x = document.createElement("button");
      x.type = "button";
      x.className = "hist-x";
      x.setAttribute("aria-label", "убрать");
      x.setAttribute("data-hist-x", url);
      x.innerHTML = ico("x");
      wrap.appendChild(chip);
      wrap.appendChild(x);
      box.appendChild(wrap);
    }
  }

  window.biosSubmods = function (raw) {
    var rows = [];
    try {
      rows = JSON.parse(raw || "[]");
    } catch (e) {
      rows = [];
    }
    packRows = rows;
    fillLibrary($("allPackTable"), packRows);
  };

  window.biosUrlHistory = function (raw) {
    var rows = [];
    try {
      rows = JSON.parse(raw || "[]");
    } catch (e) {
      rows = [];
    }
    urlRows = rows;
    fillHistory($("urlHistory"), urlRows);
  };

  function fmtSize(n) {
    n = Number(n) || 0;
    if (n < 1024) {
      return n + " Б";
    }
    if (n < 1024 * 1024) {
      return (n / 1024).toFixed(1) + " КБ";
    }
    return (n / (1024 * 1024)).toFixed(1) + " МБ";
  }

  function fillExports(tbody, rows) {
    if (!tbody) {
      return;
    }
    tbody.innerHTML = "";
    var i;
    var n = 0;
    for (i = 0; i < rows.length; i++) {
      var row = rows[i] || {};
      var name = String(row.name || "");
      if (!name) {
        continue;
      }
      var tr = document.createElement("tr");
      tr.innerHTML = "<td><span class=\"pack-name\">" + esc(name)
        + "</span></td><td>" + esc(row.when || "") + "</td>"
        + "<td class=\"num\">" + esc(fmtSize(row.size)) + "</td><td></td>";
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "pack-share";
      btn.setAttribute("data-share", name);
      btn.innerHTML = ico("share") + '<span class="mini-txt"> отправить</span>';
      tr.lastChild.appendChild(btn);
      tbody.appendChild(tr);
      n++;
    }
    if (n === 0) {
      var tr0 = document.createElement("tr");
      tr0.innerHTML = "<td class=\"pack-empty\" colspan=\"4\">пока пусто — экспорт появится после кнопки Экспорт</td>";
      tbody.appendChild(tr0);
    }
  }

  window.biosExports = function (raw) {
    var rows = [];
    try {
      rows = JSON.parse(raw || "[]");
    } catch (e) {
      rows = [];
    }
    exportRows = rows;
    fillExports($("exportTable"), exportRows);
  };

  function archBtn(cmd, title, sub, primary, iconName, jobName) {
    return '<button type="button" class="arch-btn' + (primary ? " primary" : "") +
      '" data-cmd="' + cmd + '" data-t="' + esc(title) + '"' +
      (jobName ? ' data-job="' + jobName + '"' : "") + ">" + wrapIco(iconName || "dot") +
      '<span class="arch-copy"><b>' + esc(title) + "</b><span>" + esc(sub) + "</span></span></button>";
  }

  function archPanelHtml() {
    var working = archiveWorking();
    var ok = !!status.archivesOk;
    var title = ok ? "База на месте" : "База DDLC не стоит";
    if (working) {
      if (dl.state === "paused" || job.phase === "pause") {
        title = "Пауза";
      } else if (job.phase === "unpack") {
        title = "Распаковка";
      } else {
        title = "Скачивание";
      }
    }
    var mark = working ? "spin" : (archFlash === "bad" || !ok ? "bad" : "ok");
    var markIco = working ? '<i class="spin"></i>' : ico(mark === "ok" ? "checkCircle" : "x");
    var note = ok
      ? "Картинки и музыка официальной игры уже в папке. Проверь или удали, если нужно поставить заново. Сейвы и подарки удаление не трогает."
      : "Без картинок и музыки MAS не запустится. Нужен официальный файл ddlc-win.zip.";
    var html = '<div class="arch-panel' + (archFlash === "bad" ? " fail" : "") + '"><div class="arch-head">' + wrapIco("archive") +
      '<div><div class="k">архивы игры</div><b id="archTitle">' + title + "</b></div>" +
      '<span class="arch-ready ' + mark + '">' + markIco + "</span></div>";
    if (working) {
      html += '<p class="arch-note" id="archLine">' + esc(dl.text || "Идёт загрузка базы…") + "</p>";
      html += '<div class="arch-bar" id="archBar">' +
        '<div class="dl-line"><span>прогресс</span><span id="dlJobPct"></span></div>' +
        bar(dl.pct < 0 ? 8 : dl.pct, "dlBar") +
        '<div class="arch-actions arch-controls">' +
        '<button type="button" class="arch-mini dl-pause" data-cmd="pauseDownload">' + ico("pause") + " Пауза</button>" +
        '<button type="button" class="arch-mini dl-resume" data-cmd="resumeDownload">' + ico("play") + " Продолжить</button>" +
        '<button type="button" class="arch-mini" data-cmd="cancelDownload">' + ico("x") + " Отмена</button>" +
        "</div></div>";
    } else {
      html += '<p class="arch-note">' + esc(note) + "</p>";
      if (archFlash === "bad") {
        html += '<p class="arch-fail">' + ico("x") + " Не вышло. Можно попробовать снова.</p>";
      }
      html += '<div class="arch-actions">';
      if (!ok) {
        html += archBtn("downloadDdlcMoe", "Скачать автоматически", "Рекомендуется. Игра сама скачает ddlc-win.zip с ddlc.moe и поставит.", true, "download");
        html += archBtn("pickArchive", "Выбрать ddlc-win.zip", "Укажи файл ddlc-win.zip с диска. Это официальный архив игры.", false, "file");
      } else {
        html += archBtn("checkArchives", "Проверить", "Посмотреть, на месте ли картинки и музыка.", false, "search");
        html += archBtn("deleteArchives", "Удалить архивы", "Убрать базу DDLC, чтобы скачать её заново.", false, "trash");
      }
      html += "</div>";
    }
    html += "</div>";
    return html;
  }

  function boardHtml() {
    var bentoClass = "bento";
    if (catId === "content") {
      bentoClass += " content-board";
    }
    if (catId === "play") {
      bentoClass += " play-board";
    }
    if (catId === "dl") {
      bentoClass += " dl-board";
    }
    var html = '<p class="lead">' + cat().hint + '</p><div class="' + bentoClass + '">';
    if (catId === "play") {
      html += '<div class="play-side">' +
        '<div class="tile main' + (!status.archivesOk ? " locked" : (status.safeMode ? " safe" : "")) + '" data-cmd="startGame" data-t="Запустить MAS">' +
        wrapIco("play") + '<div class="k">запуск</div><b>Запустить MAS</b>' +
        '<span class="s">' + (!status.archivesOk ? "Не установлено" : (status.safeMode ? "Безопасный режим" : "Ren'Py → MAS OS → комната")) + "</span></div>" +
        '<div class="tile main quiet" data-cmd="peekCharacters" data-t="characters">' +
        (status.charsNew ? '<em class="dot"></em>' : "") +
        wrapIco("gift") + '<div class="k">characters</div><b>Папка characters</b>' +
        '<span class="s">Подарки и файлы, которые Моника кладёт сюда.</span>' +
        '<div class="facts">' +
        fact("файлов", String(status.charsCount || 0)) +
        fact("новое", status.charsNew ? "есть" : "нет", status.charsNew ? "bad" : "ok") +
        "</div></div></div>";
      html += archPanelHtml();
    } else if (catId === "content") {
      html += '<div class="arch-panel pack-panel">' +
        '<div class="arch-head">' + wrapIco("package") +
        '<div><div class="k">установить</div><b>Поставить пакет</b></div></div>' +
        '<div class="pack-split">' +
        '<div class="pack-copy"><p>Сабмод, спрайт или рескин. Файл с телефона или ссылка на zip — тип определится сам. Сейвы и база DDLC не затрагиваются.</p></div>' +
        '<div class="pack-actions">' +
        archBtn("pickSubmodZip", "Установить с диска", "Zip-файл пакета на телефоне.", false, "filePlus") +
        archBtn("openPackUrl", "По ссылке", "Адрес zip и недавние ссылки.", true, "link", "downloadSubmodUrl") +
        "</div></div></div>";
      html += '<div class="arch-panel library">' +
        '<div class="arch-head">' + wrapIco("library") +
        '<div><div class="k">библиотека</div><b>Что уже стоит</b></div></div>' +
        '<p class="arch-note">Снятие пака в таблице не трогает остальные.</p>' +
        '<div class="pack-table-wrap"><table class="pack-table"><thead><tr><th>Пак</th><th>тип</th><th>файлов</th><th></th></tr></thead><tbody id="allPackTable"></tbody></table></div></div>';
    } else if (catId === "data") {
      html += '<div class="arch-panel">' +
        '<div class="arch-head">' + wrapIco("save") +
        '<div><div class="k">сейвы</div><b>Импорт</b></div></div>' +
        '<p class="arch-note">Архив с другой сборки или уже распакованная папка. BIOS разложит persistent и слоты.</p>' +
        '<div class="arch-actions">' +
        archBtn("pickSavesZip", "Импорт zip", "Файл zip с сейвами.", false, "archive") +
        archBtn("pickSavesFolder", "Импорт папки", "Уже распакованные saves.", false, "folderOpen") +
        "</div></div>";
      html += '<div class="tile main quiet" data-cmd="exportSaves" data-t="Экспорт">' +
        wrapIco("archive") + '<div class="k">сейвы</div><b>Экспорт</b>' +
        '<span class="s">saves → mas_bios/backups. Потом можно поделиться архивом.</span>' +
        '<div class="facts">' + fact("куда", "mas_bios/backups") + fact("формат", "zip") + "</div></div>";
      html += '<div class="tile library" data-cmd="listExports" data-t="Экспорты">' +
        wrapIco("archive") + '<div class="k">экспорты</div><b>Сделанные архивы</b>' +
        '<span class="s">Удалить отсюда нельзя — чисти вручную в mas_bios/backups. Поделиться — у строки.</span>' +
        '<div class="pack-table-wrap"><table class="pack-table"><thead><tr><th>Файл</th><th>когда</th><th>размер</th><th></th></tr></thead><tbody id="exportTable"></tbody></table></div></div>';
    } else if (catId === "dl") {
      html += '<div class="tile main quiet wide">' +
        wrapIco("smartphone") + '<div class="k">порт</div><b>Обновление MAS</b>' +
        '<span class="s">Проверка релиза, скачивание APK и установка. Архивы базы — в разделе Игра.</span>' +
        '<div class="facts">' +
        fact("версия", esc(status.version || "порт")) +
        fact("обновление", status.updateNeeded ? "есть новое" : "не проверяли", status.updateNeeded ? "bad" : "") +
        "</div></div>";
      html += '<div class="dl-grid">';
      html += sm({ t: "Проверить APK", s: "последний release", cmd: "checkUpdate", icon: "search" });
      html += sm({ t: "Скачать APK", s: "если есть новая версия", cmd: "downloadUpdate", icon: "smartphone" });
      html += sm({ t: "Поставить скачанный", s: "files/update.apk", cmd: "installLocalApk", icon: "package" });
      html += sm({ t: "Скачать заново", s: "даже если тег тот же", cmd: "downloadUpdateAgain", icon: "refresh" });
      html += "</div>";
    } else if (catId === "repair") {
      html += '<div class="tile main" data-cmd="toggleSafeMode" data-t="Безопасный режим">' +
        wrapIco("shield") + '<div class="k">ремонт</div><b>Безопасный режим</b>' +
        '<span class="s">Заморозить сабмоды, спрайты, обои и музыку. Игра стартует стоком.</span>' +
        '<button type="button" class="tog' + (status.safeMode ? " on" : "") + '" id="safeTog"><i></i></button>' +
        '<div class="note">Контент лежит в mas_bios/frozen, пока тумблер включён. Выключи здесь же, когда починишь.</div>' +
        '<div class="facts">' +
        fact("сейчас", status.safeMode ? "включён" : "выключен", status.safeMode ? "bad" : "ok") +
        fact("контент", status.safeMode ? "заморожен" : "как стоит") +
        "</div></div>";
      html += '<div class="tile main quiet" data-cmd="recoverMonikaHome" data-t="Вернуть Монику">' +
        wrapIco("heart") + '<div class="k">моника</div><b>Вернуть за стол</b>' +
        '<span class="s">Пустой стол в игре ждёт characters/monika.</span>' +
        '<div class="facts">' + fact("файл", "проверить статус") + fact("поиск", "обход Documents") + "</div></div>";
      html += sm({ t: "Статус файла", s: "есть ли monika", cmd: "checkMonikaFile", icon: "file" });
      html += sm({ t: "Найти в Documents", s: "обход папок", cmd: "recoverMonikaScan", icon: "search" });
      html += sm({ t: "Вернуть в characters", s: "перенести найденный", cmd: "recoverMonikaRestore", icon: "home" });
      html += sm({ t: "Собрать заново", s: "из mbase", cmd: "recoverMonikaRebuild", icon: "refresh" });
      html += sm({ t: "uci шахмат", s: "libstockfish.so", cmd: "testStockfish", icon: "terminal" });
      html += sm({ t: "isready", s: "readyok", cmd: "stockfishReady", icon: "checkCircle" });
      html += sm({ t: "Ход depth 1", s: "startpos → bestmove", cmd: "stockfishGo", icon: "play" });
      html += '<div class="tile wide" data-cmd="sendStockfish" data-t="Отправить команду">' +
        '<span class="row">' + wrapIco("terminal") +
        '<span class="copy"><b>Команда UCI</b><span class="s">ответ Stockfish в журнал</span></span></span>' +
        '<input class="uci" id="uciCmd" type="text" autocomplete="off" placeholder="position startpos moves e2e4">' +
        "</div>";
    } else {
      html += '<div class="tile main" id="skipHero" data-cmd="toggleSkip" data-t="Сразу MAS">' +
        wrapIco("play") + '<div class="k">холодный старт</div><b>Сразу MAS</b>' +
        '<span class="s">Миновать BIOS при запуске приложения.</span>' +
        '<button type="button" class="tog' + (status.skipBios ? " on" : "") + '" id="skip"><i></i></button>' +
        '<div class="note">Вернуть BIOS из игры: в MAS OS открой плитку «BIOS». Если тумблер выключен, лаунчер снова встретит при холодном старте.</div></div>';
      html += '<div class="tile main quiet" data-cmd="setTheme" data-t="Тема">' +
        wrapIco(theme === "dark" ? "moon" : "sun") +
        '<div class="k">вид</div><b>' + (theme === "dark" ? "Тёмная тема" : "Светлая тема") + "</b>" +
        '<span class="s">Нажми, чтобы переключить. Запоминается на устройстве.</span>' +
        '<div class="swatch ' + (theme === "dark" ? "d" : "l") + '"></div>' +
        '<div class="facts">' + fact("сейчас", theme === "dark" ? "тёмная" : "светлая") + "</div></div>";
      html += '<div class="tile wide" id="animHero" data-cmd="toggleAnim" data-t="Анимации">' +
        '<span class="row">' + wrapIco("sparkles") +
        '<span class="copy"><b>Анимации</b><span class="s">Появление плиток и плавные переходы. Выключи, если мешают.</span></span>' +
        '<button type="button" class="tog' + (anim ? " on" : "") + '" id="animTog"><i></i></button></span></div>';
      html += sm({ t: "Все файлы", s: "разрешение Android 11+", cmd: "grantAllFiles", icon: "folderOpen" });
      html += sm({ t: "Documents", s: "папка порта", cmd: "openDocuments", icon: "folder" });
      html += sm({ t: "traceback", s: "почему не стартовала", cmd: "showTraceback", icon: "alert" });
      html += sm({ t: "Поделиться логами", s: "log.txt и traceback", cmd: "shareLogs", icon: "share" });
      html += sm({ t: "Проверить ELF", s: "libdir, размер, exec", cmd: "installEngine", icon: "cpu" });
      html += sm({ t: "hello_engine", s: "HELLO ENGINE OK", cmd: "testEngine", icon: "code" });
      html += sm({ t: "Старый xml", s: "если страница не грузится", cmd: "useNativeUi", icon: "layout" });
    }
    return html + "</div>";
  }

  function afterBoard() {
    var url = $("contentUrl");
    if (url) {
      url.value = contentUrl;
    }
    var uci = $("uciCmd");
    if (uci) {
      uci.value = uciCmd;
    }
    if (catId === "content") {
      fillLibrary($("allPackTable"), packRows);
      fillHistory($("urlHistory"), urlRows);
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
    if (catId === "data") {
      fillExports($("exportTable"), exportRows);
      try {
        if (window.BiosBridge && BiosBridge.listExports) {
          BiosBridge.listExports();
        }
      } catch (e5) {
      }
    }
    paintDlStrip();
    paintJobs();
  }

  function render() {
    rememberInputs();
    applyChrome();
    rail();
    var title = $("title");
    if (title) {
      title.textContent = cat().label;
    }
    var board = $("board");
    if (board) {
      if (!enterAnim) {
        board.className = "board no-enter";
      } else {
        board.className = "board";
      }
      try {
        board.innerHTML = boardHtml();
      } catch (err) {
        board.innerHTML = '<p class="lead">Раздел не открылся: ' + esc(err && err.message ? err.message : err) + "</p>";
      }
      board.scrollTop = 0;
    }
    afterBoard();
  }

  function quietRender() {
    enterAnim = false;
    render();
    enterAnim = true;
  }

  window.biosOpen = function (name) {
    var id = String(name || "play").toLowerCase();
    if (id === "submods" || id === "sprites") {
      id = "content";
    }
    catId = SEC_TO_CAT[id] || "play";
    render();
  };

  function pulseDownload() {
    var el = $("dlHero");
    if (!el) {
      return;
    }
    el.classList.remove("pulse");
    try {
      void el.offsetWidth;
    } catch (e) {
    }
    el.classList.add("pulse");
    setTimeout(function () {
      if (el && el.classList) {
        el.classList.remove("pulse");
      }
    }, 2200);
  }

  window.biosNeedArchives = function () {
    pokeArchives();
  };

  window.sendUci = function () {
    var el = $("uciCmd");
    var cmd = el && el.value ? String(el.value) : uciCmd;
    biosLog("\n→ sendStockfish " + cmd);
    try {
      if (window.BiosBridge && BiosBridge.sendStockfish) {
        BiosBridge.sendStockfish(cmd);
        return;
      }
    } catch (e) {
      biosLog("\nкнопка не сработала: sendStockfish");
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
    if (PREVIEW) {
      biosLog("  (предпросмотр, Java ещё нет)");
    }
    return false;
  }

  function closePackUrl() {
    var modal = $("packUrlModal");
    if (modal) {
      modal.setAttribute("hidden", "hidden");
    }
  }

  function openPackUrl() {
    var modal = $("packUrlModal");
    var input = $("contentUrl");
    if (input) {
      input.value = contentUrl || "";
      input.setAttribute("readonly", "readonly");
      try {
        input.blur();
      } catch (eBlur) {
      }
    }
    fillHistory($("urlHistory"), urlRows);
    if (modal) {
      modal.removeAttribute("hidden");
    }
    setTimeout(function () {
      var again = $("contentUrl");
      if (again && document.activeElement === again) {
        try {
          again.blur();
        } catch (eBlur2) {
        }
      }
    }, 60);
    try {
      if (window.BiosBridge && BiosBridge.listUrlHistory) {
        BiosBridge.listUrlHistory();
      }
    } catch (eHistOpen) {
    }
  }

  function unlockPackUrl() {
    var input = $("contentUrl");
    if (!input) {
      return;
    }
    input.removeAttribute("readonly");
    try {
      input.focus();
    } catch (eUnlock) {
    }
  }

  function closePackHistory() {
    var modal = $("packHistModal");
    if (modal) {
      modal.setAttribute("hidden", "hidden");
    }
  }

  function openPackHistory() {
    var modal = $("packHistModal");
    fillHistory($("urlHistory"), urlRows);
    if (modal) {
      modal.removeAttribute("hidden");
    }
    try {
      if (window.BiosBridge && BiosBridge.listUrlHistory) {
        BiosBridge.listUrlHistory();
      }
    } catch (eHist) {
    }
  }

  function pastePackUrl() {
    try {
      if (window.BiosBridge && BiosBridge.pasteClipboard) {
        BiosBridge.pasteClipboard();
        return;
      }
    } catch (ePaste) {
    }
    var input = $("contentUrl");
    if (window.navigator && navigator.clipboard && navigator.clipboard.readText) {
      navigator.clipboard.readText().then(function (text) {
        window.biosPaste(text);
      }, function () {
        biosLog("буфер недоступен");
      });
      return;
    }
    if (input) {
      try {
        input.focus();
      } catch (eFocus2) {
      }
    }
    biosLog("буфер недоступен");
  }

  window.biosPaste = function (text) {
    var value = String(text || "");
    var input = $("contentUrl");
    if (!value) {
      biosLog("в буфере нет текста");
      return;
    }
    contentUrl = value;
    if (input) {
      input.value = value;
      try {
        input.focus();
      } catch (eFocus3) {
      }
    }
  };

  window.downloadContent = function () {
    var el = $("contentUrl");
    var url = String(el && el.value ? el.value : contentUrl || "").replace(/^\s+|\s+$/g, "");
    if (!url) {
      biosLog("сначала вставь ссылку");
      return;
    }
    contentUrl = url;
    beginJob("downloadSubmodUrl");
    if (!sendPackUrl(url)) {
      job.cmd = "";
      job.phase = "idle";
      job.text = "";
      paintJobs();
      return;
    }
    closePackUrl();
  };

  window.downloadSubmod = window.downloadContent;
  window.downloadSpritepack = window.downloadContent;

  window.useHistoryUrl = function (url) {
    contentUrl = String(url || "");
    closePackHistory();
    openPackUrl();
    biosLog("подставил ссылку из истории");
  };

  window.shareExport = function (name) {
    var id = String(name || "");
    biosLog("\n→ shareExport " + id);
    try {
      if (window.BiosBridge && BiosBridge.shareExport) {
        BiosBridge.shareExport(id);
        return;
      }
    } catch (e) {
      biosLog("\nкнопка не сработала: shareExport");
    }
    if (PREVIEW) {
      biosLog("  (предпросмотр, Java ещё нет)");
    }
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
    if (PREVIEW) {
      biosLog("  (предпросмотр, Java ещё нет)");
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

  function runCmd(name, title) {
    beginJob(name);
    if (name === "startGame") {
      if (!status.archivesOk) {
        pokeArchives();
        return;
      }
      callBridge("startGame");
      return;
    }
    if (name === "toggleSafeMode") {
      if (PREVIEW) {
        status.safeMode = !status.safeMode;
        biosLog("безопасный режим: " + (status.safeMode ? "вкл, контент заморожен" : "выкл, контент возвращён"));
        quietRender();
        return;
      }
      callBridge("toggleSafeMode");
      return;
    }
    if (name === "downloadSubmodUrl" || name === "openPackUrl") {
      openPackUrl();
      return;
    }
    if (name === "openPackHistory") {
      openPackUrl();
      return;
    }
    if (name === "sendStockfish") {
      sendUci();
      return;
    }
    if (name === "setTheme") {
      theme = theme === "dark" ? "light" : "dark";
      persistPref("theme", theme);
      biosLog("тема: " + (theme === "light" ? "светлая" : "тёмная"));
      quietRender();
      return;
    }
    if (name === "toggleSkip") {
      status.skipBios = !status.skipBios;
      callBridge("toggleBoot");
      quietRender();
      return;
    }
    if (name === "toggleAnim") {
      anim = !anim;
      persistPref("anim", anim ? "on" : "off");
      biosLog("анимации: " + (anim ? "вкл" : "выкл"));
      applyChrome();
      quietRender();
      return;
    }
    if (name === "clearBiosLog") {
      clearBiosLog();
      return;
    }
    callBridge(name);
  }

  function upAttr(el, attr) {
    while (el && el !== document) {
      if (el.getAttribute && el.getAttribute(attr) != null && el.getAttribute(attr) !== "") {
        return el;
      }
      el = el.parentNode;
    }
    return null;
  }

  function upClass(el, cls) {
    while (el && el !== document) {
      if (el.classList && el.classList.contains(cls)) {
        return el;
      }
      el = el.parentNode;
    }
    return null;
  }

  function bindStatic() {
    var fold = $("fold");
    if (fold) {
      fold.onclick = function () {
        slim = !slim;
        persistPref("rail", slim ? "slim" : "open");
        applyChrome();
      };
    }
    var logfold = $("logfold");
    if (logfold) {
      logfold.onclick = function () {
        logOpen = !logOpen;
        persistPref("log", logOpen ? "open" : "slim");
        applyChrome();
      };
    }
    var railEl = $("rail");
    if (railEl) {
      railEl.addEventListener("click", function (e) {
        var b = upAttr(e.target, "data-cat");
        if (!b) {
          return;
        }
        catId = b.getAttribute("data-cat");
        render();
      });
    }
    var board = $("board");
    if (board) {
      board.addEventListener("click", function (e) {
        var uninstall = upAttr(e.target, "data-uninstall");
        var share = upAttr(e.target, "data-share");
        var histX = upAttr(e.target, "data-hist-x");
        var hist = upAttr(e.target, "data-hist");
        var cmd = upAttr(e.target, "data-cmd");
        if (uninstall) {
          e.stopPropagation();
          window.uninstallSubmod(uninstall.getAttribute("data-uninstall"));
          return;
        }
        if (share) {
          e.stopPropagation();
          window.shareExport(share.getAttribute("data-share"));
          return;
        }
        if (histX) {
          e.stopPropagation();
          biosLog("\n→ removeUrlHistory");
          try {
            if (window.BiosBridge && BiosBridge.removeUrlHistory) {
              BiosBridge.removeUrlHistory(histX.getAttribute("data-hist-x"));
            }
          } catch (err) {
          }
          if (PREVIEW) {
            biosLog("  (предпросмотр, Java ещё нет)");
          }
          return;
        }
        if (hist) {
          window.useHistoryUrl(hist.getAttribute("data-hist"));
          return;
        }
        if (upClass(e.target, "opt") || upClass(e.target, "url") || upClass(e.target, "uci")
            || upClass(e.target, "history-list")) {
          return;
        }
        if (cmd) {
          runCmd(cmd.getAttribute("data-cmd"), cmd.getAttribute("data-t"));
        }
      });
    }
    var logBtn = $("logBtn");
    if (logBtn) {
      logBtn.onclick = openLog;
    }
    var logClose = $("logClose");
    if (logClose) {
      logClose.innerHTML = ico("x");
      logClose.onclick = closeLog;
    }
    var charsModal = $("charsModal");
    var charsClose = $("charsClose");
    if (charsClose) {
      charsClose.innerHTML = ico("x");
      charsClose.onclick = function () {
        if (charsModal) {
          charsModal.setAttribute("hidden", "hidden");
        }
      };
    }
    if (charsModal) {
      charsModal.addEventListener("click", function (e) {
        if (e.target === charsModal) {
          charsModal.setAttribute("hidden", "hidden");
        }
      });
    }
    var packUrlModal = $("packUrlModal");
    var packUrlClose = $("packUrlClose");
    if (packUrlClose) {
      packUrlClose.innerHTML = ico("x");
      packUrlClose.onclick = closePackUrl;
    }
    if (packUrlModal) {
      packUrlModal.addEventListener("click", function (e) {
        if (e.target === packUrlModal) {
          closePackUrl();
        }
      });
    }
    var packPaste = $("packPaste");
    if (packPaste) {
      packPaste.innerHTML = ico("clipboard") + " Вставить";
      packPaste.onclick = pastePackUrl;
    }
    var packClear = $("packClear");
    if (packClear) {
      packClear.innerHTML = ico("eraser") + " Очистить";
      packClear.onclick = function () {
        contentUrl = "";
        var input = $("contentUrl");
        if (input) {
          input.value = "";
          input.setAttribute("readonly", "readonly");
          try {
            input.blur();
          } catch (eClear) {
          }
        }
      };
    }
    var packUrlInput = $("contentUrl");
    if (packUrlInput && !packUrlInput._arm) {
      packUrlInput._arm = true;
      packUrlInput.addEventListener("touchstart", unlockPackUrl);
      packUrlInput.addEventListener("mousedown", unlockPackUrl);
    }
    var packHistTitle = $("packHistTitle");
    if (packHistTitle) {
      packHistTitle.innerHTML = ico("clock") + " История";
    }
    var packGo = $("packGo");
    if (packGo) {
      packGo.innerHTML = ico("download") + " Установить";
      packGo.onclick = function () {
        downloadContent();
      };
    }
    var packHistModal = $("packHistModal");
    var packHistClose = $("packHistClose");
    if (packHistClose) {
      packHistClose.innerHTML = ico("x");
      packHistClose.onclick = closePackHistory;
    }
    var packHistClear = $("packHistClear");
    if (packHistClear) {
      packHistClear.innerHTML = ico("broom") + " Очистить";
      packHistClear.onclick = function () {
        callBridge("clearUrlHistory");
      };
    }
    if (packHistModal) {
      packHistModal.addEventListener("click", function (e) {
        if (e.target === packHistModal) {
          closePackHistory();
          return;
        }
        var histX = upAttr(e.target, "data-hist-x");
        var hist = upAttr(e.target, "data-hist");
        if (histX) {
          e.stopPropagation();
          try {
            if (window.BiosBridge && BiosBridge.removeUrlHistory) {
              BiosBridge.removeUrlHistory(histX.getAttribute("data-hist-x"));
            }
          } catch (errHist) {
          }
          return;
        }
        if (hist) {
          window.useHistoryUrl(hist.getAttribute("data-hist"));
        }
      });
    }
    var saveBtn = $("saveJournal");
    if (saveBtn) {
      saveBtn.innerHTML = ico("save") + " Сохранить";
      saveBtn.onclick = function () {
        try {
          if (window.BiosBridge && BiosBridge.saveJournal) {
            BiosBridge.saveJournal(journalPlain());
            return;
          }
        } catch (eSave) {
        }
        biosLog("\nЖурнал: мост сохранения не готов");
      };
    }
    var shareBtn = $("shareJournal");
    if (shareBtn) {
      shareBtn.innerHTML = ico("share") + " Поделиться";
      shareBtn.onclick = function () {
        try {
          if (window.BiosBridge && BiosBridge.shareJournal) {
            BiosBridge.shareJournal(journalPlain());
            return;
          }
        } catch (eShare) {
        }
        biosLog("\nЖурнал: мост отправки не готов");
      };
    }
    var wipe = $("wipeLog");
    if (wipe) {
      wipe.innerHTML = ico("eraser") + " Очистить";
      wipe.onclick = function () {
        clearBiosLog();
      };
    }
    var tr = $("btnTrace");
    if (tr) {
      tr.innerHTML = ico("alert") + " Traceback";
      tr.onclick = function () {
        callBridge("showTraceback");
      };
    }
    var go = $("permGo");
    if (go) {
      go.innerHTML = ico("folderOpen") + " Открыть настройки";
      go.onclick = function () {
        callBridge("grantAllFiles");
      };
    }
    var strip = $("dlstrip");
    if (strip) {
      strip.addEventListener("click", function (e) {
        var cmd = upAttr(e.target, "data-cmd");
        if (cmd) {
          callBridge(cmd.getAttribute("data-cmd"));
        }
      });
      var pause = strip.querySelector(".dl-pause");
      var resume = strip.querySelector(".dl-resume");
      var cancel = strip.querySelector("[data-cmd='cancelDownload']");
      if (pause) {
        pause.innerHTML = ico("pause") + '<span class="mini-txt">Пауза</span>';
      }
      if (resume) {
        resume.innerHTML = ico("play") + '<span class="mini-txt">Продолжить</span>';
      }
      if (cancel) {
        cancel.innerHTML = ico("x") + '<span class="mini-txt">Отмена</span>';
      }
    }
  }

  function tickClock() {
    var d = new Date();
    var el = $("clock");
    if (el) {
      el.textContent = pad(d.getHours()) + ":" + pad(d.getMinutes());
    }
  }

  function loadLocalPrefs() {
    var t = lsGet("mas_bios_theme", "");
    if (t === "light" || t === "dark") {
      theme = t;
    }
    var a = lsGet("mas_bios_anim", "");
    if (a === "off") {
      anim = false;
    } else if (a === "on") {
      anim = true;
    }
    var r = lsGet("mas_bios_rail", "");
    if (r === "slim") {
      slim = true;
    } else if (r === "open") {
      slim = false;
    } else {
      slim = (window.innerWidth || 0) < 960;
    }
    var lg = lsGet("mas_bios_log", "");
    if (lg === "open") {
      logOpen = true;
    } else if (lg === "slim") {
      logOpen = false;
    }
  }

  function boot() {
    loadLocalPrefs();
    bindStatic();
    tickClock();
    setInterval(tickClock, 10000);
    applyChrome();
    try {
      window.addEventListener("resize", function () {
        applyChrome();
      });
    } catch (eResize) {
    }
    var open = queryOpen();
    if (open) {
      biosOpen(open);
    } else {
      render();
    }
    if (PREVIEW) {
      biosSetStatus({
        path: "Documents/Monika_after_story",
        version: "предпросмотр",
        filesOk: true,
        engineOk: true,
        skipBios: false,
        archivesOk: false,
        tracebackOk: false,
        updateNeeded: true,
        safeMode: false,
        charsNew: true,
        charsCount: 2
      });
      biosLog("MAS BIOS · идеальный 3\nслева категории, в центре плитки, справа журнал.\n");
      biosSubmods(JSON.stringify([
        { id: "demo", pack: "пример сабмода", files: 12, added: 8, replaced: 4, kind: "submod" },
        { id: "angel", pack: "Fallen Angel", files: 40, added: 40, replaced: 0, kind: "spritepack" },
        { id: "neon", pack: "pong neon", files: 2, added: 0, replaced: 2, kind: "assetpack" }
      ]));
      biosUrlHistory(JSON.stringify([
        { url: "https://github.com/user/mas-submod" },
        { url: "https://example.com/pong-neon.zip" }
      ]));
      biosExports(JSON.stringify([
        { name: "saves_20261009_2240.zip", size: 1843200, when: "2026-10-09 22:40" },
        { name: "saves_20261008_1102.zip", size: 902144, when: "2026-10-08 11:02" }
      ]));
      biosProgress("пример загрузки 42 МБ", 42);
      biosDlState("running");
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
