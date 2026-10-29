"""查词：内置离线词典（ECDICT 裁剪）+ 在线词典（有道 / Free Dictionary）。"""
from __future__ import annotations

import base64
import re
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

from ..engines.base import EngineError, http
from ..paths import resource

DB_NAME = "dict.sqlite3"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

_SUFFIX = (
    ("iest", "y"), ("ier", "y"), ("ies", "y"), ("ied", "y"),
    ("ing", ""), ("est", ""), ("ed", ""), ("es", ""), ("er", ""),
    ("ly", ""), ("s", ""),
)


def _connect() -> sqlite3.Connection | None:
    path = resource(DB_NAME)
    if not path.exists():
        return None
    try:
        return sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    except Exception:
        return None


def _candidates(word: str) -> list[str]:
    w = word.strip().lower()
    out = [w]
    for suf, rep in _SUFFIX:
        if len(w) > len(suf) + 2 and w.endswith(suf):
            stem = w[: -len(suf)] + rep
            out.append(stem)
            if len(stem) > 3 and stem[-1] == stem[-2]:
                out.append(stem[:-1])
    return out


def _to_entry(row) -> dict:
    (word, phonetic, trans, pos, tag, collins, oxford, frq, bnc, exchange) = row
    forms = []
    for part in (exchange or "").split("/"):
        if ":" in part:
            k, v = part.split(":", 1)
            if v.strip():
                forms.append(f"{k.strip()}:{v.strip()}")
    raw_trans = (trans or "").replace("\\n", "\n")
    return {
        "word": word,
        "phonetic": phonetic or "",
        "senses": [ln.strip() for ln in raw_trans.split("\n") if ln.strip()][:8],
        "pos": pos or "",
        "tag": tag or "",
        "collins": collins or 0,
        "oxford": oxford or 0,
        "frq": frq or 0,
        "bnc": bnc or 0,
        "forms": forms[:6],
    }


def lookup_local(word: str) -> dict:
    """离线词典查询：精确命中 → 词形还原 → 前缀联想。"""
    w = (word or "").strip()
    if not w:
        return {"ok": False, "error": "empty"}
    conn = _connect()
    if conn is None:
        return {"ok": False, "error": "no-dict"}
    try:
        cols = "word, phonetic, trans, pos, tag, collins, oxford, frq, bnc, exchange"
        row = None
        matched = ""
        for cand in _candidates(w):
            row = conn.execute(
                f"SELECT {cols} FROM entries WHERE lower = ?", (cand,)
            ).fetchone()
            if row:
                matched = cand
                break
        suggestions = []
        if row is None:
            key = w.lower()
            if " " in key:
                key = key.split()[0]
            suggestions = [
                r[0] for r in conn.execute(
                    "SELECT word FROM entries WHERE lower LIKE ? ORDER BY bnc LIMIT 8",
                    (key + "%",),
                ).fetchall()
            ]
        return {
            "ok": True,
            "hit": row is not None,
            "query": w,
            "matched": matched,
            "entry": _to_entry(row) if row else None,
            "suggestions": suggestions,
        }
    finally:
        conn.close()


def _brief(trans: str, n: int = 34) -> str:
    first = (trans or "").replace("\\n", "\n").split("\n")[0].strip()
    return first[:n]


def _distance(a: str, b: str, cap: int = 3) -> int:
    """Levenshtein，提前剪枝。"""
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        best = i
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
            best = min(best, cur[j])
        if best > cap:
            return cap + 1
        prev = cur
    return prev[-1]


def suggest_local(text: str, limit: int = 8) -> list[dict]:
    """本地联想：精确 → 前缀 → 包含 → 编辑距离纠错。"""
    w = (text or "").strip().lower()
    if not w:
        return []
    conn = _connect()
    if conn is None:
        return []
    out: list[dict] = []
    seen: set[str] = set()

    def push(rows) -> None:
        for word, trans in rows:
            key = word.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append({"word": word, "brief": _brief(trans)})

    try:
        push(conn.execute(
            "SELECT word, trans FROM entries WHERE lower = ? LIMIT 1", (w,)).fetchall())
        push(conn.execute(
            "SELECT word, trans FROM entries WHERE lower LIKE ? "
            "ORDER BY CASE WHEN bnc > 0 THEN 0 ELSE 1 END, bnc, length(lower) LIMIT ?",
            (w + "%", limit)).fetchall())
        if len(out) < limit:
            push(conn.execute(
                "SELECT word, trans FROM entries WHERE lower LIKE ? "
                "ORDER BY length(lower), CASE WHEN bnc > 0 THEN bnc ELSE 999999 END LIMIT ?",
                ("%" + w + "%", limit)).fetchall())
        if len(out) < limit and len(w) >= 4:
            pool = conn.execute(
                "SELECT word, trans, lower, bnc FROM entries "
                "WHERE lower LIKE ? AND length(lower) BETWEEN ? AND ? LIMIT 4000",
                (w[0] + "%", len(w) - 2, len(w) + 2),
            ).fetchall()
            scored = []
            for word, trans, low, bnc in pool:
                d = _distance(w, low)
                if d <= 2:
                    scored.append((d, 0 if bnc > 0 else 1, bnc, len(word), word, trans))
            scored.sort()
            push([(it[4], it[5]) for it in scored[:limit]])
        return out[:limit]
    finally:
        conn.close()


