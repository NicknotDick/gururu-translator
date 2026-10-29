"""术语库：内置预置 + 用户自定义，支持术语强制锁定（占位符法）。"""
from __future__ import annotations

import hashlib
import json
import re
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from ..paths import data_dir, resource

USER_TERMS_FILE = "terms.json"
PLACEHOLDER_RE = re.compile(r"\[\[\s*T(\d+)\s*\]\]", re.IGNORECASE)


@dataclass
class TermEntry:
    s: str
    t: str
    a: str
    b: str

    def to_dict(self) -> dict[str, str]:
        return {"s": self.s, "t": self.t, "a": self.a, "b": self.b}


@dataclass
class TermSet:
    id: str
    name: str
    terms: list[TermEntry] = field(default_factory=list)
    builtin: bool = True
    name_en: str = ""

    def display_name(self, lang: str = "zh") -> str:
        return (self.name_en or self.name) if lang == "en" else self.name

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "builtin": self.builtin,
            "count": len(self.terms),
            "terms": [t.to_dict() for t in self.terms],
        }


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text("utf-8"))
    except Exception:
        return {}


def _parse_sets(raw: dict, builtin: bool) -> list[TermSet]:
    out: list[TermSet] = []
    for item in raw.get("sets", []) or []:
        try:
            terms = [
                TermEntry(str(t["s"]), str(t["t"]), str(t["a"]), str(t["b"]))
                for t in item.get("terms", [])
                if t.get("a") and t.get("b")
            ]
            out.append(TermSet(
                str(item["id"]), str(item.get("name") or item["id"]), terms, builtin,
                str(item.get("name_en") or item.get("name") or item["id"]),
            ))
        except Exception:
            continue
    return out


class TermBook:
    """术语库集合与方向化索引。"""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._builtin: list[TermSet] = []
        self._user: list[TermSet] = []
        self.reload()

    def reload(self) -> None:
        with self._lock:
            self._builtin = _parse_sets(_load_json(resource("terms", "default.json")), True)
            user_path = data_dir() / USER_TERMS_FILE
            self._user = _parse_sets(_load_json(user_path), False) if user_path.exists() else []

    def sets(self) -> list[TermSet]:
        with self._lock:
            return self._builtin + self._user

    def summary(self) -> list[dict]:
        return [
            {"id": s.id, "name": s.name, "name_en": s.name_en or s.name,
             "builtin": s.builtin, "count": len(s.terms)}
            for s in self.sets()
        ]

    def get(self, set_id: str) -> TermSet | None:
        for s in self.sets():
            if s.id == set_id:
                return s
        return None

    # ---------- 用户术语库维护 ----------
    def _save_user(self) -> None:
        payload = {"version": 1, "sets": [
            {"id": s.id, "name": s.name, "terms": [t.to_dict() for t in s.terms]}
            for s in self._user
        ]}
        (data_dir() / USER_TERMS_FILE).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), "utf-8"
        )

    def create_set(self, name: str) -> str:
        with self._lock:
            base = "user_" + re.sub(r"\W+", "", str(abs(hash(name))))[:8]
            sid = base
            i = 2
            while self.get(sid):
                sid = f"{base}{i}"
                i += 1
            self._user.append(TermSet(sid, name, [], False))
            self._save_user()
            return sid

    def delete_set(self, set_id: str) -> bool:
        with self._lock:
            before = len(self._user)
            self._user = [s for s in self._user if s.id != set_id]
            changed = len(self._user) != before
            if changed:
                self._save_user()
            return changed

    def upsert_terms(self, set_id: str, rows: Iterable[dict]) -> int:
        with self._lock:
            target = None
            for s in self._user:
                if s.id == set_id:
                    target = s
            if target is None:
                raise KeyError(f"术语库不存在或为内置库：{set_id}")
            existing = {(t.a, t.b) for t in target.terms}
            added = 0
            for r in rows:
                a = str(r.get("a") or "").strip()
                b = str(r.get("b") or "").strip()
                if not a or not b or (a, b) in existing:
                    continue
                target.terms.append(TermEntry(str(r.get("s") or "zh"), str(r.get("t") or "en"), a, b))
                existing.add((a, b))
                added += 1
            if added:
                self._save_user()
            return added

    def remove_term(self, set_id: str, src_text: str) -> bool:
        with self._lock:
            for s in self._user:
                if s.id == set_id:
                    before = len(s.terms)
                    s.terms = [t for t in s.terms if t.a != src_text]
                    if len(s.terms) != before:
                        self._save_user()
                        return True
            return False

    def import_file(self, set_id: str, path: str) -> tuple[int, str]:
        """导入 CSV/Excel 术语表。列序：源词, 译词[, 源语言, 目标语言]。"""
        p = Path(path)
        rows: list[dict] = []
        try:
            if p.suffix.lower() in (".xlsx", ".xlsm"):
                import openpyxl

                wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
                ws = wb.active
                for i, row in enumerate(ws.iter_rows(values_only=True)):
                    if i == 0:
                        continue
                    if row and len(row) >= 2 and row[0] and row[1]:
                        rows.append({
                            "a": str(row[0]).strip(),
                            "b": str(row[1]).strip(),
                            "s": str(row[2]).strip() if len(row) > 2 and row[2] else "zh",
                            "t": str(row[3]).strip() if len(row) > 3 and row[3] else "en",
                        })
                wb.close()
            else:
                import csv

                text = p.read_text("utf-8-sig", errors="replace")
                for i, row in enumerate(csv.reader(text.splitlines())):
                    if i == 0:
                        continue
                    if len(row) >= 2 and row[0].strip() and row[1].strip():
                        rows.append({
                            "a": row[0].strip(),
                            "b": row[1].strip(),
                            "s": row[2].strip() if len(row) > 2 and row[2].strip() else "zh",
                            "t": row[3].strip() if len(row) > 3 and row[3].strip() else "en",
                        })
        except Exception as exc:  # noqa: BLE001
            return 0, f"读取失败：{exc}"
        n = self.upsert_terms(set_id, rows)
        return n, ""


