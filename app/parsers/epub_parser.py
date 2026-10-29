"""EPUB 解析器：按 spine 顺序改写 XHTML 文本节点，保留标签结构与样式。"""
from __future__ import annotations

import re
import zipfile
from typing import Any

from lxml import etree

from ..core.ir import is_translatable
from .base import MODE_BILINGUAL, BaseParser, Holder

XHTML_EXT = (".xhtml", ".html", ".htm")
BLOCK_TAGS = {
    "p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "td", "th",
    "blockquote", "dt", "dd", "figcaption", "caption", "div", "section", "article",
}
PROTECTED_TAGS = {"a", "img", "code", "pre", "script", "style", "svg", "br", "ruby", "rt", "rp"}
SKIP_TAGS = {"script", "style", "pre", "code", "svg", "head"}


def _ln(el: Any) -> str:
    try:
        return etree.QName(el).localname.lower()
    except Exception:
        return ""


def _has_protected(el: Any) -> bool:
    for sub in el.iter():
        if sub is el:
            continue
        if _ln(sub) in PROTECTED_TAGS:
            return True
    return False


def _has_skip(el: Any) -> bool:
    for sub in el.iter():
        if _ln(sub) in SKIP_TAGS:
            return True
    return False


def _flatten(el: Any, value: str) -> None:
    for child in list(el):
        el.remove(child)
    el.text = value


class EpubParser(BaseParser):
    ext = ".epub"
    label = "EPUB 电子书"
    supports_bilingual = True

    def _open_and_scan(self, path: str, opts: dict):
        zin = zipfile.ZipFile(path)
        items = [(info, zin.read(info.filename)) for info in zin.infolist()]
        zin.close()

        by_name = {info.filename: data for info, data in items}
        docs: list[str] = [n for n in by_name if n.lower().endswith(XHTML_EXT)]
        # 按 OPF spine 排序，读不到时按文件名
        order: list[str] = []
        try:
            opf_name = next(n for n in by_name if n.lower().endswith(".opf"))
            opf = etree.fromstring(by_name[opf_name])
            base = opf_name.rsplit("/", 1)[0] + "/" if "/" in opf_name else ""
            idmap = {}
            for el in opf.iter():
                if _ln(el) == "item" and el.get("id") and el.get("href"):
                    href = el.get("href")
                    if href.lower().endswith(XHTML_EXT):
                        idmap[el.get("id")] = base + href
            for el in opf.iter():
                if _ln(el) == "itemref" and el.get("idref") in idmap:
                    order.append(idmap[el.get("idref")])
        except Exception:
            pass
        docs = [d for d in order if d in by_name] + [d for d in docs if d not in order]

        roots: dict[str, Any] = {}
        holders: list[Holder] = []
        for name in docs:
            try:
                root = etree.fromstring(by_name[name], etree.XMLParser(
                    remove_blank_text=False, recover=True, huge_tree=True))
            except Exception:
                continue
            roots[name] = root
            body = None
            for el in root.iter():
                if _ln(el) == "body":
                    body = el
                    break
            if body is None:
                continue
            for el in body.iter():
                tag = _ln(el)
                if tag not in BLOCK_TAGS:
                    continue
                if _has_skip(el):
                    continue
                text = "".join(el.itertext())
                if not text.strip() or not is_translatable(text):
                    continue
                if _has_protected(el):
                    # 含链接/图片/行内代码：逐文本节点处理，保留标签
                    for node in el.iter():
                        for attr in ("text", "tail"):
                            val = getattr(node, attr)
                            if val and val.strip() and is_translatable(val):
                                def _set(v: str, _n=node, _a=attr) -> None:
                                    setattr(_n, _a, v)
                                holders.append(Holder(kind="para", text=val.strip(),
                                                      setter=_set, obj=node))
                    continue

                def _set(v: str, _el=el) -> None:
                    _flatten(_el, v)

                holders.append(Holder(kind="para", text=text.strip(), setter=_set, obj=el))
        return items, roots, holders

    def scan(self, path: str, opts: dict) -> list[Holder]:
        return self._open_and_scan(path, opts)[2]

    def commit(self, path: str, out_path: str, mapping: dict[int, str],
               mode: str, opts: dict) -> dict:
        items, roots, holders = self._open_and_scan(path, opts)
        warnings: list[str] = []
        for i, h in enumerate(holders):
            tgt = mapping.get(i)
            if not tgt or not h.setter:
                continue
            try:
                if mode == MODE_BILINGUAL and h.obj is not None and _ln(h.obj) in BLOCK_TAGS:
                    el = h.obj
                    para = etree.SubElement(el.getparent(), el.tag)
                    para.text = tgt
                    el.addnext(para)
                else:
                    h.setter(tgt)
            except Exception:
                continue
        payload: dict[str, bytes] = {}
        for name, root in roots.items():
            payload[name] = etree.tostring(root, xml_declaration=False, encoding="utf-8")
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
            first = True
            for info, data in items:
                if info.filename in payload:
                    data = payload[info.filename]
                if first and info.filename == "mimetype":
                    zout.writestr(zipfile.ZipInfo("mimetype"), data,
                                  compress_type=zipfile.ZIP_STORED)
                    first = False
                    continue
                zout.writestr(info, data)
        return {"warnings": warnings}