def suggest_online(text: str, limit: int = 8) -> list[dict]:
    """有道联想词，兼作拼写纠错。"""
    w = (text or "").strip()
    if not w:
        return []
    try:
        r = http().get(
            "https://dict.youdao.com/suggest",
            params={"q": w, "num": limit, "doctype": "json"},
            headers={"User-Agent": UA},
            timeout=6,
        )
        if r.status_code >= 400:
            return []
        data = r.json()
        entries = ((data.get("data") or {}).get("entries") or [])[:limit]
        return [{"word": str(e.get("entry") or "").strip(),
                 "brief": str(e.get("explain") or "").strip()[:34]} for e in entries
                if e.get("entry")]
    except Exception:
        return []


def fetch_image(url: str, max_bytes: int = 2_500_000) -> dict:
    """代理下载配图，返回 data URI 供前端内联显示。"""
    if not (url or "").startswith("http"):
        return {"ok": False}
    try:
        r = http().get(url, headers={"User-Agent": UA, "Referer": "https://dict.youdao.com/"},
                       timeout=12, stream=True)
        if r.status_code >= 400:
            return {"ok": False}
        ctype = (r.headers.get("Content-Type") or "image/jpeg").split(";")[0]
        if not ctype.startswith("image/"):
            return {"ok": False}
        buf = b""
        for chunk in r.iter_content(65536):
            buf += chunk
            if len(buf) > max_bytes:
                return {"ok": False}
        if not buf:
            return {"ok": False}
        import base64

        return {"ok": True, "data": f"data:{ctype};base64," + base64.b64encode(buf).decode()}
    except Exception:
        return {"ok": False}


# ---------------- 在线词典 ----------------
def _youdao(word: str, timeout: int = 9) -> dict | None:
    url = "https://dict.youdao.com/jsonapi?q=" + quote(word)
    r = http().get(url, headers={"User-Agent": UA}, timeout=timeout)
    if r.status_code >= 400:
        return None
    data = r.json()
    ec = data.get("ec") or {}
    node = ec
    if isinstance(ec.get("word"), list) and ec["word"]:
        node = ec["word"][0]
        if isinstance(node.get("trs"), list) is False and ec.get("trs"):
            node = ec

    phonetic = ""
    for key in ("usphone", "ukphone", "phone"):
        if isinstance(node, dict) and node.get(key):
            phonetic = str(node[key])
            break
    if not phonetic:
        simple = data.get("simple") or {}
        for key in ("usphone", "ukphone"):
            if simple.get(key):
                phonetic = str(simple[key])
                break

    defs: list[str] = []

    def walk(obj) -> None:
        if len(defs) >= 14:
            return
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "trs" or k == "tr":
                    walk(v)
            item = obj.get("l")
            if isinstance(item, dict):
                val = item.get("i")
                if isinstance(val, str):
                    defs.append(val)
                elif isinstance(val, list):
                    for x in val:
                        if isinstance(x, str):
                            defs.append(x)
        elif isinstance(obj, list):
            for x in obj:
                walk(x)

    walk(node.get("trs") if isinstance(node, dict) else None)
    if not defs:
        return None

    seen, uniq = set(), []
    for d in defs:
        d = d.strip()
        if d and d not in seen:
            seen.add(d)
            uniq.append(d)

    # 百科：维基摘要 + 配图（有道接口自带，无需额外数据源）
    summary = ""
    for item in ((data.get("wikipedia_digest") or {}).get("summarys") or []):
        text = (item.get("summary") or "").strip()
        if text:
            summary = text
            break
    images = []
    for item in ((data.get("pic_dict") or {}).get("pic") or []):
        url = (item.get("image") or "").strip()
        if url.startswith("http"):
            images.append(url)
    enc = None
    if summary or images:
        enc = {
            "summary": summary[:1200],
            "summary_lang": "zh" if re.search(r"[\u4e00-\u9fff]", summary[:80]) else "en",
            "images": images[:3],
            "source": "wikipedia/youdao",
        }
    return {"name": "youdao", "phonetic": phonetic, "senses": uniq[:12], "encyclopedia": enc}


def _free_dictionary(word: str, timeout: int = 9) -> dict | None:
    url = "https://api.dictionaryapi.dev/api/v2/entries/en/" + quote(word)
    r = http().get(url, headers={"User-Agent": UA}, timeout=timeout)
    if r.status_code >= 400:
        return None
    data = r.json()
    if not isinstance(data, list) or not data:
        return None
    first = data[0]
    phonetic = ""
    for p in first.get("phonetics") or []:
        if p.get("text"):
            phonetic = p["text"]
            break
    groups = []
    for m in (first.get("meanings") or [])[:4]:
        pos = m.get("partOfSpeech") or ""
        defs = []
        for d in (m.get("definitions") or [])[:4]:
            text = (d.get("definition") or "").strip()
            if text:
                defs.append(text)
        if defs:
            groups.append({"pos": pos, "defs": defs})
    if not groups:
        return None
    return {"name": "freedict", "phonetic": phonetic, "groups": groups}


class _Timeout(Exception):
    pass


def lookup_online(word: str, timeout: int = 9) -> dict:
    """并行请求多个在线词典，单个失败不影响其它。"""
    w = (word or "").strip()
    if not w:
        return {"ok": False, "sources": []}
    jobs = {"youdao": _youdao, "freedict": _free_dictionary}
    out = []
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        futures = {k: pool.submit(fn, w, timeout) for k, fn in jobs.items()}
        for key, fut in futures.items():
            try:
                res = fut.result(timeout=timeout + 2)
            except Exception:
                res = None
            if res:
                out.append(res)
    return {"ok": True, "sources": out}
