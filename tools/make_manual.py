"""生成《Gururu 翻译 操作手册》Word 文档。"""
from __future__ import annotations

import sys
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "manual" / "shots"
OUT = ROOT / "manual" / "Gururu 翻译 操作手册.docx"

sys.path.insert(0, str(ROOT))
from app.version import APP_NAME, AUTHOR, version, version_parts  # noqa: E402

VER = version()
VP = version_parts()

CJK = "微软雅黑"
MONO = "Consolas"
GREY = RGBColor(0x6B, 0x72, 0x80)
ACCENT = RGBColor(0x1F, 0x66, 0xD8)


def set_font(run, size=10.5, bold=False, mono=False, color=None, cjk=CJK):
    run.font.size = Pt(size)
    run.bold = bold
    name = MONO if mono else "Segoe UI"
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), cjk)
    if color is not None:
        run.font.color.rgb = color


def para(doc, text="", size=10.5, bold=False, color=None, align=None,
         space_after=6, line=1.5, indent=0, mono=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_after = Pt(space_after)
    pf.line_spacing = line
    if indent:
        pf.left_indent = Cm(indent)
    if align is not None:
        p.alignment = align
    if text:
        set_font(p.add_run(text), size=size, bold=bold, color=color, mono=mono)
    return p


def h1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after = Pt(8)
    set_font(p.add_run(text), size=16, bold=True, color=ACCENT)
    # 下边框
    pPr = p._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), "1F66D8")
    borders.append(bottom)
    pPr.append(borders)
    return p


def h2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.keep_with_next = True
    set_font(p.add_run(text), size=12.5, bold=True)
    return p


def h3(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    set_font(p.add_run(text), size=11, bold=True, color=RGBColor(0x33, 0x3A, 0x45))
    return p


def bullet(doc, text, level=0):
    p = doc.add_paragraph(style="List Bullet" if level == 0 else "List Bullet 2")
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.45
    set_font(p.add_run(text), size=10.5)
    return p


_NUM = {"n": 0}


def numbered(doc, text, first=False):
    """编号列表。first=True 表示本组第一条，编号从 1 重新开始。

    不使用 Word 的 List Number 样式，避免编号跨章节连续累加。
    """
    if first:
        _NUM["n"] = 0
    _NUM["n"] += 1
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.85)
    p.paragraph_format.first_line_indent = Cm(-0.85)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.45
    set_font(p.add_run(f"{_NUM['n']}. "), size=10.5, bold=True)
    set_font(p.add_run(text), size=10.5)
    return p


def tip(doc, text, label="提示"):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.left_indent = Cm(0.3)
    p.paragraph_format.line_spacing = 1.45
    set_font(p.add_run(f"【{label}】"), size=10, bold=True, color=ACCENT)
    set_font(p.add_run(text), size=10)
    pPr = p._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    left = OxmlElement("w:left")
    left.set(qn("w:val"), "single")
    left.set(qn("w:sz"), "18")
    left.set(qn("w:space"), "8")
    left.set(qn("w:color"), "1F66D8")
    borders.append(left)
    pPr.append(borders)
    return p


def image(doc, name, caption, width=15.2):
    path = SHOTS / name
    if not path.exists():
        para(doc, f"[缺少插图 {name}]", color=GREY)
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(str(path), width=Cm(width))
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(10)
    set_font(c.add_run(caption), size=9, color=GREY)


