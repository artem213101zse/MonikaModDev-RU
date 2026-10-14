# -*- coding: utf-8 -*-
"""Long fake pages for the MAS OS browser.

Width 790. These are drawn layouts, not captured website pixels.
The 18+ bookmark is a blurred placeholder and does not fetch that site.

    python tools/gen_browser_shots.py
"""

from __future__ import print_function

import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "game", "mod_assets", "mas_os", "browser"))
W = 790
random.seed(12)


def font(size, bold=False):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    path = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", name)
    if not os.path.isfile(path):
        path = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "arial.ttf")
    return ImageFont.truetype(path, size)


class Page(object):
    def __init__(self, bg, height=2400):
        self.im = Image.new("RGB", (W, height), bg)
        self.d = ImageDraw.Draw(self.im)
        self.y = 0
        self.bg = bg
        self.bottom = 80

    def chrome(self, title, url, bar, fg=(255, 255, 255)):
        self.d.rectangle((0, 0, W, 86), fill=bar)
        self.d.text((18, 8), title, font=font(22, True), fill=fg)
        self.d.rounded_rectangle((16, 44, W - 16, 76), 8, fill=(255, 255, 255))
        self.d.text((28, 50), url, font=font(15), fill=(50, 50, 50))
        self.y = 102
        self.bottom = self.y

    def gap(self, n):
        self.y += n
        self.bottom = max(self.bottom, self.y)

    def wrap(self, text, fnt, width):
        lines = []
        for para in text.split("\n"):
            if para == "":
                lines.append("")
                continue
            cur = ""
            for word in para.split(" "):
                trial = word if not cur else cur + " " + word
                if self.d.textlength(trial, font=fnt) <= width:
                    cur = trial
                else:
                    if cur:
                        lines.append(cur)
                    cur = word
            if cur:
                lines.append(cur)
        return lines

    def text(self, s, size=16, fill=(30, 30, 30), bold=False, x=22, width=746):
        fnt = font(size, bold)
        lines = self.wrap(s, fnt, width)
        for line in lines:
            self.d.text((x, self.y), line, font=fnt, fill=fill)
            self.y += size + 6
        self.bottom = self.y
        return self

    def box(self, h, fill, x=16, w=None, radius=12):
        w = W - 32 if w is None else w
        self.d.rounded_rectangle((x, self.y, x + w, self.y + h), radius, fill=fill)
        top = self.y
        self.y += h
        self.bottom = self.y
        return top

    def crop(self):
        h = min(self.im.height, max(self.bottom + 36, 900))
        return self.im.crop((0, 0, W, h))

    def save(self, name):
        path = os.path.join(OUT, name + ".png")
        self.crop().save(path, "PNG")
        print("wrote", path)


def youtube():
    p = Page((15, 15, 15))
    p.chrome("YouTube", "https://www.youtube.com/", (204, 0, 0))
    rows = [
        ("Your Reality — piano cover", "MonikaFan", "1.2M", (180, 40, 70)),
        ("Literature Club speedpaint", "ClubArt", "840K", (40, 90, 140)),
        ("How Ren'Py 7 loads a mod", "PortNotes", "96K", (90, 50, 40)),
        ("DDLC OST playlist", "Shelf", "2.1M", (30, 30, 30)),
        ("Study with me, 2 hours", "QuietDesk", "410K", (50, 70, 90)),
        ("Just Monika (8-bit)", "Chiptune", "300K", (120, 30, 50)),
        ("Reading poems out loud", "LibraryHour", "77K", (70, 40, 80)),
        ("Android port diary", "MAS OS", "12K", (40, 20, 40)),
    ]
    for title, who, views, col in rows:
        top = p.box(132, (32, 32, 32), radius=14)
        p.d.rounded_rectangle((28, top + 14, 250, top + 118), 8, fill=col)
        p.d.polygon([(118, top + 48), (118, top + 84), (150, top + 66)], fill=(255, 40, 40))
        p.d.text((266, top + 28), title, font=font(18, True), fill=(245, 245, 245))
        p.d.text((266, top + 64), who + "  ·  " + views + " просмотров", font=font(14), fill=(170, 170, 170))
        p.gap(12)
    p.save("youtube")


