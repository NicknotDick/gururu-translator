"""Visio (.vsdx) 解析器：直接改写页面 XML 中的文本节点，几何坐标完全不动。"""
from __future__ import annotations

import re
import zipfile

from lxml import etree

from ..core.ir import is_translatable
from .base import MODE_BILINGUAL, BaseParser, Holder

PAGE_RE = re.compile(r"^visio/pages/page\d+\.xml$")


def _localname(el) -> str:
    try:
        return etree.QName(el).localname
    except Exception:
        return ""


class VsdxParser(BaseParser):
    ext = ".vsdx"
    label = "Visio 图表"
    supports_bilingual = False  # Visio 文本定位在形状内，双语会互相覆盖

    def _open_and_scan(self, path: str, opts: dict):
        zin = zipfile.ZipFile(path)
        items = [(info, zin.read(info.filename)) for info in zin.infolist()]
        zin.close()

        roots: dict[str, object] = {}
        holders: list[Holder] = []
        for info, data in items:
            if not PAGE_RE.match(info.filename):
                continue
            try:
                root = etree.fromstring(data, etree.XMLParser(remove_blank_text=False,
                                                             huge_tree=True))
            except Exception:
                continue
            roots[info.filename] = root
            for el in root.iter():
                if _localname(el) != "Text":
                    continue
                text = "".join(el.itertext())
                if not text.strip() or not is_translatable(text):
                    continue

                def _set(value: str, _el=el) -> None:
                    for child in list(_el):
                        _el.remove(child)
                    _el.text = value

                holders.append(Holder(kind="shape", text=text.strip(), setter=_set, obj=el,
                                      extra={"file": info.filename}))
        return items, roots, holders

    def scan(self, path: str, opts: dict) -> list[Holder]:
        return self._open_and_scan(path, opts)[2]

    def commit(self, path: str, out_path: str, mapping: dict[int, str],
               mode: str, opts: dict) -> dict:
        items, roots, holders = self._open_and_scan(path, opts)
        for i, h in enumerate(holders):
            tgt = mapping.get(i)
            if tgt and h.setter:
                try:
                    h.setter(tgt)
                except Exception:
                    pass
        payload: dict[str, bytes] = {}
        for name, root in roots.items():
            payload[name] = etree.tostring(
                root, xml_declaration=True, encoding="UTF-8", standalone=True
            )
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for info, data in items:
                if info.filename in payload:
                    data = payload[info.filename]
                zout.writestr(info, data)
        return {"warnings": [] if mode != MODE_BILINGUAL else ["Visio 不支持双语对照，已按仅译文输出"]}
