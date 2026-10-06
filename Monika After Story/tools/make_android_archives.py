# -*- coding: utf-8 -*-
# Pack DDLC images/audio into RPA-3.0 for BIOS download.
# Writes tools/android-archives/*.rpa + *.sha256 and fills hashes in
# game/mod_assets/mas_os/bios/archives.json.
# Upload the .rpa and .sha256 to GitHub Releases (same names).

from __future__ import print_function

import hashlib
import json
import os
import sys
import zlib

try:
    import cPickle as pickle
except ImportError:
    import pickle

HERE = os.path.dirname(os.path.abspath(__file__))
GAME_ROOT = os.path.normpath(os.path.join(HERE, ".."))
GAME = os.path.join(GAME_ROOT, "game")
BIOS_JSON = os.path.join(GAME, "mod_assets", "mas_os", "bios", "archives.json")
OUT = os.path.join(HERE, "android-archives")
RPA_KEY = 0x42424242


def _walk(rel_dir):
    root = os.path.join(GAME, rel_dir)
    out = []
    if not os.path.isdir(root):
        return out
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, GAME).replace("\\", "/")
            out.append((rel, path))
    out.sort(key=lambda item: item[0].lower())
    return out


def _sha256(path):
    digest = hashlib.sha256()
    handle = open(path, "rb")
    try:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    finally:
        handle.close()
    return digest.hexdigest()


def _pack(dest, files):
    # RPA-3.0, pickle protocol 2 — его читает Java BIOS.
    if os.path.exists(dest):
        os.remove(dest)
    handle = open(dest, "wb")
    try:
        handle.write(b"RPA-3.0 XXXXXXXXXXXXXXXX XXXXXXXX\n")
        index = {}
        for name, path in files:
            handle.write(b"Made with Ren'Py.")
            offset = handle.tell()
            src = open(path, "rb")
            try:
                data = src.read()
            finally:
                src.close()
            handle.write(data)
            key_name = name
            if sys.version_info[0] < 3 and not isinstance(key_name, unicode):
                key_name = key_name.decode("utf-8")
            index[key_name] = [(offset ^ RPA_KEY, len(data) ^ RPA_KEY, b"")]
        indexoff = handle.tell()
        handle.write(zlib.compress(pickle.dumps(index, 2)))
        handle.seek(0)
        header = "RPA-3.0 %016x %08x\n" % (indexoff, RPA_KEY)
        handle.write(header.encode("ascii"))
    finally:
        handle.close()


def _update_manifest(info):
    data = json.load(open(BIOS_JSON, "r"))
    packs = data.get("packs") or []
    for pack in packs:
        item = info.get(pack.get("file"))
        if not item:
            continue
        pack["sha256"] = item["sha256"]
        pack["bytes"] = item["bytes"]
    handle = open(BIOS_JSON, "w")
    try:
        json.dump(data, handle, indent=2, sort_keys=False, ensure_ascii=False)
        handle.write("\n")
    finally:
        handle.close()


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    jobs = (
        ("images.rpa", _walk("images")),
        ("audio.rpa", _walk("bgm") + _walk("sfx")),
    )
    info = {}
    for name, files in jobs:
        if not files:
            print("пусто: " + name)
            continue
        dest = os.path.join(OUT, name)
        print("pack %s (%d files)" % (name, len(files)))
        _pack(dest, files)
        digest = _sha256(dest)
        size = os.path.getsize(dest)
        sha_path = dest + ".sha256"
        sha_handle = open(sha_path, "w")
        try:
            sha_handle.write(digest + "  " + name + "\n")
        finally:
            sha_handle.close()
        info[name] = {"sha256": digest, "bytes": size}
        print("  %s  %d bytes  %s" % (name, size, digest))
        sys.path.insert(0, HERE)
        import rpa_extract
        check = os.path.join(OUT, "_check_" + name.replace(".", "_"))
        count, error = rpa_extract.extract_rpa(dest, check)
        if error:
            raise Exception("%s roundtrip failed: %s" % (name, error))
        print("  unpacked %d files" % count)
    _update_manifest(info)
    print("updated " + BIOS_JSON)
    print("upload tools/android-archives/*.rpa and *.sha256 to GitHub Releases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
