from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

API_PREFIX = "/cwm/public/api/v1"
ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
MSK = timezone(timedelta(hours=3))


def load_env(path: Path = ENV_PATH) -> dict[str, str]:
    if not path.exists():
        sys.exit(f"нет файла {path}")
    env: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def api_url(host: str, path: str) -> str:
    host = host.rstrip("/")
    if path.startswith("http://") or path.startswith("https://"):
        return path
    if not path.startswith("/"):
        path = "/" + path
    if path.startswith(API_PREFIX):
        return host + path
    return host + API_PREFIX + path


def credentials() -> tuple[str, str]:
    env = load_env()
    host = env.get("TEAMSTORM_API_URL")
    token = env.get("TEAMSTORM_API_TOKEN")
    if not host or not token:
        sys.exit("в .env нужны TEAMSTORM_API_URL и TEAMSTORM_API_TOKEN")
    return host, token


def call(method: str, path: str, body: dict | None = None) -> tuple[int, object]:
    host, token = credentials()
    data = None
    headers = {
        "Authorization": f"PrivateToken {token}",
        "Accept": "application/json",
    }
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        api_url(host, path),
        data=data,
        headers=headers,
        method=method.upper(),
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            status = resp.status
    except urllib.error.HTTPError as err:
        raw = err.read()
        status = err.code
    except urllib.error.URLError as err:
        sys.exit(f"сеть: {err.reason}")
    text = raw.decode("utf-8", errors="replace")
    if not text:
        return status, None
    try:
        return status, json.loads(text)
    except json.JSONDecodeError:
        return status, text


def must(method: str, path: str, body: dict | None = None) -> object:
    status, data = call(method, path, body)
    if status >= 400:
        print(f"HTTP {status}")
        print(data if isinstance(data, str) else json.dumps(data, ensure_ascii=False, indent=2))
        sys.exit(1)
    return data


def get_all(path: str) -> list:
    items: list = []
    token = None
    while True:
        url = path
        if token:
            url += ("&" if "?" in path else "?") + "fromToken=" + urllib.parse.quote(str(token))
        data = must("GET", url)
        if isinstance(data, list):
            return data
        if not isinstance(data, dict):
            sys.exit(f"непонятный ответ: {data}")
        items.extend(data.get("items") or [])
        token = data.get("nextToken")
        if not token:
            return items


def safe_all(path: str, limit: int = 300) -> list | None:
    items: list = []
    token = None
    while len(items) < limit:
        url = path
        if token:
            url += ("&" if "?" in path else "?") + "fromToken=" + urllib.parse.quote(str(token))
        status, data = call("GET", url)
        if status >= 400 or not isinstance(data, (dict, list)):
            return None if not items else items
        if isinstance(data, list):
            return data[:limit]
        items.extend(data.get("items") or [])
        token = data.get("nextToken")
        if not token:
            break
    return items


def day(value: str | None) -> str:
    if not value:
        return "—"
    dt = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(MSK)
    return dt.strftime("%d.%m")


def plain(html: str | None) -> str:
    text = re.sub(r"<br\s*/?>", "\n", html or "", flags=re.I)
    text = re.sub(r"</p>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()
