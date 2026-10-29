#!/usr/bin/env bash
# 采集手册截图（开发模式，界面与 EXE 一致）
set -u
ROOT="E:/WorkBuddy/文档翻译软件"
OUT="$ROOT/manual/shots"
cd "$ROOT" || exit 1

shot() {          # $1=文件名 $2=注入脚本 $3=等待秒
  taskkill //F //IM "Gururu 翻译.exe" >/dev/null 2>&1
  sleep 0.5
  rm -f "$OUT/$1.png"
  WB_SHOT="$OUT/$1.png" WB_SHOT_JS="$2" WB_SHOT_DELAY=3 WB_SHOT_WAIT="$3" \
    WB_SELFTEST_MS=$(( 3000 + $3 * 1000 + 4000 )) timeout 60 python -W ignore -m app.main >/dev/null 2>&1
  SZ=$(stat -c%s "$OUT/$1.png" 2>/dev/null || echo 0)
  echo "$1  ${SZ} bytes"
}

shot 01-dict "document.querySelector('[data-page=\"dict\"]').click(); setTimeout(function(){document.getElementById('dictInput').value='apple'; document.getElementById('btnLookup').click();},400);" 8

shot 02-suggest "document.querySelector('[data-page=\"dict\"]').click(); setTimeout(function(){var e=document.getElementById('dictInput'); e.value='appl'; e.dispatchEvent(new Event('input'));},400);" 4

shot 03-text "setTimeout(function(){var t=document.getElementById('srcText'); t.value='供应商应在 2026-12-31 前完成数据库迁移与接口联调，并提交验收报告。'; t.dispatchEvent(new Event('input')); document.getElementById('btnTranslate').click();},300);" 6

shot 04-docs "document.querySelector('[data-page=\"docs\"]').click(); setTimeout(function(){window.pywebview.api.add_files(['$ROOT/samples/sample.docx','$ROOT/samples/sample.xlsx','$ROOT/samples/sample.pdf']).then(function(r){syncJobs(r.jobs);});},400);" 4

PREVIEW="document.querySelector('[data-page=\"docs\"]').click();
window.pywebview.api.add_files(['$ROOT/samples/sample.docx']);
setTimeout(function(){ window.pywebview.api.start_jobs({src:'zh',tgt:'en',style:'general',term_sets:['it','sap'],mode:'bilingual',engine:'public'}); }, 1200);
setTimeout(function(){ window.pywebview.api.jobs().then(function(r){ syncJobs(r.jobs); var j=r.jobs.filter(function(x){return x.status==='done';})[0]; if(j){ openPreview(j.id).then(function(){ setTimeout(function(){ var s=document.querySelectorAll('.pv-src'); if(s[1]) s[1].click(); }, 500); }); } }); }, 6000);"
shot 05-preview "$PREVIEW" 9

shot 06-settings "document.querySelector('[data-page=\"settings\"]').click();" 3

shot 07-settings-down "document.querySelector('[data-page=\"settings\"]').click(); setTimeout(function(){ var el=document.querySelector('.settings'); el.scrollTop = el.scrollHeight; }, 400);" 3

shot 08-about "document.getElementById('cornerAbout').click();" 3
