"""后端文案的极简双语支持。

界面语言存在 settings.ui.lang；后端只翻译会直接出现在界面上的少数文案，
其余技术信息（HTTP 状态、库异常原文）保持原文，便于排查。
"""
from __future__ import annotations

from ..config import settings


def ui_lang() -> str:
    try:
        return "en" if str(settings.get("ui.lang") or "zh") == "en" else "zh"
    except Exception:
        return "zh"


def tr(zh: str, en: str) -> str:
    return en if ui_lang() == "en" else zh
