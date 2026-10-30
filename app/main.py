"""程序入口：单实例、DPI 感知、WebView2 窗口、异常兜底。"""
from __future__ import annotations

import ctypes
import logging
import os
import sys
import threading
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.api.bridge import APP_TITLE, Bridge  # noqa: E402
from app.paths import ensure_dirs, logs_dir  # noqa: E402

_MUTEX_NAME = "Local\\DocTranslator_SingleInstance_v1"
_mutex_handle = None


def setup_logging() -> None:
    try:
        ensure_dirs()
        handler = RotatingFileHandler(
            logs_dir() / "app.log", maxBytes=1_500_000, backupCount=2, encoding="utf-8"
        )
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        root = logging.getLogger()
        root.setLevel(logging.INFO)
        root.addHandler(handler)
        if not getattr(sys, "frozen", False):
            root.addHandler(logging.StreamHandler(sys.stderr))
    except Exception:
        pass


def already_running() -> bool:
    global _mutex_handle
    if sys.platform != "win32":
        return False
    try:
        _mutex_handle = ctypes.windll.kernel32.CreateMutexW(None, False, _MUTEX_NAME)
        return ctypes.windll.kernel32.GetLastError() == 183  # ERROR_ALREADY_EXISTS
    except Exception:
        return False


def _window_icon() -> str | None:
    """窗口左上角图标：与桌面快捷方式同源（resources/icon.ico 由同一图标生成）。"""
    try:
        from app.paths import app_dir, resource

        ico = resource("icon.ico")
        if ico.is_file():
            return str(ico)
        dev = app_dir() / "build" / "app.ico"
        return str(dev) if dev.is_file() else None
    except Exception:
        return None


def start_tray(window) -> object | None:
    """系统托盘：最小化后驻留通知区，双击恢复，右键可退出。"""
    import time

    log = logging.getLogger("main")
    try:
        import pystray
        from PIL import Image

        from app.paths import resource

        image = Image.open(resource("icon.png"))
    except Exception:
        log.warning("托盘不可用，跳过", exc_info=True)
        return None

    def _show(*_a) -> None:
        try:
            window.restore()
            window.show()
        except Exception:
            log.exception("恢复窗口失败")

    def _hide(*_a) -> None:
        try:
            window.hide()
        except Exception:
            log.exception("隐藏窗口失败")

    def _quit(icon=None, *_a) -> None:
        try:
            if icon is not None:
                icon.stop()
        except Exception:
            pass
        try:
            window.destroy()
        except Exception:
            pass

    try:
        menu = pystray.Menu(
            pystray.MenuItem("显示主窗口", _show, default=True),
            pystray.MenuItem("隐藏到托盘", _hide),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", _quit),
        )
        icon = pystray.Icon("gururu_translate", image, APP_TITLE, menu)
        threading.Thread(target=icon.run, daemon=True).start()
        time.sleep(0.6)
        if not getattr(icon, "visible", False):
            log.warning("托盘图标未显示，关闭最小化到托盘")
            return None
        log.info("托盘已就绪")
        return icon
    except Exception:
        log.warning("托盘启动失败", exc_info=True)
        return None


def ask_existing_action() -> int:
    """已运行时的三选弹窗。返回 6=显示 / 7=重启 / 2=取消。"""
    from app.core.i18n import tr

    text = tr(
        "Gururu 翻译 已在运行。\n\n"
        "「是」：显示正在运行的窗口\n"
        "「否」：关闭它并启动新程序\n"
        "「取消」：不启动",
        "Gururu Translate is already running.\n\n"
        "Yes:    show the existing window\n"
        "No:     close it and start a new instance\n"
        "Cancel: do nothing",
    )
    try:
        return int(ctypes.windll.user32.MessageBoxW(
            None, text, APP_TITLE, 0x03 | 0x20 | 0x10000  # YESNOCANCEL|ICONQUESTION|SETFOREGROUND
        ))
    except Exception:
        return 2


def close_existing(timeout: float = 4.0) -> bool:
    """先请求关闭已有实例，超时后强制结束。"""
    import time

    try:
        hwnd = ctypes.windll.user32.FindWindowW(None, APP_TITLE)
        if not hwnd:
            return True
        pid = ctypes.c_ulong(0)
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE

        deadline = time.time() + timeout
        while time.time() < deadline:
            time.sleep(0.15)
            if not ctypes.windll.user32.IsWindow(hwnd):
                return True

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x0001, False, pid.value)  # PROCESS_TERMINATE
        if handle:
            kernel32.TerminateProcess(handle, 0)
            kernel32.CloseHandle(handle)
        time.sleep(0.4)
        return True
    except Exception:
        return False


