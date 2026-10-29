"""统一中间表示：所有格式解析后都归一为 Segment 列表。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

STATUS_PENDING = "pending"
STATUS_RUNNING = "translating"
STATUS_DONE = "done"
STATUS_EDITED = "edited"
STATUS_REFINED = "refined"
STATUS_FAILED = "failed"
STATUS_OVERFLOW = "overflow"
STATUS_TERM = "term_violation"
STATUS_SKIPPED = "skipped"


@dataclass
class Segment:
    sid: str                      # 稳定定位符，如 "body.p[12]" / "Sheet1!B7"
    src: str = ""
    tgt: str = ""
    status: str = STATUS_PENDING
    kind: str = "para"            # para|heading|cell|shape|code|meta|title
    group: str = ""               # 所属分组（幻灯片页 / 工作表 / PDF 页），用于全文预览
    loc: Any = None               # 解析器内部定位数据（不跨界序列化）
    note: str = ""
    send: str = ""                # 实际送引擎的文本（含保护占位符）；为空则用 src

    @property
    def engine_text(self) -> str:
        return self.send or self.src

    def to_dict(self) -> dict[str, Any]:
        return {
            "sid": self.sid,
            "src": self.src,
            "tgt": self.tgt,
            "status": self.status,
            "kind": self.kind,
            "group": self.group,
            "note": self.note,
        }


@dataclass
class DocumentIR:
    path: str
    ext: str
    segments: list[Segment] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)
    parser: str = ""
    warnings: list[str] = field(default_factory=list)
    overflow: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.segments)

    def texts(self) -> list[str]:
        return [s.src for s in self.segments]

    def by_sid(self) -> dict[str, Segment]:
        return {s.sid: s for s in self.segments}

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "ext": self.ext,
            "parser": self.parser,
            "meta": self.meta,
            "warnings": self.warnings,
            "overflow": self.overflow,
            "segments": [s.to_dict() for s in self.segments],
        }


def has_letters(text: str) -> bool:
    return any(ch.isalpha() for ch in text)


def is_translatable(text: str, min_len: int = 2) -> bool:
    """过滤纯数字、纯符号、纯代码标识等无需翻译的片段。"""
    if not text:
        return False
    stripped = text.strip()
    if len(stripped) < min_len:
        return False
    if not has_letters(stripped):
        return False
    # 形如 3.14 / 2024-01-01 / v1.2.3 / 100% / #FF00AA 的纯数值或代号
    core = stripped.strip("%#()（）[]【】 ")
    if not has_letters(core):
        return False
    return True
