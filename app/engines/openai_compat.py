"""OpenAI 兼容接口引擎（DeepSeek / OpenAI / 通义 / 智谱 / Kimi / 自建端点）。"""
from __future__ import annotations

import json
import re

from ..core.style import style_prompt
from .base import BaseEngine, EngineError, http, lang_name_en

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)

SYSTEM_TMPL = (
    "You are a professional translator. Translate each item from {src} to {tgt}.\n"
    "Hard rules:\n"
    "1. Reply with ONLY a JSON object: {{\"t\": [\"...\", ...]}} containing exactly {n} strings, "
    "in the same order as the input items.\n"
    "2. Placeholders such as [[T0]], [[T1]] must be copied verbatim and kept in the correct position. "
    "Never translate, renumber or drop them.\n"
    "3. Do not translate: code, CLI flags, file paths, URLs, e-mail addresses, version numbers, "
    "pure numbers, or identifiers in backticks.\n"
    "4. Keep leading numbering/bullet prefixes (e.g. \"1.\", \"- \", \"（一）\") and trailing punctuation.\n"
    "5. Never merge, split, reorder, add or omit items. No explanations, no extra keys.\n"
    "6. Style: {style}"
)

REFINE_TMPL = (
    "You are a senior bilingual editor. Each item has \"src\" (the source text) and \"cur\" "
    "(the current translation from {src} to {tgt}). Revise every \"cur\" according to the "
    "editorial instruction below, while staying faithful to \"src\".\n"
    "Hard rules:\n"
    "1. Reply with ONLY a JSON object: {{\"t\": [\"...\", ...]}} containing exactly {n} strings, "
    "in the same order as the input items.\n"
    "2. Placeholders such as [[T0]], [[K0]] must be copied verbatim and kept in place. "
    "Never translate, renumber or drop them.\n"
    "3. Never alter code, file paths, URLs, e-mail addresses, version numbers, pure numbers, "
    "or identifiers in backticks.\n"
    "4. Preserve numbering/bullet prefixes and trailing punctuation.\n"
    "5. If the instruction conflicts with the original meaning, meaning wins.\n"
    "6. Do not merge, split, reorder, add or omit items. No explanations.\n"
    "7. Baseline style: {style}\n"
    "Editorial instruction: {instruction}"
)


def _endpoint(base_url: str) -> str:
    b = (base_url or "").strip().rstrip("/")
    if not b:
        raise EngineError("未填写接口地址")
    if b.endswith("/chat/completions"):
        return b
    return b + "/chat/completions"


def _extract_json(text: str) -> dict:
    s = _FENCE.sub("", (text or "").strip())
    try:
        return json.loads(s)
    except Exception:
        pass
    i, j = s.find("{"), s.rfind("}")
    if i >= 0 and j > i:
        try:
            return json.loads(s[i:j + 1])
        except Exception:
            pass
    raise EngineError(f"模型未返回合法 JSON：{(text or '')[:160]}")


class OpenAIEngine(BaseEngine):
    id = "llm"
    label = "大语言模型（OpenAI 兼容）"
    kind = "llm"

    def __init__(self, cfg: dict | None = None, api_key: str = "") -> None:
        super().__init__(cfg)
        self.api_key = api_key or ""

    def available(self) -> tuple[bool, str]:
        if not self.api_key:
            return False, "未配置 API Key"
        if not (self.cfg or {}).get("base_url"):
            return False, "未配置接口地址"
        return True, ""

    # ---------- 底层 ----------
    def _post(self, payload: dict, timeout: int) -> dict:
        url = _endpoint(str(self.cfg.get("base_url") or ""))
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            r = http().post(url, headers=headers, json=payload, timeout=timeout)
        except Exception as exc:  # noqa: BLE001
            raise EngineError(f"网络请求失败：{exc}") from exc
        if r.status_code == 401:
            raise EngineError("API Key 无效或已过期（401）")
        if r.status_code == 402:
            raise EngineError("账户余额不足（402）")
        if r.status_code == 429:
            raise EngineError("触发限流（429），请降低并发")
        if r.status_code >= 400:
            raise EngineError(f"HTTP {r.status_code}：{r.text[:180]}")
        try:
            return r.json()
        except Exception as exc:  # noqa: BLE001
            raise EngineError(f"响应不是合法 JSON：{r.text[:120]}") from exc

    def _chat(self, system: str, user_obj: dict, timeout: int) -> list[str]:
        payload = {
            "model": self.cfg.get("model") or "deepseek-chat",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(user_obj, ensure_ascii=False)},
            ],
            "temperature": float(self.cfg.get("temperature", 0.2)),
            "stream": False,
        }
        if self.cfg.get("json_mode", True):
            payload["response_format"] = {"type": "json_object"}
        try:
            data = self._post(payload, timeout)
        except EngineError as exc:
            if "response_format" in str(exc).lower() or "json_object" in str(exc).lower():
                payload.pop("response_format", None)
                data = self._post(payload, timeout)
            else:
                raise
        try:
            content = data["choices"][0]["message"]["content"]
        except Exception as exc:  # noqa: BLE001
            raise EngineError(f"响应缺少 choices：{str(data)[:160]}") from exc
        obj = _extract_json(content)
        arr = obj.get("t") or obj.get("translations") or obj.get("items")
        if not isinstance(arr, list):
            raise EngineError(f"响应缺少结果数组：{str(obj)[:160]}")
        return ["" if x is None else str(x) for x in arr]

    # ---------- 翻译 ----------
    def translate(self, texts, src, tgt, style_id="general", timeout=120):
        texts = list(texts)
        if not texts:
            return []
        if src == tgt:
            return texts
        n = len(texts)
        system = SYSTEM_TMPL.format(
            src=lang_name_en(src), tgt=lang_name_en(tgt), n=n, style=style_prompt(style_id)
        )
        arr = self._chat(system, {"items": texts}, timeout)
        if len(arr) != n:
            if n > 1:
                mid = n // 2
                return (self.translate(texts[:mid], src, tgt, style_id, timeout)
                        + self.translate(texts[mid:], src, tgt, style_id, timeout))
            raise EngineError(f"译文数量不匹配：期望 {n}，实际 {len(arr)}")
        return arr

    # ---------- 按指令改写 ----------
    def refine(self, items, src, tgt, instruction, style_id="general", timeout=120):
        items = list(items)
        if not items:
            return []
        n = len(items)
        system = REFINE_TMPL.format(
            src=lang_name_en(src), tgt=lang_name_en(tgt), n=n,
            style=style_prompt(style_id), instruction=instruction or "优化表达，保持原意",
        )
        arr = self._chat(system, {"items": items}, timeout)
        if len(arr) != n:
            if n > 1:
                mid = n // 2
                return (self.refine(items[:mid], src, tgt, instruction, style_id, timeout)
                        + self.refine(items[mid:], src, tgt, instruction, style_id, timeout))
            raise EngineError(f"改写结果数量不匹配：期望 {n}，实际 {len(arr)}")
        return arr

    def test(self) -> tuple[bool, str]:
        ok, msg = self.available()
        if not ok:
            return False, msg
        try:
            out = self.translate(["你好"], "zh", "en", "general", 20)
            return True, f"连接成功，样例输出：{out[0][:60]}"
        except EngineError as exc:
            return False, str(exc)