def focus_existing() -> bool:
    """把已在运行的实例窗口提到前台，避免用户以为程序没反应。"""
    try:
        hwnd = ctypes.windll.user32.FindWindowW(None, APP_TITLE)
        if not hwnd:
            return False
        ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        ctypes.windll.user32.SetForegroundWindow(hwnd)
        return True
    except Exception:
        return False


def set_dpi_awareness() -> None:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def system_prefers_light() -> bool:
    """读取 Windows「应用模式」是否为浅色。"""
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return bool(value)
    except Exception:
        return False


def initial_theme() -> str:
    try:
        from app.config import settings

        pref = str(settings.get("ui.theme") or "auto")
    except Exception:
        pref = "auto"
    if pref in ("light", "dark"):
        return pref
    return "light" if system_prefers_light() else "dark"


def load_html() -> str:
    if getattr(sys, "frozen", False):
        try:
            from app.ui_bundle import HTML  # type: ignore

            return HTML.replace("<body", f'<body data-theme="{initial_theme()}"', 1)
        except Exception:
            pass
    base = Path(__file__).resolve().parent / "ui"
    html = (base / "index.html").read_text("utf-8")
    css = (base / "app.css").read_text("utf-8")
    js = (base / "app.js").read_text("utf-8")
    html = html.replace(
        '<link rel="stylesheet" href="app.css">', f"<style>\n{css}\n</style>"
    )
    html = html.replace('<script src="app.js"></script>', f"<script>\n{js}\n</script>")
    return html.replace("<body", f'<body data-theme="{initial_theme()}"', 1)


def _pil(name: str):
    """动态导入 PIL，避免调试截图依赖被静态打包进 EXE。"""
    import importlib

    return importlib.import_module(".".join(["PIL", name]))


