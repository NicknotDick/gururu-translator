"""PowerPoint (.pptx) 解析器：形状/表格/组合内文字，保留幻灯片版式。

译文回填后会按源文本框尺寸自动缩放字号（只缩不放，设可读下限），
尽力填满又不溢出；实在放不下时返回溢出提示。
"""
from __future__ import annotations

import copy
import math
from typing import Any

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.oxml.ns import qn
from pptx.util import Pt

from ..core.i18n import tr
from ..core.ir import is_translatable
from .base import MODE_BILINGUAL, BaseParser, Holder

EMU_PER_PT = 12700.0
MIN_FONT_PT = 8.0          # 可读下限：任何情况下不小于此值
FIT_RATIO_FLOOR = 0.6      # 相对原始字号的最小比例，保证标题不会缩得离谱


def _para_text(p: Any) -> str:
    try:
        txt = "".join(r.text for r in p.runs)
    except Exception:
        txt = ""
    if not txt:
        txt = p.text or ""
    return txt


def _set_para_text(p: Any, text: str) -> None:
    runs = list(p.runs)
    if runs:
        runs[0].text = text
        for r in runs[1:]:
            r.text = ""
    else:
        p.add_run().text = text


def _ensure_autofit(text_frame: Any) -> None:
    try:
        bodyPr = text_frame._txBody.find(qn("a:bodyPr"))
        if bodyPr is None:
            return
        for tag in ("a:normAutofit", "a:spAutoFit", "a:noAutofit"):
            el = bodyPr.find(qn(tag))
            if el is not None:
                bodyPr.remove(el)
        el = bodyPr.makeelement(qn("a:normAutofit"), {})
        bodyPr.insert(0, el)
    except Exception:
        pass


def _strip_bullet(p: Any) -> None:
    try:
        pPr = p._p.find(qn("a:pPr"))
        if pPr is None:
            pPr = p._p.makeelement(qn("a:pPr"), {})
            p._p.insert(0, pPr)
        for tag in ("a:buChar", "a:buAutoNum"):
            el = pPr.find(qn(tag))
            if el is not None:
                pPr.remove(el)
        pPr.append(pPr.makeelement(qn("a:buNone"), {}))
    except Exception:
        pass


def _insets_pt(tf: Any) -> tuple[float, float, float, float]:
    """文本框内边距（左 上 右 下，磅）。默认 0.1 英寸 = 7.2pt。"""
    d = 7.2
    try:
        bodyPr = tf._txBody.find(qn("a:bodyPr"))
        if bodyPr is not None:
            vals = []
            for attr in ("lIns", "tIns", "rIns", "bIns"):
                raw = bodyPr.get(attr)
                vals.append(float(raw) / EMU_PER_PT if raw else d)
            return vals[0], vals[1], vals[2], vals[3]
    except Exception:
        pass
    return d, d, d, d


def _base_size_pt(tf: Any, default: float = 18.0) -> float:
    """取当前字号：run 显式字号 > 段落字号 > 默认。"""
    try:
        for p in tf.paragraphs:
            for r in p.runs:
                try:
                    if r.font.size is not None:
                        return float(r.font.size.pt)
                except Exception:
                    pass
            try:
                if p.font is not None and p.font.size is not None:
                    return float(p.font.size.pt)
            except Exception:
                pass
    except Exception:
        pass
    return default


def _width_units(text: str) -> float:
    """以字号为 1 单位的文本宽度估算（CJK 记 1.0，西文按字形近似）。"""
    w = 0.0
    for ch in text or "":
        if ord(ch) > 0x2E80:          # CJK / 全角
            w += 1.0
        elif ch in "iljI|.,:;!'’":
            w += 0.30
        elif ch in "MWmw@%":
            w += 0.88
        elif ch.isupper():
            w += 0.68
        elif ch == " ":
            w += 0.28
        else:
            w += 0.52
    return w


def _needed_height_pt(tf: Any, size: float, avail_w: float) -> float:
    """给定字号时渲染所需高度（磅）。"""
    total = 0.0
    per_line_units = max(1.0, avail_w / max(0.5, size))
    try:
        paras = list(tf.paragraphs)
    except Exception:
        return size * 1.2
    for p in paras:
        text = _para_text(p)
        if not text.strip():
            total += size * 1.25
            continue
        lines = max(1, math.ceil(_width_units(text) / per_line_units))
        total += lines * size * 1.22
    return total


def _apply_size(tf: Any, size: float) -> None:
    try:
        tf.word_wrap = True
    except Exception:
        pass
    try:
        for p in tf.paragraphs:
            for r in p.runs:
                try:
                    r.font.size = Pt(round(size, 1))
                except Exception:
                    pass
    except Exception:
        pass


