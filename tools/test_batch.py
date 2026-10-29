"""队列级端到端测试：八种格式一次性批量翻译。"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.api.bridge import Bridge  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples"


def main() -> int:
    mode = "bilingual" if "--bi" in sys.argv else "target_only"
    b = Bridge()
    files = [str(f) for f in sorted(SAMPLES.glob("sample.*")) if f.is_file()]
    r = b.add_files(files)
    print(f"加入队列 {r['added']} 个文件，跳过 {r['skipped']}")
    t0 = time.time()
    r2 = b.start_jobs({
        "src": "zh", "tgt": "en", "style": "general", "term_sets": ["it"],
        "mode": mode, "engine": "public", "skip_header_footer": False,
    })
    if not r2.get("ok"):
        print("启动失败:", r2)
        return 1
    deadline = time.time() + 240
    while time.time() < deadline:
        time.sleep(0.6)
        js = b.jobs()["jobs"]
        if js and all(j["status"] in ("done", "failed", "cancelled") for j in js):
            break
    ok = 0
    for j in js:
        flag = "OK " if j["status"] == "done" else "FAIL"
        ok += 1 if j["status"] == "done" else 0
        exists = Path(j["output"]).exists() if j["output"] else False
        size = Path(j["output"]).stat().st_size if exists else 0
        print(f"[{flag}] {j['name']:14s} {j['translated']:>3}/{j['segments']:<3} "
              f"{j['elapsed']:>5.1f}s  {size:>7d}B  {j['error'][:40]}")
        for w in j["warnings"][:2]:
            print(f"        警告: {w}")
    print(f"\n通过 {ok}/{len(js)}  用时 {time.time() - t0:.1f}s  模式 {mode}")
    return 0 if ok == len(js) else 1


if __name__ == "__main__":
    sys.exit(main())