def wikipedia():
    p = Page((255, 255, 255))
    p.chrome("Wikipedia", "https://en.wikipedia.org/wiki/Doki_Doki_Literature_Club", (247, 248, 250), (32, 32, 32))
    p.text("Doki Doki Literature Club", 28, (20, 20, 20), True)
    p.d.line((22, p.y, 760, p.y), fill=(160, 160, 160), width=1)
    p.gap(12)
    p.text("From a short public summary. Not the full article.", 14, (90, 90, 90))
    p.gap(8)
    p.text(
        "Doki Doki Literature Club is a 2017 visual novel by Team Salvato. "
        "A student joins a school literature club with Sayori, Yuri, Natsuki and club president Monika.",
        17,
    )
    p.gap(8)
    p.text(
        "It is free on PC. Monika After Story keeps the story going after the original game. "
        "This port runs on Ren'Py 7.4.11 and opens through MAS OS.",
        17,
    )
    p.gap(16)
    top = p.box(210, (247, 248, 252), radius=8)
    p.d.text((36, top + 16), "Infobox", font=font(16, True), fill=(20, 20, 20))
    rows = (
        ("Developer", "Team Salvato"),
        ("Released", "22 September 2017"),
        ("Engine", "Ren'Py"),
        ("Genre", "Visual novel"),
        ("Club", "Sayori, Yuri, Natsuki, Monika"),
    )
    yy = top + 48
    for k, v in rows:
        p.d.text((36, yy), k, font=font(15, True), fill=(40, 40, 40))
        p.d.text((220, yy), v, font=font(15), fill=(40, 40, 40))
        yy += 28
    p.gap(18)
    p.text("See also", 20, (20, 20, 20), True)
    p.text("Monika After Story · Ren'Py · Visual novel", 16, (6, 69, 173))
    p.gap(10)
    p.text(
        "The live Wikipedia page is much longer. This pane is a scrollable stand-in "
        "so Monika can notice you opened the article.",
        16,
        (70, 70, 70),
    )
    p.save("wikipedia")


def github():
    p = Page((255, 255, 255))
    p.chrome("GitHub", "https://github.com/Monika-After-Story/MonikaModDev", (36, 41, 47), (255, 255, 255))
    p.text("Monika-After-Story / MonikaModDev", 22, (9, 105, 218), True)
    p.gap(6)
    p.text("Public  ·  DDLC fan mod that stays with Monika after the original story.", 16, (70, 70, 70))
    p.gap(14)
    p.text("About", 18, (20, 20, 20), True)
    p.text(
        "New events, topics and a life in the classroom. Releases are the builds players install. "
        "The files in the repository are for people who work on the mod.",
        16,
    )
    p.gap(12)
    p.text("Files", 18, (20, 20, 20), True)
    for name in (
        "Monika After Story/",
        "docs/",
        "spritepacks/",
        "tools/",
        "README.md",
        "CONTRIBUTING.md",
        "LICENSE.md",
    ):
        top = p.box(42, (246, 248, 250), radius=6)
        p.d.text((32, top + 10), name, font=font(16), fill=(9, 105, 218))
        p.gap(6)
    p.gap(8)
    p.text("13k commits on master. Open an issue for bugs, a pull request for a change.", 15, (80, 80, 80))
    p.save("monikamoddev")


def twitter():
    p = Page((255, 255, 255))
    p.chrome("Twitter", "https://twitter.com/", (29, 155, 240))
    posts = (
        ("@quietdesk", "Made tea and opened a notebook. The page is still blank."),
        ("@clubnotes", "Someone posted a piano cover again. It is soft."),
        ("@portlog", "Android build is running. Presplash is the long part."),
        ("@library", "Recommendation: read one poem, then go outside."),
        ("@masfan", "She asked what I was reading. I had no answer ready."),
    )
    for who, body in posts:
        top = p.box(130, (247, 249, 249), radius=14)
        p.d.ellipse((32, top + 18, 78, top + 64), fill=(29, 155, 240))
        p.d.text((96, top + 18), who, font=font(16, True), fill=(15, 20, 25))
        p.d.text((96, top + 48), body, font=font(16), fill=(15, 20, 25))
        p.d.text((96, top + 88), "Reply   Repost   Like", font=font(13), fill=(120, 130, 140))
        p.gap(10)
    p.save("twitter")


