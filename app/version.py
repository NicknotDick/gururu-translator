"""程序标识：作者与版本号。

版本号规则：Gurutu + YYMMDDHHMM（打包时刻），例如 Gurutu2610291845。
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

APP_NAME = "Gururu 翻译"
AUTHOR = "Gururu Nick"
BRAND = "Gurutu"

try:
    from ._stamp import STAMP as _STAMP  # type: ignore
except Exception:  # pragma: no cover
    _STAMP = ""


def _fallback_stamp() -> str:
    """开发模式未打戳时，用源码修改时间兜底，保证版本号始终是合法格式。"""
    try:
        mtime = Path(__file__).stat().st_mtime
        return datetime.fromtimestamp(mtime).strftime("%y%m%d%H%M")
    except Exception:
        return datetime.now().strftime("%y%m%d%H%M")


def build_stamp() -> str:
    s = (_STAMP or "").strip()
    return s if len(s) == 10 and s.isdigit() else _fallback_stamp()


def version() -> str:
    return f"{BRAND}{build_stamp()}"


def version_parts() -> dict[str, str]:
    """拆成可读片段，便于界面展示。"""
    s = build_stamp()
    return {
        "brand": BRAND,
        "stamp": s,
        "date": f"20{s[0:2]}-{s[2:4]}-{s[4:6]}",
        "time": f"{s[6:8]}:{s[8:10]}",
        "version": version(),
    }
