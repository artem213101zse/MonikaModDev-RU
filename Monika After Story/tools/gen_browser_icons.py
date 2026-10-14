# -*- coding: utf-8 -*-
"""Small marks shown beside browser bookmarks. Not official logos."""

from __future__ import print_function

import os

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "game", "mod_assets", "mas_os", "browser", "ico",
))


def font(size, bold=True):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    path = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", name)
    return ImageFont.truetype(path, size)


def base(color):
    im = Image.new("RGB", (64, 64), color)
    return im, ImageDraw.Draw(im)


def letter(name, color, ch, fg=(255, 255, 255)):
    im, d = base(color)
    f = font(32)
    box = d.textbbox((0, 0), ch, font=f)
    w, h = box[2] - box[0], box[3] - box[1]
    d.text(((64 - w) / 2 - box[0], (64 - h) / 2 - box[1] - 1), ch, font=f, fill=fg)
    im.save(os.path.join(OUT, name + ".png"), "PNG")


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    im, d = base((204, 0, 0))
    d.polygon([(22, 14), (22, 50), (48, 32)], fill=(255, 255, 255))
    im.save(os.path.join(OUT, "youtube.png"), "PNG")
    letter("wikipedia", (255, 255, 255), "W", (32, 32, 32))
    letter("twitter", (29, 155, 240), "X")
    letter("reddit", (255, 69, 0), "r")
    letter("pinterest", (189, 8, 28), "P")
    letter("netflix", (20, 20, 20), "N", (229, 9, 20))
    letter("monikamoddev", (13, 17, 23), "G")
    letter("duolingo", (88, 204, 2), "D")
    letter("twitch", (145, 70, 255), "T")
    letter("4chan", (240, 224, 214), "4", (128, 0, 0))
    letter("r34m", (74, 16, 36), "18")
    letter("pixiv", (0, 150, 250), "p")
    letter("deviantart", (5, 206, 124), "d", (6, 8, 12))
    letter("mal", (46, 81, 162), "M")
    letter("docs", (66, 133, 244), "D")
    letter("crunchyroll", (244, 117, 33), "C")
    im, d = base((28, 22, 32))
    for i in range(4):
        d.rectangle((8 + i * 13, 16, 18 + i * 13, 50), fill=(245, 245, 245))
    d.rectangle((16, 16, 24, 34), fill=(12, 12, 12))
    d.rectangle((42, 16, 50, 34), fill=(12, 12, 12))
    im.save(os.path.join(OUT, "virtualpiano.png"), "PNG")
    print("icons", OUT)


if __name__ == "__main__":
    main()
