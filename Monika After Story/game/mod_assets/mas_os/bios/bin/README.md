# Android chess ELFs

`hello_engine-arm64`, `hello_engine-x86_64`, `stockfish-arm64`, `stockfish-x86_64`.

`sync_mas_bios.py` copies them into rapt `jniLibs` as `libhello_engine.so` / `libstockfish.so`. BIOS and Ren'Py exec from `nativeLibraryDir`. Android 10+ (`targetSdk 33`) returns EACCES for exec from `getFilesDir()`.

Build: `python tools/build_android_engines.py` after NDK 21.3.6528147 is in `Documents/renpy-7.4.11-sdk/rapt/Sdk/ndk`.
