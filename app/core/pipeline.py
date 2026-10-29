"""翻译管线：解析 → 术语遮蔽 → 记忆命中 → 分批翻译 → 校验 → 写回。"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from ..config import settings
from ..engines.chain import Translator
from ..engines.base import chunk_texts, is_cjk
from ..parsers.registry import parser_for
from .bus import bus
from .i18n import tr
from .ir import (STATUS_DONE, STATUS_FAILED, STATUS_OVERFLOW, STATUS_REFINED,
                 STATUS_TERM, DocumentIR, Segment)
from .terms import Glossary, build_glossary, termbook
from .tm import make_key, tm


@dataclass
class TransOptions:
    src: str = "zh"
    tgt: str = "en"
    style: str = "general"
    term_sets: list[str] = field(default_factory=list)
    mode: str = "target_only"
    engine: str = "auto"
    skip_header_footer: bool = False

    @classmethod
    def from_settings(cls, patch: dict | None = None) -> "TransOptions":
        o = cls(
            src=str(settings.get("translate.src") or "zh"),
            tgt=str(settings.get("translate.tgt") or "en"),
            style=str(settings.get("translate.style") or "general"),
            term_sets=list(settings.get("translate.term_sets") or []),
            mode=str(settings.get("translate.mode") or "target_only"),
            engine=str(settings.get("engine.active") or "auto"),
            skip_header_footer=bool(settings.get("doc.skip_header_footer")),
        )
        for k, v in (patch or {}).items():
            if hasattr(o, k) and v is not None:
                setattr(o, k, v)
        return o


@dataclass
class FileResult:
    path: str
    output: str = ""
    ok: bool = True
    error: str = ""
    segments: int = 0
    translated: int = 0
    cached: int = 0
    failed: int = 0
    warnings: list[str] = field(default_factory=list)
    overflow: list[str] = field(default_factory=list)
    engine: str = ""
    elapsed: float = 0.0
    ir: DocumentIR | None = None


def output_path_for(src: str, out_dir: str | Path, suffix: str) -> Path:
    p = Path(src)
    return Path(out_dir) / f"{p.stem}{suffix}{p.suffix}"


def summarize_ir(ir: DocumentIR) -> dict:
    return {
        "segments": len(ir.segments),
        "chars": sum(len(s.src) for s in ir.segments),
        "warnings": ir.warnings,
    }


def translate_document(
    path: str,
    opts: TransOptions | None = None,
    out_path: str | Path | None = None,
    progress: Callable[[float, str], None] | None = None,
    cancel: threading.Event | None = None,
    write: bool = True,
) -> FileResult:
    opts = opts or TransOptions.from_settings()
    started = time.time()
    result = FileResult(path=path)

    def tick(pct: float, msg: str = "") -> None:
        if progress:
            progress(max(0.0, min(1.0, pct)), msg)

    tick(0.02, tr("解析文件", "Parsing"))
    try:
        parser = parser_for(path)
    except ValueError as exc:
        result.ok = False
        result.error = str(exc)
        return result

    try:
        ir = parser.load(path, {"skip_header_footer": opts.skip_header_footer,
                                "skip_code": bool(settings.get("doc.skip_code"))})
    except Exception as exc:  # noqa: BLE001
        result.ok = False
        result.error = f"{type(exc).__name__}: {exc}"
        return result

    result.ir = ir
    result.warnings.extend(ir.warnings)
    result.segments = len(ir.segments)
    if not ir.segments:
        result.ok = False
        result.error = tr("未找到可翻译的文字内容", "No translatable text found")
        return result

    tick(0.08, tr(f"共 {len(ir.segments)} 段待翻译",
                  f"{len(ir.segments)} segments to translate"))

    glossary: Glossary = build_glossary(termbook, opts.src, opts.tgt, opts.term_sets)
    term_ver = glossary.version()
    pad_terms = not is_cjk(opts.tgt)

    send_texts: list[str] = []
    tokens: list[list[tuple[str, str]]] = []
    keys: list[str] = []
    for seg in ir.segments:
        masked, toks = glossary.mask(seg.engine_text) if not glossary.empty else (seg.engine_text, [])
        send_texts.append(masked)
        tokens.append(toks)
        keys.append(make_key(masked, opts.src, opts.tgt, opts.style, term_ver, opts.engine))

    # 翻译记忆
    cached: dict[str, str] = {}
    if settings.get("tm.enabled"):
        try:
            cached = tm.get_many(keys)
        except Exception:
            cached = {}

    pending_idx = [i for i, k in enumerate(keys) if k not in cached]
    result.cached = len(ir.segments) - len(pending_idx)

    for i, key in enumerate(keys):
        if key in cached:
            ir.segments[i].tgt = _restore_terms(cached[key], tokens[i], pad_terms)
            ir.segments[i].status = STATUS_DONE

    if pending_idx and cancel is not None and cancel.is_set():
        result.ok = False
        result.error = tr("已取消", "Cancelled")
        return result

    translator = Translator(opts.engine if opts.engine in ("public", "llm") else None)
    result.engine = ",".join(e.id for e in translator.engines if e.kind != "fallback")

    if pending_idx:
        texts = [send_texts[i] for i in pending_idx]

        def on_prog(done: int, total: int) -> None:
            base = 0.12
            tick(base + 0.72 * (done / max(1, total)),
                 tr(f"翻译中 {done}/{total}", f"Translating {done}/{total}"))

        res = translator.translate(
            texts, opts.src, opts.tgt, opts.style, progress=on_prog, cancel=cancel
        )
        result.warnings.extend(res.warnings)
        failed_local = set(res.failed)
        for local_i, out in enumerate(res.texts):
            gi = pending_idx[local_i]
            seg = ir.segments[gi]
            if local_i in failed_local or not (out or "").strip():
                seg.status = STATUS_FAILED
                seg.tgt = seg.src
                continue
            restored = _restore_terms(out, tokens[gi], pad_terms)
            seg.tgt = restored
            seg.status = STATUS_DONE
        # 回填缓存
        if settings.get("tm.enabled"):
            rows = []
            min_len = int(settings.get("tm.min_len") or 4)
            for local_i, out in enumerate(res.texts):
                gi = pending_idx[local_i]
                if ir.segments[gi].status == STATUS_DONE and len(send_texts[gi]) >= min_len:
                    rows.append((keys[gi], send_texts[gi], out, result.engine, opts.style))
            try:
                tm.put_many(rows)
            except Exception:
                pass
        if res.cancelled:
            result.warnings.append(tr("任务已取消，部分段落未翻译",
                                      "Cancelled — some segments were not translated"))

    # 术语校验
    if not glossary.empty:
        for i, seg in enumerate(ir.segments):
            if seg.status != STATUS_DONE:
                continue
            for _ph, tgt_term in tokens[i]:
                if tgt_term and tgt_term not in seg.tgt:
                    seg.status = STATUS_TERM
                    seg.note = f"术语未锁定：{tgt_term}"
                    break

    result.translated = sum(1 for s in ir.segments if s.status in (STATUS_DONE, STATUS_TERM))
    result.failed = sum(1 for s in ir.segments if s.status == STATUS_FAILED)

    if not write:
        result.elapsed = time.time() - started
        tick(1.0, tr("完成", "Done"))
        return result

    tick(0.9, tr("写回文件", "Writing output"))
    target = Path(out_path) if out_path else output_path_for(
        path, settings.output_dir(), str(settings.get("output.suffix") or "_译文")
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        info = parser.run_write(ir, str(target), opts.mode)
    except Exception as exc:  # noqa: BLE001
        result.ok = False
        result.error = tr("写回失败：", "Write failed: ") + f"{type(exc).__name__}: {exc}"
        return result

    result.output = str(target)
    result.overflow.extend(info.get("overflow") or [])
    result.warnings.extend(info.get("warnings") or [])
    if result.overflow:
        for seg in ir.segments:
            if seg.status == STATUS_DONE and len(seg.tgt) > 800:
                seg.status = STATUS_OVERFLOW
    result.elapsed = time.time() - started
    tick(1.0, "完成")
    return result


def _restore_terms(text: str, toks: list[tuple[str, str]], pad: bool = False) -> str:
    if not toks:
        return text
    return Glossary.unmask(text, toks, pad=pad)


def retranslate_segments(ir: DocumentIR, segs: list[Segment], opts: TransOptions,
                         cancel: threading.Event | None = None) -> None:
    """预览界面的局部重译。"""
    glossary = build_glossary(termbook, opts.src, opts.tgt, opts.term_sets)
    pad_terms = not is_cjk(opts.tgt)
    send: list[str] = []
    toks: list[list[tuple[str, str]]] = []
    for seg in segs:
        m, t = glossary.mask(seg.src) if not glossary.empty else (seg.src, [])
        send.append(m)
        toks.append(t)
    translator = Translator(opts.engine if opts.engine in ("public", "llm") else None)
    res = translator.translate(send, opts.src, opts.tgt, opts.style, cancel=cancel)
    for i, seg in enumerate(segs):
        out = res.texts[i] if i < len(res.texts) else ""
        if not (out or "").strip():
            seg.status = STATUS_FAILED
            continue
        seg.tgt = _restore_terms(out, toks[i], pad_terms)
        seg.status = STATUS_DONE
        for _ph, term in toks[i]:
            if term and term not in seg.tgt:
                seg.status = STATUS_TERM
                seg.note = f"术语未锁定：{term}"
                break
    bus.emit("preview_updated", sids=[s.sid for s in segs])


def estimate_batches(texts: list[str], budget: int | None = None) -> int:
    return len(chunk_texts(texts, max_chars=int(budget or settings.get("engine.llm.batch_chars") or 1800)))


def refine_segments(ir: DocumentIR, segs: list[Segment], instruction: str,
                    opts: TransOptions, cancel: threading.Event | None = None,
                    progress: Callable[[int, int], None] | None = None) -> int:
    """调用大模型按自然语言指令改写译文（预览界面的「AI 调整」）。"""
    from concurrent.futures import ThreadPoolExecutor

    from ..engines.openai_compat import OpenAIEngine

    eng = OpenAIEngine(settings.get("engine.llm") or {}, settings.api_key)
    ok, msg = eng.available()
    if not ok:
        raise RuntimeError(tr(
            f"未配置大模型：{msg}。请到「设置 → 大语言模型」填写 API Key",
            f"LLM unavailable: {msg}. Configure an API key under Settings → Large language model.",
        ))

    todo = [s for s in segs if (s.tgt or "").strip()]
    if not todo:
        return 0

    instruction = (instruction or "").strip() or "优化表达，使其更自然、更符合目标语言习惯"
    budget = int(settings.get("engine.llm.batch_chars") or 1800)
    concurrency = max(1, min(6, int(settings.get("engine.llm.concurrency") or 6)))
    timeout = int(settings.get("engine.llm.timeout") or 120)

    batches = chunk_texts([s.src for s in todo], max_chars=budget, max_items=20)
    changed = 0
    done = 0
    lock = threading.Lock()

    def _run(batch: list[tuple[int, str]]) -> None:
        nonlocal changed, done
        if cancel is not None and cancel.is_set():
            return
        items = [{"src": src, "cur": todo[i].tgt or todo[i].src} for i, src in batch]
        try:
            outs = eng.refine(items, opts.src, opts.tgt, instruction, opts.style, timeout)
        except Exception as exc:  # noqa: BLE001
            bus.log(f"AI 调整失败：{exc}", "warn")
            with lock:
                done += len(batch)
                if progress:
                    progress(min(done, len(todo)), len(todo))
            return
        for (i, _src), out in zip(batch, outs):
            seg = todo[i]
            text = (out or "").strip()
            if not text or text == (seg.tgt or "").strip():
                continue
            seg.tgt = text
            if seg.status not in (STATUS_TERM,):
                seg.status = STATUS_REFINED
            seg.note = "AI 调整"
            with lock:
                changed += 1
        with lock:
            done += len(batch)
            if progress:
                progress(min(done, len(todo)), len(todo))

    with ThreadPoolExecutor(max_workers=min(concurrency, max(1, len(batches)))) as pool:
        list(pool.map(_run, batches))

    bus.emit("preview_updated", sids=[s.sid for s in segs])
    return changed
