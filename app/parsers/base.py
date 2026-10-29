"""解析器基类：统一「扫描文本槽位 → 回写」模型。

设计要点：load 与 write 都调用同一个 scan()，保证两次遍历得到的槽位顺序完全一致，
因此 Segment 只需记录槽位下标即可稳定回写，无需构造脆弱的路径表达式。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

from ..core.ir import DocumentIR, Segment, is_translatable

MODE_TARGET = "target_only"
MODE_BILINGUAL = "bilingual"


@dataclass
class Holder:
    kind: str
    text: str
    setter: Callable[[str], None] | None = None
    obj: Any = None
    extra: dict[str, Any] = field(default_factory=dict)


class BaseParser:
    ext = ""
    label = ""
    supports_bilingual = True

    # ---------- 子类实现 ----------
    def scan(self, path: str, opts: dict) -> list[Holder]:
        raise NotImplementedError

    def commit(self, path: str, out_path: str, mapping: dict[int, str],
               mode: str, opts: dict) -> dict:
        """按 mapping（槽位下标 → 译文）写回并另存为 out_path。"""
        raise NotImplementedError

    # ---------- 公共流程 ----------
    def load(self, path: str, opts: dict | None = None) -> DocumentIR:
        opts = opts or {}
        holders = self.scan(path, opts)
        ir = DocumentIR(path=path, ext=self.ext, parser=self.ext.lstrip("."))
        ir.meta["opts"] = opts
        for i, h in enumerate(holders):
            if not is_translatable(h.text):
                continue
            ir.segments.append(
                Segment(
                    sid=f"s{i}",
                    src=h.text,
                    send=str(h.extra.get("masked") or ""),
                    kind=h.kind,
                    group=str(h.extra.get("group") or ""),
                    loc=i,
                )
            )
        ir.meta["holders"] = len(holders)
        return ir

    def run_write(self, ir: DocumentIR, out_path: str, mode: str = MODE_TARGET) -> dict:
        opts = ir.meta.get("opts") or {}
        mapping: dict[int, str] = {}
        for seg in ir.segments:
            if isinstance(seg.loc, int) and (seg.tgt or "").strip():
                mapping[seg.loc] = seg.tgt
        info = self.commit(ir.path, out_path, mapping, mode, opts) or {}
        info.setdefault("overflow", [])
        info.setdefault("warnings", [])
        return info

    # ---------- 工具 ----------
    @staticmethod
    def filter_holders(holders: Iterable[Holder], opts: dict) -> list[Holder]:
        return list(holders)


def open_any(path: str, opts: dict) -> DocumentIR:
    from .registry import parser_for

    return parser_for(path).load(path, opts)
