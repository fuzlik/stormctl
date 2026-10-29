"""Команды TeamStorm. Пространство берётся из ключа задачи: KEY-1."""

from __future__ import annotations

import json
import sys
import urllib.parse

from ts.client import call, day, get_all, must, plain, safe_all

HELP = """
Клиент TeamStorm. Хост и PrivateToken берёт из .env в корне проекта.

Сырой запрос:
  python3 -m ts GET /workspaces
  python3 -m ts PATCH /workspaces/KEY/workitems/KEY-1 '{"name":"..."}'

Команды:
  python3 -m ts workspaces
  python3 -m ts users ivan
  python3 -m ts find текст
  python3 -m ts find --assignee ivan
  python3 -m ts folders KEY
  python3 -m ts folders KEY --parent <id папки>
  python3 -m ts tasks KEY <папка или ключ родителя>
  python3 -m ts show KEY-1
  python3 -m ts due KEY-1 2026-11-02 2026-11-06
""".strip()

METHODS = {"GET", "POST", "PATCH", "PUT", "DELETE"}


def flag(args: list[str], name: str) -> str | None:
    if name not in args:
        return None
    i = args.index(name)
    if i + 1 >= len(args):
        sys.exit(f"после {name} нужно значение")
    return args[i + 1]


def positionals(args: list[str]) -> list[str]:
    skip = False
    out: list[str] = []
    flags = {"--assignee", "--parent", "--name"}
    for arg in args:
        if skip:
            skip = False
            continue
        if arg in flags:
            skip = True
            continue
        out.append(arg)
    return out


def workspace_of(key: str) -> tuple[str, str]:
    left, sep, right = key.rpartition("-")
    if sep and right.isdigit():
        return left, key
    sys.exit(f"не вижу пространство в ключе {key}. Пример: KEY-1")


def cmd_workspaces() -> None:
    for it in get_all("/workspaces?maxItemsCount=200"):
        print(f"{it.get('key')}\t{it.get('name')}")


def cmd_folders(ws: str, args: list[str]) -> None:
    parent = flag(args, "--parent")
    name = flag(args, "--name")
    query = ["maxItemsCount=200"]
    if parent:
        query.append("parentId=" + urllib.parse.quote(parent))
    if name:
        query.append("name=" + urllib.parse.quote(name))
    items = get_all(f"/workspaces/{ws}/folders?{'&'.join(query)}")
    if not items:
        print("пусто")
        return
    for it in items:
        print(f"{it.get('id')}\t{it.get('name')}")


def cmd_tasks(ws: str, parent: str, args: list[str]) -> None:
    assignee = (flag(args, "--assignee") or "").lower()
    items = get_all(f"/workspaces/{ws}/workitems/by-parent/{parent}?withSubItems=true")
    by_id = {it.get("id"): it for it in items}
    rows = []
    for it in items:
        person = it.get("assignee") or {}
        who = f"{person.get('displayName') or ''} {person.get('username') or ''}".lower()
        if assignee and assignee not in who:
            continue
        rows.append(it)
    rows.sort(key=lambda it: (it.get("startDate") or "", it.get("key") or ""))
    print(f"{len(rows)}")
    for it in rows:
        parent_item = by_id.get((it.get("parent") or {}).get("id"))
        parent_name = (parent_item or {}).get("name") or (it.get("folder") or {}).get("name") or ""
        person = (it.get("assignee") or {}).get("displayName") or "—"
        status = (it.get("status") or {}).get("name") or ""
        print(
            f"{it.get('key')}\t{day(it.get('startDate'))}–{day(it.get('dueDate'))}\t"
            f"{status}\t{person}\t{parent_name}\t{it.get('name')}"
        )


def cmd_users(query: str) -> None:
    items = safe_all("/users?displayName=" + urllib.parse.quote(query) + "&maxItemsCount=100") or []
    if not items:
        items = safe_all("/users?username=" + urllib.parse.quote(query) + "&maxItemsCount=100") or []
    if not items:
        print("пусто")
        return
    for it in items:
        print(f"{it.get('username')}\t{it.get('displayName')}")


