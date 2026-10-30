"""批量任务队列：逐文件处理、进度上报、可取消、结果留驻供预览编辑。"""
from __future__ import annotations

import threading
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path

from ..config import settings
from ..parsers.registry import LEGACY_MAP, SUPPORTED_EXTS, is_supported
from .bus import bus
from .i18n import tr
from .ir import STATUS_EDITED, DocumentIR
from .pipeline import (TransOptions, output_path_for, refine_segments,
                       retranslate_segments, translate_document,
                       translate_filename)

MAX_IRS = 5


@dataclass
class Job:
    id: str
    path: str
    name: str
    ext: str
    size: int
    status: str = "queued"
    percent: float = 0.0
    message: str = ""
    output: str = ""
    segments: int = 0
    translated: int = 0
    failed: int = 0
    warnings: list[str] = field(default_factory=list)
    error: str = ""
    elapsed: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "path": self.path,
            "name": self.name,
            "ext": self.ext,
            "size": self.size,
            "status": self.status,
            "percent": round(self.percent * 100, 1),
            "message": self.message,
            "output": self.output,
            "segments": self.segments,
            "translated": self.translated,
            "failed": self.failed,
            "warnings": self.warnings[:6],
            "error": self.error,
            "elapsed": round(self.elapsed, 1),
        }


