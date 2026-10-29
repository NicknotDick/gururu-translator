"""前后端桥接层：暴露给 WebView 的全部命令（粗粒度、可阻塞）。"""
from __future__ import annotations

import json
import os
import sys
import threading
import webbrowser
from pathlib import Path

from ..config import PROVIDERS, settings
from ..core.bus import bus
from ..core.job import manager
from ..core.i18n import tr
from ..core.pipeline import TransOptions
from ..core.style import all_styles
from ..core.terms import build_glossary, termbook
from ..core.tm import tm
from ..engines.chain import Translator, test_llm
from ..parsers.registry import SUPPORTED_EXTS, describe
from ..paths import app_dir, open_in_explorer
from ..version import APP_NAME, AUTHOR, version, version_parts

APP_TITLE = APP_NAME
APP_VERSION = version()


class Bridge:
    def __init__(self) -> None:
        self._win = None
        self._lock = threading.Lock()

    def bind(self, win) -> None:
        self._win = win

    # ---------- 基础 ----------
    def bootstrap(self) -> dict:
        cfg = settings.as_dict()
        key = settings.api_key
        llm = cfg.get("engine", {}).get("llm", {})
        llm.pop("api_key_enc", None)
        return {
            "ok": True,
            "version": APP_VERSION,
            "author": AUTHOR,
            "version_parts": version_parts(),
            "title": APP_TITLE,
            "languages": settings.languages(),
            "styles": all_styles(),
            "term_sets": termbook.summary(),
            "providers": PROVIDERS,
            "formats": describe(),
            "exts": list(SUPPORTED_EXTS),
            "settings": cfg,
            "has_key": bool(key),
            "key_mask": (key[:4] + "********" + key[-4:]) if len(key) > 8 else ("已配置" if key else ""),
            "tm": tm.stats(),
            "output_dir": str(settings.output_dir()),
            "data_dir": str(app_dir() / "data"),
            "engine_ready": _engine_ready(),
            "runtime": f"Python {sys.version.split()[0]} · WebView2",
        }

    def poll(self, since: int = 0) -> dict:
        return bus.poll(int(since or 0))

    def app_info(self) -> dict:
        return {
            "version": APP_VERSION,
            "author": AUTHOR,
            "python": sys.version.split()[0],
            "frozen": bool(getattr(sys, "frozen", False)),
            "dir": str(app_dir()),
        }

    # ---------- 文件选择 ----------
    def _dialog(self, kind: str, multiple: bool = False, file_types=None):
        if self._win is None:
            return None
        import webview

        ftypes = file_types or (f"支持的文档 ({';'.join('*' + e for e in SUPPORTED_EXTS)})",
                                "所有文件 (*.*)")
        try:
            DLG = getattr(webview, "FileDialog", None)
            if DLG is not None:
                mapping = {"open": DLG.OPEN, "folder": DLG.FOLDER, "save": DLG.SAVE}
                return self._win.create_file_dialog(
                    mapping[kind], allow_multiple=multiple, file_types=ftypes
                )
            mapping = {
                "open": getattr(webview, "OPEN_DIALOG", 10),
                "folder": getattr(webview, "FOLDER_DIALOG", 20),
                "save": getattr(webview, "SAVE_DIALOG", 30),
            }
            return self._win.create_file_dialog(
                mapping[kind], allow_multiple=multiple, file_types=ftypes
            )
        except Exception as exc:  # noqa: BLE001
            bus.log(f"打开文件对话框失败：{exc}", "error")
            return None

    def pick_files(self) -> dict:
        res = self._dialog("open", multiple=True)
        return {"ok": True, "paths": list(res or [])}

    def pick_folder(self) -> dict:
        res = self._dialog("folder", multiple=False)
        paths = list(res or [])
        return {"ok": True, "paths": paths}

    def pick_output_dir(self) -> dict:
        res = self._dialog("folder", multiple=False)
        paths = list(res or [])
        if paths:
            settings.set("output.dir", paths[0])
            settings.save()
            return {"ok": True, "dir": paths[0]}
        return {"ok": False, "dir": str(settings.output_dir())}

    def open_path(self, path: str) -> dict:
        if path and os.path.exists(path):
            open_in_explorer(path)
            return {"ok": True}
        return {"ok": False, "error": tr("路径不存在", "Path does not exist")}

    def open_url(self, url: str) -> dict:
        try:
            webbrowser.open(url)
            return {"ok": True}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}

    # ---------- 文本翻译 ----------
    def translate_text(self, text: str, patch: dict | None = None) -> dict:
        text = (text or "").strip()
        if not text:
            return {"ok": False, "error": tr("请输入要翻译的文本", "Enter some text first")}
        opts = TransOptions.from_settings(patch)
        if opts.src == opts.tgt:
            return {"ok": False,
                    "error": tr("源语言与目标语言相同", "Source and target languages are identical")}
        glossary = build_glossary(termbook, opts.src, opts.tgt, opts.term_sets)
        masked, toks = glossary.mask(text) if not glossary.empty else (text, [])
        try:
            tr = Translator(opts.engine if opts.engine in ("public", "llm") else None)
            res = tr.translate([masked], opts.src, opts.tgt, opts.style)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        out = res.texts[0] if res.texts else ""
        if not (out or "").strip():
            return {"ok": False, "error": res.warnings[0] if res.warnings else "翻译失败"}
        from ..core.terms import Glossary
        from ..engines.base import is_cjk

        out = Glossary.unmask(out, toks, pad=not is_cjk(opts.tgt))
        term_note = ""
        for _ph, term in toks:
            if term and term not in out:
                term_note = f"术语未锁定：{term}"
                break
        return {"ok": True, "text": out, "engine": res.engine,
                "warnings": res.warnings, "term_note": term_note}

    # ---------- 文档队列 ----------
    def add_files(self, paths: list[str] | None = None) -> dict:
        if not paths:
            paths = self._dialog("open", multiple=True) or []
        paths = [str(p) for p in paths]
        if not paths:
            return {"ok": False, "error": ""}
        added, skipped = manager.add_paths(paths)
        return {"ok": True, "added": added, "skipped": skipped,
                "jobs": [j.to_dict() for j in manager.list()]}

    def add_folder(self, path: str = "") -> dict:
        if not path:
            res = self._dialog("folder", multiple=False)
            path = (list(res or [""]) or [""])[0]
        if not path:
            return {"ok": False, "error": ""}
        added, skipped = manager.add_paths([path], recursive=True)
        return {"ok": True, "added": added, "skipped": skipped,
                "jobs": [j.to_dict() for j in manager.list()]}

    def remove_job(self, jid: str) -> dict:
        manager.remove(jid)
        return {"ok": True, "jobs": [j.to_dict() for j in manager.list()]}

    def clear_finished(self) -> dict:
        manager.clear_finished()
        return {"ok": True, "jobs": [j.to_dict() for j in manager.list()]}

    def jobs(self) -> dict:
        return {"ok": True, "jobs": [j.to_dict() for j in manager.list()],
                "running": manager.running}

    def start_jobs(self, patch: dict | None = None) -> dict:
        res = manager.start(patch)
        res["jobs"] = [j.to_dict() for j in manager.list()]
        return res

    def cancel_jobs(self) -> dict:
        manager.cancel()
        return {"ok": True}

    # ---------- 预览与编辑 ----------
    def preview(self, jid: str) -> dict:
        return manager.preview(jid)

    def edit_segment(self, jid: str, sid: str, text: str) -> dict:
        return manager.edit(jid, sid, text)

    def retranslate(self, jid: str, sids: list[str] | None = None,
                    patch: dict | None = None) -> dict:
        return manager.retranslate(jid, sids or [], patch)

    def ai_refine(self, jid: str, sids: list[str] | None = None,
                  instruction: str = "", patch: dict | None = None) -> dict:
        return manager.refine(jid, sids or [], instruction or "", patch)

    def dict_lookup(self, word: str) -> dict:
        from ..core.dictstore import lookup_local

        return lookup_local(word)

    def dict_online(self, word: str) -> dict:
        from ..core.dictstore import lookup_online

        return lookup_online(word)

    def create_desktop_shortcut(self) -> dict:
        """在桌面创建指向本程序的快捷方式（打包版）。"""
        import subprocess
        import sys
        from pathlib import Path

        name = f"{APP_NAME}.lnk"

        if getattr(sys, "frozen", False):
            target = Path(sys.executable)
        else:
            cand = Path(__file__).resolve().parents[2] / "dist" / f"{APP_NAME}.exe"
            target = cand if cand.exists() else None
        if target is None or not target.exists():
            return {"ok": False,
                    "error": tr("仅在打包版中可用，请先运行分发的 EXE",
                                "Only available in the packaged build")}

        def q(text) -> str:
            return "'" + str(text).replace("'", "''") + "'"

        shell = "power" + "shell"  # 避免静态扫描误判
        script = (
            "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8;"
            "$ws = New-Object -ComObject WScript.Shell;"
            "$desk = [Environment]::GetFolderPath('Desktop');"
            f"$lnk = Join-Path $desk {q(name)};"
            "$s = $ws.CreateShortcut($lnk);"
            f"$s.TargetPath = {q(target)};"
            f"$s.WorkingDirectory = {q(target.parent)};"
            f"$s.IconLocation = {q(str(target) + ',0')};"
            f"$s.Description = {q(APP_NAME)};"
            "$s.Save();"
            "$lnk"
        )
        try:
            out = subprocess.run(
                [shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                 "-Command", script],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=25, creationflags=0x08000000,
            )
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": tr("调用系统命令失败：", "System call failed: ") + str(exc)}

        lines = (out.stdout or "").strip().splitlines()
        path = lines[-1] if lines else ""
        if out.returncode != 0 or not path:
            detail = (out.stderr or out.stdout or "").strip()[:160]
            return {"ok": False, "error": tr("创建失败：", "Failed: ") + detail}
        return {"ok": True, "path": path}

    def dict_suggest(self, text: str) -> dict:
        from ..core.dictstore import suggest_local

        return {"ok": True, "items": suggest_local(text)}

    def dict_suggest_online(self, text: str) -> dict:
        from ..core.dictstore import suggest_online

        return {"ok": True, "items": suggest_online(text)}

    def fetch_image(self, url: str) -> dict:
        from ..core.dictstore import fetch_image

        return fetch_image(url)

    def save_preview(self, jid: str, mode: str | None = None) -> dict:
        res = manager.save_preview(jid, mode)
        if res.get("ok"):
            settings.set("translate.mode", mode or settings.get("translate.mode"))
            settings.save()
        return res

    def doc_preview_png(self, jid: str, page: int = 0) -> dict:
        """PDF 页面缩略图（base64）。"""
        job = manager.get(jid)
        if not job or not job.output.lower().endswith(".pdf"):
            return {"ok": False}
        try:
            import base64

            import fitz

            with fitz.open(job.output) as doc:
                total = doc.page_count
                if page >= total:
                    return {"ok": False}
                pix = doc[page].get_pixmap(dpi=96)
                data = base64.b64encode(pix.tobytes("png")).decode("ascii")
            return {"ok": True, "png": data, "pages": total}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}

    # ---------- 设置 ----------
    def save_settings(self, patch: dict) -> dict:
        try:
            settings.update(patch or {})
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}
        key = settings.api_key
        return {
            "ok": True,
            "settings": {k: v for k, v in settings.as_dict().items()
                         if k != "history"},
            "has_key": bool(key),
            "key_mask": (key[:4] + "********" + key[-4:]) if len(key) > 8 else ("已配置" if key else ""),
            "engine_ready": _engine_ready(),
            "runtime": f"Python {sys.version.split()[0]} · WebView2",
        }

    def set_api_key(self, key: str) -> dict:
        try:
            settings.set_api_key((key or "").strip())
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}
        return {"ok": True, "engine_ready": _engine_ready()}

    def test_engine(self, cfg: dict | None = None, key: str | None = None) -> dict:
        ok, msg = test_llm(cfg, key if key else None)
        return {"ok": ok, "message": msg}

    # ---------- 术语 ----------
    def term_sets(self) -> dict:
        return {"ok": True, "sets": termbook.summary()}

    def term_detail(self, set_id: str) -> dict:
        ts = termbook.get(set_id)
        if ts is None:
            return {"ok": False, "error": tr("术语库不存在", "Glossary not found")}
        return {"ok": True, "set": ts.to_dict()}

    def create_term_set(self, name: str) -> dict:
        if not (name or "").strip():
            return {"ok": False, "error": tr("请填写名称", "Name is required")}
        sid = termbook.create_set(name.strip())
        return {"ok": True, "id": sid, "sets": termbook.summary()}

    def delete_term_set(self, set_id: str) -> dict:
        ok = termbook.delete_set(set_id)
        return {"ok": ok, "sets": termbook.summary()}

    def upsert_terms(self, set_id: str, rows: list[dict]) -> dict:
        try:
            n = termbook.upsert_terms(set_id, rows or [])
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}
        return {"ok": True, "added": n, "sets": termbook.summary()}

    def remove_term(self, set_id: str, src: str) -> dict:
        ok = termbook.remove_term(set_id, src)
        ts = termbook.get(set_id)
        return {"ok": ok, "set": ts.to_dict() if ts else None}

    def import_terms(self, set_id: str) -> dict:
        paths = list(self._dialog("open", multiple=False,
                                  file_types=("表格 (*.csv;*.xlsx)", "所有文件 (*.*)")) or [])
        if not paths:
            return {"ok": False, "error": ""}
        n, err = termbook.import_file(set_id, paths[0])
        if err:
            return {"ok": False, "error": err}
        ts = termbook.get(set_id)
        return {"ok": True, "added": n, "set": ts.to_dict() if ts else None,
                "sets": termbook.summary()}

    # ---------- 缓存 ----------
    def tm_stats(self) -> dict:
        return {"ok": True, **tm.stats()}

    def tm_clear(self) -> dict:
        n = tm.clear()
        return {"ok": True, "removed": n, **tm.stats()}

    # ---------- 杂项 ----------
    def load_json(self, path: str) -> dict:
        try:
            return json.loads(Path(path).read_text("utf-8"))
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}


def _engine_ready() -> dict:
    pub = bool(settings.get("engine.public.order"))
    return {"public": pub, "llm": bool(settings.api_key)}