def cmd_find(args: list[str]) -> None:
    words = positionals(args)
    query = " ".join(words).strip()
    assignee = flag(args, "--assignee")
    if not query and not assignee:
        sys.exit("нужна строка поиска или --assignee")
    needle = query.lower()
    spaces = get_all("/workspaces?maxItemsCount=200")
    hits = 0
    for space in spaces:
        key = space.get("key") or ""
        name = space.get("name") or ""
        if needle and (needle in key.lower() or needle in name.lower()):
            print(f"пространство\t{key}\t{name}")
            hits += 1
        if needle:
            folders = safe_all(
                f"/workspaces/{key}/folders?name={urllib.parse.quote(query)}&maxItemsCount=100"
            ) or []
            for folder in folders:
                print(f"папка\t{key}\t{folder.get('id')}\t{folder.get('name')}")
                hits += 1
        q = ["maxItemsCount=100"]
        if query:
            q.append("name=" + urllib.parse.quote(query))
        if assignee:
            q.append("assignee=" + urllib.parse.quote(assignee))
        tasks = safe_all(f"/workspaces/{key}/workitems?{'&'.join(q)}") or []
        for task in tasks:
            person = (task.get("assignee") or {}).get("displayName") or "—"
            folder = (task.get("folder") or {}).get("name") or ""
            print(f"задача\t{key}\t{task.get('key')}\t{person}\t{folder}\t{task.get('name')}")
            hits += 1
    print(f"всего {hits}")


def cmd_show(ws: str, key: str) -> None:
    it = must("GET", f"/workspaces/{ws}/workitems/{key}")
    if not isinstance(it, dict):
        sys.exit(str(it))
    person = (it.get("assignee") or {}).get("displayName") or "—"
    print(ws, it.get("key"), it.get("name"))
    print("тип:", (it.get("type") or {}).get("name"), "| статус:", (it.get("status") or {}).get("name"))
    print("кто:", person)
    print("папка:", (it.get("folder") or {}).get("name"))
    print("срок:", day(it.get("startDate")), "–", day(it.get("dueDate")))
    text = plain(it.get("description"))
    if text:
        print()
        print(text)


def cmd_due(ws: str, key: str, start: str, end: str) -> None:
    data = must(
        "PATCH",
        f"/workspaces/{ws}/workitems/{key}",
        {
            "startDate": f"{start}T00:00:00+03:00",
            "dueDate": f"{end}T23:59:59+03:00",
        },
    )
    if isinstance(data, dict):
        print(data.get("key"), day(data.get("startDate")), "–", day(data.get("dueDate")), data.get("name"))


def raw(method: str, path: str, body: str | None) -> None:
    payload = json.loads(body) if body else None
    status, data = call(method, path, payload)
    print(f"HTTP {status}")
    if data is None:
        sys.exit(0 if status < 400 else 1)
    if isinstance(data, str):
        print(data)
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    if status >= 400:
        sys.exit(1)


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(HELP)
        sys.exit(0 if args else 2)
    cmd = args[0]
    if cmd.upper() in METHODS:
        if len(args) < 2:
            sys.exit("нужен путь, например GET /workspaces")
        raw(cmd.upper(), args[1], args[2] if len(args) > 2 else None)
        return
    if cmd == "workspaces":
        cmd_workspaces()
    elif cmd == "users" and len(args) >= 2:
        cmd_users(" ".join(args[1:]))
    elif cmd == "find":
        cmd_find(args[1:])
    elif cmd == "folders" and len(args) >= 2:
        cmd_folders(args[1], args[2:])
    elif cmd == "tasks" and len(args) >= 3:
        cmd_tasks(args[1], args[2], args[3:])
    elif cmd == "show" and len(args) == 2:
        cmd_show(*workspace_of(args[1]))
    elif cmd == "show" and len(args) >= 3:
        cmd_show(args[1], args[2])
    elif cmd == "due" and len(args) == 4:
        ws, key = workspace_of(args[1])
        cmd_due(ws, key, args[2], args[3])
    elif cmd == "due" and len(args) >= 5:
        cmd_due(args[1], args[2], args[3], args[4])
    else:
        print(HELP)
        sys.exit(2)
