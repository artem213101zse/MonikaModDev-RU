# --- FILE MAP ---
# overrides.rpy — заплатки поверх DDLC, без замены целых ванильных файлов
#
# Ванильные script.rpy / screens мы не копируем целиком. Если надо
# поменять одну переменную «как в DDLC, но по-нашему» — сюда.
# init 10 / init -10 специально раньше или позже обычных блоков,
# чтобы гарантированно перебить дефолт.
#
# Перевод: только если здесь торчат строки UI.
# ---

## This file is for overriding specific declarations from DDLC
## Use this if you want to change a few variables, but don't want
## to replace entire script files that are otherwise fine.

## Normal overrides
## These overrides happen after any of the normal init blocks in scripts.
## Use these to change variables on screens, effects, and the like.
init 10 python:
    pass

## Early overrides
## These overrides happen before the normal init blocks in scripts.
## Use this in the rare event that you need to overwrite some variable
## before it's called in another init block.
## You likely won't use this.
init -10 python:
    pass

## Super early overrides
## You'll need a block like this for creator defined screen language
## Don't use this unless you know you need it
python early:
    pass