def _fit_frame(tf: Any, box_w_emu: float, box_h_emu: float) -> bool:
    """按文本框尺寸缩放字号使其放得下；返回 True 表示缩放后仍可能溢出。

    只缩小、不放大；下限为 max(8pt, 原始字号 × 0.6)，保证可读性。
    """
    try:
        if not box_w_emu or not box_h_emu:
            return False
        l, t, r, b = _insets_pt(tf)
        avail_w = max(20.0, float(box_w_emu) / EMU_PER_PT - l - r)
        avail_h = max(10.0, float(box_h_emu) / EMU_PER_PT - t - b)
        base = _base_size_pt(tf)
        floor = max(MIN_FONT_PT, base * FIT_RATIO_FLOOR)
        size = base
        for _ in range(4):
            need = _needed_height_pt(tf, size, avail_w)
            if need <= avail_h:
                break
            size = max(floor, size * math.sqrt(avail_h / max(1.0, need)))
            if size <= floor + 0.01:
                break
        if size >= base - 0.05:
            return False
        _apply_size(tf, size)
        return _needed_height_pt(tf, size, avail_w) > avail_h * 1.05
    except Exception:
        return False


class PptxParser(BaseParser):
    ext = ".pptx"
    label = "PowerPoint 演示文稿"
    supports_bilingual = True

    def _walk_shapes(self, shapes, slide_no: int, loc_prefix: str):
        for shape in shapes:
            try:
                if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                    yield from self._walk_shapes(shape.shapes, slide_no, loc_prefix)
                    continue
            except Exception:
                pass
            if getattr(shape, "has_table", False) and shape.has_table:
                try:
                    widths = [c.width for c in shape.table.columns]
                    heights = [r.height for r in shape.table.rows]
                except Exception:
                    widths, heights = [], []
                for r_i, row in enumerate(shape.table.rows):
                    for c_i, cell in enumerate(row.cells):
                        w = widths[c_i] if c_i < len(widths) else 0
                        h = heights[r_i] if r_i < len(heights) else 0
                        yield ("cell", cell.text_frame, slide_no, (w, h))
                continue
            if getattr(shape, "has_text_frame", False) and shape.has_text_frame:
                yield ("shape", shape.text_frame, slide_no,
                       (getattr(shape, "width", 0), getattr(shape, "height", 0)))

    def _open_and_scan(self, path: str, opts: dict):
        prs = Presentation(path)
        holders: list[Holder] = []

        def add_frame(kind: str, tf: Any, slide_no: int, box=None) -> None:
            group = tr(f"第 {slide_no} 页", f"Slide {slide_no}")
            for p in tf.paragraphs:
                text = _para_text(p)
                if not is_translatable(text):
                    continue

                def _set(value: str, _p=p, _tf=tf) -> None:
                    _set_para_text(_p, value)
                    _ensure_autofit(_tf)

                holders.append(Holder(kind=kind, text=text, setter=_set, obj=p,
                                      extra={"slide": slide_no, "group": group,
                                             "tf": tf, "box": box or (0, 0)}))

        for idx, slide in enumerate(prs.slides, start=1):
            for kind, tf, no, box in self._walk_shapes(slide.shapes, idx, ""):
                add_frame(kind, tf, no, box)
            try:
                if slide.has_notes_slide:
                    add_frame("meta", slide.notes_slide.notes_text_frame, idx)
            except Exception:
                pass
        return prs, holders

    def scan(self, path: str, opts: dict) -> list[Holder]:
        return self._open_and_scan(path, opts)[1]

    def commit(self, path: str, out_path: str, mapping: dict[int, str],
               mode: str, opts: dict) -> dict:
        prs, holders = self._open_and_scan(path, opts)
        touched: dict[int, tuple[Any, tuple]] = {}
        for i, h in enumerate(holders):
            tgt = mapping.get(i)
            if not tgt:
                continue
            p = h.obj
            if mode == MODE_BILINGUAL:
                try:
                    new_el = copy.deepcopy(p._p)
                    p._p.addnext(new_el)
                    from pptx.text.text import _Paragraph  # type: ignore

                    new_p = _Paragraph(new_el, p._parent)
                    _strip_bullet(new_p)
                    _set_para_text(new_p, tgt)
                    _ensure_autofit(p._parent)
                except Exception:
                    if h.setter:
                        h.setter(tgt)
            else:
                if h.setter:
                    h.setter(tgt)
            ex = h.extra or {}
            tf = ex.get("tf")
            if tf is not None:
                touched[id(tf)] = (tf, tuple(ex.get("box") or (0, 0)))

        overflow: list[str] = []
        for tf, (w, h) in touched.values():
            if _fit_frame(tf, w, h):
                try:
                    sample = " / ".join(x for x in (_para_text(pp) for pp in tf.paragraphs)
                                        if x)[:40]
                except Exception:
                    sample = ""
                overflow.append(tr("文本框偏小，字号已缩至下限：",
                                   "Text box too small, font shrunk to minimum: ") + sample)

        prs.save(out_path)
        return {"overflow": overflow, "warnings": []}
