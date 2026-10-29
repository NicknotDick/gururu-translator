"""腾讯 TranSmart 免 Key 公共翻译（支持批量保序）。"""
from __future__ import annotations

from .base import BaseEngine, EngineError, http, lang_code


class TencentEngine(BaseEngine):
    id = "tencent"
    label = "腾讯翻译（免 Key）"
    kind = "public"

    def translate(self, texts, src, tgt, style_id="general", timeout=60):
        texts = list(texts)
        if not texts:
            return []
        sl, tl = lang_code(src, "tencent"), lang_code(tgt, "tencent")
        if src == tgt:
            return texts
        cfg = (self.cfg or {})
        url = cfg.get("url") or "https://transmart.qq.com/api/imt"
        payload = {
            "header": {
                "fn": "auto_translation",
                "client_key": cfg.get("client_key") or "browser-chrome-110.0.0",
            },
            "type": "plain",
            "model_category": "normal",
            "source": {"lang": sl, "text_list": texts},
            "target": {"lang": tl},
        }
        try:
            r = http().post(url, json=payload, timeout=timeout)
        except Exception as exc:  # noqa: BLE001
            raise EngineError(f"网络请求失败：{exc}") from exc
        if r.status_code != 200:
            raise EngineError(f"HTTP {r.status_code}")
        try:
            data = r.json()
        except Exception as exc:  # noqa: BLE001
            raise EngineError(f"响应不是合法 JSON：{r.text[:120]}") from exc
        out = data.get("auto_translation") or data.get("data") or data.get("target_list")
        if not isinstance(out, list) or len(out) != len(texts):
            head = data.get("header") or {}
            raise EngineError(f"返回结构异常：{str(head)[:160] or r.text[:160]}")
        return [str(x) if x is not None else "" for x in out]