def _print_window(hwnd: int, path: str) -> bool:
    """用 PrintWindow 直接抓取窗口自身内容，不受窗口遮挡影响（仅调试用）。"""
    try:
        import ctypes.wintypes as wt

        Image = _pil("Image")

        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32
        rect = wt.RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return False
        w = rect.right - rect.left
        h = rect.bottom - rect.top
        if w < 50 or h < 50:
            return False

        hdc = user32.GetWindowDC(hwnd)
        mem = gdi32.CreateCompatibleDC(hdc)
        bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
        gdi32.SelectObject(mem, bmp)
        ok = user32.PrintWindow(hwnd, mem, 2)

        class BIH(ctypes.Structure):
            _fields_ = [
                ("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG),
                ("biPlanes", wt.WORD), ("biBitCount", wt.WORD),
                ("biCompression", wt.DWORD), ("biSizeImage", wt.DWORD),
                ("biXPelsPerMeter", wt.LONG), ("biYPelsPerMeter", wt.LONG),
                ("biClrUsed", wt.DWORD), ("biClrImportant", wt.DWORD),
            ]

        bi = BIH()
        bi.biSize = ctypes.sizeof(BIH)
        bi.biWidth = w
        bi.biHeight = -h
        bi.biPlanes = 1
        bi.biBitCount = 32
        buf = ctypes.create_string_buffer(w * h * 4)
        gdi32.GetDIBits(mem, bmp, 0, h, buf, ctypes.byref(bi), 0)
        Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB").save(path)

        gdi32.DeleteObject(bmp)
        gdi32.DeleteDC(mem)
        user32.ReleaseDC(hwnd, hdc)
        return bool(ok)
    except Exception:
        return False


def fatal(message: str) -> None:
    try:
        ctypes.windll.user32.MessageBoxW(None, message, APP_TITLE, 0x10)
    except Exception:
        print(message, file=sys.stderr)


def main() -> int:
    setup_logging()
    set_dpi_awareness()
    log = logging.getLogger("main")

    if already_running():
        choice = ask_existing_action()
        if choice == 6:  # 显示已运行
            if focus_existing():
                return 0
            fatal("未能找到正在运行的窗口，请从任务栏恢复。")
            return 0
        if choice == 7:  # 关闭它并重启
            if not close_existing():
                fatal("无法关闭正在运行的实例，请在任务栏手动退出后重试。")
                return 0
        else:  # 取消
            return 0

    try:
        import webview
    except Exception as exc:  # noqa: BLE001
        fatal(f"界面组件加载失败：{exc}\n请确认系统已安装 Microsoft Edge WebView2 运行时。")
        return 1

    bridge = Bridge()
    try:
        html = load_html()
    except Exception as exc:  # noqa: BLE001
        log.exception("加载界面失败")
        fatal(f"加载界面失败：{exc}")
        return 1

    window = webview.create_window(
        APP_TITLE,
        html=html,
        js_api=bridge,
        width=1220,
        height=800,
        min_size=(980, 640),
        background_color="#12151a",
        text_select=True,
    )
    bridge.bind(window)

    def _bind_dnd() -> None:
        """页面就绪后再注册拖放监听，避免在 loaded 回调里同步执行 JS。"""

        def _worker() -> None:
            import time

            time.sleep(0.4)
            try:
                from app.core.dnd import install as install_dnd

                ok = install_dnd(window, lambda paths: bridge.add_dropped(paths))
                log.info("拖放支持：%s", "已启用" if ok else "不可用")
            except Exception:  # noqa: BLE001
                log.warning("拖放支持未启用", exc_info=True)

        threading.Thread(target=_worker, daemon=True).start()

    window.events.loaded += _bind_dnd

    tray = start_tray(window)
    if tray is not None:
        def _on_minimized(*_a) -> None:
            try:
                window.hide()
            except Exception:
                pass

        window.events.minimized += _on_minimized

    def warm_up() -> None:
        try:
            import fitz  # noqa: F401
        except Exception:
            pass

    threading.Thread(target=warm_up, daemon=True).start()

    selftest = os.environ.get("WB_SELFTEST_MS")
    if selftest:
        def _close() -> None:
            try:
                window.destroy()
            except Exception:
                pass
            log.info("SELFTEST_OK")

        threading.Timer(int(selftest) / 1000.0, _close).start()

    if os.environ.get("WB_TEST_MIN"):
        def _min_test() -> None:
            import time as _t

            _t.sleep(2.5)
            hwnd = ctypes.windll.user32.FindWindowW(None, APP_TITLE)
            before = bool(ctypes.windll.user32.IsWindowVisible(hwnd)) if hwnd else None
            try:
                window.minimize()
            except Exception:
                log.exception("minimize 调用失败")
            _t.sleep(1.5)
            after = bool(ctypes.windll.user32.IsWindowVisible(hwnd)) if hwnd else None
            log.info("MIN_TEST before_visible=%s after_visible=%s", before, after)

        threading.Timer(1.0, _min_test).start()

    shot = os.environ.get("WB_SHOT")

    def _maybe_shot() -> None:
        if not shot:
            return
        import time

        time.sleep(float(os.environ.get("WB_SHOT_DELAY", "3.0")))
        js = os.environ.get("WB_SHOT_JS")
        if js:
            try:
                window.evaluate_js(js)
            except Exception:
                log.exception("注入脚本失败")
            time.sleep(float(os.environ.get("WB_SHOT_WAIT", "1.5")))
        try:
            hwnd = ctypes.windll.user32.FindWindowW(None, APP_TITLE)
            time.sleep(0.5)
            if hwnd and _print_window(hwnd, shot):
                log.info("SHOT_SAVED %s", shot)
                return
            ImageGrab = _pil("ImageGrab")

            if os.environ.get("WB_SHOT_FULL"):
                ImageGrab.grab().save(shot)
                log.info("SHOT_SAVED_FULL %s", shot)
                return

            import ctypes.wintypes as wt

            box = None
            if hwnd:
                rect = wt.RECT()
                ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                box = (rect.left, rect.top, rect.right, rect.bottom)
            ImageGrab.grab(bbox=box).save(shot)
            log.info("SHOT_SAVED_GRAB %s", shot)
        except Exception:
            log.exception("截图失败")

    if shot:
        threading.Timer(2.0, _maybe_shot).start()

    try:
        import time as _time

        def _after_start() -> None:
            _time.sleep(0.8)
            if not os.environ.get("_PYI_SPLASH_IPC"):
                return
            try:
                import pyi_splash  # type: ignore

                pyi_splash.close()
            except Exception:
                pass

        webview.start(gui="edgechromium", debug=False, private_mode=False, func=_after_start,
                      icon=_window_icon())
    except Exception:  # noqa: BLE001
        log.exception("窗口启动失败")
        fatal("窗口启动失败：\n" + traceback.format_exc(limit=3))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
