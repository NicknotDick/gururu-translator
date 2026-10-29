# 第三方组件与许可声明

Gururu 翻译 本体源码采用 **MIT License**（见 `LICENSE`）。程序依赖以下第三方组件，
其许可各自独立，**编译产物（EXE）中包含它们**：

| 组件 | 用途 | 许可 | 源码地址 |
|---|---|---|---|
| PyMuPDF | PDF 解析与译文回填 | **AGPL-3.0**（商业分发需遵循 AGPL 或购买 Artifex 商业许可） | https://github.com/pymupdf/PyMuPDF |
| ECDICT | 内置英汉词典数据源（裁剪 3 万词） | MIT | https://github.com/skywind3000/ECDICT |
| python-docx | Word 读写 | MIT | https://github.com/python-openxml/python-docx |
| openpyxl | Excel 读写 | MIT | https://foss.heptapod.net/openpyxl/openpyxl |
| python-pptx | PowerPoint 读写 | MIT | https://github.com/scanny/python-pptx |
| pywebview + WebView2 | 界面外壳 | BSD-3-Clause / Microsoft 条款 | https://github.com/r0x0r/pywebview |
| pystray | 系统托盘 | LGPL-3.0 | https://github.com/moses-palmer/pystray |
| Pillow | 图标与截图 | HPND | https://github.com/python-pillow/Pillow |

## 关于 AGPL 的重要提示

本仓库源码为 MIT，但**随 Release 分发的 `GururuTranslator-*.exe` 内嵌了 AGPL-3.0 的 PyMuPDF**。
若你要对外分发该可执行文件，AGPL 要求你同时以相同方式向接收者提供「对应源码」。

可行做法三选一：

1. 保留 EXE 分发，并在分发页面显著位置提供本仓库完整源码链接与 PyMuPDF 源码链接（上方表格已列）；
2. 仅分发源码，不发布预编译 EXE（删除 Release 中的 `.exe` 附件）；
3. 移除 PDF 相关功能后重新打包，或为 PyMuPDF 购买 Artifex 商业许可。

> 个人自用不构成分发，不受上述约束。
