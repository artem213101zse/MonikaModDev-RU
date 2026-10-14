(function (w) {
  "use strict";

  var PACKS = [
    { id: "images", group: "need", name: "Картинки DDLC", file: "images.rpa", mb: 127.2, src: "GitHub / ddlc.moe", status: "ready", pct: 100, cmd: "downloadArchives", required: 1 },
    { id: "audio", group: "need", name: "Музыка и звуки", file: "audio.rpa", mb: 62.6, src: "GitHub / ddlc.moe", status: "downloading", pct: 38, cmd: "downloadArchives", required: 1, speed: 1.8 },
    { id: "ddlc", group: "need", name: "Официальный zip", file: "ddlc-win.zip", mb: 294, src: "ddlc.moe", status: "missing", pct: 0, cmd: "downloadDdlcMoe", required: 1 },
    { id: "stockfish", group: "need", name: "Движок шахмат", file: "libstockfish.so", mb: 5.1, src: "APK jniLibs", status: "ready", pct: 100, cmd: "testStockfish", required: 1 },
    { id: "apk", group: "update", name: "Обновление APK", file: "update.apk", mb: 48.0, src: "GitHub Release", status: "missing", pct: 0, cmd: "downloadUpdate" },
    { id: "extra", group: "content", name: "Extra Plus", file: "extraplus.zip", mb: 12.4, src: "zip", status: "ready", pct: 100, cmd: "listSubmods", selected: 1 },
    { id: "gsm", group: "content", name: "GSM", file: "gsm.zip", mb: 4.2, src: "zip", status: "paused", pct: 61, cmd: "downloadSubmodUrl", selected: 1 },
    { id: "sprites", group: "content", name: "Just Monika sprites", file: "sprites.zip", mb: 28.0, src: "zip", status: "missing", pct: 0, cmd: "pickSubmodZip" },
    { id: "bgm", group: "content", name: "Пользовательская музыка", file: "custom_bgm/", mb: 0, src: "пикер", status: "ready", pct: 100, cmd: "pickMusic" }
  ];

  var LABELS = {
    ready: "скачано",
    missing: "нет на диске",
    downloading: "загрузка",
    paused: "пауза",
    queued: "очередь",
    error: "ошибка"
  };

  w.biosDlPacks = PACKS;
  w.biosDlLabels = LABELS;

  w.biosDlGet = function (id) {
    var i;
    for (i = 0; i < PACKS.length; i++) if (PACKS[i].id === id) return PACKS[i];
    return null;
  };

  w.biosDlFilter = function (group) {
    var i, out = [];
    if (!group || group === "all") return PACKS.slice();
    for (i = 0; i < PACKS.length; i++) if (PACKS[i].group === group) out.push(PACKS[i]);
    return out;
  };

  w.biosDlTotals = function () {
    var i, p, need = 0, needOk = 0, down = 0, haveMb = 0, allMb = 0, active = 0;
    for (i = 0; i < PACKS.length; i++) {
      p = PACKS[i];
      allMb += p.mb;
      haveMb += p.mb * (p.pct / 100);
      if (p.required) {
        need += 1;
        if (p.status === "ready") needOk += 1;
      }
      if (p.status === "downloading") {
        down += 1;
        active += 1;
      }
      if (p.status === "paused" || p.status === "queued") active += 1;
    }
    return {
      need: need,
      needOk: needOk,
      down: down,
      active: active,
      haveMb: haveMb,
      allMb: allMb,
      pct: allMb ? Math.round((haveMb / allMb) * 100) : 0,
      readyToPlay: needOk === need
    };
  };

  w.biosDlAct = function (id) {
    var p = w.biosDlGet(id);
    if (!p) return;
    if (p.status === "missing" || p.status === "paused" || p.status === "error" || p.status === "queued") {
      p.status = "downloading";
      if (!p.speed) p.speed = 1.2 + Math.random() * 2;
      if (p.pct >= 100) p.pct = 0;
    } else if (p.status === "downloading") {
      p.status = "paused";
    } else if (p.status === "ready") {
      if (!p.required) {
        p.status = "missing";
        p.pct = 0;
      }
    }
  };

  w.biosDlQueueAllMissing = function () {
    var i, p, first = true;
    for (i = 0; i < PACKS.length; i++) {
      p = PACKS[i];
      if (p.status === "ready") continue;
      if (first) {
        p.status = "downloading";
        if (!p.speed) p.speed = 1.6;
        first = false;
      } else if (p.status !== "downloading") {
        p.status = "queued";
      }
    }
  };

  w.biosDlDownloadRequired = function () {
    var i, p, first = true;
    for (i = 0; i < PACKS.length; i++) {
      p = PACKS[i];
      if (!p.required || p.status === "ready") continue;
      if (first) {
        p.status = "downloading";
        if (!p.speed) p.speed = 1.8;
        first = false;
      } else p.status = "queued";
    }
  };

  w.biosDlTick = function () {
    var i, p, n, started = false;
    for (i = 0; i < PACKS.length; i++) {
      p = PACKS[i];
      if (p.status !== "downloading") continue;
      p.pct += 1.4 + (p.speed || 1);
      if (p.pct >= 100) {
        p.pct = 100;
        p.status = "ready";
      }
      started = true;
      break;
    }
    if (!started) {
      for (i = 0; i < PACKS.length; i++) {
        n = PACKS[i];
        if (n.status === "queued") {
          n.status = "downloading";
          if (!n.speed) n.speed = 1.4;
          break;
        }
      }
    }
  };

  w.biosDlStartTick = function (redraw) {
    setInterval(function () {
      var before = PACKS.map(function (p) { return p.status + p.pct; }).join();
      w.biosDlTick();
      var after = PACKS.map(function (p) { return p.status + p.pct; }).join();
      if (before !== after && redraw) redraw();
    }, 140);
  };

  w.biosDlMb = function (n) {
    if (n >= 100) return Math.round(n) + " МБ";
    return (Math.round(n * 10) / 10) + " МБ";
  };

  w.biosDlLog = function (cmd, extra) {
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
})(window);