def table(doc, header, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.autofit = False
    t.allow_autofit = False
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, h in enumerate(header):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        set_font(p.add_run(h), size=9.5, bold=True)
        shade = OxmlElement("w:shd")
        shade.set(qn("w:fill"), "EEF3FB")
        hdr[i]._tc.get_or_add_tcPr().append(shade)
    for row in rows:
        trow = t.add_row()
        trPr = trow._tr.get_or_add_trPr()
        cant = OxmlElement("w:cantSplit")
        trPr.append(cant)
        cells = trow.cells
        for i, val in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            set_font(p.add_run(str(val)), size=9.5)
    if widths:
        for i, w in enumerate(widths):
            t.columns[i].width = Cm(w)
            for row in t.rows:
                row.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def add_page_number(section):
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    run._r.addnext(fld)


PAGES: dict[str, int] = {}


def build() -> Path:
    doc = Document()

    # 页面与默认样式
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.top_margin = Cm(2.2)
    sec.bottom_margin = Cm(2.0)
    sec.left_margin = Cm(2.4)
    sec.right_margin = Cm(2.4)
    add_page_number(sec)

    normal = doc.styles["Normal"]
    normal.font.name = "Segoe UI"
    normal.font.size = Pt(10.5)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), CJK)

    # ---------- 封面 ----------
    para(doc, "", space_after=24)
    icon = ROOT / "resources" / "icon.png"
    if icon.exists():
        pi = doc.add_paragraph()
        pi.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pi.paragraph_format.space_after = Pt(18)
        pi.add_run().add_picture(str(icon), width=Cm(3.2))

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p.add_run(APP_NAME), size=34, bold=True, color=ACCENT)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    set_font(p.add_run("操 作 手 册"), size=20, color=RGBColor(0x44, 0x4C, 0x57))

    pl = doc.add_paragraph()
    pl.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pl.paragraph_format.space_before = Pt(14)
    pl.paragraph_format.space_after = Pt(10)
    set_font(pl.add_run("Windows 10 / 11  ·  单文件绿色版"), size=10.5, color=GREY)

    # 分隔线
    pdiv = doc.add_paragraph()
    pdiv.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pPr = pdiv._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "4")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "C9CFD8")
    borders.append(bottom)
    pPr.append(borders)

    para(doc, "", space_after=96)

    for label, value in (
        ("版本", VER),
        ("构建时间", f"{VP['date']} {VP['time']}"),
        ("作者", AUTHOR),
        ("文档日期", "2026-10-30"),
    ):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(6)
        set_font(p.add_run(f"{label}   "), size=11, color=GREY)
        set_font(p.add_run(value), size=11, bold=True)

    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # ---------- 目录 ----------
    h1(doc, "目录")
    toc = [
        "1  产品概述", "2  安装与启动", "3  界面总览", "4  查词", "5  文本翻译",
        "6  文档翻译", "7  预览与 AI 调整", "8  设置详解", "9  托盘与窗口行为",
        "10  数据与备份", "11  常见问题 FAQ", "12  附录",
    ]
    for title in toc:
        page = str(PAGES.get(title, "—"))
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.9
        p.paragraph_format.tab_stops.add_tab_stop(
            Cm(15.6), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        set_font(p.add_run(title), size=11)
        set_font(p.add_run("\t" + page), size=10.5, color=GREY)

    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # ---------- 1 产品概述 ----------
    h1(doc, "1  产品概述")
    h2(doc, "1.1  这是什么")
    para(doc, "Gururu 翻译 是一款 Windows 单文件绿色版翻译工具。双击即可运行，无需安装、"
              "不写注册表，所有配置与产出都保存在程序同级目录，整个文件夹可拷到 U 盘随身使用。")
    para(doc, "它把三件事做在一起：查词、文本翻译、文档保版翻译。文档翻译支持 Word、Excel、"
              "PowerPoint、PDF、Visio、Markdown、纯文本与 EPUB 八种格式，输出文件自动加「_译文」后缀，"
              "并在翻译完成后提供预览界面逐段修改、或让 AI 按自然语言指令调整译文。")

    h2(doc, "1.2  核心能力一览")
    table(doc,
          ["能力", "说明"],
          [["查词", "内置 3 万高频词离线英汉词典；联网时并列显示有道词典、英文释义与百科图文"],
           ["文本翻译", "左右对照即时翻译，支持 23 种语言互译、6 种风格、术语强制锁定"],
           ["文档翻译", "八种格式保版翻译，支持「仅目标语言」与「双语对照」两种输出模式"],
           ["预览调整", "译文逐段可编辑、可单段重译、可切换风格整篇重译"],
           ["AI 调整", "选中段落并输入自然语言要求（更正式/更简洁/统一术语…），由大模型定向改写"],
           ["术语库", "6 个内置行业库（含 115 条 SAP 术语），支持自建与 CSV/Excel 导入"],
           ["翻译记忆", "SQLite 本地缓存，重复内容不再重复请求"],
           ["界面", "中文 / English 双语界面，深色 / 浅色 / 跟随系统三档色调"]],
          widths=[3.2, 12.0])

    h2(doc, "1.3  适用与不适用")
    para(doc, "适合：合同与技术文档、SAP 项目交付物、论文摘要、日常邮件、批量办公文件转译。")
    para(doc, "不适合：扫描件（无文字层）PDF、图片中的文字、语音字幕；Visio 不支持双语对照输出。")

    # ---------- 2 安装与启动 ----------
    h1(doc, "2  安装与启动")
    h2(doc, "2.1  系统要求")
    table(doc, ["项目", "要求"],
          [["操作系统", "Windows 10 1809 及以上 / Windows 11"],
           ["运行库", "WebView2 运行时（Win11 自带；Win10 如缺失会提示，可从微软官网下载 Evergreen 版）"],
           ["磁盘", "约 120 MB（程序 59 MB + 运行时解包空间）"],
           ["网络", "查词在线词典、百科、公共翻译引擎、大模型均需联网；离线仅内置词典可用"]],
          widths=[3.0, 12.2])

    h2(doc, "2.2  放置与首次启动")
    para(doc, "把 Gururu 翻译.exe 放到任意可写目录（例如 D:\\Tools\\Gururu），双击运行。"
              "建议不要放在 Program Files，因为程序需要在同级目录写入 data 与 output。")
    para(doc, "首次运行会自动生成：")
    table(doc, ["路径", "用途"],
          [["data\\settings.json", "全部配置项；API Key 经 Windows DPAPI 加密后存放"],
           ["data\\tm.db", "翻译记忆缓存（SQLite）"],
           ["data\\logs\\app.log", "运行日志，排查问题时提供"],
           ["output\\", "默认译文输出目录"]],
          widths=[5.0, 10.2])

    tip(doc, "首次启动需要把 59 MB 的程序解包到临时目录，约需 6～8 秒；之后每次启动时间基本相同，属单文件打包的固有代价。")
    tip(doc, "若程序目录不可写（例如放在 Program Files），程序会自动把 data 与 output 转存到"
             " %LOCALAPPDATA%\\Gururu 翻译\\，仍可正常启动；设置 → 缓存与运行中的「数据目录」"
             "会显示实际位置。如需「配置随软件走」，请把软件移到普通可写目录。", "注意")

    h2(doc, "2.3  重复启动时的处理")
    para(doc, "程序同一时间只允许运行一个实例。若已在运行，再次双击会弹出三选对话框：")
    table(doc, ["选项", "行为"],
          [["是", "把正在运行的窗口切到前台，本次启动自动退出"],
           ["否", "先请求关闭旧实例（4 秒内未退出则强制结束），随后启动新实例"],
           ["取消", "不启动，直接退出"]],
          widths=[2.6, 12.6])
    tip(doc, "若旧实例处于托盘隐藏状态、窗口找不回来，选择「否」重启是最快的恢复方式。", "建议")

    # ---------- 3 界面总览 ----------
    h1(doc, "3  界面总览")
    para(doc, "主窗口自上而下分为四个区域：左侧导航、顶部语言栏、中央工作区、底部状态栏。")
    image(doc, "03-text.png", "图 3-1  文本翻译页整体布局")

    h2(doc, "3.1  左侧导航")
    para(doc, "四项依次为：查词、文本翻译、文档翻译、设置。点击切换工作区；"
              "可在 设置 → 常规 → 启动页 指定启动时默认停在哪一页。")

    h2(doc, "3.2  顶部语言栏")
    para(doc, "两个下拉框分别选择源语言与目标语言，中间 ⇄ 按钮一键互换。"
              "语言名始终以该语言的本名显示（English / 中文 / 日本語 / Deutsch …），"
              "因此在英文界面下翻译方向会呈现为 English → 中文。")

    h2(doc, "3.3  底部状态栏")
    para(doc, "左侧显示当前引擎（公共引擎或大语言模型）与翻译记忆命中情况；"
              "右侧显示作者名，点击可打开【关于】窗口，查看版本、构建时间、运行环境、"
              "数据目录与支持格式。")

    h2(doc, "3.4  界面语言与色调")
    para(doc, "两者都在 设置 → 常规 中切换：色调可选跟随系统 / 浅色 / 深色；"
              "界面语言可选中文 / English，切换后立即生效并自动保存。")

    # ---------- 4 查词 ----------
    h1(doc, "4  查词")
    h2(doc, "4.1  基本查询")
    para(doc, "在查词页输入英文单词或短语，回车或点「查询」。结果按来源分为多张卡片依次呈现：")
    table(doc, ["卡片", "内容", "是否需要联网"],
          [["内置离线词典", "音标、词性、多义项、Collins/Oxford 等级、词形变化", "否"],
           ["有道词典", "中文多义项与音标", "是"],
           ["Free Dictionary", "英文释义、词性分组、例句", "是"],
           ["百科（维基摘要）", "摘要正文 + 配图，英文摘要自动补中文翻译", "是"]],
          widths=[3.6, 8.6, 3.0])
    image(doc, "01-dict.png", "图 4-1  查词结果：内置词典、有道、英文释义、百科图文并列")

    h2(doc, "4.2  输入联想与模糊匹配")
    para(doc, "输入 2 个字符后自动弹出候选列表，来源分两级并标注「本地 / 在线」：")
    bullet(doc, "本地：精确 → 前缀 → 包含 → 编辑距离纠错（如 recieve 会给出 receive）")
    bullet(doc, "在线：有道联想词，擅长处理拼写错误与生僻组合")
    para(doc, "合并规则：查询词有精确命中时本地结果优先，否则在线结果优先（因其纠错更准），重复项按首次出现去重。")
    image(doc, "02-suggest.png", "图 4-2  输入 appl 时的候选列表")
    table(doc, ["按键", "作用"],
          [["↑ / ↓", "在候选中移动"],
           ["Enter", "有高亮项则采用该项并查询；否则直接查询输入内容"],
           ["Esc", "关闭候选列表"],
           ["鼠标点击", "直接采用该候选词并查询"]],
          widths=[3.0, 12.2])

    h2(doc, "4.3  断网时的表现")
    para(doc, "只显示内置词典卡片；查不到时给出同前缀候选词。在线卡片区域提示「未获取到在线释义」，"
              "不会报错中断。")

    # ---------- 5 文本翻译 ----------
    h1(doc, "5  文本翻译")
    h2(doc, "5.1  基本流程")
    numbered(doc, "在左侧文本框粘贴或输入原文，右上角实时显示字数与行数。", first=True)
    numbered(doc, "选择源语言与目标语言（默认 中文 → 英语）。")
    numbered(doc, "按 Ctrl+Enter 或点击「翻译」。")
    numbered(doc, "右侧出现译文，可直接编辑，点「复制译文」取走。")
    image(doc, "03-text.png", "图 5-1  文本翻译结果")

    h2(doc, "5.2  引擎选择")
    para(doc, "底部工具条可选择引擎：")
    table(doc, ["引擎", "特点", "适用"],
          [["公共引擎", "免 API Key，内置腾讯通道 + MyMemory 兜底，自动降级", "快速直译，日常使用"],
           ["大语言模型", "需在设置中配置 Key，可套用风格与术语锁定，质量更高", "正式文档、专业内容"]],
          widths=[3.0, 8.4, 3.8])

    h2(doc, "5.3  风格与术语库")
    para(doc, "风格（标准通用 / 正式公文 / 学术论文 / 技术文档 / 商务沟通 / 口语自然）与术语库仅在大语言模型"
              "引擎下生效。术语命中后会强制锁定译法，译后校验，未通过则标记为待确认。")

    # ---------- 6 文档翻译 ----------
    h1(doc, "6  文档翻译")
    h2(doc, "6.1  支持格式")
    table(doc, ["格式", "扩展名", "保版方式", "双语对照"],
          [["Word", ".docx", "段落级替换，样式/编号/表格/页眉页脚保留", "原文段后插入译文段"],
           ["Excel", ".xlsx / .xlsm", "单元格级替换，公式与合并区不受影响", "右侧插入译文列，公式引用平移"],
           ["PowerPoint", ".pptx", "形状/表格/组合内文字替换，自动缩字号", "原段落下方插入译文段"],
           ["PDF", ".pdf", "按文字块坐标擦除后原位回填，页数/图片/表格线不变", "同一文字块上下各半"],
           ["Visio", ".vsdx", "改写页面 XML 文本节点，图形位置不动", "不支持"],
           ["Markdown", ".md / .markdown", "保护 front-matter、代码块、链接与 URL", "原文行下插入引用块"],
           ["纯文本", ".txt", "合并软换行后按段落翻译", "原文段后插入译文段"],
           ["EPUB", ".epub", "按 spine 顺序改写 XHTML 文本节点", "段落下方插入译文段"]],
          widths=[2.4, 3.2, 7.0, 4.6])

    h2(doc, "6.2  添加文件")
    para(doc, "三种方式任选：拖拽文件到虚线区域；点击虚线区域选择文件（可多选）；"
              "点「添加文件夹」批量导入整个目录（仅识别受支持格式）。")
    image(doc, "04-docs.png", "图 6-1  文档翻译页与待翻译队列")

    h2(doc, "6.3  翻译选项")
    table(doc, ["选项", "说明"],
          [["引擎", "公共引擎或大语言模型"],
           ["翻译模式", "仅目标语言：只保留译文；双语对照：原文与译文并存"],
           ["风格", "6 种语体，选择后作用于全部段落"],
           ["术语库", "可多选，命中的术语强制使用指定译法"],
           ["同时翻译页眉页脚", "勾选后连同页眉页脚文字一并翻译（Word/PDF）"],
           ["同时翻译文件名", "勾选后输出文件直接使用译名（英文自动词首大写、非法字符自动清理）；"
                          "此时设置 → 常规中的「输出文件名后缀」自动置灰失效"],
           ["完成后自动输出译文", "翻译结束自动写文件；取消勾选则仅在预览中查看"],
           ["输出目录", "点击显示路径的按钮打开该目录，点右侧「…」更换目录"]],
          widths=[4.0, 11.2])
    image(doc, "11-docs-transname.png", "图 6-2  文档翻译页：翻译选项中的「同时翻译文件名」")

    h2(doc, "6.4  队列与状态")
    para(doc, "每行显示文件名、扩展名、实时进度、段数与操作按钮。状态含义：")
    bullet(doc, "排队 / 处理中 / 完成 / 失败 / 已取消，失败行会给出错误摘要")
    bullet(doc, "完成后出现「✎」预览调整与「↗」打开译文；「×」将文件移出队列")
    para(doc, "底部按钮：开始翻译、取消（正在进行的任务）、添加文件夹、清理已完成。")

    h2(doc, "6.5  输出规则")
    para(doc, "输出文件默认写入设置中的输出目录，文件名追加「_译文」后缀，例如 "
              "「技术服务合同.docx」→「技术服务合同_译文.docx」。同名文件会被覆盖。")
    para(doc, "勾选「同时翻译文件名」后，输出直接使用译名而不再追加后缀，例如 "
              "「季度财务报告.docx」→「Quarterly Financial Report.docx」；"
              "译名中的 \\ / : * ? \" < > | 等非法字符会被自动清理，超过 80 字会截断。")
    tip(doc, "输出目录不可写时（例如指向 Program Files），程序会自动把译文转存到默认输出目录，"
             "并在任务行的警告中提示实际保存位置，不会丢失翻译结果。", "注意")

    # ---------- 7 预览与 AI 调整 ----------
    h1(doc, "7  预览与 AI 调整")
    h2(doc, "7.1  打开预览")
    para(doc, "翻译完成后点击队列行的「✎」进入预览。左栏为原文（只读），右栏为译文（可直接编辑）。")
    image(doc, "05-preview.png", "图 7-1  预览调整：逐段对照与底部 AI 指令栏")

    h2(doc, "7.2  视图切换：逐段对照 / 全文预览")
    para(doc, "预览页顶部提供两种视图，随时可切换，改动在两种视图间实时同步：")
    table(doc, ["视图", "用途与特点"],
          [["逐段对照", "左栏原文、右栏译文逐段并列，适合逐句校对与精细修改"],
           ["全文预览", "按幻灯片页 / PDF 页 / Excel 工作表分组，以连续文档流通篇呈现，"
                     "适合查看整体版式与段落分布；译文同样可直接编辑"]],
          widths=[3.4, 11.8])
    image(doc, "10-preview-full.png", "图 7-2  全文预览：通篇查看译文布局")

    h2(doc, "7.3  显示设置（全文预览）")
    para(doc, "全文预览模式下点顶部「显示设置」可调整呈现方式，三项设置会自动记住，下次打开保持：")
    table(doc, ["设置项", "可选值与效果"],
          [["显示效果", "默认 / 高亮（译文加底色）/ 分割线（译文上方虚线）/ 引用（左侧竖线）/ "
                     "模糊（弱化原文、突出译文）。仅作用于译文，每项都带实时示例"],
           ["译文字体", "默认、微软雅黑、宋体、黑体、楷体、仿宋、Times New Roman、Arial、Calibri、Georgia"],
           ["分布方式", "上下同段（原文在上、译文在下）/ 左右对照（原文左栏、译文右栏）"]],
          widths=[3.4, 11.8])
    image(doc, "12-pv-display-settings.png", "图 7-3  显示设置面板：效果、字体与分布方式")
    tip(doc, "超长文档（上千段）在全文预览下为一次性渲染，打开可能变慢；"
             "此时切回「逐段对照」编辑即可。", "建议")

    h2(doc, "7.4  逐段修改与全部重译")
    bullet(doc, "在右栏直接修改文字，改动即时写回内存；被修改的段落状态点变为蓝色")
    bullet(doc, "切换风格或术语库后点「全部重译」，可整篇重译，已手动修改的段落会被保留")

    h2(doc, "7.5  AI 调整")
    para(doc, "需先在设置中配置大模型 API Key。用法：")
    numbered(doc, "点击左栏原文可选中该段落（再点一次取消），不选则作用于全部。", first=True)
    numbered(doc, "在底部指令框写明要求，例如「更正式一些」「压缩到原句一半」「统一把接口改称 API」。")
    numbered(doc, "点「AI 调整」或按回车，仅将受影响段落送模型，返回后原地刷新。")
    para(doc, "被 AI 改写的段落状态点变为紫色，统计行显示「AI 润色 N」。")

    h2(doc, "7.6  保存输出")
    para(doc, "顶部可切换输出模式，点「保存输出」按当前设置重写文件。"
              "预览中的修改、AI 调整结果都会写入，不会丢失。")

    # ---------- 8 设置详解 ----------
    h1(doc, "8  设置详解")
    para(doc, "设置页固定两列卡片，同行等高；「保存设置」按钮固定在右下角，滚动时始终可见。")
    image(doc, "06-settings.png", "图 8-1  设置页上半部分：常规与大语言模型")

    h2(doc, "8.1  常规")
    table(doc, ["项目", "说明", "默认"],
          [["色调", "跟随系统 / 浅色 / 深色", "跟随系统"],
           ["界面语言", "中文 / English", "中文"],
           ["启动页", "文本翻译 / 查词 / 文档翻译", "文本翻译"],
           ["默认引擎", "公共引擎 / 大语言模型", "公共引擎"],
           ["默认风格", "6 种语体之一", "标准通用"],
           ["输出文件名后缀", "追加到文件名末尾", "_译文"],
           ["输出目录", "点击打开，右侧「…」更换", "程序同级 output"],
           ["启用翻译记忆缓存", "相同内容不再重复请求引擎", "开启"]],
          widths=[4.2, 8.4, 2.6])

    h2(doc, "8.2  大语言模型")
    para(doc, "填写服务商、接口地址、模型与 API Key，点「测试连接」验证后，把默认引擎切到大语言模型即可。")
    table(doc, ["服务商", "接口地址", "常用模型"],
          [["DeepSeek", "https://api.deepseek.com", "deepseek-chat"],
           ["OpenAI", "https://api.openai.com/v1", "gpt-4o-mini"],
           ["阿里百炼 / 通义", "https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-plus"],
           ["智谱 GLM", "https://open.bigmodel.cn/api/paas/v4", "glm-4-air"],
           ["月之暗面 Kimi", "https://api.moonshot.cn/v1", "moonshot-v1-8k"],
           ["自定义", "任意 OpenAI 兼容端点", "—"]],
          widths=[3.4, 8.6, 3.2])
    tip(doc, "API Key 使用 Windows DPAPI 加密存储在本机，不会回传明文；换机器后需重新填写。")

    h2(doc, "8.3  术语库")
    image(doc, "07-settings-down.png", "图 8-2  设置页下半部分：术语库与缓存运行信息")
    para(doc, "内置 6 个库：IT/软件（24）、医疗/生物（22）、法律/合同（21）、机械/制造（22）、"
              "金融/财务（20）、SAP 企业应用（115）。默认启用前两个中的「IT / 软件」与「SAP 企业应用」。")
    bullet(doc, "新建：自建空库，可逐条添加术语")
    bullet(doc, "导入 CSV / Excel：列顺序为 源词、译词、源语言、目标语言，模板见 resources\\glossary_import\\")
    bullet(doc, "删除当前库：仅对自建库有效，内置库只读")

    h2(doc, "8.4  缓存与运行")
    table(doc, ["项目", "说明"],
          [["记忆条目 / 本次命中率", "翻译记忆规模与本次会话的复用比例"],
           ["版本 / 构建时间", "当前程序版本（Ver. + 打包时刻）与构建时间"],
           ["数据目录", "配置、缓存、日志所在路径"],
           ["配置文件", "当前生效配置的完整路径；标注「内嵌出厂配置」表示本程序已内置出厂设置，"
                     "标注「便携降级模式」表示程序目录不可写、配置已转存到系统目录"],
           ["导出配置", "把当前配置另存为随身 JSON，用于备份或迁移到其他机器"],
           ["导入配置", "从之前导出的 JSON 恢复配置，导入后立即刷新界面"],
           ["固化为出厂默认", "把当前配置（含本机加密的 API Key）写入软件目录的「出厂配置.json」，"
                       "随软件文件夹一起迁移。程序目录不可写时会提示失败"],
           ["创建桌面快捷方式", "在当前用户桌面生成指向本程序的快捷方式，重复点击会覆盖更新"],
           ["打开数据目录", "在资源管理器中打开 data 目录"],
           ["清空翻译记忆", "删除全部缓存条目，不可恢复"]],
          widths=[4.6, 10.6])
    image(doc, "13-settings-config.png", "图 8-3  设置页：缓存与运行（配置导出、导入、固化与文件位置）")

    # ---------- 9 托盘 ----------
    h1(doc, "9  托盘与窗口行为")
    bullet(doc, "点击窗口最小化按钮 → 隐藏到系统通知区，任务栏不再占位")
    bullet(doc, "双击托盘图标 → 恢复主窗口")
    bullet(doc, "托盘右键菜单：显示主窗口 / 隐藏到托盘 / 退出")
    bullet(doc, "点击窗口关闭按钮 → 直接退出程序（不会留在托盘）")
    tip(doc, "若托盘图标被系统折叠，可从任务栏「^」中拖出常驻。")

    # ---------- 10 数据与备份 ----------
    h1(doc, "10  数据与备份")
    h2(doc, "10.1  目录结构")
    para(doc, "data\\settings.json　　配置（含加密后的 API Key）", mono=True, size=9.5, space_after=2)
    para(doc, "data\\tm.db　　　　　　翻译记忆缓存", mono=True, size=9.5, space_after=2)
    para(doc, "data\\terms.json　　　　自建术语库", mono=True, size=9.5, space_after=2)
    para(doc, "data\\logs\\app.log　　　运行日志", mono=True, size=9.5, space_after=2)
    para(doc, "出厂配置.json　　　　　便携出厂配置（点「固化为出厂默认」后生成，随软件迁移）",
         mono=True, size=9.5, space_after=2)
    para(doc, "output\\　　　　　　　译文输出", mono=True, size=9.5, space_after=10)

    h2(doc, "10.2  配置随软件分发")
    para(doc, "程序启动时按以下顺序确定配置，后者覆盖前者：")
    table(doc, ["优先级", "来源", "说明"],
          [["1（最低）", "内置默认值", "程序内置的出厂参数"],
           ["2", "内嵌出厂配置", "打包时烧入 EXE 的设置，新机器首次打开即为配置好的状态"],
           ["3", "出厂配置.json", "位于软件目录，由「固化为出厂默认」生成，随文件夹迁移"],
           ["4（最高）", "data\\settings.json", "用户在本机的实际配置"]],
          widths=[2.6, 4.4, 8.2])
    para(doc, "要让配置跟着软件走，有两种方式：")
    numbered(doc, "迁移整个文件夹：把软件目录（含 data 与 output）整体拷贝到新机器或 U 盘。", first=True)
    numbered(doc, "先固化再迁移：在设置页配置好并保存，点「固化为出厂默认」，"
                  "之后即使不带 data 目录，只拷 EXE 与「出厂配置.json」也能恢复配置。")
    tip(doc, "Windows 不允许运行中的程序改写自身 EXE，因此「配置固化进软件」以软件目录下的"
             "「出厂配置.json」实现——效果等同，且随时可以重新固化。", "原理")
    tip(doc, "API Key 使用 Windows DPAPI 加密且绑定本机账户：本机固化后可直接使用；"
             "换电脑会解密失败，届时在设置页重新填写一次即可。", "注意")

    h2(doc, "10.3  备份与迁移")
    para(doc, "整个程序文件夹（含 data 与 output）直接拷贝即可完成迁移或备份。"
              "换到新机器后若 API Key 因 DPAPI 无法解密，重新填写一次即可。")
    para(doc, "输出目录按「相对程序目录」的方式保存，因此把软件整体移到别的盘符或电脑后，"
              "输出目录会自动指向新位置的 output，无需重新设置。")

    h2(doc, "10.4  关键配置项")
    table(doc, ["字段", "含义"],
          [["ui.theme / ui.lang / ui.start_page", "色调、界面语言、启动页"],
           ["engine.active / engine.llm.*", "默认引擎与大模型参数"],
           ["translate.src / tgt / style / mode / term_sets", "默认语言方向、风格、输出模式、术语库"],
           ["output.dir / suffix / auto_save / translate_name",
            "输出目录（相对程序目录存储）、文件名后缀、自动写盘、是否翻译文件名"],
           ["preview.fx / font / dist", "全文预览的显示效果、译文字体、分布方式"],
           ["tm.enabled", "是否启用翻译记忆"]],
          widths=[6.0, 9.2])

    # ---------- 11 FAQ ----------
    h1(doc, "11  常见问题 FAQ")
    qa = [
        ("启动要 6～8 秒，正常吗？",
         "正常。单文件版每次启动都要把约 59 MB 解包到临时目录，属打包方式决定，与机器性能关系不大。"),
        ("公共引擎翻译报错或译文质量差？",
         "公共引擎为免 Key 接口，可能出现限流或个别批次失败。可在设置中配置大模型后切换，质量与稳定性更好。"),
        ("AI 调整点了没反应？",
         "AI 调整必须使用大语言模型，请先在设置中填写 API Key 并「测试连接」成功。"),
        ("PDF 译文超出原来的框怎么办？",
         "程序会逐级缩小字号（最低约 30%）以适配原文字块。极端情况仍可能溢出，预览中以黄点标出，可手动微调。"),
        ("Excel 翻译后图片不见了？",
         "openpyxl 重新保存会丢失内嵌图片，这是库的已知限制，程序在解析时会给出警告。"),
        ("Visio 为什么不能双语对照？",
         "Visio 页面文本节点不支持稳定的段落插入，当前仅支持「仅目标语言」输出。"),
        ("Markdown 里的链接没有翻译？",
         "为保证 URL 不被破坏，链接文字与 URL 整段保持原文，属有意设计。"),
        ("托盘图标消失了？",
         "可能被系统折叠到「^」区域；若确认已退出，重新启动即可。"),
        ("杀毒软件报毒？",
         "单文件打包程序偶发误报，可将程序目录加入信任区；文件哈希可在交付记录中核对。"),
        ("能翻译扫描件 PDF 吗？",
         "不能。当前版本无 OCR，扫描件（无文字层）会提示未找到可翻译文字。"),
        ("提示「写回失败 PermissionError」怎么办？",
         "翻译本身已完成，只是保存译文时被系统拒绝——多半是输出目录指向了 Program Files 等受保护位置。"
         "把输出目录改到普通可写目录即可；新版本会自动转存并在任务警告中提示实际保存位置。"),
        ("启动时报「Access is denied: ...\\data」？",
         "程序目录不可写。请把整个软件文件夹移到普通目录（如 D:\\Gururu 翻译），"
         "或以管理员身份运行一次；新版本会自动降级到 %LOCALAPPDATA%\\Gururu 翻译 而不崩溃。"),
        ("换电脑后配置还在吗？",
         "在。要么整个软件文件夹一起拷贝，要么先在原机器点「固化为出厂默认」再拷贝 EXE 与"
         "「出厂配置.json」。注意 API Key 为 DPAPI 本机加密，换机后需在设置页重新填写。"),
        ("「固化为出厂默认」点了提示失败？",
         "说明程序目录不可写（常见于 Program Files）。把软件移到普通目录后重试即可。"),
        ("全文预览打开很慢？",
         "全文预览为一次性渲染全部段落，上千段的长文档会变慢。切回「逐段对照」即可流畅编辑。"),
    ]
    for q, a in qa:
        h3(doc, "Q：" + q)
        para(doc, "A：" + a, space_after=8)

    # ---------- 12 附录 ----------
    h1(doc, "12  附录")
    h2(doc, "附录 A  快捷键")
    table(doc, ["快捷键", "作用域", "功能"],
          [["Ctrl + Enter", "文本翻译页", "立即翻译"],
           ["↑ / ↓", "查词页候选列表", "移动候选"],
           ["Enter", "查词页", "查询 / 采用选中候选"],
           ["Esc", "查词页 / 弹层", "关闭候选或弹层"]],
          widths=[3.6, 5.0, 6.6])

    h2(doc, "附录 B  支持语言（23 种）")
    para(doc, "中文、English、日本語、한국어、Français、Deutsch、Русский、Español、Português、"
              "Italiano、العربية、ไทย、Tiếng Việt、Bahasa Indonesia、Bahasa Melayu、Türkçe、"
              "Nederlands、Polski、हिन्दी、Українська、Svenska、עברית、Ελληνικά。")

    h2(doc, "附录 C  内置术语库")
    table(doc, ["术语库", "条数", "典型术语"],
          [["IT / 软件", "24", "缓存 cache、接口 API、线程 thread"],
           ["医疗 / 生物", "22", "适应证 indication、剂量 dosage"],
           ["法律 / 合同", "21", "违约金 liquidated damages、不可抗力 force majeure"],
           ["机械 / 制造", "22", "公差 tolerance、装配 assembly"],
           ["金融 / 财务", "20", "应收账款 accounts receivable、摊销 amortization"],
           ["SAP 企业应用", "115", "会计凭证 Accounting Document、成本中心 Cost Center、事务代码 Transaction Code"]],
          widths=[4.0, 2.2, 9.0])

    h2(doc, "附录 D  第三方组件与许可")
    table(doc, ["组件", "用途", "许可"],
          [["PyMuPDF", "PDF 解析与回写", "AGPL（自用无影响，商业分发需遵循 AGPL 或购买商业许可）"],
           ["ECDICT", "内置英汉词典数据源", "MIT"],
           ["python-docx / openpyxl / python-pptx", "Office 文档读写", "MIT / BSD"],
           ["pywebview + WebView2", "界面外壳", "BSD / Microsoft 条款"],
           ["pystray", "系统托盘", "LGPL"]],
          widths=[5.2, 5.0, 5.0])

    h2(doc, "附录 E  版本号规则")
    para(doc, "版本号格式为 Ver. + 打包时刻（YYMMDDHHMM），例如 Ver.2610292129 表示 "
              "2026-10-29 21:29 构建。可在【关于】窗口或设置 → 缓存与运行中查看。")

    para(doc, "", space_after=16)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p.add_run(f"— 本手册对应 {APP_NAME} {VER} —"), size=9.5, color=GREY)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    return OUT


if __name__ == "__main__":
    import json

    toc_file = ROOT / "manual" / "toc.json"
    if toc_file.exists():
        PAGES.update({k: int(v) for k, v in json.loads(toc_file.read_text("utf-8")).items()})
    path = build()
    print(f"已生成：{path}  {path.stat().st_size / 1024:.0f} KB")
