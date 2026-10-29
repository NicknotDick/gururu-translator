"""兜底引擎：所有通道都失败时原文返回，保证流程不中断。"""
from __future__ import annotations

from .base import BaseEngine


class PassthroughEngine(BaseEngine):
    id = "passthrough"
    label = "原文回退（失败兜底）"
    kind = "fallback"

    def translate(self, texts, src, tgt, style_id="general", timeout=10):
        return list(texts)
