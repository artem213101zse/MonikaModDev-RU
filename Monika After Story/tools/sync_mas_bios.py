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

WWW_NAMES = ("index.html", "styles.css", "app.js", "archives.json")
RAW_NAMES = (
    ("index.html", "bios_index.html"),
    ("styles.css", "bios_styles.css"),
    ("app.js", "bios_app.js"),
    ("archives.json", "bios_archives.json"),
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

    java_root = os.path.join(BIOS, "java")
    java_dst_root = os.path.join(rapt, "renpyandroid", "src", "main", "java")
    for dirpath, _, filenames in os.walk(java_root):
        for name in filenames:
            if not name.endswith(".java"):
                continue
            src = os.path.join(dirpath, name)
            rel = os.path.relpath(src, java_root)
            copy_bytes(src, os.path.join(java_dst_root, rel))

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

    bin_src = os.path.join(BIOS, "bin")
    jni_map = (
        ("hello_engine-arm64", "arm64-v8a", "libhello_engine.so"),
        ("hello_engine-x86_64", "x86_64", "libhello_engine.so"),
        ("stockfish-arm64", "arm64-v8a", "libstockfish.so"),
        ("stockfish-x86_64", "x86_64", "libstockfish.so"),
    )
    if os.path.isdir(bin_src):
        for name in os.listdir(bin_src):
            if name.endswith(".md") or name.startswith("."):
                continue
            src = os.path.join(bin_src, name)
            if not os.path.isfile(src):
                continue
            copy_bytes(src, os.path.join(rapt, "app", "src", "main", "assets", name))
            copy_bytes(src, os.path.join(
                rapt, "renpyandroid", "src", "main", "assets", name
            ))
        for name, abi, so_name in jni_map:
            src = os.path.join(bin_src, name)
            if not os.path.isfile(src):
                print("missing jni ELF " + src)
                continue
            for module in ("app", "renpyandroid"):
                copy_bytes(src, os.path.join(
                    rapt, module, "src", "main", "jniLibs", abi, so_name
                ))

    copy_android_icons(GAME, rapt)

    print("BIOS overlay synced into " + rapt)


def _resize_png(src, dst, size):
    folder = os.path.dirname(dst)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    try:
        from PIL import Image
        im = Image.open(src).convert("RGBA")
        resample = getattr(
            getattr(Image, "Resampling", Image),
            "LANCZOS",
            getattr(Image, "ANTIALIAS", 1),
        )
        im = im.resize((size, size), resample)
        im.save(dst, "PNG")
        print("icon {0}x{0} -> {1}".format(size, dst))
        return
    except Exception:
        pass
    shutil.copyfile(src, dst)
    print("copied icon (no resize) " + src + " -> " + dst)


def copy_android_icons(game_dir, rapt):
    """Write custom Monika art into rapt mipmaps.

    Ren'Py IconMaker skips existing mipmaps when update_always is false,
    so the default Sayori icon stays unless we overwrite it here.
    """
    fg = os.path.join(game_dir, "android-icon_foreground.png")
    bg = os.path.join(game_dir, "android-icon_background.png")
    legacy = os.path.join(game_dir, "android-icon.png")
    if os.path.isfile(fg) and not os.path.isfile(legacy):
        shutil.copyfile(fg, legacy)
        print("copied " + fg + " -> " + legacy)
    if not os.path.isfile(fg):
        print("no android-icon_foreground.png, skip icons")
        return
    if not os.path.isfile(bg):
        bg = fg
    densities = (
        ("mdpi", 48, 108),
        ("hdpi", 72, 162),
        ("xhdpi", 96, 216),
        ("xxhdpi", 144, 324),
        ("xxxhdpi", 192, 432),
    )
    res = os.path.join(rapt, "app", "src", "main", "res")
    for dpi, icon_px, layer_px in densities:
        folder = os.path.join(res, "mipmap-" + dpi)
        _resize_png(fg, os.path.join(folder, "icon.png"), icon_px)
        _resize_png(fg, os.path.join(folder, "icon_foreground.png"), layer_px)
        _resize_png(bg, os.path.join(folder, "icon_background.png"), layer_px)


if __name__ == "__main__":
    main()
