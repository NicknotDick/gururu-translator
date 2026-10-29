"""运行时路径解析。绿色版语义：配置与缓存全部落在程序所在目录。"""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "文档翻译"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def app_dir() -> Path:
    """程序根目录。打包后为 EXE 所在目录，开发时为项目根目录。"""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def resource_dir() -> Path:
    """只读资源目录（打包后位于 PyInstaller 解压目录）。"""
    if is_frozen():
        base = getattr(sys, "_MEIPASS", None)
        if base:
            return Path(base) / "resources"
    return app_dir() / "resources"


def data_dir() -> Path:
    """可写数据目录：settings.json / tm.db / logs。"""
    d = app_dir() / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def logs_dir() -> Path:
    d = data_dir() / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def default_output_dir() -> Path:
    d = app_dir() / "output"
    d.mkdir(parents=True, exist_ok=True)
    return d


def ensure_dirs() -> None:
    for fn in (data_dir, logs_dir, default_output_dir):
        try:
            fn()
        except OSError:
            pass


def resource(*parts: str) -> Path:
    return resource_dir().joinpath(*parts)


def open_in_explorer(path: str | os.PathLike, select: bool = True) -> None:
    """在资源管理器中定位文件或目录。"""
    p = Path(path)
    try:
        if select and p.exists() and p.is_file():
            os.system(f'explorer /select,"{p}"')
        elif p.exists():
            os.startfile(str(p))  # type: ignore[attr-defined]
        else:
            os.startfile(str(p.parent))  # type: ignore[attr-defined]
    except Exception:
        pass
