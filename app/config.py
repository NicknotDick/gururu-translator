"""配置读写：单文件 JSON、原子写入、深度合并默认值。"""
from __future__ import annotations

import copy
import json
import os
import threading
from pathlib import Path
from typing import Any

from . import secrets
from .paths import (app_dir, data_dir, default_output_dir, portable_config_path,
                    resource)

SETTINGS_FILE = "settings.json"

# 出厂配置：打包时由 tools/build.py 从当前配置生成并内嵌到 EXE。
# 首次运行（无外部 settings.json）时以它为基础，实现「配置随软件分发」。
FACTORY_FILE = "default_settings.json"


def _to_stored_dir(value: str) -> str:
    """存储形式：位于程序目录下时改写为相对路径，整个文件夹迁移后仍有效。"""
    try:
        p = Path(str(value or ""))
        if not p.is_absolute():
            return str(p).replace("\\", "/")
        base = app_dir().resolve()
        rp = p.resolve()
        if rp == base or base in rp.parents:
            rel = rp.relative_to(base)
            return str(rel).replace("\\", "/") or "."
    except Exception:
        pass
    return str(value or "")


def to_abs_dir(value: str) -> Path:
    """读取形式：相对路径基于程序目录解析，绝对路径原样返回。"""
    p = Path(str(value or ""))
    if not p.is_absolute():
        p = app_dir() / p
    return p

# 大模型服务商预置（仅作为默认值，全部可改）
PROVIDERS: dict[str, dict[str, Any]] = {
    "deepseek": {
        "label": "DeepSeek 深度求索",
        "label_en": "DeepSeek",
        "base_url": "https://api.deepseek.com",
        "models": ["deepseek-chat", "deepseek-reasoner"],
    },
    "openai": {
        "label": "OpenAI",
        "label_en": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini"],
    },
    "dashscope": {
        "label": "阿里百炼 / 通义千问",
        "label_en": "Aliyun Bailian / Qwen",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": ["qwen-plus", "qwen-max", "qwen-turbo"],
    },
    "zhipu": {
        "label": "智谱 GLM",
        "label_en": "Zhipu GLM",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "models": ["glm-4-plus", "glm-4-air", "glm-4-flash"],
    },
    "moonshot": {
        "label": "月之暗面 Kimi",
        "label_en": "Moonshot Kimi",
        "base_url": "https://api.moonshot.cn/v1",
        "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
    },
    "custom": {
        "label": "自定义 / 内网端点",
        "label_en": "Custom / intranet",
        "base_url": "",
        "models": [],
    },
}

DEFAULTS: dict[str, Any] = {
    "version": 1,
    "engine": {
        "active": "public",  # public | llm
        "llm": {
            "provider": "deepseek",
            "base_url": "https://api.deepseek.com",
            "model": "deepseek-chat",
            "api_key_enc": "",
            "temperature": 0.2,
            "timeout": 120,
            "concurrency": 6,
            "batch_chars": 1800,
            "json_mode": True,
        },
        "public": {
            "order": ["tencent", "mymemory"],
            "tencent": {
                "url": "https://transmart.qq.com/api/imt",
                "client_key": "browser-chrome-110.0.0",
            },
            "mymemory": {
                "url": "https://api.mymemory.translated.net/get",
                "email": "",
            },
        },
    },
    "translate": {
        "src": "zh",
        "tgt": "en",
        "style": "general",
        "term_sets": ["it", "sap"],
        "mode": "target_only",  # target_only | bilingual
    },
    "output": {
        "dir": "",
        "suffix": "_译文",
        "translate_name": False,
        "auto_save": True,
    },
    # 预览全文模式的显示设置：效果 / 译文字体 / 分布方式
    "preview": {
        "fx": "default",
        "font": "",
        "dist": "stack",
    },
    "doc": {
        "skip_header_footer": False,
        "skip_code": True,
    },
    "tm": {"enabled": True, "min_len": 4},
    "ocr": {"enabled": False, "backend": "none"},  # v2 预留
    "ui": {"theme": "auto", "lang": "zh", "start_page": "text", "last_page": "text"},
    "history": [],
}


