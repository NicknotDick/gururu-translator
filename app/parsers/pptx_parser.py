"""PowerPoint (.pptx) 解析器：形状/表格/组合内文字，保留幻灯片版式。"""
from __future__ import annotations

import copy
from typing import Any

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.oxml.ns import qn

from ..core.ir import is_translatable
from .base import MODE_BILINGUAL, BaseParser, Holder


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
                for r_i, row in enumerate(shape.table.rows):
                    for c_i, cell in enumerate(row.cells):
                        yield ("cell", cell.text_frame, slide_no)
                continue
            if getattr(shape, "has_text_frame", False) and shape.has_text_frame:
                yield ("shape", shape.text_frame, slide_no)

    def _open_and_scan(self, path: str, opts: dict):
        prs = Presentation(path)
        holders: list[Holder] = []

        def add_frame(kind: str, tf: Any, slide_no: int) -> None:
            for p in tf.paragraphs:
                text = _para_text(p)
                if not is_translatable(text):
                    continue

                def _set(value: str, _p=p, _tf=tf) -> None:
                    _set_para_text(_p, value)
                    _ensure_autofit(_tf)

                holders.append(Holder(kind=kind, text=text, setter=_set, obj=p,
                                      extra={"slide": slide_no}))

        for idx, slide in enumerate(prs.slides, start=1):
            for kind, tf, no in self._walk_shapes(slide.shapes, idx, ""):
                add_frame(kind, tf, no)
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
        prs.save(out_path)
        return {}
