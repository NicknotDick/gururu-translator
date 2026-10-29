"""打包前刷新版本号：把当前时间写进 app/_stamp.py。"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "app" / "_stamp.py"


def stamp(now: datetime | None = None) -> str:
    s = (now or datetime.now()).strftime("%y%m%d%H%M")
    TARGET.write_text(
        '"""构建时间戳（由 tools/stamp_version.py 生成，打包前自动刷新）。"""\n\n'
        f'STAMP = "{s}"\n',
        "utf-8",
    )
    return s


if __name__ == "__main__":
    s = stamp()
    print(f"版本号：Ver.{s}")
