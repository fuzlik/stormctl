# stormctl

TeamStorm from the terminal. Every workspace, not just one.

Клиент публичного API TeamStorm. Ищет задачи по всем пространствам, открывает карточку по ключу и ставит сроки. Сторонних библиотек нет.

```
$ python3 -m ts find launch
пространство    APP     Product
папка   APP     3f1c...    Launch
задача  APP     APP-14  Ivan Petrov   Launch   Release checklist
всего 3

$ python3 -m ts show APP-14
APP APP-14 Release checklist
тип: Task | статус: Open
кто: Ivan Petrov
папка: Launch
срок: 02.11 – 06.11
```

## Setup

Python 3.9+. Скопируй файл окружения и впиши свой хост и токен:

```bash
cp .env.example .env
```

```
TEAMSTORM_API_URL=https://your-teamstorm-host
TEAMSTORM_API_TOKEN=your-private-token
```

Токен — PrivateToken из профиля TeamStorm. В адресе только хост, без `/cwm/public/api/v1`.

## Commands

Запуск из этой папки:

```bash
python3 -m ts workspaces
python3 -m ts find text
python3 -m ts find --assignee ivan
python3 -m ts users ivan
python3 -m ts folders KEY
python3 -m ts tasks KEY <folder-id>
python3 -m ts show KEY-1
python3 -m ts due KEY-1 2026-11-02 2026-11-06
```

Ключ задачи уже содержит пространство: `KEY-1` — пространство `KEY`, задача `1`.

Сырой вызов API:

```bash
python3 -m ts GET /workspaces
python3 -m ts PATCH /workspaces/KEY/workitems/KEY-1 '{"name":"New name"}'
```

## Privacy

Клиент не сохраняет задачи, пространства и тексты карточек. Хост и токен лежат в `.env` на твоей машине. Этого файла в репозитории нет.

## License

[MIT](LICENSE)