class Glossary:
    """面向单次翻译任务的只读术语索引。"""

    def __init__(self, mapping: dict[str, str], set_ids: list[str]) -> None:
        self.mapping = {k: v for k, v in mapping.items() if k and v}
        self.set_ids = list(set_ids)
        keys = sorted(self.mapping, key=len, reverse=True)[:4000]
        self._keys = keys
        self._rx = None
        if keys:
            parts = []
            for k in keys:
                esc = re.escape(k)
                if k[0].isascii() and k[0].isalnum():
                    esc = r"(?<![A-Za-z0-9_])" + esc
                if k[-1].isascii() and k[-1].isalnum():
                    esc += r"(?![A-Za-z0-9_])"
                parts.append(esc)
            try:
                self._rx = re.compile("|".join(parts), re.IGNORECASE)
            except re.error:
                self._rx = None

    @property
    def empty(self) -> bool:
        return not self.mapping

    def version(self) -> str:
        h = hashlib.sha256()
        for k in sorted(self.mapping):
            h.update(k.encode("utf-8"))
            h.update(b"\x00")
            h.update(self.mapping[k].encode("utf-8"))
            h.update(b"\x01")
        return h.hexdigest()[:16]

    def hits(self, text: str) -> list[tuple[int, int, str, str]]:
        if not text or self._rx is None:
            return []
        out = []
        for m in self._rx.finditer(text):
            src = m.group(0)
            tgt = self.mapping.get(src)
            if tgt is None:
                for k, v in self.mapping.items():
                    if k.lower() == src.lower():
                        tgt = v
                        break
            if tgt:
                out.append((m.start(), m.end(), src, tgt))
        return out

    def mask(self, text: str) -> tuple[str, list[tuple[str, str]]]:
        """把命中的术语替换为 [[T0]] 占位符，返回 (遮蔽文本, [(占位符, 目标译法)])。"""
        hits = self.hits(text)
        if not hits:
            return text, []
        out: list[str] = []
        tokens: list[tuple[str, str]] = []
        last = 0
        for start, end, src, tgt in hits:
            if start < last:
                continue
            ph = f"[[T{len(tokens)}]]"
            out.append(text[last:start])
            out.append(ph)
            tokens.append((ph, tgt))
            last = end
        out.append(text[last:])
        return "".join(out), tokens

    @staticmethod
    def unmask(text: str, tokens: list[tuple[str, str]], pad: bool = False) -> str:
        """把占位符还原为固定译法。

        pad=True 用于空格分隔的目标语言（英/法/德等）：占位符两侧补空格再压缩，
        避免出现 "databasecache" 这类粘连。
        """
        src = text or ""
        if not tokens:
            return PLACEHOLDER_RE.sub("", src)

        mapping = {i: tgt for i, (_ph, tgt) in enumerate(tokens)}

        def _rep(m: re.Match) -> str:
            tgt = mapping.get(int(m.group(1)))
            if tgt is None:
                return ""
            return f" {tgt} " if pad else tgt

        out = PLACEHOLDER_RE.sub(_rep, src)
        if pad:
            out = re.sub(r"[ \t]{2,}", " ", out)
            out = re.sub(r"\s+([,.;:!?%)\]])", r"\1", out)
            out = re.sub(r"([(\[])\s+", r"\1", out)
            out = out.strip()
        return out

    @staticmethod
    def leftovers(text: str) -> int:
        return len(PLACEHOLDER_RE.findall(text or ""))


def build_glossary(book: TermBook, src: str, tgt: str, set_ids: list[str]) -> Glossary:
    mapping: dict[str, str] = {}
    wanted = set(set_ids or [])
    for ts in book.sets():
        if ts.id not in wanted:
            continue
        for t in ts.terms:
            if t.s == src and t.t == tgt:
                mapping.setdefault(t.a, t.b)
            elif t.s == tgt and t.t == src:
                mapping.setdefault(t.b, t.a)
    return Glossary(mapping, list(set_ids or []))


termbook = TermBook()
