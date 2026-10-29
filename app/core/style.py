"""翻译风格模板。"""
from __future__ import annotations

from ..config import settings

_FALLBACK = {
    "id": "general",
    "name": "标准通用",
    "desc": "忠实、通顺、中性",
    "prompt": "Use clear, faithful, neutral modern prose.",
}


def all_styles() -> list[dict]:
    styles = settings.styles()
    return styles or [_FALLBACK]


def get_style(style_id: str) -> dict:
    for s in all_styles():
        if s.get("id") == style_id:
            return s
    return all_styles()[0]


def style_prompt(style_id: str) -> str:
    return str(get_style(style_id).get("prompt") or "")


def style_name(style_id: str) -> str:
    return str(get_style(style_id).get("name") or style_id)
