"""SQLite 翻译记忆：相同段落不重复调用 API。"""
from __future__ import annotations

import hashlib
import threading
import time
import unicodedata
from pathlib import Path

from ..paths import data_dir


def make_key(text: str, src: str, tgt: str, style: str, term_ver: str, engine: str) -> str:
    norm = unicodedata.normalize("NFKC", (text or "").strip())
    h = hashlib.sha256()
    for part in (norm, src, tgt, style, term_ver, engine):
        h.update(part.encode("utf-8"))
        h.update(b"\x1f")
    return h.hexdigest()


class TranslationMemory:
    def __init__(self, path: Path | None = None) -> None:
        import sqlite3

        self._sqlite = sqlite3
        self._lock = threading.RLock()
        self._path = path or (data_dir() / "tm.db")
        self._conn = sqlite3.connect(str(self._path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS tm ("
            " k TEXT PRIMARY KEY, src TEXT, tgt TEXT, st TEXT, tt TEXT,"
            " engine TEXT, style TEXT, ts INTEGER)"
        )
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_tm_ts ON tm(ts)")
        self._conn.commit()
        self.hits = 0
        self.misses = 0

    def get_many(self, keys: list[str]) -> dict[str, str]:
        if not keys:
            return {}
        out: dict[str, str] = {}
        with self._lock:
            for i in range(0, len(keys), 500):
                chunk = keys[i:i + 500]
                q = "SELECT k, tt FROM tm WHERE k IN (%s)" % ",".join("?" * len(chunk))
                for k, tt in self._conn.execute(q, chunk):
                    if tt:
                        out[k] = tt
        self.hits += len(out)
        self.misses += max(0, len(keys) - len(out))
        return out

    def put_many(self, rows: list[tuple[str, str, str, str, str]]) -> None:
        """rows: (key, source, target, engine, style)"""
        if not rows:
            return
        now = int(time.time())
        with self._lock:
            self._conn.executemany(
                "INSERT OR REPLACE INTO tm(k,src,tgt,st,tt,engine,style,ts) VALUES(?,?,?,?,?,?,?,?)",
                [(k, "", "", src, tgt, engine, style, now) for k, src, tgt, engine, style in rows],
            )
            self._conn.commit()

    def put(self, key: str, source: str, target: str, engine: str, style: str) -> None:
        now = int(time.time())
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO tm(k,src,tgt,st,tt,engine,style,ts) VALUES(?,?,?,?,?,?,?,?)",
                (key, "", "", source, target, engine, style, now),
            )
            self._conn.commit()

    def stats(self) -> dict:
        with self._lock:
            try:
                total = self._conn.execute("SELECT COUNT(*) FROM tm").fetchone()[0]
            except Exception:
                total = 0
        hit_total = self.hits + self.misses
        return {
            "entries": total,
            "session_hits": self.hits,
            "session_misses": self.misses,
            "hit_rate": round(self.hits / hit_total, 3) if hit_total else 0.0,
            "path": str(self._path),
        }

    def clear(self) -> int:
        with self._lock:
            n = self._conn.execute("SELECT COUNT(*) FROM tm").fetchone()[0]
            self._conn.execute("DELETE FROM tm")
            self._conn.commit()
            try:
                self._conn.execute("VACUUM")
            except Exception:
                pass
            return int(n)

    def close(self) -> None:
        with self._lock:
            try:
                self._conn.close()
            except Exception:
                pass


tm = TranslationMemory()
