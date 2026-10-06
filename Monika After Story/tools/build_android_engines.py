# -*- coding: utf-8 -*-
# Build hello_engine + Stockfish 11 ELFs for Android (arm64, x86_64).
# Needs NDK 21.3.6528147 in the MAS rapt SDK.

from __future__ import print_function

import os
import shutil
import subprocess
import sys
import tarfile
import zipfile

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.normpath(os.path.join(HERE, ".."))
BIOS = os.path.join(GAME, "game", "mod_assets", "mas_os", "bios")
OUT = os.path.join(BIOS, "bin")
NATIVE = os.path.join(BIOS, "native")
SDK = os.path.normpath(os.path.join(os.path.expanduser("~"), "Documents", "renpy-7.4.11-sdk"))
NDK_VER = "21.3.6528147"
SF_URL = "https://github.com/official-stockfish/Stockfish/archive/refs/tags/sf_11.tar.gz"
WORK = os.path.join(HERE, "_engine_build")


def ndk_root():
    env = os.environ.get("ANDROID_NDK_HOME") or os.environ.get("NDK")
    if env and os.path.isdir(env):
        return env
    path = os.path.join(SDK, "rapt", "Sdk", "ndk", NDK_VER)
    if os.path.isdir(path):
        return path
    return None


def clang_bin(ndk):
    return os.path.join(ndk, "toolchains", "llvm", "prebuilt", "windows-x86_64", "bin")


def clang_cc(ndk, triple):
    base = os.path.join(clang_bin(ndk), triple + "21-clang")
    for cand in (base + ".cmd", base):
        if os.path.isfile(cand):
            return cand
    return base + ".cmd"


def clang_cxx(ndk, triple):
    base = os.path.join(clang_bin(ndk), triple + "21-clang++")
    for cand in (base + ".cmd", base):
        if os.path.isfile(cand):
            return cand
    return base + ".cmd"


def run(cmd, cwd=None, env=None):
    print(" ".join(cmd))
    if os.name == "nt" and cmd and str(cmd[0]).lower().endswith(".cmd"):
        quoted = subprocess.list2cmdline(cmd)
        subprocess.check_call(quoted, cwd=cwd, env=env, shell=True)
        return
    subprocess.check_call(cmd, cwd=cwd, env=env)


def download(url, dest):
    print("download " + url)
    folder = os.path.dirname(dest)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    req = urlopen(url)
    try:
        data = req.read()
    finally:
        req.close()
    handle = open(dest, "wb")
    try:
        handle.write(data)
    finally:
        handle.close()
    print("saved " + dest + " (" + str(len(data)) + " bytes)")


def extract_tar_gz(archive, dest):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    os.makedirs(dest)
    tar = tarfile.open(archive, "r:gz")
    try:
        tar.extractall(dest)
    finally:
        tar.close()


def find_sf_src(root):
    for dirpath, dirnames, filenames in os.walk(root):
        if "Makefile" in filenames and "stockfish.cpp" in filenames:
            return dirpath
        if "Makefile" in filenames and "main.cpp" in filenames:
            return dirpath
    return None


def build_hello(ndk, triple, dest_name):
    src = os.path.join(NATIVE, "hello_engine.c")
    dest = os.path.join(OUT, dest_name)
    cc = clang_cc(ndk, triple)
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    run([cc, "-O2", "-fPIE", "-pie", "-o", dest, src])
    print("built " + dest)


def list_cpp(src):
    files = []
    for dirpath, _, names in os.walk(src):
        for name in names:
            if name.endswith(".cpp"):
                files.append(os.path.join(dirpath, name))
    files.sort()
    return files


def build_stockfish(ndk, triple, extra_flags, dest_name):
    archive = os.path.join(WORK, "sf_11.tar.gz")
    unpacked = os.path.join(WORK, "sf_11")
    if not os.path.isfile(archive):
        download(SF_URL, archive)
    if not os.path.isdir(unpacked):
        extract_tar_gz(archive, unpacked)
    src = find_sf_src(unpacked)
    if not src:
        raise Exception("Stockfish src not found in " + unpacked)
    cpp = list_cpp(src)
    if not cpp:
        raise Exception("no C++ files in " + src)
    cxx = clang_cxx(ndk, triple)
    dest = os.path.join(OUT, dest_name)
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    cmd = [
        cxx,
        "-O3",
        "-DNDEBUG",
        "-DIS_64BIT",
        "-fPIE",
        "-pie",
        "-static-libstdc++",
        "-pthread",
        "-o",
        dest,
    ]
    cmd.extend(extra_flags)
    cmd.extend(cpp)
    run(cmd, cwd=src)
    if not os.path.isfile(dest):
        raise Exception("stockfish ELF not produced: " + dest)
    print("built " + dest + " (" + str(os.path.getsize(dest)) + " bytes)")


def main():
    ndk = ndk_root()
    if not ndk:
        print("NDK " + NDK_VER + " not found. Install into rapt/Sdk/ndk or set ANDROID_NDK_HOME.")
        return 1
    print("NDK " + ndk)
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    build_hello(ndk, "aarch64-linux-android", "hello_engine-arm64")
    build_hello(ndk, "x86_64-linux-android", "hello_engine-x86_64")
    # make is from Git for Windows or MSYS. Stockfish Makefile is GNU make.
    try:
        build_stockfish(
            ndk,
            "aarch64-linux-android",
            ["-DUSE_NEON", "-DUSE_POPCNT", "-DUSE_PREFETCH"],
            "stockfish-arm64",
        )
        build_stockfish(
            ndk,
            "x86_64-linux-android",
            ["-DUSE_POPCNT", "-DUSE_PREFETCH"],
            "stockfish-x86_64",
        )
    except Exception as err:
        print("stockfish build failed: " + str(err))
        print("hello_engine ELFs are still usable for the process probe.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
