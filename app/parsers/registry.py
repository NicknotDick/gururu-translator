"""解析器注册表与格式能力声明。"""
from __future__ import annotations

from pathlib import Path

from .base import BaseParser
from .docx_parser import DocxParser
from .epub_parser import EpubParser
from .pdf_parser import PdfParser
from .pptx_parser import PptxParser
from .text_parser import MarkdownParser, PlainTextParser
from .vsdx_parser import VsdxParser
from .xlsx_parser import XlsxParser

_REGISTRY: dict[str, BaseParser] = {}


def _reg(parser: BaseParser, exts: tuple[str, ...]) -> None:
    for e in exts:
        _REGISTRY[e] = parser


_reg(DocxParser(), (".docx",))
_reg(XlsxParser(), (".xlsx", ".xlsm"))
_reg(PptxParser(), (".pptx",))
_reg(PdfParser(), (".pdf",))
_reg(VsdxParser(), (".vsdx",))
_reg(MarkdownParser(), (".md", ".markdown"))
_reg(PlainTextParser(), (".txt",))
_reg(EpubParser(), (".epub",))

SUPPORTED_EXTS = tuple(sorted(_REGISTRY))

LEGACY_MAP = {
    ".doc": "旧版 Word（.doc）请先另存为 .docx",
    ".xls": "旧版 Excel（.xls）请先另存为 .xlsx",
    ".ppt": "旧版 PowerPoint（.ppt）请先另存为 .pptx",
    ".vsd": "旧版 Visio（.vsd）请先另存为 .vsdx",
    ".csv": "CSV 请用文本方式翻译或先转为 .xlsx",
    ".rtf": "RTF 请先另存为 .docx",
    ".pages": "Pages 请先导出为 .docx 或 .pdf",
}


def parser_for(path: str) -> BaseParser:
    ext = Path(path).suffix.lower()
    p = _REGISTRY.get(ext)
    if p is None:
        hint = LEGACY_MAP.get(ext)
        raise ValueError(hint or f"暂不支持该格式：{ext or '未知'}")
    return p


def is_supported(path: str) -> bool:
    return Path(path).suffix.lower() in _REGISTRY


_RANK = {
    ".docx": 0, ".xlsx": 1, ".xlsm": 9, ".pptx": 2, ".pdf": 3,
    ".vsdx": 4, ".md": 5, ".markdown": 6, ".txt": 7, ".epub": 8,
}


def _rank(ext: str) -> tuple[int, int]:
    return (_RANK.get(ext, 50), len(ext))


def describe() -> list[dict]:
    """按解析器去重，一个格式只出一个条目，并按常见程度排序。"""
    group: dict[int, dict] = {}
    for ext in SUPPORTED_EXTS:
        parser = _REGISTRY[ext]
        key = id(parser)
        if key not in group:
            group[key] = {"ext": ext, "exts": [], "label": parser.label,
                          "bilingual": parser.supports_bilingual}
        group[key]["exts"].append(ext)
    for item in group.values():
        item["exts"].sort(key=_rank)
        item["ext"] = item["exts"][0]
    return sorted(group.values(), key=lambda d: _rank(d["ext"]))
