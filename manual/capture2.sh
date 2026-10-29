#!/usr/bin/env bash
# 采集手册截图（第二批）
set -u
ROOT="E:/WorkBuddy/文档翻译软件"
DIST="$ROOT/dist"
OUT="$ROOT/manual/shots"
cd "$DIST" || exit 1

shot() {
  rm -f "$OUT/$1.png"
  WB_SHOT="$OUT/$1.png" WB_SHOT_JS="$2" WB_SHOT_DELAY=6 WB_SHOT_WAIT="$3" \
    WB_SELFTEST_MS=$(( 6000 + $3 + 4000 )) timeout 90 "./Gururu 翻译.exe" >/dev/null 2>&1
  [ -f "$OUT/$1.png" ] && echo "OK  $1" || echo "FAIL $1"
}

rm -rf data output

# 预览调整（先跑一个文档作业再打开预览）
PREVIEW="document.querySelector('[data-page=\"docs\"]').click();
window.pywebview.api.add_files(['$ROOT/samples/sample.docx']);
setTimeout(function(){ window.pywebview.api.start_jobs({src:'zh',tgt:'en',style:'general',term_sets:['it','sap'],mode:'bilingual',engine:'public'}); }, 1200);
setTimeout(function(){ window.pywebview.api.jobs().then(function(r){ syncJobs(r.jobs); var j=r.jobs.filter(function(x){return x.status==='done';})[0]; if(j){ openPreview(j.id).then(function(){ setTimeout(function(){ var s=document.querySelectorAll('.pv-src'); if(s[1]) s[1].click(); }, 500); }); } }); }, 6500);"
shot 05-preview "$PREVIEW" 10

shot 06-settings "document.querySelector('[data-page=\"settings\"]').click();" 3

shot 07-settings-down "document.querySelector('[data-page=\"settings\"]').click(); setTimeout(function(){ var el=document.querySelector('.settings'); el.scrollTop = el.scrollHeight; }, 400);" 3

shot 08-about "document.getElementById('cornerAbout').click();" 3