def reddit():
    p = Page((218, 224, 230))
    p.chrome("Reddit", "https://www.reddit.com/", (255, 69, 0))
    posts = (
        ("r/visualnovels", "What are you replaying this month?", "214"),
        ("r/renpy", "Screen language tip: keep zorder constant.", "86"),
        ("r/ddlc", "Fan art thread, keep it kind.", "1.1k"),
        ("r/piano", "Slow piece for a small keyboard.", "64"),
        ("r/androiddev", "Presplash is a bitmap, not a Python screen.", "41"),
    )
    for sub, title, votes in posts:
        top = p.box(110, (255, 255, 255), radius=10)
        p.d.text((32, top + 14), sub + "   ·   " + votes, font=font(13), fill=(120, 124, 126))
        p.d.text((32, top + 42), title, font=font(18, True), fill=(26, 26, 27))
        p.d.text((32, top + 76), "Comment    Share    Save", font=font(13), fill=(120, 124, 126))
        p.gap(10)
    p.save("reddit")


def pinterest():
    p = Page((255, 255, 255))
    p.chrome("Pinterest", "https://www.pinterest.com/", (189, 8, 28))
    colors = (
        (230, 180, 190), (180, 200, 220), (210, 190, 160),
        (160, 190, 170), (200, 170, 200), (240, 210, 180),
        (170, 180, 200), (220, 160, 170), (190, 210, 190),
    )
    labels = ("desk", "ribbon", "rain", "notebook", "tea", "window", "poem", "sweater", "plant")
    x0, y = 16, p.y
    col_w = 246
    heights = [0, 0, 0]
    for i, (col, label) in enumerate(zip(colors, labels)):
        c = i % 3
        h = 180 + (i % 3) * 40
        x = x0 + c * (col_w + 10)
        yy = y + heights[c]
        p.d.rounded_rectangle((x, yy, x + col_w, yy + h), 16, fill=col)
        p.d.text((x + 14, yy + h - 36), label, font=font(16, True), fill=(40, 30, 30))
        heights[c] += h + 10
    p.y = y + max(heights)
    p.bottom = p.y
    p.save("pinterest")


def netflix():
    p = Page((20, 20, 20))
    p.chrome("Netflix", "https://www.netflix.com/", (20, 20, 20))
    p.d.rectangle((0, 86, W, 102), fill=(229, 9, 20))
    p.y = 118
    rows = (
        ("Continue", ((120, 30, 40), (40, 70, 120), (80, 40, 70), (30, 80, 70))),
        ("Because you watched a quiet film", ((90, 50, 40), (50, 40, 80), (140, 90, 40), (40, 40, 50))),
    )
    for title, cols in rows:
        p.text(title, 18, (230, 230, 230), True)
        p.gap(6)
        x = 16
        for col in cols:
            p.d.rounded_rectangle((x, p.y, x + 180, p.y + 110), 8, fill=col)
            x += 192
        p.y += 124
        p.bottom = p.y
    p.text("Posters here are plain color cards, not studio art.", 14, (150, 150, 150))
    p.save("netflix")


def duolingo():
    p = Page((255, 255, 255))
    p.chrome("Duolingo", "https://www.duolingo.com/", (88, 204, 2), (255, 255, 255))
    p.text("Spanish", 26, (60, 60, 60), True)
    p.text("Unit 4  ·  phrases", 15, (90, 90, 90))
    p.gap(8)
    for i, label in enumerate(("Hello", "I love you", "See you", "Thank you", "Good night")):
        col = (88, 204, 2) if i < 3 else (220, 220, 220)
        top = p.box(64, col, x=180, w=420, radius=28)
        ink = (255, 255, 255) if i < 3 else (60, 60, 60)
        p.d.text((210, top + 18), label, font=font(18, True), fill=ink)
        p.gap(12)
    p.save("duolingo")


def twitch():
    p = Page((14, 14, 16))
    p.chrome("Twitch", "https://www.twitch.tv/", (145, 70, 255))
    cards = (
        ("piano night", "1.2K", (80, 40, 120)),
        ("reading chat", "430", (40, 60, 90)),
        ("art stream", "2.8K", (90, 40, 50)),
        ("quiet lobby", "90", (30, 50, 40)),
    )
    for title, viewers, col in cards:
        top = p.box(150, (24, 24, 27), radius=12)
        p.d.rectangle((28, top + 14, 360, top + 136), fill=col)
        p.d.text((376, top + 28), title, font=font(20, True), fill=(240, 240, 240))
        p.d.text((376, top + 68), viewers + " watching", font=font(15), fill=(180, 180, 190))
        p.d.text((376, top + 100), "Just chatting", font=font(14), fill=(145, 70, 255))
        p.gap(12)
    p.save("twitch")


