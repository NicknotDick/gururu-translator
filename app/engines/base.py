"""引擎公共设施：语言映射、分批、HTTP 会话。"""
from __future__ import annotations

import threading
from typing import Iterable

import requests

from ..config import settings

_session_lock = threading.Lock()
_session: requests.Session | None = None


class EngineError(RuntimeError):
    pass


def http() -> requests.Session:
    global _session
    with _session_lock:
        if _session is None:
            s = requests.Session()
            s.headers.update({
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
                ),
                "Accept": "*/*",
            })
            adapter = requests.adapters.HTTPAdapter(pool_connections=16, pool_maxsize=16, max_retries=0)
            s.mount("http://", adapter)
            s.mount("https://", adapter)
            _session = s
        return _session


_LANG_CACHE: dict[str, dict[str, dict]] = {}


def lang_table() -> dict[str, dict]:
    key = "v1"
    if key not in _LANG_CACHE:
        _LANG_CACHE[key] = {l["code"]: l for l in settings.languages()}
    return _LANG_CACHE[key]


def lang_code(code: str, field: str) -> str:
    return str(lang_table().get(code, {}).get(field) or code)


def lang_name_cn(code: str) -> str:
    return str(lang_table().get(code, {}).get("cn") or code)


def lang_name_en(code: str) -> str:
    return str(lang_table().get(code, {}).get("en") or code)


def is_cjk(code: str) -> bool:
    return bool(lang_table().get(code, {}).get("cjk"))


def chunk_texts(texts: list[str], max_chars: int = 1800, max_items: int = 40) -> list[list[tuple[int, str]]]:
    """按字符预算与条目上限切批，保持原顺序。"""
    batches: list[list[tuple[int, str]]] = []
    cur: list[tuple[int, str]] = []
    size = 0
    for idx, t in enumerate(texts):
        n = len(t or "")
        if cur and (size + n > max_chars or len(cur) >= max_items):
            batches.append(cur)
            cur = []
            size = 0
        cur.append((idx, t))
        size += n
    if cur:
        batches.append(cur)
    return batches


class BaseEngine:
    id = "base"
    label = "基础引擎"
    kind = "public"  # public | llm | fallback

    def __init__(self, cfg: dict | None = None) -> None:
        self.cfg = cfg or {}

    def available(self) -> tuple[bool, str]:
        return True, ""

    def translate(self, texts: Iterable[str], src: str, tgt: str,
                  style_id: str = "general", timeout: int = 60) -> list[str]:
        raise NotImplementedError

    def __repr__(self) -> str:  # pragma: no cover
        return f"<{self.__class__.__name__} {self.id}>"
