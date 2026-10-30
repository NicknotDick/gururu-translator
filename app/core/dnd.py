"""拖放支持：借助 pywebview 的 DOM 事件拿到拖入文件的完整路径。

WebView2 出于安全考虑不会把绝对路径暴露给页面 JS，pywebview 5.0+ 在
document 级 drop 事件里补了一个 ``pywebviewFullPath`` 字段（仅在 Python 侧可见），
本模块负责订阅该事件并把路径交给回调。
"""
from __future__ import annotations

import logging
from typing import Any, Callable

log = logging.getLogger("dnd")


def install(window: Any, on_paths: Callable[[list[str]], None]) -> bool:
    """注册 document 级 drop 监听。必须在页面加载完成后调用。"""
    try:
        from webview.dom import DOMEventHandler  # type: ignore
    except Exception as exc:  # noqa: BLE001
        log.info("当前运行环境不支持拖放事件：%s", exc)
        return False

    def _handle(event: Any) -> None:
        try:
            data = (event or {}).get("dataTransfer") or {}
            files = data.get("files") or []
            paths: list[str] = []
            for f in files:
                if not isinstance(f, dict):
                    continue
                p = f.get("pywebviewFullPath")
                if p:
                    paths.append(str(p))
            paths = list(dict.fromkeys(paths))
        except Exception:  # noqa: BLE001
            log.exception("解析拖放事件失败")
            return
        if not paths:
            # 极少数情况下拿不到绝对路径（例如非资源管理器来源的拖放），给用户提示而不是静默
            names = [str(f.get("name")) for f in files if isinstance(f, dict)]
            log.warning("拖放：未取到完整路径（%d 项）：%s", len(names), names[:5])
            if names:
                from ..core.bus import bus

                bus.emit("dropped", added=0, skipped=names[:5], jobs=[], failed=True)
            return
        try:
            on_paths(paths)
        except Exception:  # noqa: BLE001
            log.exception("处理拖入文件失败")

    try:
        window.dom.document.events.drop += DOMEventHandler(
            _handle, prevent_default=True, stop_propagation=False
        )
    except Exception:  # noqa: BLE001
        log.exception("注册拖放监听失败")
        return False
    log.info("拖放监听已就绪")
    return True
