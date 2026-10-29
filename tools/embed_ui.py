"""把前端资源内联成 Python 模块，避免打包后 _MEIPASS 路径问题。"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UI = ROOT / "app" / "ui"
TARGET = ROOT / "app" / "ui_bundle.py"


def build() -> Path:
    html = (UI / "index.html").read_text("utf-8")
    css = (UI / "app.css").read_text("utf-8")
    js = (UI / "app.js").read_text("utf-8")
    html = html.replace('<link rel="stylesheet" href="app.css">', f"<style>\n{css}\n</style>")
    html = html.replace('<script src="app.js"></script>', f"<script>\n{js}\n</script>")
    body = (
        '"""自动生成，请勿手工编辑。运行 python tools/embed_ui.py 重新生成。"""\n'
        f"HTML = {html!r}\n"
    )
    TARGET.write_text(body, "utf-8")
    return TARGET


if __name__ == "__main__":
    p = build()
    print(f"已生成 {p.relative_to(ROOT)}  ({p.stat().st_size} bytes)")
