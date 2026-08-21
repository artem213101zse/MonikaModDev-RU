# MAS OS — park Submods before Ren'Py compiles them.
# Must live OUTSIDE game/: game/Submods_disabled/*.rpy would still load.
# Flag files sit next to the game folder (config.basedir).

python early:
    import os

    def _mas_os_early_park_submods():
        based = os.path.normpath(renpy.config.basedir)
        src = os.path.join(based, "game", "Submods")
        dst = os.path.join(based, "Submods_disabled")
        oneshot = os.path.join(based, "mas_os_safe_mode")
        sticky = os.path.join(based, "mas_os_safe_mode_on")
        if not (os.path.isfile(oneshot) or os.path.isfile(sticky)):
            return
        if not os.path.isdir(src):
            if os.path.isfile(oneshot):
                try:
                    os.remove(oneshot)
                except Exception:
                    pass
            return
        try:
            if not os.path.isdir(dst):
                os.makedirs(dst)
        except Exception:
            return
        try:
            for name in os.listdir(src):
                s = os.path.join(src, name)
                d = os.path.join(dst, name)
                if os.path.exists(d):
                    base, ext = os.path.splitext(name)
                    n = 2
                    while os.path.exists(d):
                        d = os.path.join(
                            dst,
                            "{0}_off{1}{2}".format(base, n, ext),
                        )
                        n += 1
                try:
                    os.rename(s, d)
                except Exception:
                    pass
            try:
                os.rmdir(src)
            except Exception:
                pass
        except Exception:
            pass
        if os.path.isfile(oneshot):
            try:
                os.remove(oneshot)
            except Exception:
                pass

    try:
        _mas_os_early_park_submods()
    except Exception:
        pass
