# -*- coding: utf-8 -*-
# Copies MAS BIOS HTML/Java/res into the MAS Ren'Py 7.4.11 RAPT tree.
# WebView reads getFilesDir()/bios_www; those bytes come from
# app/assets/www (no x- prefix) and/or renpyandroid res/raw.

from __future__ import print_function

import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.normpath(os.path.join(HERE, ".."))
BIOS = os.path.join(GAME, "game", "mod_assets", "mas_os", "bios")
SDK = os.path.normpath(os.path.join(os.path.expanduser("~"), "Documents", "renpy-7.4.11-sdk"))

WWW_NAMES = ("index.html", "styles.css", "app.js")
RAW_NAMES = (
    ("index.html", "bios_index.html"),
    ("styles.css", "bios_styles.css"),
    ("app.js", "bios_app.js"),
)


def copy_bytes(src, dst):
    folder = os.path.dirname(dst)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    shutil.copyfile(src, dst)
    print("copied " + src + " -> " + dst)


def copy_www(dest_dir):
    for name in WWW_NAMES:
        src = os.path.join(BIOS, name)
        if not os.path.isfile(src):
            raise Exception("missing " + src)
        copy_bytes(src, os.path.join(dest_dir, name))


def copy_raw(dest_dir):
    for name, raw_name in RAW_NAMES:
        src = os.path.join(BIOS, name)
        if not os.path.isfile(src):
            raise Exception("missing " + src)
        copy_bytes(src, os.path.join(dest_dir, raw_name))


def main():
    rapt = os.path.join(SDK, "rapt", "project")
    if not os.path.isdir(rapt):
        print("rapt tree missing: " + rapt)
        return

    copy_www(os.path.join(rapt, "app", "src", "main", "assets", "www"))
    copy_raw(os.path.join(rapt, "renpyandroid", "src", "main", "res", "raw"))

    java_src = os.path.join(
        BIOS, "java", "ru", "kurokawa", "mas", "bios", "LauncherActivity.java"
    )
    java_dst = os.path.join(
        rapt, "renpyandroid", "src", "main", "java",
        "ru", "kurokawa", "mas", "bios", "LauncherActivity.java",
    )
    copy_bytes(java_src, java_dst)

    res_pairs = (
        ("res/layout/activity_launcher.xml",
         "renpyandroid/src/main/res/layout/activity_launcher.xml"),
        ("res/values/mas_bios.xml",
         "renpyandroid/src/main/res/values/mas_bios.xml"),
        ("res/xml/file_paths.xml",
         "renpyandroid/src/main/res/xml/file_paths.xml"),
        ("res/xml/file_paths.xml",
         "app/src/main/res/xml/file_paths.xml"),
        ("res/drawable/sideload_button.xml",
         "renpyandroid/src/main/res/drawable/sideload_button.xml"),
        ("res/drawable/sideload_button_start.xml",
         "renpyandroid/src/main/res/drawable/sideload_button_start.xml"),
    )
    for rel_src, rel_dst in res_pairs:
        src = os.path.join(BIOS, rel_src.replace("/", os.sep))
        dst = os.path.join(rapt, rel_dst.replace("/", os.sep))
        copy_bytes(src, dst)

    print("BIOS overlay synced into " + rapt)


if __name__ == "__main__":
    main()
