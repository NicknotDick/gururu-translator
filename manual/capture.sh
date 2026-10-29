#!/usr/bin/env bash
# 批量采集手册截图（EXE 版）——每张前清理残留实例
set -u
ROOT="E:/WorkBuddy/文档翻译软件"
DIST="$ROOT/dist"
OUT="$ROOT/manual/shots"
cd "$DIST" || exit 1

shot() {          # $1=文件名 $2=注入脚本 $3=等待毫秒
  taskkill //F //IM "Gururu 翻译.exe" >/dev/null 2>&1
  sleep 1
  rm -f "$OUT/$1.png"
  WB_SHOT="$OUT/$1.png" WB_SHOT_JS="$2" WB_SHOT_DELAY=8 WB_SHOT_WAIT="$3" \
    WB_SELFTEST_MS=$(( 8000 + $3 + 5000 )) timeout 90 "./Gururu 翻译.exe" >/dev/null 2>&1
  SZ=$(stat -c%s "$OUT/$1.png" 2>/dev/null || echo 0)
  echo "$1  ${SZ} bytes"
}

rm -rf data output

shot 01-dict "document.querySelector('[data-page=\"dict\"]').click(); setTimeout(function(){document.getElementById('dictInput').value='apple'; document.getElementById('btnLookup').click();},500);" 9

shot 02-suggest "document.querySelector('[data-page=\"dict\"]').click(); setTimeout(function(){var e=document.getElementById('dictInput'); e.value='appl'; e.dispatchEvent(new Event('input'));},500);" 5

shot 03-text "setTimeout(function(){var t=document.getElementById('srcText'); t.value='供应商应在 2026-12-31 前完成数据库迁移与接口联调，并提交验收报告。'; t.dispatchEvent(new Event('input')); document.getElementById('btnTranslate').click();},400);" 7

shot 04-docs "document.querySelector('[data-page=\"docs\"]').click(); setTimeout(function(){window.pywebview.api.add_files(['$ROOT/samples/sample.docx','$ROOT/samples/sample.xlsx','$ROOT/samples/sample.pdf']).then(function(r){syncJobs(r.jobs);});},500);" 5
