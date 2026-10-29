"""MyMemory 免 Key 兜底引擎（单条请求，频率受限）。"""
from __future__ import annotations

import time

from .base import BaseEngine, EngineError, http, lang_code


class MyMemoryEngine(BaseEngine):
    id = "mymemory"
    label = "MyMemory（免 Key 兜底）"
    kind = "public"

    def translate(self, texts, src, tgt, style_id="general", timeout=45):
        texts = list(texts)
        if not texts:
            return []
        if src == tgt:
            return texts
        cfg = self.cfg or {}
        url = cfg.get("url") or "https://api.mymemory.translated.net/get"
        pair = f"{lang_code(src, 'mymemory')}|{lang_code(tgt, 'mymemory')}"
        out: list[str] = []
        for t in texts:
            if not (t or "").strip():
                out.append(t or "")
                continue
            if len(t) > 480:
                raise EngineError("单条超出 MyMemory 长度限制")
            params = {"q": t, "langpair": pair}
            if cfg.get("email"):
                params["de"] = cfg["email"]
            try:
                r = http().get(url, params=params, timeout=timeout)
                data = r.json()
            except Exception as exc:  # noqa: BLE001
                raise EngineError(f"请求失败：{exc}") from exc
            tr = (data.get("responseData") or {}).get("translatedText")
            if not tr:
                raise EngineError(f"无译文：{str(data)[:120]}")
            out.append(str(tr))
            time.sleep(0.12)
        return out
