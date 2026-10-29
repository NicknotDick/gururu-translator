"""运行时路径解析。

绿色版语义：配置与缓存优先落在程序所在目录；
当程序目录不可写（如放在 Program Files 等受保护位置）时，
自动降级到 %LOCALAPPDATA%\\Gururu 翻译，保证程序在任何位置都能启动。
"""
from __future__ import annotations

import logging
import os
import sys
import tempfile
from pathlib import Path

APP_NAME = "文档翻译"
FALLBACK_DIR_NAME = "Gururu 翻译"

log = logging.getLogger(__name__)

_writable_root: Path | None = None
_using_fallback: bool = False


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


def _probe_writable(d: Path) -> bool:
    """目录能否创建并写入。"""
    try:
        d.mkdir(parents=True, exist_ok=True)
        probe = d / ".write_test"
        probe.write_bytes(b"")
        probe.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def _resolve_writable_root() -> tuple[Path, bool]:
    """返回 (可写根目录, 是否为降级目录)。结果进程内缓存。"""
    base = app_dir()
    if _probe_writable(base):
        return base, False
    fallback = Path(os.environ.get("LOCALAPPDATA") or str(Path.home())) / FALLBACK_DIR_NAME
    if _probe_writable(fallback):
        return fallback, True
    last = Path(tempfile.gettempdir()) / FALLBACK_DIR_NAME
    return last, _probe_writable(last)


def writable_root() -> Path:
    """可写数据根目录（缓存）。"""
    global _writable_root, _using_fallback
    if _writable_root is None:
        _writable_root, _using_fallback = _resolve_writable_root()
        if _using_fallback:
            log.warning("程序目录不可写，数据目录降级为 %s", _writable_root)
    return _writable_root


def using_fallback() -> bool:
    """当前是否运行在降级数据目录（程序目录不可写）。"""
    writable_root()  # 确保已解析
    return _using_fallback


def data_dir() -> Path:
    """可写数据目录：settings.json / tm.db / logs。"""
    d = writable_root() / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def logs_dir() -> Path:
    d = data_dir() / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def portable_config_path() -> Path:
    """便携出厂配置：位于程序目录，随整个软件文件夹迁移。

    EXE 在运行时无法改写自身，因此「把配置固化进软件」以这个与软件同级的
    文件实现——拷贝软件文件夹即带走配置，首次在新机器运行时自动生效。
    """
    return app_dir() / "出厂配置.json"


def default_output_dir() -> Path:
    d = writable_root() / "output"
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
