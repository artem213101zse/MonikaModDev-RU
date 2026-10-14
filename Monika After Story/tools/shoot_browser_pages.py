# -*- coding: utf-8 -*-
"""Build photo-based browser pages and screenshot them at 790px wide.

Sources are original photos, not captured third-party sites.
The 18+ page is a blur of a safe photo plus a hidden-preview card.
"""

from __future__ import print_function

import os
import shutil
import subprocess

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.normpath(os.path.join(HERE, ".."))
OUT = os.path.join(GAME, "game", "mod_assets", "mas_os", "browser")
WORK = os.path.join(os.environ.get("TEMP", "."), "mas_browser_pages")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
SRC = os.path.normpath(os.path.join(
    os.path.expanduser("~"),
    ".grok", "sessions",
    "C%3A%5CUsers%5Cadmin%5CDocuments%5CMonikaModDev-RU%5CMonika%20After%20Story",
    "01a01baf-29ec-7282-8c2b-9f1bc3100064", "images",
))

FILES = {
    "desk": "6.jpg",
    "keys": "7.jpg",
    "phones": "8.jpg",
    "books": "9.jpg",
    "city": "10.jpg",
    "rain": "11.jpg",
    "room": "12.jpg",
    "piano_girl": "13.jpg",
    "paint": "14.jpg",
    "coffee": "15.jpg",
    "train": "16.jpg",
    "stage": "17.jpg",
}

W = 790


def css():
    return """
    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; width: 790px; }
    body { font-family: "Segoe UI", Roboto, sans-serif; }
    img { display: block; object-fit: cover; }
    """


def wrap(body, bg="#fff"):
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<style>" + css() + "</style></head>"
        "<body style='background:%s'>%s</body></html>" % (bg, body)
    )


