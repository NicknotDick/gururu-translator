"""Word (.docx) 解析器：段落级翻译，保留样式、编号与表格结构。"""
from __future__ import annotations

import copy
from typing import Any

from docx import Document
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

from ..core.ir import is_translatable
from .base import MODE_BILINGUAL, BaseParser, Holder


def _in_textbox(el: Any, root: Any) -> bool:
    anc = el.getparent()
    while anc is not None and anc is not root:
        if anc.tag == qn("w:txbxContent"):
            return True
        anc = anc.getparent()
    return False


def _para_text(p_el: Any) -> str:
    parts: list[str] = []
    for t in p_el.iter(qn("w:t")):
        if _in_textbox(t, p_el):
            continue
        parts.append(t.text or "")
    return "".join(parts)


def _set_para_text(p_el: Any, text: str, parent: Any) -> None:
    ts = [t for t in p_el.iter(qn("w:t")) if not _in_textbox(t, p_el)]
    if not ts:
        Paragraph(p_el, parent).add_run(text)
        return
    ts[0].text = text
    ts[0].set(qn("xml:space"), "preserve")
    for t in ts[1:]:
        t.text = ""


def _strip_numbering(p_el: Any) -> None:
    pPr = p_el.find(qn("w:pPr"))
    if pPr is None:
        return
    numPr = pPr.find(qn("w:numPr"))
    if numPr is not None:
        pPr.remove(numPr)


def _drop_drawings(p_el: Any) -> None:
    for tag in ("w:drawing", "w:pict"):
        for el in list(p_el.iter(qn(tag))):
            parent = el.getparent()
            if parent is not None:
                parent.remove(el)


class DocxParser(BaseParser):
    ext = ".docx"
    label = "Word 文档"
    supports_bilingual = True

    # ---------- 扫描 ----------
    def _open_and_scan(self, path: str, opts: dict) -> tuple[Any, list[Holder]]:
        doc = Document(path)
        parent = doc._body
        holders: list[Holder] = []

        def add(p_el: Any, kind: str = "para") -> None:
            text = _para_text(p_el)

            def _set(value: str, _el=p_el) -> None:
                _set_para_text(_el, value, parent)

            holders.append(Holder(kind=kind, text=text, setter=_set, obj=p_el))

        for p_el in doc.element.body.iter(qn("w:p")):
            add(p_el)

        if not opts.get("skip_header_footer"):
            seen: set[int] = set()
            for section in doc.sections:
                for part in (section.header, section.footer,
                             section.first_page_header, section.first_page_footer,
                             section.even_page_header, section.even_page_footer):
                    try:
                        el = part._element
                    except Exception:
                        continue
                    if el is None or id(el) in seen:
                        continue
                    seen.add(id(el))
                    for p_el in el.iter(qn("w:p")):
                        add(p_el, "meta")

        return doc, holders

    def scan(self, path: str, opts: dict) -> list[Holder]:
        return self._open_and_scan(path, opts)[1]

    # ---------- 回写 ----------
    def commit(self, path: str, out_path: str, mapping: dict[int, str],
               mode: str, opts: dict) -> dict:
        doc, holders = self._open_and_scan(path, opts)
        overflow: list[str] = []
        for i, h in enumerate(holders):
            tgt = mapping.get(i)
            if not tgt:
                continue
            if mode == MODE_BILINGUAL:
                src_el = h.obj
                if len(tgt) > 900:
                    overflow.append(f"第 {i + 1} 段译文过长，可能溢出")
                try:
                    new_el = copy.deepcopy(src_el)
                    _drop_drawings(new_el)
                    _strip_numbering(new_el)
                    _set_para_text(new_el, tgt, doc._body)
                    src_el.addnext(new_el)
                except Exception:
                    if h.setter:
                        h.setter(tgt)
            else:
                try:
                    if h.setter:
                        h.setter(tgt)
                except Exception:
                    pass
        doc.save(out_path)
        return {"overflow": overflow}

    def preview_meta(self, path: str) -> dict:
        try:
            doc = Document(path)
            return {"paragraphs": len(doc.paragraphs), "tables": len(doc.tables)}
        except Exception:
            return {}
