"""API Key 本地加密：优先 DPAPI（当前用户绑定），不可用时降级为混淆存储。

存储格式：``dpapi:<base64>`` / ``plain:<base64>``。绝不落明文。
"""
from __future__ import annotations

import base64
import ctypes
import sys
from ctypes import wintypes

_IS_WIN = sys.platform == "win32"
_PREFIX_DPAPI = "dpapi:"
_PREFIX_PLAIN = "plain:"


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


def _make_blob(data: bytes):
    buf = ctypes.create_string_buffer(data, len(data))
    blob = _DataBlob(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    return blob, buf


def _blob_bytes(blob: _DataBlob) -> bytes:
    try:
        return ctypes.string_at(blob.pbData, blob.cbData)
    finally:
        if blob.pbData:
            ctypes.windll.kernel32.LocalFree(blob.pbData)


def _dpapi_protect(data: bytes) -> bytes | None:
    if not _IS_WIN:
        return None
    try:
        blob_in, _buf = _make_blob(data)
        blob_out = _DataBlob()
        ok = ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(blob_in), None, None, None, None, 0x1, ctypes.byref(blob_out)
        )
        if not ok:
            return None
        return _blob_bytes(blob_out)
    except Exception:
        return None


def _dpapi_unprotect(data: bytes) -> bytes | None:
    if not _IS_WIN:
        return None
    try:
        blob_in, _buf = _make_blob(data)
        blob_out = _DataBlob()
        ok = ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(blob_in), None, None, None, None, 0x1, ctypes.byref(blob_out)
        )
        if not ok:
            return None
        return _blob_bytes(blob_out)
    except Exception:
        return None


def encrypt(plain: str) -> str:
    if not plain:
        return ""
    raw = plain.encode("utf-8")
    enc = _dpapi_protect(raw)
    if enc is not None:
        return _PREFIX_DPAPI + base64.b64encode(enc).decode("ascii")
    return _PREFIX_PLAIN + base64.b64encode(raw).decode("ascii")


def decrypt(stored: str) -> str:
    if not stored:
        return ""
    try:
        if stored.startswith(_PREFIX_DPAPI):
            raw = _dpapi_unprotect(base64.b64decode(stored[len(_PREFIX_DPAPI):]))
            return raw.decode("utf-8") if raw else ""
        if stored.startswith(_PREFIX_PLAIN):
            return base64.b64decode(stored[len(_PREFIX_PLAIN):]).decode("utf-8")
        # 兼容历史明文
        return stored
    except Exception:
        return ""


def mask(plain: str) -> str:
    if not plain:
        return ""
    if len(plain) <= 8:
        return "*" * len(plain)
    return f"{plain[:4]}{'*' * 8}{plain[-4:]}"
