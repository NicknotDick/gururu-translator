"""生成打包所需的图标与启动图。

图标参照 Google Translate 的构图：圆角方块左右分色，左侧蓝底白「文」、右侧白底蓝「A」。
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
BUILD.mkdir(exist_ok=True)

GOOGLE_BLUE = (66, 133, 244)
BORDER = (218, 220, 224)
WHITE = (255, 255, 255)

# 深色界面用的启动图配色
BG = (28, 33, 41)
FG = (232, 235, 240)


def _font(size: int, cjk: bool = False, bold: bool = True):
    names = (
        ("msyhbd.ttc", "msyh.ttc", "simhei.ttf")
        if cjk
        else ("arialbd.ttf", "seguisb.ttf", "msyhbd.ttc")
    )
    for name in names:
        try:
            return ImageFont.truetype(f"C:/Windows/Fonts/{name}", size)
        except Exception:
            continue
    return ImageFont.load_default()


def _rounded_mask(size: int, radius: int) -> Image.Image:
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    return m


def make_icon() -> Path:
    size = 512
    radius = 104
    half = size // 2

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    base = _rounded_mask(size, radius)

    # 白底
    img.paste(Image.new("RGBA", (size, size), WHITE + (255,)), (0, 0), base)

    # 左半蓝色（保留圆角）
    left = Image.new("L", (size, size), 0)
    ImageDraw.Draw(left).rectangle((0, 0, half - 1, size), fill=255)
    img.paste(
        Image.new("RGBA", (size, size), GOOGLE_BLUE + (255,)),
        (0, 0),
        ImageChops.multiply(base, left),
    )

    d = ImageDraw.Draw(img)
    # 左侧「文」
    f_cjk = _font(int(size * 0.40), cjk=True)
    d.text((half // 2, size // 2 - int(size * 0.01)), "文", font=f_cjk,
           fill=WHITE + (255,), anchor="mm")
    # 右侧「A」
    f_lat = _font(int(size * 0.46), cjk=False)
    d.text((half + half // 2, size // 2 + int(size * 0.01)), "A", font=f_lat,
           fill=GOOGLE_BLUE + (255,), anchor="mm")

    # 描边
    d.rounded_rectangle(
        (2, 2, size - 3, size - 3), radius=radius, outline=BORDER + (255,), width=5
    )

    path = BUILD / "app.ico"
    img.save(path, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

    # 托盘图标：单独一张 PNG，随 resources/ 打包
    tray = ROOT / "resources" / "icon.png"
    img.resize((256, 256), Image.LANCZOS).save(tray)
    return path


def make_splash() -> Path:
    w, h = 520, 300
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, w - 1, h - 1), outline=(58, 67, 80))
    icon = Image.open(BUILD / "app.ico").convert("RGBA").resize((96, 96), Image.LANCZOS)
    img.paste(icon, (46, 78), icon)
    d.text((166, 92), "文档翻译", font=_font(36, cjk=True), fill=FG)
    d.text((168, 142), "Gururu Nick · Gurutu 版本", font=_font(14, cjk=False), fill=(154, 164, 178))
    d.line((46, 222, w - 46, 222), fill=(44, 51, 61), width=1)
    d.text((46, 240), "Word · Excel · PPT · PDF · Visio · MD · TXT · EPUB",
           font=_font(13, cjk=False), fill=(111, 122, 136))
    path = BUILD / "splash.png"
    img.save(path)
    return path


if __name__ == "__main__":
    print(make_icon())
    print(make_splash())