def _deep_merge(base: dict, patch: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (patch or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


class Settings:
    """线程安全的配置容器。"""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or (data_dir() / SETTINGS_FILE)
        self._lock = threading.RLock()
        self._data: dict[str, Any] = copy.deepcopy(DEFAULTS)
        self._api_key_plain: str = ""
        self.load()
        if not self._path.exists():
            # 首次运行就落地配置文件，方便用户查看与手工编辑
            try:
                self.save()
            except Exception:
                pass

    # ---------- 持久化 ----------
    def _load_factory(self) -> dict | None:
        """读取内嵌在 EXE 中的出厂配置（打包时烧入）。"""
        try:
            p = resource(FACTORY_FILE)
            if p and p.exists():
                raw = json.loads(p.read_text("utf-8"))
                return raw if isinstance(raw, dict) else None
        except Exception:
            pass
        return None

    def has_factory(self) -> bool:
        return self._load_factory() is not None

    def has_portable(self) -> bool:
        return self._load_portable() is not None

    def _load_portable(self) -> dict | None:
        """读取软件目录中的便携出厂配置。"""
        try:
            p = portable_config_path()
            if p.exists():
                raw = json.loads(p.read_text("utf-8"))
                return raw if isinstance(raw, dict) else None
        except Exception:
            pass
        return None

    def freeze(self) -> Path:
        """把当前配置固化为软件目录中的便携出厂配置（含本机加密的 API Key）。"""
        p = portable_config_path()
        self.export_to(p)
        return p

    def load(self) -> None:
        with self._lock:
            data = copy.deepcopy(DEFAULTS)
            # 1) 出厂内嵌配置（随 EXE 分发，优先级高于内置默认值）
            factory = self._load_factory()
            if factory:
                data = _deep_merge(data, factory)
            # 2) 便携出厂配置（位于软件目录，随文件夹迁移）
            portable = self._load_portable()
            if portable:
                data = _deep_merge(data, portable)
            # 3) 用户配置（最高优先级）
            if self._path.exists():
                try:
                    raw = json.loads(self._path.read_text("utf-8"))
                    if isinstance(raw, dict):
                        data = _deep_merge(data, raw)
                except Exception:
                    pass
            self._data = data
            self._api_key_plain = secrets.decrypt(
                str(data.get("engine", {}).get("llm", {}).get("api_key_enc", ""))
            )
            if not data.get("output", {}).get("dir"):
                data.setdefault("output", {})["dir"] = _to_stored_dir(
                    str(default_output_dir()))

    def save(self) -> None:
        with self._lock:
            self._data.setdefault("engine", {}).setdefault("llm", {})["api_key_enc"] = (
                secrets.encrypt(self._api_key_plain) if self._api_key_plain else ""
            )
            # 输出目录按相对形式存储，保证整个软件目录迁移后仍然有效
            if self._data.get("output", {}).get("dir"):
                self._data["output"]["dir"] = _to_stored_dir(
                    str(self._data["output"]["dir"]))
            payload = json.dumps(self._data, ensure_ascii=False, indent=2)
            tmp = self._path.with_suffix(".json.tmp")
            try:
                tmp.write_text(payload, "utf-8")
                os.replace(tmp, self._path)
            except Exception:
                try:
                    tmp.unlink(missing_ok=True)
                except Exception:
                    pass

    # ---------- 访问 ----------
    @property
    def path(self) -> Path:
        """当前用户配置文件的实际路径。"""
        return self._path

    def as_dict(self) -> dict[str, Any]:
        with self._lock:
            out = copy.deepcopy(self._data)
            # 界面一律使用绝对路径显示
            if out.get("output", {}).get("dir"):
                out["output"]["dir"] = str(to_abs_dir(str(out["output"]["dir"])))
            return out

    def get(self, dotted: str, default: Any = None) -> Any:
        with self._lock:
            cur: Any = self._data
            for part in dotted.split("."):
                if not isinstance(cur, dict) or part not in cur:
                    return default
                cur = cur[part]
            return copy.deepcopy(cur)

    def set(self, dotted: str, value: Any) -> None:
        with self._lock:
            parts = dotted.split(".")
            cur = self._data
            for p in parts[:-1]:
                nxt = cur.get(p)
                if not isinstance(nxt, dict):
                    nxt = {}
                    cur[p] = nxt
                cur = nxt
            cur[parts[-1]] = value

    def update(self, patch: dict) -> dict[str, Any]:
        """深度更新并落盘；api_key 明文单独处理。"""
        with self._lock:
            patch = copy.deepcopy(patch or {})
            llm = patch.get("engine", {}).get("llm", {})
            if isinstance(llm, dict) and "api_key" in llm:
                key = str(llm.pop("api_key") or "")
                if key:
                    self._api_key_plain = key
            self._data = _deep_merge(self._data, patch)
            self.save()
            return self.as_dict()

    # ---------- API Key ----------
    @property
    def api_key(self) -> str:
        with self._lock:
            return self._api_key_plain

    def set_api_key(self, key: str) -> None:
        with self._lock:
            self._api_key_plain = key or ""
            self.save()

    # ---------- 配置迁移（导出 / 导入） ----------
    def export_to(self, target: str | Path) -> Path:
        """把当前配置导出为随身 JSON（API Key 保持加密态）。"""
        with self._lock:
            self._data.setdefault("engine", {}).setdefault("llm", {})["api_key_enc"] = (
                secrets.encrypt(self._api_key_plain) if self._api_key_plain else ""
            )
            out = copy.deepcopy(self._data)
            out["_exported_by"] = "Gururu 翻译"
            p = Path(target)
            if p.suffix.lower() != ".json":
                p = p.with_suffix(".json")
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(out, ensure_ascii=False, indent=2), "utf-8")
            return p

    def import_from(self, source: str | Path) -> dict[str, Any]:
        """导入配置：整体替换后深度补全缺失项。"""
        with self._lock:
            raw = json.loads(Path(source).read_text("utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("配置文件格式不正确")
            raw.pop("_exported_by", None)
            # 豁免项：不清空现存的 API Key，避免导入覆盖导致无法调用
            incoming_key = str(raw.get("engine", {}).get("llm", {}).get("api_key_enc") or "")
            merged = _deep_merge(DEFAULTS, raw)
            self._data = merged
            self._api_key_plain = secrets.decrypt(incoming_key)
            self.save()
            return self.as_dict()

    # ---------- 派生 ----------
    def output_dir(self) -> Path:
        d = self.get("output.dir") or str(default_output_dir())
        p = to_abs_dir(str(d))
        try:
            p.mkdir(parents=True, exist_ok=True)
        except OSError:
            p = default_output_dir()
        return p

    def languages(self) -> list[dict]:
        try:
            return json.loads(resource("langs.json").read_text("utf-8"))
        except Exception:
            return [{"code": "zh", "cn": "中文", "en": "Chinese", "cjk": True, "rtl": False,
                     "tencent": "zh", "mymemory": "zh-CN"},
                    {"code": "en", "cn": "英语", "en": "English", "cjk": False, "rtl": False,
                     "tencent": "en", "mymemory": "en-US"}]

    def styles(self) -> list[dict]:
        try:
            return json.loads(resource("styles.json").read_text("utf-8"))
        except Exception:
            return [{"id": "general", "name": "标准通用", "desc": "", "prompt": ""}]


settings = Settings()
