"""PDF 解析器：按文字块坐标擦除原文并用译文原位回填，页面与图形完全不变。"""
from __future__ import annotations

import html
import re
from typing import Any

from ..core.i18n import tr
from ..core.ir import is_translatable
from .base import MODE_BILINGUAL, BaseParser, Holder

CJK_RE = re.compile(r"[\u3000-\u9fff\uac00-\ud7af\uff00-\uffef]")


class PdfScannedError(RuntimeError):
    """无文字层（扫描件），需要 OCR 但 v1 未内置。"""


def _join_lines(parts: list[str]) -> str:
    out = ""
    for raw in parts:
        p = raw.strip()
        if not p:
            continue
        if not out:
            out = p
            continue
        if out.endswith("-") and p[:1].islower():
            out = out[:-1] + p
        elif CJK_RE.search(out[-1:]) or CJK_RE.search(p[:1]):
            out += p
        else:
            out += " " + p
    return out


def _hex_color(value: int) -> str:
    try:
        return f"#{(int(value) & 0xFFFFFF):06x}"
    except Exception:
        return "#000000"


def _css(fontsize: float, color: str, align: int) -> str:
    align_map = {1: "center", 2: "right", 3: "justify"}
    return (
        "* {margin:0;padding:0;}"
        f"body{{font-size:{max(4.0, fontsize):.2f}px;line-height:1.22;color:{color};"
        f"text-align:{align_map.get(align, 'left')};}}"
        "p{margin:0;}"
    )


class PdfParser(BaseParser):
    ext = ".pdf"
    label = "PDF 文档"
    supports_bilingual = True

    # ---------- 扫描 ----------
    def _open_and_scan(self, path: str, opts: dict):
        import fitz

        doc = fitz.open(path)
        holders: list[Holder] = []
        scanned_pages = 0
        total_chars = 0
        bad_chars = 0

        for pno in range(doc.page_count):
            page = doc[pno]
            try:
                data = page.get_text("dict")
            except Exception:
                continue
            page_has_text = False
            for block in data.get("blocks", []):
                if block.get("type") != 0:
                    continue
                lines = block.get("lines") or []
                parts: list[str] = []
                max_size = 0.0
                color = 0
                for line in lines:
                    for span in line.get("spans", []):
                        t = span.get("text") or ""
                        parts.append(t)
                        max_size = max(max_size, float(span.get("size") or 0))
                        color = int(span.get("color") or 0)
                text = _join_lines(parts) if len(parts) > 1 else "".join(parts)
                if not text.strip():
                    continue
                page_has_text = True
                total_chars += len(text)
                bad_chars += text.count("\ufffd")
                if not is_translatable(text):
                    continue
                holders.append(Holder(
                    kind="para",
                    text=text,
                    obj=None,
                    extra={
                        "page": pno,
                        "group": tr(f"第 {pno} 页", f"Page {pno}"),
                        "bbox": tuple(block.get("bbox") or (0, 0, 0, 0)),
                        "size": max_size or 10.0,
                        "color": _hex_color(color),
                        "align": 0,
                    },
                ))
            if not page_has_text:
                scanned_pages += 1

        page_count = doc.page_count
        doc.close()
        if total_chars and bad_chars / total_chars > 0.05:
            raise PdfScannedError(
                "该 PDF 文字层无法正确解码（疑似扫描件或字体未嵌入编码），需要 OCR 扩展"
            )
        if total_chars == 0 and page_count > 0:
            raise PdfScannedError("该 PDF 没有文字层（扫描件），当前版本需要 OCR 扩展才能翻译")
        return holders

    def scan(self, path: str, opts: dict) -> list[Holder]:
        return self._open_and_scan(path, opts)

    def load(self, path, opts=None):
        ir = super().load(path, opts)
        try:
            import fitz

            with fitz.open(path) as d:
                ir.meta["pages"] = d.page_count
                if d.needs_pass:
                    ir.warnings.append("PDF 已加密，可能无法完整处理")
        except Exception:
            pass
        return ir

    # ---------- 回写 ----------
    @staticmethod
    def _place(page: Any, rect: Any, text: str, size: float, color: str,
               align: int) -> float:
        """在 rect 内排入译文，返回剩余高度（<0 表示溢出）。"""
        import fitz

        body = "<p>" + html.escape(text).replace("\n", "<br/>") + "</p>"
        try:
            spare, scale = page.insert_htmlbox(
                rect, body, css=_css(size, color, align), scale_low=0.30
            )
            if spare is not None and spare >= -0.5:
                return float(spare)
        except Exception:
            pass
        # 兜底：insert_textbox + PyMuPDF 内置 CJK 字体，逐级缩字号
        try:
            rgb = tuple(int(color[i:i + 2], 16) / 255.0 for i in (1, 3, 5))
        except Exception:
            rgb = (0, 0, 0)
        for factor in (1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.42, 0.35, 0.3):
            try:
                rc = page.insert_textbox(
                    rect, text, fontsize=max(3.0, size * factor),
                    fontname="china-s", color=rgb, align=align, lineheight=1.15,
                )
                if rc >= 0:
                    return float(rc)
            except Exception:
                continue
        return -1.0

    def commit(self, path: str, out_path: str, mapping: dict[int, str],
               mode: str, opts: dict) -> dict:
        import fitz

        holders = self._open_and_scan(path, opts)
        doc = fitz.open(path)
        overflow: list[str] = []

        by_page: dict[int, list[tuple[int, Holder]]] = {}
        for i, h in enumerate(holders):
            if mapping.get(i):
                by_page.setdefault(int(h.extra["page"]), []).append((i, h))

        for pno, items in by_page.items():
            if pno >= doc.page_count:
                continue
            page = doc[pno]
            for _i, h in items:
                try:
                    page.add_redact_annot(fitz.Rect(h.extra["bbox"]), fill=False)
                except Exception:
                    continue
            try:
                page.apply_redactions(
                    images=fitz.PDF_REDACT_IMAGE_NONE,
                    graphics=fitz.PDF_REDACT_LINE_ART_NONE,
                    text=fitz.PDF_REDACT_TEXT_REMOVE,
                )
            except TypeError:
                try:
                    page.apply_redactions(images=0, graphics=0)
                except Exception:
                    pass
            for i, h in items:
                tgt = mapping[i] or ""
                rect = fitz.Rect(h.extra["bbox"])
                size = float(h.extra.get("size") or 10.0)
                color = str(h.extra.get("color") or "#000000")
                if mode == MODE_BILINGUAL:
                    src = h.text
                    h1 = max(4.0, rect.height * 0.5)
                    top = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y0 + h1)
                    bottom = fitz.Rect(rect.x0, rect.y0 + h1, rect.x1, rect.y1)
                    s1 = self._place(page, top, src, size * 0.62, "#666666", 0)
                    s2 = self._place(page, bottom, tgt, size * 0.62, color, 0)
                    if min(s1, s2) < -0.5:
                        overflow.append(f"第 {pno + 1} 页存在溢出的对照块")
                else:
                    spare = self._place(page, rect, tgt, size, color,
                                        int(h.extra.get("align") or 0))
                    if spare < -0.5:
                        overflow.append(f"第 {pno + 1} 页文字块溢出（已自动缩小字号）")

        try:
            doc.save(out_path, garbage=3, deflate=True, clean=False)
        finally:
            doc.close()
        return {"overflow": overflow}