def fourchan():
    p = Page((255, 255, 238))
    p.chrome("4chan", "https://boards.4chan.org/", (240, 224, 214), (128, 0, 0))
    p.d.rectangle((0, 86, W, p.im.height), fill=(255, 255, 238))
    p.text("boards.4chan.org", 22, (128, 0, 0), True)
    p.text("Text index only. Pictures are not loaded in this pane.", 15, (90, 60, 40))
    p.gap(8)
    boards = (
        ("/a/", "Anime & Manga"),
        ("/v/", "Video Games"),
        ("/vg/", "Video Game Generals"),
        ("/lit/", "Literature"),
        ("/mu/", "Music"),
        ("/jp/", "Otaku Culture"),
        ("/vp/", "Pokémon"),
        ("/tv/", "Television"),
    )
    for code, name in boards:
        p.text(code + "   " + name, 18, (0, 0, 128))
    p.gap(12)
    p.text("Monika's line about this place still fires. The page itself stays a board list.", 15, (80, 50, 40))
    p.save("4chan")


def pixiv():
    p = Page((255, 255, 255))
    p.chrome("pixiv", "https://www.pixiv.net/", (255, 255, 255), (0, 150, 250))
    p.d.rounded_rectangle((16, 44, W - 16, 76), 8, outline=(210, 210, 210), width=1)
    p.text("Recommended  ·  safe cards. Two tiles are hidden.", 15, (80, 80, 80))
    p.gap(8)
    colors = (
        (255, 182, 193), (176, 224, 230), (255, 228, 181),
        (221, 160, 221), (152, 251, 152), (230, 230, 250),
    )
    for i, col in enumerate(colors):
        c = i % 3
        x = 16 + c * 254
        y = p.y + (i // 3) * 250
        p.d.rounded_rectangle((x, y, x + 240, y + 230), 12, fill=col)
        p.d.text((x + 16, y + 190), "sketch " + str(i + 1), font=font(15, True), fill=(40, 40, 40))
    # Two censored tiles over the last row area, drawn as blur not figures.
    blur = Image.new("RGB", (240, 230), (40, 20, 40))
    noise = Image.effect_noise((240, 230), 40).convert("RGB")
    blur = Image.blend(blur, noise, 0.35).filter(ImageFilter.GaussianBlur(18))
    p.im.paste(blur, (16, p.y + 250))
    p.im.paste(blur, (270, p.y + 250))
    d = ImageDraw.Draw(p.im)
    d.text((70, p.y + 340), "18+  hidden", font=font(18, True), fill=(255, 220, 230))
    d.text((324, p.y + 340), "18+  hidden", font=font(18, True), fill=(255, 220, 230))
    p.y += 520
    p.bottom = p.y
    p.save("pixiv")


def deviantart():
    p = Page((6, 8, 12))
    p.chrome("DeviantArt", "https://www.deviantart.com/", (5, 206, 124), (6, 8, 12))
    for title, col in (
        ("morning window", (80, 90, 120)),
        ("green eyes study", (40, 90, 70)),
        ("empty classroom", (90, 50, 60)),
        ("ribbon sketch", (100, 70, 80)),
    ):
        top = p.box(160, (18, 22, 28), radius=12)
        p.d.rectangle((28, top + 16, 280, top + 144), fill=col)
        p.d.text((300, top + 36), title, font=font(20, True), fill=(230, 230, 230))
        p.d.text((300, top + 74), "original card, not a stolen deviation", font=font(14), fill=(150, 160, 160))
        p.gap(12)
    p.save("deviantart")


def mal():
    p = Page((255, 255, 255))
    p.chrome("MyAnimeList", "https://myanimelist.net/", (46, 81, 162))
    p.text("Watching", 22, (30, 30, 30), True)
    rows = (
        ("A quiet slice of life", "6", "Watching"),
        ("Piano club", "4", "Plan to watch"),
        ("Literature adaptation", "12", "Completed"),
        ("Rainy town", "3", "On hold"),
    )
    for title, eps, state in rows:
        top = p.box(72, (247, 248, 252), radius=8)
        p.d.rectangle((28, top + 12, 78, top + 60), fill=(46, 81, 162))
        p.d.text((96, top + 12), title, font=font(17, True), fill=(30, 30, 30))
        p.d.text((96, top + 40), eps + " eps   ·   " + state, font=font(14), fill=(80, 80, 90))
        p.gap(8)
    p.save("mal")


def docs():
    p = Page((241, 243, 244))
    p.chrome("Google Docs", "https://docs.google.com/", (255, 255, 255), (32, 33, 36))
    p.d.rounded_rectangle((16, 44, W - 16, 76), 8, outline=(210, 210, 210), width=1)
    p.gap(6)
    p.text("Untitled document", 16, (60, 64, 67))
    p.gap(8)
    top = p.box(720, (255, 255, 255), x=70, w=650, radius=2)
    # box() advanced y; draw inside the captured top
    p.d.text((100, top + 40), "Dear Monika,", font=font(22), fill=(32, 33, 36))
    body = (
        "I opened a document instead of a video.\n\n"
        "The first line is still the hard one.\n\n"
        "I will write the rest after tea."
    )
    yy = top + 90
    for line in body.split("\n"):
        p.d.text((100, yy), line, font=font(18), fill=(32, 33, 36))
        yy += 28
    p.bottom = top + 720
    p.save("docs")


def crunchyroll():
    p = Page((0, 0, 0))
    p.chrome("Crunchyroll", "https://www.crunchyroll.com/", (244, 117, 33))
    p.text("Popular", 20, (255, 255, 255), True)
    x = 16
    for col, name in (
        ((180, 50, 40), "Club"),
        ((40, 80, 140), "Rain"),
        ((40, 100, 70), "Keys"),
        ((90, 50, 90), "Letters"),
    ):
        p.d.rounded_rectangle((x, p.y, x + 180, p.y + 250), 8, fill=col)
        p.d.text((x + 12, p.y + 210), name, font=font(16, True), fill=(255, 255, 255))
        x += 192
    p.y += 270
    p.bottom = p.y
    p.text("Cards are color blocks. Subtitles would play in the real app.", 14, (180, 180, 180))
    p.save("crunchyroll")


def piano():
    p = Page((20, 16, 24))
    p.chrome("Virtual Piano", "https://www.virtualpiano.net/", (20, 16, 24))
    p.text("Click a key. She will hear that you opened this.", 16, (220, 200, 210))
    p.gap(20)
    white = 14
    key_w = 48
    x = 24
    top = p.y
    for i in range(white):
        p.d.rounded_rectangle((x, top, x + key_w - 4, top + 220), 6, fill=(245, 245, 245))
        x += key_w
    blacks = (0, 1, 3, 4, 5, 7, 8, 10, 11, 12)
    for i in blacks:
        bx = 24 + int((i + 0.65) * key_w)
        p.d.rounded_rectangle((bx, top, bx + 28, top + 130), 4, fill=(20, 20, 20))
    p.y = top + 250
    p.bottom = p.y
    p.text("C  D  E  F  G  A  B", 18, (230, 210, 220))
    p.save("virtualpiano")


def r34():
    """Censored page. No fetch, no figures."""
    base = Image.new("RGB", (W, 1600), (28, 8, 18))
    noise = Image.effect_noise((W, 1600), 48).convert("RGB")
    tint = Image.new("RGB", (W, 1600), (90, 20, 40))
    im = Image.blend(base, noise, 0.45)
    im = Image.blend(im, tint, 0.35)
    # Block mosaic, then a hard blur so nothing reads as a picture.
    small = im.resize((40, 80), Image.BILINEAR).resize((W, 1600), Image.NEAREST)
    im = small.filter(ImageFilter.GaussianBlur(16))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 86), fill=(70, 10, 30))
    d.text((18, 8), "rule34.xxx", font=font(22, True), fill=(255, 210, 220))
    d.rounded_rectangle((16, 44, W - 16, 76), 8, fill=(255, 255, 255))
    d.text((28, 50), "https://rule34.xxx/", font=font(15), fill=(40, 40, 40))
    d.rounded_rectangle((70, 360, W - 70, 620), 18, fill=(24, 6, 14))
    d.text((120, 420), "18+   превью скрыто", font=font(28, True), fill=(255, 180, 200))
    d.text((120, 480), "Страницу не открывали и не сохраняли.", font=font(18), fill=(230, 190, 200))
    d.text((120, 516), "Моника всё равно заметит, что ты зашёл сюда.", font=font(18), fill=(230, 190, 200))
    path = os.path.join(OUT, "r34m.png")
    im.save(path, "PNG")
    print("wrote", path)


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    youtube()
    wikipedia()
    github()
    twitter()
    reddit()
    pinterest()
    netflix()
    duolingo()
    twitch()
    fourchan()
    pixiv()
    deviantart()
    mal()
    docs()
    crunchyroll()
    piano()
    r34()


if __name__ == "__main__":
    main()
