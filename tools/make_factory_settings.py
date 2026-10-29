"""把当前配置固化为「出厂配置」，打包时随 EXE 分发。

产出 resources/default_settings.json：程序首次运行（尚无外部 settings.json）时
以它为基础初始化，实现「配置跟着 EXE 走」。

用法：
    python tools/make_factory_settings.py                     # 固化全部分组（含加密的 API Key）
    python tools/make_factory_settings.py --groups ui output  # 只固化指定分组
    python tools/make_factory_settings.py --no-key            # 不固化 API Key（要分发给他人时）
    python tools/make_factory_settings.py --clear             # 清除已固化的出厂配置

分组：
    engine     引擎设置（默认引擎、大模型服务商/模型、温度/并发/分批长度、公共引擎顺序）
    translate  翻译偏好（源/目标语言、风格、术语库、双语模式、翻译记忆开关）
    output     输出设置（输出目录、文件名后缀、翻译文件名、自动输出、跳过页眉页脚/代码）
    ui         界面与预览（主题、界面语言、启动页、预览效果/译文字体/分布方式）

注意：API Key 用 Windows DPAPI 加密后固化，密钥绑定**本机账户**——
本机打开即可直接用；拷贝到别的电脑会解密失败（程序提示重新填写），
不会泄露明文，这是安全设计。要分发给他人时用 --no-key。
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import DEFAULTS, _to_stored_dir  # noqa: E402

SRC = ROOT / "data" / "settings.json"
DST = ROOT / "resources" / "default_settings.json"

ALL_GROUPS = ("engine", "translate", "output", "ui")
GROUP_KEYS = {
    "engine": ["engine"],
    "translate": ["translate", "tm"],
    "output": ["output", "doc"],
    "ui": ["ui", "preview"],
}
GROUP_LABEL = {
    "engine": "引擎设置",
    "translate": "翻译偏好",
    "output": "输出设置",
    "ui": "界面与预览",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--groups", nargs="*", default=list(ALL_GROUPS),
                    choices=list(ALL_GROUPS), help="要固化的配置分组")
    ap.add_argument("--no-key", action="store_true",
                    help="不固化 API Key（适合要分发给他人的场景）")
    ap.add_argument("--clear", action="store_true", help="删除已固化的出厂配置")
    args = ap.parse_args()

    if args.clear:
        if DST.exists():
            DST.unlink()
            print(f"已清除出厂配置：{DST}")
        else:
            print("原本没有出厂配置")
        return 0

    if not SRC.exists():
        print(f"未找到当前配置：{SRC}\n请先运行一次程序生成配置。")
        return 1

    current = json.loads(SRC.read_text("utf-8"))
    out = copy.deepcopy(DEFAULTS)
    picked = []
    for g in args.groups:
        for key in GROUP_KEYS[g]:
            if key in current:
                out[key] = copy.deepcopy(current[key])
        picked.append(GROUP_LABEL[g])

    # 输出目录一律存相对路径，保证整个软件目录迁移后仍有效
    if out.get("output", {}).get("dir"):
        out["output"]["dir"] = _to_stored_dir(str(out["output"]["dir"]))

    # 有值时才保留（DPAPI 已加密，仅本机可解密）
    has_key = bool(out.get("engine", {}).get("llm", {}).get("api_key_enc"))
    if args.no_key:
        out["engine"]["llm"]["api_key_enc"] = ""
        has_key = False

    out["_factory"] = True
    out["_factory_groups"] = list(args.groups)

    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text(json.dumps(out, ensure_ascii=False, indent=2), "utf-8")
    print(f"已固化出厂配置 -> {DST}")
    print(f"  固化分组：{'、'.join(picked)}")
    print(f"  含 API Key：{'是（仅本机可用）' if has_key else '否'}")
    print(f"  输出目录：{out.get('output', {}).get('dir')}（相对路径，随软件迁移）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
