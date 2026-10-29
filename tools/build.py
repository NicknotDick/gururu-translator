"""一键构建：刷新版本号 → 生成图标 → 内联前端 → PyInstaller 打包。"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable


def run(*args: str) -> None:
    print(f"\n$ {' '.join(args)}", flush=True)
    subprocess.run(args, cwd=str(ROOT), check=True)


def main() -> int:
    t0 = time.time()
    dict_db = ROOT / "resources" / "dict.sqlite3"
    if not dict_db.exists():
        src = ROOT / "build" / "dict" / "ecdict.csv"
        if src.exists():
            run(PY, "tools/build_dict.py")
        else:
            print("警告：缺少 resources/dict.sqlite3 与词库源文件，离线查词将不可用")

    run(PY, "tools/stamp_version.py")
    run(PY, "tools/make_assets.py")
    # 出厂配置：把当前设置固化进 EXE，新机器首次打开即为配置好的状态
    if (ROOT / "resources" / "default_settings.json").exists() or \
            (ROOT / "data" / "settings.json").exists():
        run(PY, "tools/make_factory_settings.py")
    run(PY, "tools/embed_ui.py")
    run(PY, "-m", "PyInstaller", "build/app.spec", "--noconfirm", "--clean",
        "--distpath", "dist", "--workpath", "build/work")

    import importlib

    sys.path.insert(0, str(ROOT))
    app_name = importlib.import_module("app.version").APP_NAME
    exe = ROOT / "dist" / f"{app_name}.exe"
    if exe.exists():
        size = exe.stat().st_size / 1048576
        print(f"\n构建完成：{exe}  {size:.0f} MB  用时 {time.time() - t0:.0f}s")
        return 0
    print("\n构建失败：未找到产物")
    return 1


if __name__ == "__main__":
    sys.exit(main())
