"""AI 调整（refine）链路离线验证：本地 mock OpenAI 端点 + 真实文档。"""
from __future__ import annotations

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.core.ir import STATUS_REFINED  # noqa: E402
from app.core.pipeline import TransOptions, refine_segments, translate_document  # noqa: E402
from app.parsers.registry import parser_for  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SEEN: list[dict] = []


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        return

    def do_POST(self):  # noqa: N802
        n = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(n) or b"{}")
        SEEN.append(body)
        user = json.loads(body["messages"][-1]["content"])
        items = user.get("items") or []
        arr = []
        for it in items:
            if isinstance(it, dict):
                arr.append(f"REFINED::{it.get('cur', '')}")
            else:
                arr.append(f"EN::{it}")
        data = json.dumps(
            {"choices": [{"message": {"content": json.dumps({"t": arr}, ensure_ascii=False)}}]},
            ensure_ascii=False,
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main() -> int:
    backup = (ROOT / "data" / "settings.json")
    original = backup.read_text("utf-8") if backup.exists() else None

    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    try:
        settings.set_api_key("sk-test")
        settings.update({"engine": {"llm": {
            "base_url": f"http://127.0.0.1:{port}/v1",
            "model": "mock-refiner",
            "json_mode": True,
        }}})

        opts = TransOptions(src="zh", tgt="en", style="formal", term_sets=[], engine="public")
        src = ROOT / "samples" / "sample.docx"
        res = translate_document(str(src), opts, write=False)
        assert res.ok, res.error
        ir = res.ir
        before = [s.tgt for s in ir.segments]
        print(f"底稿完成 {len(ir.segments)} 段，示例：{before[0][:50]!r}")

        # 1) 全部段落 AI 调整
        changed = refine_segments(ir, ir.segments, "更正式一些", opts)
        after = [s.tgt for s in ir.segments]
        ok1 = changed == len(ir.segments) and all(
            t.startswith("REFINED::") for t in after if t
        )
        print(f"[全部调整] changed={changed}/{len(ir.segments)} -> {'OK' if ok1 else 'FAIL'}")

        # 2) 仅选中第 2 段
        seen_before = len(SEEN)
        target = ir.segments[1]
        changed2 = refine_segments(ir, [target], "更简洁", opts)
        body = SEEN[-1]
        user = json.loads(body["messages"][-1]["content"])
        only_one = len(user["items"]) == 1 and user["items"][0]["src"] == target.src
        print(f"[单段调整] changed={changed2} 只含1条={only_one} -> "
              f"{'OK' if changed2 == 1 and only_one else 'FAIL'}")

        # 3) 提示词检查
        sysmsg = SEEN[-1]["messages"][0]["content"]
        checks = {
            "编辑角色": "senior bilingual editor" in sysmsg,
            "指令注入": "更简洁" in sysmsg,
            "占位符规则": "[[T0]]" in sysmsg,
            "条目数": "exactly 1 strings" in sysmsg,
        }
        print("[提示词]", checks)
        ok3 = all(checks.values())

        # 4) 状态标记
        statuses = {s.status for s in ir.segments}
        ok4 = STATUS_REFINED in statuses
        print(f"[状态] {statuses} -> {'OK' if ok4 else 'FAIL'}")

        # 5) 未配置 Key 时应明确报错
        settings.set_api_key("")
        try:
            refine_segments(ir, ir.segments[:1], "测试", opts)
            print("[无 Key] 未报错 -> FAIL")
            ok5 = False
        except RuntimeError as exc:
            ok5 = "API Key" in str(exc)
            print(f"[无 Key] {str(exc)[:44]}… -> {'OK' if ok5 else 'FAIL'}")

        fails = [name for name, v in
                 (("全部", ok1), ("单段", only_one and changed2 == 1), ("提示词", ok3),
                  ("状态", ok4), ("无Key", ok5)) if not v]
        print("\n失败项:", fails or "无")
        return 1 if fails else 0
    finally:
        srv.shutdown()
        if original is not None:
            backup.write_text(original, "utf-8")
        settings.load()


if __name__ == "__main__":
    sys.exit(main())
