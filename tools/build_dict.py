"""从 ECDICT 全量词库裁剪出高频子集，生成内置离线词典（SQLite）。

用法：python tools/build_dict.py [--limit 30000]
数据来源：https://github.com/skywind3000/ECDICT （MIT）
"""
from __future__ import annotations

import argparse
import csv
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "build" / "dict" / "ecdict.csv"
OUT = ROOT / "resources" / "dict.sqlite3"

WORD_RE = re.compile(r"^[A-Za-z][A-Za-z\-'’ .]{0,38}$")


def rank(frq: int, bnc: int) -> int:
    vals = [v for v in (frq, bnc) if v and v > 0]
    return min(vals) if vals else 10 ** 9


def build(limit: int) -> int:
    if not SRC.exists():
        print(f"缺少词库源文件：{SRC}", file=sys.stderr)
        return 1

    rows = []
    with SRC.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            word = (row.get("word") or "").strip()
            trans = (row.get("translation") or "").strip()
            if not word or not trans or not WORD_RE.match(word):
                continue
            try:
                frq = int(row.get("frq") or 0)
            except ValueError:
                frq = 0
            try:
                bnc = int(row.get("bnc") or 0)
            except ValueError:
                bnc = 0
            rows.append({
                "word": word,
                "lower": word.lower(),
                "phonetic": (row.get("phonetic") or "").strip()[:80],
                "trans": trans[:600],
                "pos": (row.get("pos") or "").strip()[:120],
                "tag": (row.get("tag") or "").strip()[:80],
                "collins": int(row.get("collins") or 0),
                "oxford": int(row.get("oxford") or 0),
                "frq": frq,
                "bnc": bnc,
                "exchange": (row.get("exchange") or "").strip()[:200],
            })

    rows.sort(key=lambda r: (rank(r["frq"], r["bnc"]), len(r["word"])))
    rows = rows[:limit]

    if OUT.exists():
        OUT.unlink()
    conn = sqlite3.connect(OUT)
    conn.execute(
        "CREATE TABLE entries ("
        "lower TEXT PRIMARY KEY, word TEXT, phonetic TEXT, trans TEXT,"
        "pos TEXT, tag TEXT, collins INTEGER, oxford INTEGER,"
        "frq INTEGER, bnc INTEGER, exchange TEXT)"
    )
    conn.executemany(
        "INSERT OR REPLACE INTO entries VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [(r["lower"], r["word"], r["phonetic"], r["trans"], r["pos"], r["tag"],
          r["collins"], r["oxford"], r["frq"], r["bnc"], r["exchange"]) for r in rows],
    )
    conn.commit()
    conn.execute("VACUUM")
    conn.close()
    size = OUT.stat().st_size / 1048576
    print(f"已生成 {OUT}  词条 {len(rows)}  体积 {size:.1f} MB")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=30000)
    sys.exit(build(ap.parse_args().limit))
