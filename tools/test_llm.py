"""大模型通道离线验证：本地 mock 一个 OpenAI 兼容端点，检查请求构造与响应解析。"""
from __future__ import annotations

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.engines.openai_compat import OpenAIEngine  # noqa: E402

MODE = {"v": "ok"}
SEEN: list[dict] = []


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # noqa: D401
        return

    def do_POST(self):  # noqa: N802
        n = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(n) or b"{}")
        SEEN.append(body)
        if MODE["v"] == "401":
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'{"error":"bad key"}')
            return
        user = json.loads(body["messages"][-1]["content"])
        items = user["items"]
        arr = [f"EN:{x}" for x in items]
        if MODE["v"] == "short" and len(items) > 1:
            arr = arr[:-1]  # 故意少一条，触发二分重试
        out = json.dumps({"t": arr}, ensure_ascii=False)
        if MODE["v"] == "fence":
            out = f"```json\n{out}\n```"
        payload = {"choices": [{"message": {"role": "assistant", "content": out}}]}
        data = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main() -> int:
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    cfg = {"base_url": f"http://127.0.0.1:{port}/v1", "model": "mock-1",
           "temperature": 0.2, "json_mode": True}
    eng = OpenAIEngine(cfg, "sk-test")
    ok, msg = eng.available()
    print("available:", ok, msg)

    fails = 0
    texts = ["第一段中文。", "第二段中文。", "Third item."]

    for mode, label in (("ok", "正常"),
                        ("fence", "围栏 JSON"),
                        ("noformat", "无 response_format"),
                        ("short", "条数不足二分重试"),
                        ("401", "鉴权失败")):
        MODE["v"] = mode
        try:
            out = eng.translate(texts, "zh", "en", "formal", 10)
            good = len(out) == len(texts) and out[0] == "EN:" + texts[0]
            print(f"[{label}] -> {out}  {'OK' if good else 'MISMATCH'}")
            fails += 0 if good else 1
        except Exception as exc:  # noqa: BLE001
            expect = mode == "401"
            print(f"[{label}] -> 异常 {type(exc).__name__}: {exc}  {'OK' if expect else 'FAIL'}")
            fails += 0 if expect else 1

    # 请求体检查：风格与 JSON 模式是否注入
    MODE["v"] = "ok"
    SEEN.clear()
    eng.translate(["测试"], "zh", "en", "formal", 10)
    body = SEEN[-1]
    sysmsg = body["messages"][0]["content"]
    print("model:", body.get("model"), "| json_mode:", body.get("response_format"))
    print("含正式语体提示:", "formal written register" in sysmsg)
    print("含占位符规则:", "[[T0]]" in sysmsg)
    print("用户消息为 JSON:", body["messages"][-1]["content"])

    srv.shutdown()
    print("\n失败项:", fails)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