class JobManager:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._jobs: OrderedDict[str, Job] = OrderedDict()
        self._irs: OrderedDict[str, tuple[DocumentIR, object]] = OrderedDict()
        self._cancel = threading.Event()
        self._thread: threading.Thread | None = None
        self._running = False

    # ---------- 队列维护 ----------
    def add_paths(self, paths: list[str], recursive: bool = True) -> tuple[int, list[str]]:
        added = 0
        skipped: list[str] = []
        with self._lock:
            for raw in paths:
                p = Path(raw)
                if p.is_dir():
                    pattern = "**/*" if recursive else "*"
                    for f in sorted(p.glob(pattern)):
                        if f.is_file() and is_supported(str(f)):
                            if self._append(f):
                                added += 1
                    continue
                if not p.exists():
                    skipped.append(f"{p.name}（文件不存在）")
                    continue
                if not is_supported(str(p)):
                    hint = LEGACY_MAP.get(Path(p).suffix.lower())
                    skipped.append(f"{p.name}：{hint}" if hint else f"{p.name}（格式不支持）")
                    continue
                if self._append(p):
                    added += 1
        if added:
            bus.emit("queue", jobs=[j.to_dict() for j in self.list()])
        return added, skipped

    def _append(self, p: Path) -> bool:
        for j in self._jobs.values():
            if j.path.lower() == str(p).lower():
                return False
        jid = uuid.uuid4().hex[:10]
        self._jobs[jid] = Job(
            id=jid, path=str(p), name=p.name, ext=p.suffix.lower().lstrip("."),
            size=p.stat().st_size if p.exists() else 0,
        )
        return True

    def remove(self, jid: str) -> None:
        with self._lock:
            self._jobs.pop(jid, None)
            self._irs.pop(jid, None)
        bus.emit("queue", jobs=[j.to_dict() for j in self.list()])

    def clear_finished(self) -> None:
        with self._lock:
            for jid in [j.id for j in self._jobs.values() if j.status in ("done", "failed", "cancelled")]:
                self._jobs.pop(jid, None)
                self._irs.pop(jid, None)
        bus.emit("queue", jobs=[j.to_dict() for j in self.list()])

    def list(self) -> list[Job]:
        with self._lock:
            return list(self._jobs.values())

    def get(self, jid: str) -> Job | None:
        with self._lock:
            return self._jobs.get(jid)

    # ---------- 运行 ----------
    @property
    def running(self) -> bool:
        return self._running

    def start(self, patch: dict | None = None) -> dict:
        with self._lock:
            if self._running:
                return {"ok": False, "error": tr("已有任务在运行", "A job is already running")}
            pending = [j for j in self._jobs.values() if j.status in ("queued", "failed", "cancelled")]
            if not pending:
                return {"ok": False, "error": tr("队列中没有待处理文件", "Nothing queued")}
            for j in pending:
                j.status = "queued"
                j.percent = 0.0
                j.message = tr("等待中", "Waiting")
                j.error = ""
            self._cancel.clear()
            self._running = True
        opts = TransOptions.from_settings(patch)
        self._thread = threading.Thread(target=self._worker, args=(opts,), daemon=True)
        self._thread.start()
        return {"ok": True, "count": len(pending)}

    def cancel(self) -> None:
        self._cancel.set()
        bus.log("正在取消…", "warn")

    def _worker(self, opts: TransOptions) -> None:
        try:
            while True:
                with self._lock:
                    nxt = next((j for j in self._jobs.values() if j.status == "queued"), None)
                if nxt is None:
                    break
                if self._cancel.is_set():
                    with self._lock:
                        for j in self._jobs.values():
                            if j.status == "queued":
                                j.status = "cancelled"
                                j.message = tr("已取消", "Cancelled")
                    bus.emit("queue", jobs=[j.to_dict() for j in self.list()])
                    break
                self._run_one(nxt, opts)
        finally:
            self._running = False
            bus.emit("queue", jobs=[j.to_dict() for j in self.list()], finished=True)
            bus.log("队列处理结束", "info")

    def _run_one(self, job: Job, opts: TransOptions) -> None:
        job.status = "running"
        job.message = tr("解析文件", "Parsing")
        bus.emit("job", job=job.to_dict())

        def on_prog(pct: float, msg: str) -> None:
            job.percent = pct
            job.message = msg or job.message
            bus.emit("progress", id=job.id, percent=round(pct * 100, 1), message=job.message)

        stem = None
        if settings.get("output.translate_name"):
            stem, warn = translate_filename(Path(job.path).stem, opts)
            if warn:
                job.warnings = list(job.warnings or []) + [warn]
        out = output_path_for(job.path, settings.output_dir(),
                              str(settings.get("output.suffix") or "_译文"), stem=stem)
        moved_out = False
        try:
            moved_out = (Path(out).resolve().parent
                         != Path(settings.output_dir()).resolve())
        except OSError:
            pass
        res = translate_document(job.path, opts, out, on_prog, self._cancel)

        job.segments = res.segments
        job.translated = res.translated
        job.failed = res.failed
        job.warnings = res.warnings
        if moved_out:
            job.warnings = list(job.warnings or []) + [
                tr("输出目录不可写，译文已改存到：", "Output dir not writable, saved to: ")
                + str(Path(out).parent)]
        job.output = res.output
        job.elapsed = res.elapsed
        if res.ok:
            job.status = "done"
            job.percent = 1.0
            job.message = tr(
                f"完成 · {res.translated}/{res.segments} 段 · {res.elapsed:.1f}s",
                f"Done · {res.translated}/{res.segments} seg · {res.elapsed:.1f}s",
            )
        else:
            job.status = "failed" if "取消" not in res.error else "cancelled"
            job.error = res.error
            job.message = res.error[:120]
        if res.ir is not None:
            with self._lock:
                self._irs[job.id] = (res.ir, None)
                while len(self._irs) > MAX_IRS:
                    self._irs.popitem(last=False)
        bus.emit("job_done", job=job.to_dict())

    # ---------- 预览与编辑 ----------
    def ir_of(self, jid: str) -> DocumentIR | None:
        with self._lock:
            item = self._irs.get(jid)
            return item[0] if item else None

    def preview(self, jid: str) -> dict:
        ir = self.ir_of(jid)
        job = self.get(jid)
        if ir is None or job is None:
            return {"ok": False, "error": tr("该文件的结果已释放，请重新翻译",
                                     "Result released — please translate again")}
        return {
            "ok": True,
            "job": job.to_dict(),
            "doc": ir.to_dict(),
            "mode": str(settings.get("translate.mode") or "target_only"),
        }

    def edit(self, jid: str, sid: str, text: str) -> dict:
        ir = self.ir_of(jid)
        if ir is None:
            return {"ok": False, "error": tr("结果已释放", "Result released")}
        for seg in ir.segments:
            if seg.sid == sid:
                seg.tgt = text
                seg.status = STATUS_EDITED if text.strip() else seg.status
                return {"ok": True}
        return {"ok": False, "error": tr("未找到该段落", "Segment not found")}

    def retranslate(self, jid: str, sids: list[str], patch: dict | None = None) -> dict:
        ir = self.ir_of(jid)
        if ir is None:
            return {"ok": False, "error": "结果已释放"}
        opts = TransOptions.from_settings(patch)
        wanted = set(sids or [])
        segs = [s for s in ir.segments if (not wanted or s.sid in wanted)]
        if not segs:
            return {"ok": False, "error": tr("没有可重译的段落", "Nothing to retranslate")}
        try:
            retranslate_segments(ir, segs, opts)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        return {"ok": True, "count": len(segs), "segments": [s.to_dict() for s in segs]}

    def refine(self, jid: str, sids: list[str], instruction: str,
               patch: dict | None = None) -> dict:
        """预览界面的 AI 实时调整：按自然语言指令改写选中段落。"""
        ir = self.ir_of(jid)
        if ir is None:
            return {"ok": False, "error": tr("结果已释放，请重新翻译",
                                             "Result released — please translate again")}
        opts = TransOptions.from_settings(patch)
        wanted = set(sids or [])
        segs = [s for s in ir.segments if (not wanted or s.sid in wanted)]
        if not segs:
            return {"ok": False, "error": tr("没有可调整的段落", "No segments to adjust")}
        try:
            changed = refine_segments(ir, segs, instruction, opts)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}
        return {
            "ok": True,
            "count": len(segs),
            "changed": changed,
            "segments": [s.to_dict() for s in segs],
        }

    def save_preview(self, jid: str, mode: str | None = None) -> dict:
        ir = self.ir_of(jid)
        job = self.get(jid)
        if ir is None or job is None:
            return {"ok": False, "error": "结果已释放"}
        from ..parsers.registry import parser_for

        target = Path(job.output) if job.output else output_path_for(
            job.path, settings.output_dir(), str(settings.get("output.suffix") or "_译文")
        )
        try:
            parser = parser_for(ir.path)
            info = parser.run_write(ir, str(target), mode or str(settings.get("translate.mode")))
        except Exception as exc:  # noqa: BLE001
            return {"ok": False,
                    "error": tr("保存失败：", "Save failed: ") + f"{type(exc).__name__}: {exc}"}
        job.output = str(target)
        job.warnings = list(info.get("warnings") or [])
        bus.emit("saved", id=jid, output=str(target))
        return {"ok": True, "output": str(target), "warnings": job.warnings}


manager = JobManager()
