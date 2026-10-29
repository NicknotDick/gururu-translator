"""配置读写：单文件 JSON、原子写入、深度合并默认值。"""
from __future__ import annotations

import copy
import json
import os
import threading
from pathlib import Path
from typing import Any

from . import secrets
from .paths import data_dir, default_output_dir, resource

SETTINGS_FILE = "settings.json"

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
    def load(self) -> None:
        with self._lock:
            data = copy.deepcopy(DEFAULTS)
            if self._path.exists():
                try:
                    raw = json.loads(self._path.read_text("utf-8"))
                    if isinstance(raw, dict):
                        data = _deep_merge(DEFAULTS, raw)
                except Exception:
                    pass
            self._data = data
            self._api_key_plain = secrets.decrypt(
                str(data.get("engine", {}).get("llm", {}).get("api_key_enc", ""))
            )
            if not data.get("output", {}).get("dir"):
                data.setdefault("output", {})["dir"] = str(default_output_dir())

    def save(self) -> None:
        with self._lock:
            self._data.setdefault("engine", {}).setdefault("llm", {})["api_key_enc"] = (
                secrets.encrypt(self._api_key_plain) if self._api_key_plain else ""
            )
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
    def as_dict(self) -> dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._data)

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

    # ---------- 派生 ----------
    def output_dir(self) -> Path:
        d = self.get("output.dir") or str(default_output_dir())
        p = Path(d)
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
