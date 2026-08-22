# MAS OS boot guard and overlay searchpath live in game/0config.rpy
# (python early). This file used to hold them, but game/Submods/ is parsed
# before mas_os_early.rpy in unicode order, so a broken submod .rpy aborted
# the load before the guard could park Submods. 0config.rpy runs first.

python early:
    pass
