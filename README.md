![Monika After Story](https://github.com/Monika-After-Story/MonikaModDev/blob/master/Monika%20After%20Story/game/mod_assets/menu_new.png?raw=True)

# Моника: Эпилог (MAS)
Моника: Эпилог - это фанатский мод для бесплатной игры [Doki Doki Literature Club](https://www.ddlc.moe) от [Team Salvato](http://teamsalvato.com/). Мод продолжает третий акт и превращает его в симулятор вечной жизни с Моникой: новые события, диалоги, обработчики тем и мета-комментарии!

Актуальную стабильную версию всегда можно скачать на странице [Релизы](http://www.monikaafterstory.com/releases.html)

Если вы хотите создать свой собственный мод, подобный этому, ознакомьтесь с нашим родственным проектом: [DDLCModTemplate](https://github.com/therationalpi/DDLCModTemplate).

### Установка

1. Перейдите на [страницу релизов](http://www.monikaafterstory.com/releases.html).

2. Нажмите на ссылку для вашей ОС.

3. После скачивания запустите установщик и следуйте инструкциям.
    * Если программа установки не работает в вашей системе, ознакомьтесь с инструкциями по установке вручную, приведенными ниже.

4. При запуске DDLC теперь будет загружен мод Моника: Эпилог.

### Установка вручную

**Следуйте этим шагам только если установщик не запускается на вашей системе**

1. Перейдите на страницу [релизов](http://www.monikaafterstory.com/releases.html).

2. Нажмите на нужную ссылку **Zips**. Это скачает zip-файл.

3. Распакуйте содержимое zip-файла в базовый каталог игры (папку, в которой лежит DDLC.exe) вашей установки DDLC.

4. При запуске DDLC теперь будет загружен мод Моника: Эпилог.

**ПРИМЕЧАНИЕ: исходные файлы и файлы, скачанные напрямую из репозитория, предназначены только для целей разработки и могут работать не так, как ожидается, если использовать их для модификации игры. Пожалуйста, используйте только одну из [релизных версий](http://www.monikaafterstory.com/releases.html).*

Более подробная помощь по установке (включая руководство пользователя для Mac, не поддерживающего steam) - в [Часто задаваемых вопросах](https://github.com/Monika-After-Story/MonikaModDev/wiki/FAQ)

### Особенности

* Проведите вечность с Моникой!

* Десятки новых тем для разговора

* Теперь вы можете сказать Монике, о чём хотите поговорить

### Будущие особенности

* Новые игры и занятия с Моникой

* Еще больше уникальных событий и сюжета


## Вклад в Моника: Эпилог

### Ошибки и предложения
Если у вас возникли проблемы с MAS, пожалуйста, отправьте [баг-репорт](https://github.com/Monika-After-Story/MonikaModDev/issues/new?labels=bug&body=Describe%20bug%20and%20steps%20for%20reproduction%20here&title=%5BBug%5D%20-%20).

Чтобы предложить идею, перейдите по [этой ссылке](https://github.com/Monika-After-Story/MonikaModDev/issues/new?labels=suggestion&body=Your%20suggestion%20goes%20here&title=%5BSuggestion%5D%20-%20)

### Другая помощь
Хотите помочь с MAS? Перейдите на [страницу issues](https://github.com/Monika-After-Story/MonikaModDev/issues) найти текущие баги или предложения, над которыми можно поработать.

Если у вас есть изменения, которые вы хотите внести, откройте [pull request](https://github.com/Monika-After-Story/MonikaModDev/pulls). Все изменения будут рассмотрены авторами и при необходимости доработаны/исправлены.

#### Добавление контента
Хотите добавить контент в MAS? Вот список важных .RPY-файлов, которые использует игра:

- **script-ch30.rpy**: Основной поток для MAS. Именно здесь происходит бездейтсвие.
- **script-topics.rpy**: Все **random** и **pool** темы, которые использует Моника. Вы можете добавить свои диалоги, проверив информацию ниже!
- **script-greetings.rpy**: Добавьте строки для приветствий Моники при загрузке игры.
- **script-farewells.rpy**: Добавьте строки, которые Моника говорит при закрытии игры.
- **script-moods.rpy**: Скажите Монике, что вы не _в настроении_.
- **script-stories.rpy**: Добавьте истории, которые рассказывает Моника.
- **script-compliments.rpy**: Добавьте комплименты, которые вы можете сказать Монике.
- **script-apologies.rpy**: Добавьте вещи, за которые можно извиниться.

Если вы хотите добавить больше диалогов в space room, перейдите в файл script-topics.rpy и используйте этот шаблон.

Пример нового блока диалога:
```renpy
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_example", # метка события (ДОЛЖНА БЫТЬ УНИКАЛЬНОЙ)
            category=["example", "topic"], # список категорий, к которым относится тема (они автоматически выделяются заглавными буквами)
            prompt="Example Topic", # текст кнопки
            random=True, # True, если тема должна появляться случайно
            pool=True # True, если тема должна появиться в разделе «Задать вопрос»
        )
    )

label monika_example:
    m 1a "Это пример темы."
    m 3d "Мне кажется, что на самом деле этому здесь не место..."
    m 2e "Зачем кто-то добавляет шаблон примера прямо в мод?"
    m 5r "Им правда не стоит больше вносить вклад в этот репозиторий."
    return
```
**Полные объяснения и детали всех возможных ключевых слов для Event смотрите в документации Event в файле `definitions.rpy`.**

Для более сложных вещей, чем простой диалог, обратитесь к документации Ren'Py, доступной в Интернете.

[Больше информации в руководстве по вкладу](https://github.com/Monika-After-Story/MonikaModDev/wiki/Contributing-Guidelines)

### Присоединяйтесь к обсуждению
Вы можете [подписаться на нас в Twitter](https://twitter.com/MonikaAfterMod), чтобы следить за обновлениями игры.

Если вы хотите найти ноты для фортепиано, спрайтпаки, сабмоды, внешний контент, переводы или просто обсудить MAS в целом - посетите [страницу обсуждений](https://github.com/Monika-After-Story/MonikaModDev/discussions)

Или, если вам ближе Discord и вы хотите постоянно получать наш любимый контент о Монике со всего интернета, а также если вас интересует участие в разработке этого мода, присоединяйтесь к нашему Discord-серверу:

 [![Discord](https://discordapp.com/api/guilds/372766620977725441/widget.png?style=banner1)](https://discord.gg/monika-after-story)

 Пожалуйста, обязательно следуйте нашему [Кодексу поведения](https://github.com/Monika-After-Story/MonikaModDev/wiki/Code-of-Conduct), который сводится к вежливости и уважению.

## Часто задаваемые вопросы

Полный FAQ доступен здесь: [Frequently Asked Questions](https://github.com/Monika-After-Story/MonikaModDev/wiki/FAQ)
Любые вопросы связанные с стилем кода: [Coding Style](https://github.com/Monika-After-Story/MonikaModDev/wiki/Coding-Style)
По тестированию багов [Testing Flow and Bug Testing](https://github.com/Monika-After-Story/MonikaModDev/wiki/Testing-Flow-and-Bug-Testing)
Устранение неполадок: [Troubleshooting](https://github.com/Monika-After-Story/MonikaModDev/wiki/Troubleshooting) Dialogue Coding: [Dialogue Coding](https://github.com/Monika-After-Story/MonikaModDev/wiki/Dialogue-Coding)
## Информация о лицензии

Мы стараемся максимально следовать рекомендациям Team Salvato's [по фан-работам](http://teamsalvato.com/ip-guidelines/). Все персонажи и оригинальный контент принадлежат Team Salvato. Монкиа: Эпилог - проект с открытым исходным кодом, и помимо именованных контрибьюторов, в этот мод входят вклады анонимных пользователей 4chan, откуда проект начинался. Подробнее на [странице лицензии](https://github.com/Monika-After-Story/MonikaModDev/wiki/License-and-Team-Salvato-Guidelines).

## Статус Сборки
### master: ![master](https://github.com/Monika-After-Story/MonikaModDev/workflows/CI/badge.svg?branch=master)
### content: ![content](https://github.com/Monika-After-Story/MonikaModDev/workflows/CI/badge.svg?branch=content)
### unstable: ![unstable](https://github.com/Monika-After-Story/MonikaModDev/workflows/CI/badge.svg?branch=unstable)
### alpha: ![alpha](https://github.com/Monika-After-Story/MonikaModDev/workflows/CI/badge.svg?branch=alpha)
