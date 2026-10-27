# -*- coding: utf-8 -*-
# Моника: Эпилог — пояснение вместо официального апдейтера MAS.
# Плашка: mod_assets/updateavailable.png (+ _d). Перехват: jump в updater.rpy.

label mas_epilogue_update_blocked:
    show monika 2eksdla at t11 zorder MAS_MONIKA_Z
    m 2eksdla "[player], официальный Monika After Story уже обновился…"
    m 3rksdlb "Но наш порт «Моника: Эпилог» к этой версии ещё не готов."
    m 1ekc "Если обновиться оттуда, подтянется английский оригинал — перевод и наши правки слетят."
    m 3eka "Подожди, пожалуйста, наш релиз. Когда порт обновим — сообщим отдельно."
    m 1hua "А пока просто продолжим как обычно, хорошо?"

    python:
        import time
        try:
            if renpy.showing("masupdateroverlay", layer="front"):
                renpy.hide("masupdateroverlay", layer="front")
        except Exception:
            pass
        try:
            if renpy.showing("masupdateroverlay", layer="overlay"):
                renpy.hide("masupdateroverlay", layer="overlay")
        except Exception:
            pass
        try:
            link = store.mas_updater.unstable if persistent._mas_unstable_mode else store.mas_updater.regular
            if persistent._update_last_checked is None:
                persistent._update_last_checked = {}
            persistent._update_last_checked[link] = time.time()
        except Exception:
            pass
    return
