# -*- coding: utf-8 -*-
# MAS BIOS: jump from MAS OS into the Java launcher, and Android relaunch
# without utter_restart (that closes the SDL process on the phone).

default persistent._mas_os_bios_note = ""

init -4 python in mas_os:
    import store

    bios_note = ""

    def android_on():
        return bool(getattr(store.renpy, "android", False))

    def _jnius_open_bios(section, force_bios=True, boot_renpy=False):
        """
        Start LauncherActivity in the default process, then kill :game.
        """
        from jnius import autoclass
        PythonActivity = autoclass("org.renpy.android.PythonSDLActivity")
        Launcher = autoclass("ru.kurokawa.mas.bios.LauncherActivity")
        Intent = autoclass("android.content.Intent")
        activity = PythonActivity.mActivity
        if activity is None:
            raise Exception("no PythonSDLActivity")
        intent = Intent(activity, Launcher)
        intent.putExtra("force_bios", bool(force_bios))
        intent.putExtra("boot_renpy", bool(boot_renpy))
        if section:
            intent.putExtra("open", str(section))
        intent.setFlags(
            Intent.FLAG_ACTIVITY_NEW_TASK
            | Intent.FLAG_ACTIVITY_CLEAR_TOP
            | Intent.FLAG_ACTIVITY_SINGLE_TOP
        )
        activity.startActivity(intent)
        Process = autoclass("android.os.Process")
        Process.killProcess(Process.myPid())

    def open_bios(section="play"):
        """
        From MAS OS: open BIOS on a section (play/files/archives/content/library/saves/update/engine/system).
        """
        global bios_note
        if not android_on():
            bios_note = u"BIOS только на Android."
            try:
                store.renpy.notify(bios_note)
            except Exception:
                pass
            return
        try:
            if game_entered:
                try:
                    end_game_session()
                except Exception:
                    pass
            try:
                os_persist()
            except Exception:
                try:
                    store.renpy.save_persistent()
                except Exception:
                    pass
            _jnius_open_bios(section, force_bios=True, boot_renpy=False)
        except Exception:
            bios_note = u"BIOS не открылся: нет jnius или класса лаунчера."
            try:
                store.renpy.notify(bios_note)
            except Exception:
                pass

    def android_relaunch(mode="boot"):
        """
        mode boot — skip BIOS UI and start the game again (MAS OS reboot).
        mode bios — show BIOS.
        """
        global bios_note
        if not android_on():
            return False
        try:
            try:
                os_persist()
            except Exception:
                try:
                    store.renpy.save_persistent()
                except Exception:
                    pass
            if mode == "bios":
                _jnius_open_bios("play", force_bios=True, boot_renpy=False)
            else:
                _jnius_open_bios("play", force_bios=False, boot_renpy=True)
            return True
        except Exception:
            bios_note = u"Перезапуск через BIOS не вышел, обычный restart."
            return False

    def open_bios_submods():
        open_bios("content")
        return None