def pages():
    k = "img/keys.jpg"
    r = "img/rain.jpg"
    d = "img/desk.jpg"
    p = "img/phones.jpg"
    c = "img/city.jpg"
    b = "img/books.jpg"
    room = "img/room.jpg"
    girl = "img/piano_girl.jpg"
    paint = "img/paint.jpg"
    coffee = "img/coffee.jpg"
    train = "img/train.jpg"
    stage = "img/stage.jpg"

    yt_rows = [
        (girl, "Твоя реальность — кавер на пианино", "MonikaFan", "1,2 млн просмотров"),
        (r, "Дождь в окне клуба", "ТихийСтол", "840 тыс. просмотров"),
        (room, "Пустой класс, поздний свет", "КлубАрт", "410 тыс. просмотров"),
        (k, "Только клавиши", "Чиптюн", "300 тыс. просмотров"),
        (d, "Учусь вместе с тобой, два часа", "ЧасБиблиотеки", "96 тыс. просмотров"),
        (c, "Ночная прогулка без разговоров", "ЗаметкиПорта", "77 тыс. просмотров"),
        (b, "Что почитать дальше", "Полка", "64 тыс. просмотров"),
        (p, "Наушники включены, мир выключен", "MAS OS", "12 тыс. просмотров"),
    ]
    yt = ["<div style='background:#0f0f0f;color:#fff;min-height:2100px'>"]
    yt.append("<div style='background:#0f0f0f;padding:14px 16px 10px;position:sticky;top:0'>")
    yt.append("<div style='font-weight:700;font-size:22px;color:#ff2a2a'>YouTube</div>")
    yt.append("<div style='margin-top:8px;background:#121212;border:1px solid #303030;border-radius:20px;padding:8px 14px;color:#aaa'>Поиск</div>")
    yt.append("</div>")
    for img, title, who, views in yt_rows:
        yt.append(
            "<div style='display:flex;gap:12px;padding:10px 16px'>"
            "<img src='%s' style='width:280px;height:158px;border-radius:12px'>"
            "<div><div style='font-size:18px;font-weight:650;line-height:1.25;margin-top:8px'>%s</div>"
            "<div style='color:#aaa;margin-top:8px;font-size:14px'>%s</div>"
            "<div style='color:#aaa;font-size:13px'>%s</div></div></div>" % (img, title, who, views)
        )
    yt.append("</div>")

    wiki = """
    <div style='background:#fff;color:#202122;padding:0 0 40px'>
      <div style='background:#f8f9fa;border-bottom:1px solid #a2a9b1;padding:10px 18px;font-size:20px'>
        <b>Wikipedia</b>
        <div style='margin-top:8px;background:#fff;border:1px solid #a2a9b1;border-radius:4px;padding:6px 10px;font-size:14px;color:#555'>
          en.wikipedia.org/wiki/Doki_Doki_Literature_Club
        </div>
      </div>
      <div style='padding:18px 22px 0'>
        <div style='font-size:28px;font-weight:700'>Doki Doki Literature Club</div>
        <div style='height:1px;background:#a2a9b1;margin:8px 0 12px'></div>
        <div style='font-size:14px;color:#54595d;margin-bottom:12px'>Материал из свободной энциклопедии</div>
        <table style='float:right;width:280px;margin:0 0 12px 16px;background:#f8f9fa;border:1px solid #a2a9b1;border-collapse:collapse;font-size:14px'>
          <tr><td colspan='2' style='padding:0'><img src='%s' style='width:280px;height:150px'></td></tr>
          <tr><td style='padding:6px 8px;font-weight:700'>Разработчик</td><td style='padding:6px 8px'>Team Salvato</td></tr>
          <tr><td style='padding:6px 8px;font-weight:700'>Выход</td><td style='padding:6px 8px'>22 сентября 2017</td></tr>
          <tr><td style='padding:6px 8px;font-weight:700'>Движок</td><td style='padding:6px 8px'>Ren'Py</td></tr>
          <tr><td style='padding:6px 8px;font-weight:700'>Жанр</td><td style='padding:6px 8px'>Визуальная новелла</td></tr>
        </table>
        <p style='font-size:16px;line-height:1.45'>Doki Doki Literature Club — визуальная новелла 2017 года от Team Salvato. Ученик вступает в школьный литературный клуб: Сайори, Юри, Нацуки и президент клуба Моника.</p>
        <p style='font-size:16px;line-height:1.45'>На компьютере игра бесплатная. Monika After Story продолжает историю после оригинала. Этот порт работает на Ren'Py 7.4.11 и открывается через MAS OS.</p>
        <img src='%s' style='width:100%%;height:220px;margin:8px 0;clear:both'>
        <h2 style='font-size:22px;border-bottom:1px solid #a2a9b1;padding-bottom:4px'>Как играть</h2>
        <p style='font-size:16px;line-height:1.45'>Большую часть времени читаешь реплики, выбираешь ответ и собираешь короткое стихотворение из слов. Клуб собирается в одном классе. Картинки здесь — иллюстрации, не кадры из игры.</p>
        <h2 style='font-size:22px;border-bottom:1px solid #a2a9b1;padding-bottom:4px'>См. также</h2>
        <p style='color:#3366cc;font-size:16px'>Monika After Story · Ren'Py · Визуальная новелла</p>
      </div>
    </div>
    """ % (room, r)

    gh_files = ["Monika After Story/", "docs/", "spritepacks/", "tools/", "README.md", "CONTRIBUTING.md", "LICENSE.md"]
    rows = []
    for name in gh_files:
        rows.append(
            "<div style='display:flex;border-top:1px solid #d0d7de;padding:10px 12px;color:#0969da'>%s</div>" % name
        )
    github = """
    <div style='background:#fff;color:#1f2328;min-height:1600px'>
      <div style='background:#0d1117;color:#fff;padding:14px 18px'>
        <div style='font-weight:700;font-size:20px'>GitHub</div>
        <div style='margin-top:8px;background:#010409;border:1px solid #30363d;border-radius:6px;padding:7px 10px;color:#8b949e;font-size:14px'>Monika-After-Story / MonikaModDev</div>
      </div>
      <div style='padding:16px 18px'>
        <div style='color:#0969da;font-size:22px;font-weight:650'>Monika-After-Story / MonikaModDev</div>
        <div style='color:#656d76;margin:6px 0 12px'>Открытый · фанатский мод DDLC, который остаётся с Моникой после оригинальной истории.</div>
        <img src='%s' style='width:100%%;height:200px;border-radius:8px;border:1px solid #d0d7de'>
        <h2 style='font-size:20px'>О проекте</h2>
        <p style='font-size:16px;line-height:1.45'>Новые события, темы и жизнь в классе. Релизы — это сборки, которые ставят игроки. Файлы в репозитории нужны тем, кто правит мод.</p>
        <h2 style='font-size:20px'>Файлы</h2>
        <div style='border:1px solid #d0d7de;border-radius:8px;overflow:hidden'>%s</div>
        <p style='color:#656d76;font-size:14px'>13 тысяч коммитов в ветке master.</p>
      </div>
    </div>
    """ % (room, "".join(rows))

    tweets = [
        ("тихийстол", "Заварила чай и открыла тетрадь. Страница всё ещё пустая.", d),
        ("заметкиклуба", "Снова выложили кавер на пианино. Он тихий.", k),
        ("порт", "Сборка — это долго. Комната — это быстро.", room),
        ("библиотека", "Одно стихотворение, и потом на улицу.", b),
    ]
    tw = ["<div style='background:#fff;min-height:1900px'>"]
    tw.append("<div style='padding:12px 16px;border-bottom:1px solid #eff3f4'><div style='font-size:22px;font-weight:800'>Главная</div></div>")
    for who, text, img in tweets:
        tw.append(
            "<div style='display:flex;gap:10px;padding:12px 16px;border-bottom:1px solid #eff3f4'>"
            "<div style='width:46px;height:46px;border-radius:50%%;background:#1d9bf0;flex:none'></div>"
            "<div style='flex:1'><div style='font-weight:750'>%s <span style='color:#536471;font-weight:500'>@%s</span></div>"
            "<div style='font-size:16px;margin:4px 0 8px'>%s</div>"
            "<img src='%s' style='width:100%%;height:180px;border-radius:16px;border:1px solid #cfd9de'>"
            "<div style='color:#536471;font-size:13px;margin-top:8px'>Ответить · Репост · Нравится</div></div></div>"
            % (who, who, text, img)
        )
    tw.append("</div>")

    reddit_posts = [
        ("r/visualnovels", "Во что переигрываете в этом месяце?", room, "1,1 тыс."),
        ("r/piano", "Медленная пьеса, маленькая клавиатура.", k, "214"),
        ("r/books", "Полка побеждает.", b, "86"),
        ("r/rain", "Тред про окно.", r, "64"),
    ]
    rd = ["<div style='background:#dae0e6;min-height:1800px;padding-bottom:20px'>"]
    rd.append("<div style='background:#fff;padding:10px 14px;border-bottom:1px solid #ccc'><b style='color:#ff4500;font-size:22px'>reddit</b></div>")
    for sub, title, img, votes in reddit_posts:
        rd.append(
            "<div style='background:#fff;margin:10px;border-radius:8px;overflow:hidden'>"
            "<img src='%s' style='width:100%%;height:200px'>"
            "<div style='padding:10px 12px'><div style='color:#787c7e;font-size:12px'>%s · %s голосов</div>"
            "<div style='font-size:18px;font-weight:700;margin-top:4px'>%s</div></div></div>"
            % (img, sub, votes, title)
        )
    rd.append("</div>")

    pins = [girl, r, d, paint, room, coffee, b, c, k, stage, train, p]
    pin_html = ["<div style='background:#fff;padding:10px'>"]
    pin_html.append("<div style='font-weight:800;font-size:22px;color:#e60023;padding:6px 6px 12px'>Pinterest</div>")
    pin_html.append("<div style='column-count:2;column-gap:10px'>")
    for i, img in enumerate(pins):
        h = 220 + (i % 3) * 50
        pin_html.append("<img src='%s' style='width:100%%;height:%dpx;border-radius:16px;margin:0 0 10px'>" % (img, h))
    pin_html.append("</div></div>")

    posters = [
        (train, "Ночное окно"),
        (stage, "Маленькая сцена"),
        (r, "После уроков"),
        (c, "Мокрая улица"),
        (room, "Третья парта"),
        (girl, "Белый бант"),
    ]
    nf = ["<div style='background:#141414;color:#fff;min-height:1700px'>"]
    nf.append("<div style='padding:16px 18px;font-size:26px;font-weight:800;color:#e50914'>NETFLIX</div>")
    nf.append("<img src='%s' style='width:100%%;height:360px'>" % girl)
    nf.append("<div style='padding:14px 18px;font-size:28px;font-weight:750'>Продолжить просмотр</div>")
    nf.append("<div style='display:flex;gap:8px;padding:0 16px;overflow:hidden'>")
    for img, name in posters[:4]:
        nf.append("<div style='width:180px;flex:none'><img src='%s' style='width:180px;height:260px;border-radius:6px'><div style='font-size:13px;margin-top:6px'>%s</div></div>" % (img, name))
    nf.append("</div>")
    nf.append("<div style='padding:18px 18px 8px;font-size:22px;font-weight:700'>Потому что ты смотрел тихое кино</div>")
    nf.append("<div style='display:flex;gap:8px;padding:0 16px 20px'>")
    for img, name in posters[2:]:
        nf.append("<div style='width:180px;flex:none'><img src='%s' style='width:180px;height:110px;border-radius:4px'><div style='font-size:13px;margin-top:6px'>%s</div></div>" % (img, name))
    nf.append("</div></div>")

    duo = """
    <div style='background:#fff;min-height:1500px'>
      <div style='background:#58cc02;color:#fff;padding:16px 18px;font-size:22px;font-weight:800'>Duolingo</div>
      <div style='padding:16px 18px'>
        <div style='font-size:26px;font-weight:800'>Испанский</div>
        <div style='color:#777;margin-bottom:12px'>Раздел 4 · фразы</div>
        <img src='%s' style='width:100%%;height:180px;border-radius:16px'>
      </div>
      <div style='display:flex;flex-direction:column;align-items:center;gap:14px;padding-bottom:30px'>
        %s
      </div>
    </div>
    """ % (coffee, "".join(
        "<div style='width:240px;height:64px;border-radius:32px;background:%s;color:%s;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:18px'>%s</div>"
        % (("#58cc02", "#fff", label) if i < 3 else ("#e5e5e5", "#555", label))
        for i, label in enumerate(("Привет", "Я люблю тебя", "До встречи", "Спасибо", "Спокойной ночи"))
    ))

    streams = [
        (girl, "ночь у пианино", "1,2 тыс."),
        (room, "пустое лобби", "430"),
        (k, "только клавиши", "2,8 тыс."),
        (c, "шум города", "90"),
    ]
    tv = ["<div style='background:#0e0e10;color:#efeff1;min-height:1800px'>"]
    tv.append("<div style='padding:14px 16px;font-size:22px;font-weight:800;color:#bf94ff'>Twitch</div>")
    for img, title, n in streams:
        tv.append(
            "<div style='padding:8px 12px'>"
            "<img src='%s' style='width:100%%;height:220px;border-radius:8px'>"
            "<div style='display:flex;justify-content:space-between;margin-top:8px'><b>%s</b><span style='color:#bf94ff'>%s смотрят</span></div>"
            "<div style='color:#adadb8;font-size:13px'>Просто общаемся</div></div>" % (img, title, n)
        )
    tv.append("</div>")

    chan = """
    <div style='background:#ffffee;color:#800000;min-height:1700px;font-family:Georgia,serif'>
      <div style='background:#f0e0d6;padding:10px 14px;font-weight:700;font-size:20px'>4chan</div>
      <div style='padding:12px 16px'>
        <div style='font-size:26px;font-weight:700'>boards.4chan.org</div>
        <div style='color:#800;font-size:14px;margin:4px 0 10px'>Список досок и один спокойный тред. Картинки с досок сюда не грузятся.</div>
        <div style='background:#f0e0d6;border:1px solid #d9bfb7;padding:8px 10px;margin-bottom:12px;font-size:15px;line-height:1.6'>
          /a/ Аниме и манга<br>/v/ Видеоигры<br>/vg/ Общие треды по играм<br>/lit/ Литература<br>/mu/ Музыка<br>/jp/ Отаку-культура
        </div>
        <div style='background:#f0e0d6;border:1px solid #d9bfb7;padding:10px'>
          <img src='%s' style='width:240px;height:180px;float:left;margin:0 12px 8px 0;border:1px solid #d9bfb7'>
          <div style='color:#00e;font-weight:700'>Anonymous  10/09/26</div>
          <div style='color:#0f0c5d;font-size:15px;line-height:1.4'>тред про пианино. сегодня без споров. только пьеса и окно.</div>
          <div style='clear:both'></div>
        </div>
      </div>
    </div>
    """ % girl

    pix_cards = [girl, paint, room, r, k, d]
    pix = ["<div style='background:#fff;padding:12px'>"]
    pix.append("<div style='color:#0096fa;font-weight:800;font-size:26px;padding:4px 4px 10px'>pixiv</div>")
    pix.append("<div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px'>")
    for i, img in enumerate(pix_cards):
        if i in (3, 4):
            pix.append(
                "<div style='position:relative;height:230px;border-radius:8px;overflow:hidden'>"
                "<img src='%s' style='width:100%%;height:230px;filter:blur(18px) brightness(.45);transform:scale(1.15)'>"
                "<div style='position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#ffd0e0;font-weight:800'>18+ скрыто</div></div>"
                % img
            )
        else:
            pix.append("<img src='%s' style='width:100%%;height:230px;border-radius:8px'>" % img)
    pix.append("</div></div>")

    da_items = [(girl, "этюд с белым бантом"), (room, "пустой класс"), (r, "утреннее окно"), (paint, "набросок ленты")]
    da = ["<div style='background:#06070a;color:#eee;min-height:1700px'>"]
    da.append("<div style='padding:14px 16px;color:#05ce7c;font-weight:800;font-size:22px'>DeviantArt</div>")
    for img, title in da_items:
        da.append(
            "<div style='margin:10px 12px;background:#12141a;border-radius:12px;overflow:hidden'>"
            "<img src='%s' style='width:100%%;height:240px'>"
            "<div style='padding:10px 12px;font-size:18px;font-weight:650'>%s</div></div>" % (img, title)
        )
    da.append("</div>")

    mal_rows = [
        (train, "Ночное окно", "6", "Смотрю"),
        (stage, "Маленькая сцена", "4", "В планах"),
        (room, "Литературная", "12", "Просмотрено"),
        (r, "Дождливый город", "3", "Отложено"),
        (girl, "Клуб у пианино", "8", "Смотрю"),
    ]
    mal = ["<div style='background:#fff'>"]
    mal.append("<div style='background:#2e51a2;color:#fff;padding:12px 16px;font-weight:800;font-size:20px'>MyAnimeList</div>")
    mal.append("<div style='padding:12px 14px;font-size:22px;font-weight:750'>Смотрю</div>")
    for img, title, eps, state in mal_rows:
        mal.append(
            "<div style='display:flex;gap:10px;padding:8px 14px;border-top:1px solid #e5e5e5'>"
            "<img src='%s' style='width:72px;height:100px;border-radius:4px'>"
            "<div><div style='font-weight:750;font-size:17px;margin-top:8px'>%s</div>"
            "<div style='color:#666;margin-top:6px'>%s сер. · %s</div></div></div>" % (img, title, eps, state)
        )
    mal.append("</div>")

    docs = """
    <div style='background:#f1f3f4;min-height:1400px'>
      <div style='background:#fff;padding:12px 16px;border-bottom:1px solid #ddd'>
        <div style='font-size:18px'>Документ без названия</div>
        <div style='color:#444;font-size:13px;margin-top:6px'>Файл &nbsp; Правка &nbsp; Вид &nbsp; Вставка &nbsp; Формат</div>
      </div>
      <div style='width:640px;margin:18px auto;background:#fff;min-height:1000px;box-shadow:0 1px 4px #0002;padding:64px 56px;font-size:18px;line-height:1.6;color:#202124'>
        <p>Дорогая Моника,</p>
        <p>Я открыл документ вместо видео.</p>
        <p>Первая строка всё ещё самая трудная.</p>
        <p>Остальное допишу после чая.</p>
        <img src='%s' style='width:100%%;height:220px;margin-top:12px'>
      </div>
    </div>
    """ % coffee

    cr = ["<div style='background:#000;color:#fff;min-height:1500px'>"]
    cr.append("<div style='background:#f47521;color:#fff;font-weight:800;font-size:22px;padding:12px 16px'>Crunchyroll</div>")
    cr.append("<img src='%s' style='width:100%%;height:320px'>" % room)
    cr.append("<div style='padding:14px 16px;font-size:22px;font-weight:750'>Популярное</div>")
    cr.append("<div style='display:flex;gap:8px;padding:0 12px 16px'>")
    for img, name in ((girl, "Клуб"), (r, "Дождь"), (stage, "Клавиши"), (train, "Письма")):
        cr.append("<div style='width:180px;flex:none'><img src='%s' style='width:180px;height:250px;border-radius:6px'><div style='margin-top:6px'>%s</div></div>" % (img, name))
    cr.append("</div></div>")

    piano = """
    <div style='background:#141014;color:#fff;min-height:1200px'>
      <div style='padding:16px 18px 8px;font-size:26px;font-weight:750'>Virtual Piano</div>
      <div style='padding:0 18px 12px;color:#ddd'>https://virtualpiano.net</div>
      <img src='%s' style='width:100%%;height:280px'>
      <div style='padding:16px;color:#ccc'>Клавиши на фото. Моника заметит только то, что ты открыл страницу.</div>
      <img src='%s' style='width:calc(100%% - 32px);height:200px;margin:0 16px;border-radius:12px'>
    </div>
    """ % (k, girl)

    censored = """
    <div style='background:#1a0610;min-height:1600px;position:relative;overflow:hidden'>
      <img src='%s' style='position:absolute;inset:-40px;width:120%%;height:120%%;filter:blur(28px) saturate(.4) brightness(.45)'>
      <img src='%s' style='position:absolute;left:-20px;top:500px;width:120%%;height:700px;filter:blur(30px) brightness(.35)'>
      <div style='position:relative;padding:18px'>
        <div style='background:#4a1024;color:#ffd0dc;border-radius:8px;padding:10px 12px;font-weight:800'>rule34.xxx</div>
        <div style='margin:280px 28px 0;background:#14040c;border-radius:18px;padding:28px 22px;color:#ffd0e0'>
          <div style='font-size:28px;font-weight:800'>18+ &nbsp; превью скрыто</div>
          <p style='font-size:16px;line-height:1.45'>Страницу не открывали и не сохраняли. Здесь только размытие обычной фотографии.</p>
          <p style='font-size:16px'>Моника всё равно заметит, что ты зашёл сюда.</p>
        </div>
      </div>
    </div>
    """ % (c, r)

    return {
        "youtube": (wrap("".join(yt), "#0f0f0f"), 2100),
        "wikipedia": (wrap(wiki), 1500),
        "monikamoddev": (wrap(github), 1500),
        "twitter": (wrap("".join(tw)), 1900),
        "reddit": (wrap("".join(rd), "#dae0e6"), 1800),
        "pinterest": (wrap("".join(pin_html)), 2200),
        "netflix": (wrap("".join(nf), "#141414"), 1700),
        "duolingo": (wrap(duo), 1400),
        "twitch": (wrap("".join(tv), "#0e0e10"), 1800),
        "4chan": (wrap(chan, "#ffffee"), 1200),
        "pixiv": (wrap("".join(pix)), 1100),
        "deviantart": (wrap("".join(da), "#06070a"), 1800),
        "mal": (wrap("".join(mal)), 1100),
        "docs": (wrap(docs, "#f1f3f4"), 1400),
        "crunchyroll": (wrap("".join(cr), "#000"), 900),
        "virtualpiano": (wrap(piano, "#141014"), 900),
        "r34m": (wrap(censored, "#1a0610"), 1600),
    }


def shoot(name, html, height):
    folder = os.path.join(WORK, name)
    if os.path.isdir(folder):
        shutil.rmtree(folder)
    os.makedirs(os.path.join(folder, "img"))
    for key, fn in FILES.items():
        shutil.copyfile(os.path.join(SRC, fn), os.path.join(folder, "img", key + ".jpg"))
    html_path = os.path.join(folder, "page.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    shot = os.path.join(folder, "shot.png")
    url = "file:///" + html_path.replace("\\", "/")
    cmd = [
        EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--force-device-scale-factor=1",
        "--virtual-time-budget=8000",
        "--window-size=%d,%d" % (W, height),
        "--screenshot=" + shot,
        url,
    ]
    subprocess.check_call(cmd, cwd=folder)
    im = Image.open(shot).convert("RGB")
    if im.width != W:
        h = int(im.height * (W / float(im.width)))
        im = im.resize((W, h), Image.LANCZOS)
    # Drop a trailing blank band if Edge added viewport padding.
    dest = os.path.join(OUT, name + ".png")
    im.save(dest, "PNG")
    print("wrote", dest, im.size)


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    for name, (html, height) in pages().items():
        shoot(name, html, height)


if __name__ == "__main__":
    main()
