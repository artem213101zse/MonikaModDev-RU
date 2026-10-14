(function (w) {
  "use strict";

  w.BIOS_TREE = [
    {
      id: "play",
      label: "Игра",
      short: "▶",
      hint: "запуск и архивы DDLC",
      kids: [
        {
          id: "boot",
          label: "Запуск",
          hint: "Python ещё не стартовал. Сессия Моники начнётся отсюда.",
          acts: [
            { t: "Запустить MAS", s: "Ren'Py → MAS OS → комната", cmd: "startGame", primary: 1 },
            { t: "Безопасный вход", s: "без сабмодов, только оболочка", cmd: "startSafe" },
            { t: "Проверить диск", s: "папки, архивы, разрешение", cmd: "healthCheck" },
            { t: "Снимок папок", s: "подарки, музыка, сейвы, паки", cmd: "diskSnapshot" }
          ]
        },
        {
          id: "archives",
          label: "Архивы DDLC",
          hint: "Картинки и музыка не внутри APK. Сначала ddlc.moe, GitHub запасной.",
          acts: [
            { t: "Скачать с ddlc.moe", s: "официальный zip · распаковка RPA", cmd: "downloadDdlcMoe", primary: 1 },
            { t: "Скачать с GitHub", s: "images.rpa / audio.rpa", cmd: "downloadArchives" },
            { t: "Выбрать .rpa / .zip", s: "Downloads, Telegram, USB", cmd: "pickArchive" },
            { t: "Поставить с диска", s: "_mas/archives", cmd: "installArchives" },
            { t: "Проверить паки", s: "какие уже на месте", cmd: "checkArchives" }
          ]
        }
      ]
    },
    {
      id: "content",
      label: "Контент",
      short: "▣",
      hint: "паки, подарки, музыка",
      kids: [
        {
          id: "install",
          label: "Установить",
          hint: "Один zip — BIOS сам поймёт: сабмод, спрайтпак или рескин.",
          input: { ph: "GitHub / прямая ссылка на zip" },
          acts: [
            { t: "Скачать и поставить", s: "по ссылке, тип определится сам", cmd: "downloadSubmodUrl", primary: 1 },
            { t: "Выбрать zip с диска", s: "с телефона или из Downloads", cmd: "pickSubmodZip", primary: 1 },
            { t: "История ссылок", s: "недавние URL", cmd: "listUrlHistory" },
            { t: "Очистить историю", s: "забыть сохранённые ссылки", cmd: "clearUrlHistory" }
          ]
        },
        {
          id: "library",
          label: "Библиотека",
          hint: "Все поставленные паки. Снятие одного не трогает остальные.",
          sample: "packs",
          acts: [
            { t: "Обновить список", s: "перечитать манифесты", cmd: "listSubmods", primary: 1 },
            { t: "Снять последний", s: "только его файлы", cmd: "uninstallLastSubmod", danger: 1 }
          ]
        },
        {
          id: "media",
          label: "Подарки и медиа",
          hint: "Пикер кладёт файл сразу в characters, custom_bgm или обои.",
          acts: [
            { t: "Положить gift", s: "в characters/", cmd: "pickGift", primary: 1 },
            { t: "Положить музыку", s: "в custom_bgm/", cmd: "pickMusic", primary: 1 },
            { t: "Обои", s: "custom_wallpaper.png", cmd: "pickImage" },
            { t: "Любой файл", s: "gift / музыка / pgn сами", cmd: "pickFile" }
          ]
        }
      ]
    },
    {
      id: "data",
      label: "Данные",
      short: "◇",
      hint: "сейвы и файл Моники",
      kids: [
        {
          id: "saves",
          label: "Сейвы",
          hint: "Zip или уже распакованная папка с другой сборки.",
          acts: [
            { t: "Импорт zip", s: "архив сейвов", cmd: "pickSavesZip", primary: 1 },
            { t: "Импорт папки", s: "уже распакованные saves", cmd: "pickSavesFolder", primary: 1 },
            { t: "Экспорт", s: "saves → _mas/backups", cmd: "exportSaves" },
            { t: "Поделиться", s: "отправить бэкап", cmd: "shareSaves" }
          ]
        },
        {
          id: "monika",
          label: "Моника",
          hint: "Пустой стол в игре ждёт characters/monika.",
          acts: [
            { t: "Статус файла", s: "есть ли characters/monika", cmd: "checkMonikaFile", primary: 1 },
            { t: "Найти monika", s: "обход Documents", cmd: "recoverMonikaScan" },
            { t: "Вернуть в characters", s: "перенести найденный файл", cmd: "recoverMonikaRestore" },
            { t: "Собрать заново", s: "из mbase, если файл потерян", cmd: "recoverMonikaRebuild", danger: 1 },
            { t: "Вернуть за стол", s: "Моника снова в комнате", cmd: "recoverMonikaHome", primary: 1 }
          ]
        }
      ]
    },
    {
      id: "sys",
      label: "Система",
      short: "⚙",
      hint: "APK, шахматы, логи",
      kids: [
        {
          id: "update",
          label: "Обновление",
          hint: "GitHub Release порта. Установщик Android, не Ren'Py.",
          acts: [
            { t: "Проверить", s: "последний release", cmd: "checkUpdate", primary: 1 },
            { t: "Скачать и поставить", s: "если есть новая версия", cmd: "downloadUpdate" },
            { t: "Поставить скачанный", s: "files/update.apk", cmd: "installLocalApk" },
            { t: "Скачать заново", s: "даже если тег тот же", cmd: "downloadUpdateAgain" }
          ]
        },
        {
          id: "engine",
          label: "Шахматы",
          hint: "libstockfish.so из nativeLibraryDir. Android 10 не exec из files/.",
          acts: [
            { t: "Проверить ELF", s: "libdir, размер, можно ли exec", cmd: "installEngine" },
            { t: "uci", s: "id name / uciok", cmd: "testStockfish", primary: 1 },
            { t: "isready", s: "readyok", cmd: "stockfishReady" },
            { t: "Ход depth 1", s: "startpos → bestmove", cmd: "stockfishGo" }
          ]
        },
        {
          id: "os",
          label: "Разрешения и логи",
          hint: "Диск, traceback, флаг холодного старта.",
          acts: [
            { t: "Все файлы", s: "разрешение Android 11+", cmd: "grantAllFiles", primary: 1 },
            { t: "Открыть Documents", s: "Monika_after_story в проводнике", cmd: "openDocuments" },
            { t: "Показать traceback", s: "почему не запустилась игра", cmd: "showTraceback", primary: 1 },
            { t: "Поделиться логами", s: "log.txt и traceback", cmd: "shareLogs" },
            { t: "Сразу MAS OS", s: "пропускать BIOS при старте", cmd: "toggleBoot", danger: 1 }
          ]
        }
      ]
    }
  ];

  w.BIOS_PACKS = [
    { name: "Extra Plus", kind: "сабмод", n: 42 },
    { name: "GSM", kind: "сабмод", n: 18 },
    { name: "Just Monika sprites", kind: "спрайт", n: 120 }
  ];

  w.BIOS_VARIANTS = [
    ["nav.html", "хаб"],
    ["rail-list.html", "список"],
    ["rail-tiles.html", "плитки"],
    ["rail-modal.html", "окна"],
    ["rail-sheet.html", "лист"],
    ["rail-split.html", "колонки"],
    ["rail-stack.html", "стек"]
  ];

  w.biosCat = function (id) {
    var i, t = w.BIOS_TREE;
    for (i = 0; i < t.length; i++) if (t[i].id === id) return t[i];
    return t[0];
  };

  w.biosKid = function (cat, kidId) {
    var i, k = cat.kids;
    for (i = 0; i < k.length; i++) if (k[i].id === kidId) return k[i];
    return k[0];
  };

  w.biosLog = function (cmd, extra) {
    var el = document.getElementById("log");
    var t, hh;
    if (!el) return;
    t = new Date();
    hh = ("0" + t.getHours()).slice(-2) + ":" +
         ("0" + t.getMinutes()).slice(-2) + ":" +
         ("0" + t.getSeconds()).slice(-2);
    el.textContent += (el.textContent ? "\n" : "") +
      "[" + hh + "] CMD  → " + cmd + (extra ? " · " + extra : "");
    el.scrollTop = el.scrollHeight;
  };

  w.biosClock = function (id) {
    function tick() {
      var d = new Date();
      var el = document.getElementById(id || "clock");
      if (el) {
        el.textContent = ("0" + d.getHours()).slice(-2) + ":" +
          ("0" + d.getMinutes()).slice(-2);
      }
    }
    tick();
    setInterval(tick, 10000);
  };

  w.biosSwitcher = function (current) {
    var el = document.getElementById("switch");
    var i, a, cur, html;
    if (!el) return;
    html = "";
    for (i = 0; i < w.BIOS_VARIANTS.length; i++) {
      a = w.BIOS_VARIANTS[i];
      cur = a[0] === current ? " on" : "";
      html += '<a class="sw' + cur + '" href="' + a[0] + '">' + a[1] + "</a>";
    }
    el.innerHTML = html;
  };

  w.biosRailHtml = function (currentId, extraClass) {
    var i, c, on, html = "";
    extraClass = extraClass || "";
    for (i = 0; i < w.BIOS_TREE.length; i++) {
      c = w.BIOS_TREE[i];
      on = c.id === currentId ? " on" : "";
      html += '<button type="button" class="rail-btn' + on + " " + extraClass +
        '" data-cat="' + c.id + '"><i>' + c.short + "</i><span>" +
        c.label + "</span></button>";
    }
    return html;
  };

  w.esc = function (s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/"/g, "&quot;");
  };

  w.biosActAttrs = function (a) {
    return 'type="button" data-cmd="' + w.esc(a.cmd) + '" data-t="' +
      w.esc(a.t) + '"' + (a.danger ? ' data-danger="1"' : "") +
      (a.primary ? ' data-primary="1"' : "");
  };

  w.biosInputHtml = function (kid) {
    if (!kid.input) return "";
    return '<input class="url" type="url" inputmode="url" autocomplete="off" placeholder="' +
      w.esc(kid.input.ph) + '" id="u-' + kid.id + '">';
  };

  w.biosPacksHtml = function (kid) {
    var i, p, html;
    if (kid.sample !== "packs") return "";
    html = '<div class="packs">';
    for (i = 0; i < w.BIOS_PACKS.length; i++) {
      p = w.BIOS_PACKS[i];
      html += '<div class="pack"><div><b>' + w.esc(p.name) + "</b><span>" +
        w.esc(p.kind) + " · " + p.n + " файлов</span></div>" +
        '<button type="button" class="pack-x" data-cmd="uninstallLastSubmod" data-t="' +
        w.esc(p.name) + '" data-danger="1">снять</button></div>';
    }
    return html + "</div>";
  };

  w.biosActsHtml = function (kid, kind) {
    var i, a, html = "", cls;
    html += w.biosInputHtml(kid);
    if (kind === "rows") {
      html += '<div class="rows">';
      for (i = 0; i < kid.acts.length; i++) {
        a = kid.acts[i];
        cls = "row" + (a.primary ? " pri" : "") + (a.danger ? " dang" : "");
        html += "<button " + w.biosActAttrs(a) + ' class="' + cls + '"><span><b>' +
          w.esc(a.t) + "</b><i>" + w.esc(a.s) + "</i></span><em>›</em></button>";
      }
      html += "</div>";
    } else if (kind === "tiles") {
      html += '<div class="tiles">';
      for (i = 0; i < kid.acts.length; i++) {
        a = kid.acts[i];
        cls = "tile" + (a.primary ? " pri" : "") + (a.danger ? " dang" : "");
        html += "<button " + w.biosActAttrs(a) + ' class="' + cls + "\"><b>" +
          w.esc(a.t) + "</b><span>" + w.esc(a.s) + "</span></button>";
      }
      html += "</div>";
    } else if (kind === "stack") {
      html += '<div class="stack-acts">';
      for (i = 0; i < kid.acts.length; i++) {
        a = kid.acts[i];
        if (a.primary) {
          html += "<button " + w.biosActAttrs(a) + ' class="hero' +
            (a.danger ? " dang" : "") + '">' + w.esc(a.t) +
            "<small>" + w.esc(a.s) + "</small></button>";
        }
      }
      html += '<div class="mini">';
      for (i = 0; i < kid.acts.length; i++) {
        a = kid.acts[i];
        if (a.primary) continue;
        html += "<button " + w.biosActAttrs(a) + ' class="mini-btn' +
          (a.danger ? " dang" : "") + '">' + w.esc(a.t) + "</button>";
      }
      html += "</div></div>";
    } else {
      html += '<div class="btns">';
      for (i = 0; i < kid.acts.length; i++) {
        a = kid.acts[i];
        cls = "btn" + (a.primary ? " pri" : "") + (a.danger ? " dang" : "");
        html += "<button " + w.biosActAttrs(a) + ' class="' + cls + '">' +
          w.esc(a.t) + "<small>" + w.esc(a.s) + "</small></button>";
      }
      html += "</div>";
    }
    html += w.biosPacksHtml(kid);
    return html;
  };

  w.biosBindActs = function (opts) {
    opts = opts || {};
    document.addEventListener("click", function (e) {
      var b = e.target.closest ? e.target.closest("[data-cmd]") : null;
      var cmd, t, danger;
      if (!b) return;
      cmd = b.getAttribute("data-cmd");
      t = b.getAttribute("data-t") || "";
      danger = b.getAttribute("data-danger");
      if (danger && opts.confirmDanger) {
        if (!window.confirm("Точно: " + t + " ?")) return;
      }
      w.biosLog(cmd, t);
    });
  };

  w.biosKidCard = function (kid) {
    return '<button type="button" class="card" data-kid="' + kid.id + '"><b>' +
      w.esc(kid.label) + "</b><span>" + w.esc(kid.hint) + "</span></button>";
  };
})(window);
