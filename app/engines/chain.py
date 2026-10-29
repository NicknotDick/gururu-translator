"""引擎降级链与并发调度。"""
from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Callable

from ..config import settings
from ..core.bus import bus
from .base import BaseEngine, EngineError, chunk_texts
from .mymemory import MyMemoryEngine
from .openai_compat import OpenAIEngine
from .passthrough import PassthroughEngine
from .tencent import TencentEngine


@dataclass
class TranslateResult:
    texts: list[str] = field(default_factory=list)
    engine: str = ""
    failed: list[int] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    cancelled: bool = False
    api_calls: int = 0

    @property
    def ok(self) -> bool:
        return not self.failed


def build_engines(preferred: str | None = None) -> list[BaseEngine]:
    """按配置组装降级链。preferred: auto|public|llm"""
    mode = preferred or str(settings.get("engine.active") or "public")
    chain: list[BaseEngine] = []

    llm_cfg = settings.get("engine.llm") or {}
    llm = OpenAIEngine(llm_cfg, settings.api_key)

    if mode == "llm":
        ok, _ = llm.available()
        if ok:
            chain.append(llm)
    pub = settings.get("engine.public") or {}
    for name in (pub.get("order") or ["tencent", "mymemory"]):
        if name == "tencent":
            chain.append(TencentEngine(pub.get("tencent") or {}))
        elif name == "mymemory":
            chain.append(MyMemoryEngine(pub.get("mymemory") or {}))
    if mode != "llm":
        ok, _ = llm.available()
        if ok and llm not in chain:
            chain.append(llm)
    chain.append(PassthroughEngine())
    return chain


class Translator:
    def __init__(self, preferred: str | None = None, concurrency: int | None = None) -> None:
        self.engines = build_engines(preferred)
        self.concurrency = max(1, int(concurrency or settings.get("engine.llm.concurrency") or 6))
        self.timeout = int(settings.get("engine.llm.timeout") or 120)

    # ---------- 单批 ----------
    def _one_batch(self, batch: list[tuple[int, str]], src: str, tgt: str,
                   style_id: str, used: set[str], lock: threading.Lock,
                   errors: list[str]) -> tuple[list[int], list[str]]:
        idxs = [i for i, _ in batch]
        texts = [t for _, t in batch]
        last_err = ""
        for eng in self.engines:
            for attempt in range(2):
                try:
                    out = eng.translate(texts, src, tgt, style_id, self.timeout)
                    if len(out) != len(texts):
                        raise EngineError(f"返回条数不符 {len(out)}/{len(texts)}")
                    with lock:
                        used.add(eng.id)
                    if eng.kind == "fallback":
                        return idxs, out
                    return idxs, out
                except Exception as exc:  # noqa: BLE001
                    last_err = f"{eng.id}: {exc}"
                    if attempt == 0:
                        time.sleep(1.0)
                    else:
                        break
        with lock:
            errors.append(last_err)
        return idxs, [""] * len(texts)

    # ---------- 全量 ----------
    def translate(self, texts: list[str], src: str, tgt: str, style_id: str = "general",
                  progress: Callable[[int, int], None] | None = None,
                  cancel: threading.Event | None = None) -> TranslateResult:
        total = len(texts)
        result = TranslateResult(texts=[""] * total)
        if total == 0:
            return result

        # 无需翻译的片段直接原样返回
        todo: list[tuple[int, str]] = []
        for i, t in enumerate(texts):
            if not (t or "").strip() or src == tgt:
                result.texts[i] = t or ""
            else:
                todo.append((i, t))
        if not todo:
            result.engine = "noop"
            return result

        mark = str(settings.get("engine.active") or "public")
        if mark == "llm":
            ok, msg = OpenAIEngine(settings.get("engine.llm") or {}, settings.api_key).available()
            if not ok:
                result.warnings.append(f"大模型不可用（{msg}），已回退公共引擎")

        batch_chars = int(settings.get("engine.llm.batch_chars") or 1800)
        batches = chunk_texts([t for _, t in todo], max_chars=batch_chars)
        index_map = [i for i, _ in todo]
        mapped: list[list[tuple[int, str]]] = [
            [(index_map[i], t) for i, t in b] for b in batches
        ]

        used: set[str] = set()
        lock = threading.Lock()
        errors: list[str] = []
        done = 0
        if progress:
            progress(0, total)

        with ThreadPoolExecutor(max_workers=min(self.concurrency, max(1, len(mapped)))) as pool:
            futures = {
                pool.submit(self._one_batch, b, src, tgt, style_id, used, lock, errors): b
                for b in mapped
            }
            for fut in as_completed(futures):
                if cancel is not None and cancel.is_set():
                    result.cancelled = True
                idxs, outs = fut.result()
                for i, t in zip(idxs, outs):
                    result.texts[i] = t
                done += len(idxs)
                if progress:
                    progress(min(done, total), total)

        for i in range(total):
            if (texts[i] or "").strip() and not (result.texts[i] or "").strip() and src != tgt:
                result.texts[i] = texts[i]
                result.failed.append(i)

        result.engine = ",".join(sorted(used)) or "none"
        result.api_calls = len(mapped)
        if errors:
            uniq = []
            for e in errors:
                if e not in uniq:
                    uniq.append(e)
            result.warnings.extend(uniq[:5])
            bus.log(f"部分批次翻译失败：{uniq[0]}", "warn")
        return result


def test_llm(cfg: dict | None = None, api_key: str | None = None) -> tuple[bool, str]:
    c = dict(cfg or settings.get("engine.llm") or {})
    key = api_key if api_key is not None else settings.api_key
    return OpenAIEngine(c, key).test()
