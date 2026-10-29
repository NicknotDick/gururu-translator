"""Markdown / 纯文本解析器：保护代码、链接、URL 等不应翻译的片段。"""
from __future__ import annotations

import re
from typing import Any

from ..core.ir import is_translatable
from .base import MODE_BILINGUAL, BaseParser, Holder

MD_PREFIX = re.compile(
    r"^(\s*(?:(?:#{1,6})\s+|[-*+]\s+|\d{1,3}[.)]\s+|>\s?|\[[ xX]\]\s+)*)"
)
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")

MD_PATTERNS = [
    r"`[^`\n]*`",
    r"!\[[^\]\n]*\]\([^)\n]*\)",
    r"\[[^\]\n]*\]\([^)\n]*\)",
    r"<[^>\n]{1,300}>",
    r"https?://[^\s<>)\]]+",
    r"\$\$?[^$\n]{1,300}\$\$?",
    r"\{\{[^}\n]{1,80}\}\}",
]
TXT_PATTERNS = [
    r"https?://[^\s<>)\]]+",
    r"[\w.+-]+@[\w-]+\.[\w.]+",
    r"\\[a-zA-Z]+\{[^}\n]{0,80}\}",
]


def _rx(patterns: list[str]) -> re.Pattern:
    return re.compile("|".join(f"({p})" for p in patterns))


def protect(text: str, patterns: list[str]) -> tuple[str, list[str]]:
    """把受保护片段替换为 [[K0]] 占位符（实测公共引擎可保真携带）。"""
    rx = _rx(patterns)
    spans: list[str] = []
    out: list[str] = []
    last = 0
    for m in rx.finditer(text):
        out.append(text[last:m.start()])
        spans.append(m.group(0))
        out.append(f"[[K{len(spans) - 1}]]")
        last = m.end()
    out.append(text[last:])
    return "".join(out), spans


TOKEN = re.compile(r"\[\[\s*K(\d+)\s*\]\]")


def restore(text: str, spans: list[str]) -> str:
    if not spans:
        return TOKEN.sub("", text)
    found: set[int] = set()

    def _rep(m: re.Match) -> str:
        i = int(m.group(1))
        if 0 <= i < len(spans):
            found.add(i)
            return spans[i]
        return ""

    out = TOKEN.sub(_rep, text or "")
    missing = [i for i in range(len(spans)) if i not in found]
    if missing:
        # 引擎吞掉占位符时，把丢失片段补在行尾，保证内容不丢
        out = out + "".join(spans[i] for i in missing)
    return out


def _join_lines(parts: list[str]) -> str:
    out = ""
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if not out:
            out = p
        elif out[-1].isascii() and p[0].isascii():
            out += " " + p
        else:
            out += p
    return out


class _LineParser(BaseParser):
    patterns: list[str] = []
    use_md_prefix = False
    join_soft_wrap = False

    def _detect_eol(self, raw: str) -> str:
        return "\r\n" if "\r\n" in raw else "\n"

    def _read(self, path: str) -> tuple[list[str], str]:
        raw = open(path, "rb").read()
        eol = self._detect_eol(raw.decode("utf-8", errors="replace"))
        text = raw.decode("utf-8-sig", errors="replace")
        return text.replace("\r\n", "\n").replace("\r", "\n").split("\n"), eol

    # ---------- 扫描 ----------
    def scan(self, path: str, opts: dict) -> list[Holder]:
        lines, _eol = self._read(path)
        holders: list[Holder] = []
        in_fence = False
        fence_mark = ""
        front = False
        i = 0
        n = len(lines)

        if lines and lines[0].strip() == "---":
            # YAML front-matter
            for j in range(1, min(n, 400)):
                if lines[j].strip() in ("---", "..."):
                    front = True
                    i = j + 1
                    break

        while i < n:
            line = lines[i]
            m = FENCE.match(line)
            if m:
                mark = m.group(1)[0]
                if not in_fence:
                    in_fence = True
                    fence_mark = mark
                elif mark == fence_mark:
                    in_fence = False
                i += 1
                continue
            if in_fence:
                i += 1
                continue

            if not line.strip():
                i += 1
                continue

            if self.join_soft_wrap:
                group = [line]
                j = i + 1
                while j < n and lines[j].strip():
                    nxt = lines[j].strip()
                    if FENCE.match(lines[j]):
                        break
                    group.append(lines[j])
                    j += 1
                body = _join_lines(group)
                if is_translatable(body):
                    masked, spans = protect(body, self.patterns)
                    holders.append(Holder(
                        kind="para",
                        text=body,
                        obj=None,
                        extra={"start": i, "end": j - 1, "prefix": "", "masked": masked,
                               "spans": spans},
                    ))
                i = j
                continue

            prefix = ""
            body = line
            if self.use_md_prefix:
                pm = MD_PREFIX.match(line)
                if pm:
                    prefix = pm.group(1)
                    body = line[len(prefix):]
            if not body.strip() or not is_translatable(body):
                i += 1
                continue
            masked, spans = protect(body, self.patterns)
            holders.append(Holder(
                kind="heading" if prefix.strip().startswith("#") else "para",
                text=body,
                obj=None,
                extra={"start": i, "end": i, "prefix": prefix, "masked": masked, "spans": spans},
            ))
            i += 1
        return holders

    # ---------- 回写 ----------
    def commit(self, path: str, out_path: str, mapping: dict[int, str],
               mode: str, opts: dict) -> dict:
        lines, eol = self._read(path)
        holders = self.scan(path, opts)
        ops: list[tuple[int, int, list[str]]] = []
        for i, h in enumerate(holders):
            tgt = mapping.get(i)
            if not tgt:
                continue
            spans = h.extra.get("spans") or []
            clean = restore(tgt, spans).strip()
            start = int(h.extra["start"])
            end = int(h.extra["end"])
            prefix = str(h.extra.get("prefix") or "")
            new_line = prefix + clean
            if mode == MODE_BILINGUAL:
                rep = lines[start:end + 1] + [("> " + clean if self.use_md_prefix else clean)]
            else:
                rep = [new_line]
            ops.append((start, end, rep))
        for start, end, rep in sorted(ops, key=lambda x: x[0], reverse=True):
            lines[start:end + 1] = rep
        data = eol.join(lines)
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            f.write(data)
        return {}


class MarkdownParser(_LineParser):
    ext = ".md"
    label = "Markdown"
    patterns = MD_PATTERNS
    use_md_prefix = True
    join_soft_wrap = False


class PlainTextParser(_LineParser):
    ext = ".txt"
    label = "纯文本"
    patterns = TXT_PATTERNS
    use_md_prefix = False
    join_soft_wrap = True
