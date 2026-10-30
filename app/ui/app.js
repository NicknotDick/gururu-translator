/* 文档翻译 · 前端逻辑（无框架，原生 DOM） */
'use strict';

const $ = (id) => document.getElementById(id);

/* ================= 多语言 ================= */
const EN = {
  'Gururu 翻译': 'Gururu Translate',
  '文本翻译': 'Text',
  '文档翻译': 'Documents',
  '查词': 'Dictionary',
  '启动页': 'Start page',
  '在线': 'online',
  '本地': 'local',
  '百科（维基摘要）': 'Encyclopedia (Wikipedia)',
  '词': 'W',
  '设置': 'Settings',
  '文': 'T',
  '档': 'D',
  '引擎：': 'Engine: ',
  '公共（免 Key）': 'Free (no key)',
  '公共引擎（免 Key）': 'Free engine (no key)',
  '大语言模型': 'LLM',
  '翻译记忆加载中…': 'Loading TM…',
  '原文': 'Source',
  '译文': 'Translation',
  '术语命中会自动锁定': 'Terms are locked automatically',
  '引擎': 'Engine',
  '风格': 'Style',
  '清空': 'Clear',
  '复制译文': 'Copy',
  '翻译': 'Translate',
  '翻译选项': 'Options',
  '翻译模式': 'Mode',
  '仅目标语言': 'Target only',
  '双语对照': 'Bilingual',
  '术语库': 'Glossary',
  '未启用': 'None',
  '其他': 'Other',
  '同时翻译页眉页脚': 'Headers & footers',
  '完成后自动输出译文': 'Auto-save output',
  '输出目录': 'Output folder',
  '点击选择文件': 'Click to choose',
  '或 把文件拖到这里': 'or drag files here',
  '支持 .docx · .xlsx/.xlsm · .pptx · .pdf · .vsdx · .md · .txt · .epub，也可直接拖入整个文件夹':
    'Supported: .docx · .xlsx/.xlsm · .pptx · .pdf · .vsdx · .md · .txt · .epub — folders can be dropped too',
  '松开即可加入队列': 'Release to add to the queue',
  '支持文档与文件夹，不受支持的文件会自动跳过': 'Documents and folders; unsupported files are skipped',
  '队列为空，先添加文件': 'Queue is empty — add files first',
  '开始翻译': 'Start',
  '取消': 'Cancel',
  '添加文件夹': 'Add folder',
  '清理已完成': 'Clear finished',
  '常规': 'General',
  '色调': 'Theme',
  '跟随系统': 'System',
  '浅色': 'Light',
  '深色': 'Dark',
  '界面语言': 'Language',
  '默认引擎': 'Default engine',
  '公共引擎': 'Free engine',
  '默认风格': 'Default style',
  '输出文件名后缀': 'Filename suffix',
  '翻译文件名': 'Translate file names',
  '同时翻译文件名': 'Translate file names too',
  '在「文档翻译」页勾选「同时翻译文件名」后，输出直接使用译名，此选项失效。':
    'Once "Translate file names" is checked on the Documents page, output uses the translated name and this is ignored.',
  '勾选后输出文件直接使用译名（非法字符自动清理），设置中的文件名后缀失效。':
    'Output files use the translated name (illegal chars removed); the suffix option in Settings is ignored.',
  '显示设置': 'Display settings',
  '效果': 'Effect',
  '译文字体': 'Translation font',
  '分布方式': 'Layout',
  '上下同段': 'Stacked',
  '左右对照': 'Side by side',
  '默认': 'Default',
  '高亮': 'Highlight',
  '分割线': 'Divider',
  '引用': 'Quote',
  '模糊': 'Blur',
  '逐段对照': 'By segment',
  '全文预览': 'Full text',
  '启用翻译记忆缓存': 'Translation memory',
  '大语言模型（可选）': 'Large language model (optional)',
  '服务商模板': 'Provider',
  '接口地址': 'Endpoint',
  '模型': 'Model',
  '温度': 'Temperature',
  'API Key（本机加密存储，不回传明文）': 'API key (stored encrypted locally)',
  '测试连接': 'Test',
  '并发数': 'Concurrency',
  '单批字符上限': 'Batch chars',
  '新建': 'New',
  '导入 CSV / Excel': 'Import CSV / Excel',
  '删除当前库': 'Delete',
  '添加术语': 'Add term',
  '缓存与运行': 'Cache & runtime',
  '记忆条目': 'TM entries',
  '本次命中率': 'Hit rate',
  '数据目录': 'Data folder',
  '版本': 'Version',
  '构建时间': 'Built',
  '打开数据目录': 'Open data folder',
  '创建桌面快捷方式': 'Create desktop shortcut',
  '导出配置': 'Export config',
  '导入配置': 'Import config',
  '固化为出厂默认': 'Save as factory defaults',
  '已固化为出厂默认：': 'Saved as factory defaults: ',
  '固化失败：程序目录不可写': 'Failed: program folder is read-only',
  '配置文件': 'Config file',
  '配置已导出：': 'Config exported: ',
  '配置已导入': 'Configuration imported',
  '导出失败': 'Export failed',
  '导入失败': 'Import failed',
  '（内嵌出厂配置）': ' (embedded defaults)',
  '（便携降级模式）': ' (fallback mode)',
  '清空翻译记忆': 'Clear TM',
  '保存设置': 'Save settings',
  '预览调整': 'Review',
  'AI 模型': 'AI model',
  '全部重译': 'Retranslate all',
  '关闭': 'Close',
  '保存输出': 'Save output',
  '点击左侧原文可选中段落，未选中时作用于全部':
    'Click a source line to select; nothing selected = apply to all',
  'AI 调整': 'AI adjust',
  '运行环境': 'Runtime',
  '支持格式': 'Formats',
  '作者：Gururu Nick': 'Author: Gururu Nick',
};

const PH_EN = {
  '在此粘贴或输入要翻译的内容，Ctrl+Enter 立即翻译…':
    'Paste or type text here, Ctrl+Enter to translate…',
  '译文显示在这里，可直接修改后复制': 'Translation appears here — edit freely before copying',
  '源词': 'Source term',
  '译词': 'Target term',
  '告诉 AI 怎么改，例如：更正式 / 更简洁 / 保留被动语态 / 统一术语为 API':
    'Tell the AI how to revise, e.g. more formal / shorter / keep passive voice',
  '输入英文单词或短语，回车查询': 'Type a word or phrase, press Enter',
};

const TT_EN = {
  '源语言': 'Source language',
  '目标语言': 'Target language',
  '交换语言': 'Swap languages',
  '在资源管理器中打开该目录': 'Open this folder in File Explorer',
  '更改输出目录': 'Change output folder',
  '关于': 'About',
  '重译所用引擎': 'Engine used for retranslation',
};

const PH_IDS = ['srcText', 'tgtText', 'setBaseUrl', 'newTermSrc', 'newTermTgt', 'pvInstr', 'dictInput'];
const TT_IDS = ['srcLang', 'tgtLang', 'swapBtn', 'btnOutDir', 'btnOutDirPick',
                'btnSetOutDir', 'btnSetOutDirPick', 'cornerAbout', 'pvEngine'];

const _origText = new WeakMap();
const _origAttr = new WeakMap();

const L = (zh, en) => (state.lang === 'en' ? en : zh);
const nm = (o) => (!o ? '' : (state.lang === 'en' ? (o.name_en || o.name) : o.name));

function translateStatic() {
  const en = state.lang === 'en';
  const map = en ? EN : null;
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  nodes.forEach((node) => {
    const p = node.parentNode;
    if (!p || /^(SCRIPT|STYLE)$/.test(p.nodeName)) return;
    if (!_origText.has(node)) _origText.set(node, node.nodeValue);
    const raw = _origText.get(node) || '';
    const base = raw.trim();
    if (!base) { node.nodeValue = raw; return; }
    const tr = map ? map[base] : undefined;
    node.nodeValue = tr === undefined ? raw : raw.replace(base, tr);
  });

  PH_IDS.forEach((id) => {
    const el = $(id);
    if (!el) return;
    let rec = _origAttr.get(el);
    if (!rec) { rec = { ph: el.getAttribute('placeholder'), tt: el.getAttribute('title') }; _origAttr.set(el, rec); }
    if (rec.ph != null) el.setAttribute('placeholder', en ? (PH_EN[rec.ph] || rec.ph) : rec.ph);
    if (rec.tt != null) el.setAttribute('title', en ? (TT_EN[rec.tt] || rec.tt) : rec.tt);
  });
  TT_IDS.forEach((id) => {
    const el = $(id);
    if (!el) return;
    let rec = _origAttr.get(el);
    if (!rec) { rec = { ph: el.getAttribute('placeholder'), tt: el.getAttribute('title') }; _origAttr.set(el, rec); }
    if (rec.tt != null) el.setAttribute('title', en ? (TT_EN[rec.tt] || rec.tt) : rec.tt);
  });
}

function applyLang(lang, persist) {
  state.lang = lang === 'en' ? 'en' : 'zh';
  document.documentElement.lang = state.lang === 'en' ? 'en' : 'zh-CN';
  translateStatic();
  document.querySelectorAll('#langSeg button').forEach((b) => {
    b.classList.toggle('active', b.dataset.lang === state.lang);
  });
  countText();
  refreshEngineChip();
  updateTermButtons();
  updateDirButtons();
  if (state.lastTm) refreshTm(state.lastTm);
  refillOptions();
  if (state.jobs.size) renderQueue();
  if (state.pvDoc) { updatePvStat(); state.pvShown = 0; $('pvBody').innerHTML = ''; renderPv(); }
  updateSelInfo();
  if (persist) {
    if (state.boot) {
      state.boot.settings = Object.assign({}, state.boot.settings, {
        ui: Object.assign({}, (state.boot.settings || {}).ui, { lang: state.lang }),
      });
    }
    api('save_settings', { ui: { lang: state.lang } }).catch(() => {});
  }
}

const state = {
  boot: null,
  langs: [], styles: [], termSets: [], providers: {},
  jobs: new Map(),
  sel: { text: [], doc: [], pv: [] },
  seq: 0,
  pvJid: null,
  pvDoc: null,
  pvSel: new Set(),
  pvShown: 0,
  pvView: 'seg',
  pvCfg: { fx: 'default', font: '', dist: 'stack' },
  outDir: '',
  theme: 'auto',
  lang: 'zh',
  timer: null,
  lastRender: 0,
};

/* ---------------- 基础工具 ---------------- */
function api(name, ...args) {
  const a = window.pywebview && window.pywebview.api;
  if (!a || !a[name]) return Promise.reject(new Error(L('接口未就绪：', 'API not ready: ') + name));
  return a[name](...args);
}

let toastTimer = null;
function toast(msg, kind = '') {
  const el = $('toast');
  el.textContent = msg;
  el.className = 'toast show ' + kind;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.className = 'toast ' + kind; }, 2600);
}

function esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function fmtSize(n) {
  if (!n) return '-';
  if (n < 1024) return n + ' B';
  if (n < 1048576) return (n / 1024).toFixed(0) + ' KB';
  return (n / 1048576).toFixed(1) + ' MB';
}

function langName(code) {
  const l = state.langs.find((x) => x.code === code);
  if (!l) return code;
  return l.native || l.cn;
}

/* ---------------- 启动 ---------------- */
window.addEventListener('pywebviewready', boot);

async function boot() {
  try {
    const b = await api('bootstrap');
    state.boot = b;
    state.langs = b.languages || [];
    state.styles = b.styles || [];
    state.termSets = b.term_sets || [];
    state.providers = b.providers || {};

    const s = b.settings || {};
    const st = s.translate || {};
    state.sel.text = (st.term_sets || []).slice();
    state.sel.doc = (st.term_sets || []).slice();
    state.sel.pv = (st.term_sets || []).slice();

    fillLangs(st.src || 'zh', st.tgt || 'en');
    fillStyles('textStyle', st.style);
    fillStyles('docStyle', st.style);
    fillStyles('pvStyle', st.style);
    fillStyles('setStyle', st.style);

    const vp = b.version_parts || {};
    $('brandName').textContent = b.title || 'Gururu 翻译';
    $('appVer').textContent = b.version || '';
    $('appBuild').textContent = vp.date ? vp.date + ' ' + vp.time : '';
    $('dataDir').textContent = b.data_dir || '';
    if (b.data_fallback) {
      $('dataDir').textContent += (L('（程序目录不可写，已自动转存到此处）', ' (program folder is read-only; data saved here instead)'));
    }
    // 配置文件实际位置 + 是否内嵌了出厂配置
    api('settings_path').then((r) => {
      const el = $('cfgFile');
      if (!el || !r || !r.ok) return;
      const p = r.path || '';
      el.textContent = p ? (p.length > 36 ? '…' + p.slice(-34) : p) : '—';
      el.title = p;
      if (r.factory) el.textContent += L('（内嵌出厂配置）', ' (embedded defaults)');
      else if (!r.portable) el.textContent += L('（便携降级模式）', ' (fallback mode)');
    });
    state.outDir = b.output_dir || '';
    applyLang((((s.ui || {}).lang) || 'zh'), false);
    refreshTm(b.tm);
    applyTheme(((s.ui || {}).theme) || 'auto', false);
    try {
      const mq = window.matchMedia('(prefers-color-scheme: light)');
      mq.addEventListener('change', () => { if (state.theme === 'auto') applyTheme('auto', false); });
    } catch (e) { /* 忽略 */ }
    refreshEngineChip();
    updateTermButtons();
    loadSettingsForm(b);
    bindEvents();
    initDnd();
    pollLoop();
    const startPage = ((s.ui || {}).start_page) || 'text';
    if (startPage !== 'text') switchPage(startPage);
  } catch (e) {
    toast(L('初始化失败：', 'Init failed: ') + e.message, 'err');
  } finally {
    document.body.classList.remove('booting');
  }
}

function fillLangs(src, tgt) {
  const opts = state.langs.map((l) => `<option value="${l.code}">${esc(l.native || l.cn)}</option>`).join('');
  $('srcLang').innerHTML = opts;
  $('tgtLang').innerHTML = opts;
  $('srcLang').value = src;
  $('tgtLang').value = tgt;
}

function fillStyles(id, cur) {
  const el = $(id);
  if (!el) return;
  el.innerHTML = state.styles
    .map((s) => `<option value="${s.id}">${esc(nm(s))}</option>`).join('');
  if (cur) el.value = cur;
}

function refreshEngineChip() {
  const s = state.boot.settings || {};
  const active = (s.engine || {}).active || 'public';
  const hasKey = state.boot.has_key;
  const label = active === 'llm'
    ? (hasKey ? L('大语言模型', 'LLM') : L('大模型（未配 Key）', 'LLM (no key)'))
    : L('公共（免 Key）', 'Free (no key)');
  $('engineChip').innerHTML = L('引擎：', 'Engine: ') + '<b>' + esc(label) + '</b>';
}

function refreshTm(t) {
  if (!t) return;
  state.lastTm = t;
  $('tmInfo').textContent = L(
    `记忆 ${t.entries} 条 · 命中率 ${(t.hit_rate * 100).toFixed(0)}%`,
    `TM ${t.entries} · hit ${(t.hit_rate * 100).toFixed(0)}%`
  );
  if ($('tmEntries')) {
    $('tmEntries').textContent = t.entries;
    $('tmRate').textContent = (t.hit_rate * 100).toFixed(0) + '%';
  }
}

/* ---------------- 事件绑定 ---------------- */
function bindEvents() {
  document.querySelectorAll('.nav-item').forEach((b) => {
    b.onclick = () => switchPage(b.dataset.page);
  });

  $('swapBtn').onclick = () => {
    const a = $('srcLang').value, b = $('tgtLang').value;
    $('srcLang').value = b;
    $('tgtLang').value = a;
  };

  $('srcText').addEventListener('input', () => countText());
  $('tgtText').addEventListener('input', () => countText());
  $('srcText').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); doTranslate(); }
  });
  $('btnTranslate').onclick = doTranslate;
  $('btnClear').onclick = () => { $('srcText').value = ''; $('tgtText').value = ''; countText(); };
  $('btnCopy').onclick = async () => {
    const t = $('tgtText').value;
    if (!t) return;
    try { await navigator.clipboard.writeText(t); toast(L('已复制', 'Copied'), 'ok'); }
    catch { $('tgtText').select(); document.execCommand('copy'); toast(L('已复制', 'Copied'), 'ok'); }
  };

  setupTermSel('textTermsWrap', 'textTermsBtn', 'textTermsPop', 'text');
  setupTermSel('docTermsWrap', 'docTermsBtn', 'docTermsPop', 'doc');
  setupTermSel('pvTermsWrap', 'pvTermsBtn', 'pvTermsPop', 'pv', () => pvRetranslateAll(true));

  $('dropzone').onclick = addFiles;
  $('btnAddFolder').onclick = addFolder;
  $('btnStart').onclick = startJobs;
  $('btnCancel').onclick = async () => { await api('cancel_jobs'); toast(L('正在取消…', 'Cancelling…')); };
  $('btnClearDone').onclick = async () => {
    const r = await api('clear_finished');
    if (r.jobs) syncJobs(r.jobs);
  };
  $('btnOutDir').onclick = openOutDir;
  $('btnOutDirPick').onclick = pickOutDir;
  $('btnSetOutDir').onclick = openOutDir;
  $('btnSetOutDirPick').onclick = pickOutDir;
  $('outDirLabel').onclick = openOutDir;
  $('cornerAbout').onclick = openAbout;
  $('btnOpenData').onclick = () => api('open_path', (state.boot || {}).data_dir || '');
  $('cfgFileRow').onclick = () => api('open_path', (state.boot || {}).data_dir || '');
  $('btnExportSettings').onclick = async () => {
    const r = await api('export_settings');
    if (!r || r.cancelled) return;
    if (!r.ok) { toast(r.error || L('导出失败', 'Export failed'), 'err'); return; }
    toast(L('配置已导出：', 'Config exported: ') + r.path, 'ok');
  };
  $('btnImportSettings').onclick = async () => {
    const r = await api('import_settings');
    if (!r || r.cancelled) return;
    if (!r.ok) { toast(r.error || L('导入失败', 'Import failed'), 'err'); return; }
    loadSettingsForm({ settings: r.settings, ...(state.boot || {}) });
    toast(L('配置已导入', 'Configuration imported'), 'ok');
  };
  $('btnFreezeSettings').onclick = async () => {
    const r = await api('freeze_settings');
    if (!r || !r.ok) {
      toast(r.error || L('固化失败：程序目录不可写', 'Failed: program folder is read-only'), 'err');
      return;
    }
    toast(L('已固化为出厂默认：', 'Saved as factory defaults: ') + r.path, 'ok');
  };
  $('btnShortcut').onclick = async () => {
    const r = await api('create_desktop_shortcut');
    if (!r.ok) { toast(r.error || L('创建失败', 'Failed'), 'err'); return; }
    toast(L('已在桌面创建快捷方式', 'Desktop shortcut created'), 'ok');
  };
  $('btnLookup').onclick = doLookup;
  $('dictInput').addEventListener('input', onDictInput);
  $('dictInput').addEventListener('blur', () => setTimeout(closeSug, 150));
  $('dictInput').addEventListener('keydown', (e) => {
    if (!sugOpen) {
      if (e.key === 'Enter') doLookup();
      return;
    }
    if (e.key === 'ArrowDown') { e.preventDefault(); setSugActive(sugActive + 1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setSugActive(sugActive - 1); }
    else if (e.key === 'Escape') { closeSug(); }
    else if (e.key === 'Enter') {
      e.preventDefault();
      if (sugActive >= 0) pickSug(sugActive);
      else { closeSug(); doLookup(); }
    }
  });
  document.querySelectorAll('#langSeg button').forEach((b) => {
    b.onclick = () => applyLang(b.dataset.lang, true);
  });
  $('btnAbClose').onclick = () => $('about').classList.add('hidden');
  $('btnAbData').onclick = () => api('open_path', (state.boot || {}).data_dir || '');
  $('about').addEventListener('click', (e) => {
    if (e.target.id === 'about') $('about').classList.add('hidden');
  });
  document.querySelectorAll('#themeSeg button').forEach((b) => {
    b.onclick = () => applyTheme(b.dataset.theme, true);
  });
  $('btnSaveSettings').onclick = saveSettings;
  $('btnTest').onclick = testEngine;
  $('setProvider').onchange = applyProvider;
  $('btnClearTm').onclick = async () => {
    if (!confirm(L('确定清空全部翻译记忆？此操作不可恢复。',
      'Clear all translation memory? This cannot be undone.'))) return;
    const r = await api('tm_clear');
    refreshTm(r); toast(L('已清空 ' + r.removed + ' 条', `Cleared ${r.removed} entries`), 'ok');
  };
  $('setTermSet').onchange = loadTermDetail;
  $('btnNewSet').onclick = newTermSet;
  $('btnDelSet').onclick = delTermSet;
  $('btnAddTerm').onclick = addTerm;
  $('btnImportTerms').onclick = importTerms;

  $('btnPvClose').onclick = closePreview;
  $('btnPvSave').onclick = savePreview;
  $('btnPvRetrans').onclick = () => pvRetranslateAll(false);
  $('pvStyle').onchange = () => pvRetranslateAll(true);
  $('btnPvAi').onclick = aiRefine;
  $('pvInstr').addEventListener('keydown', (e) => { if (e.key === 'Enter') aiRefine(); });
  $('pvMode').onchange = () => { if (state.pvDoc) renderPv(); };
  const vs = $('pvViewSeg');
  if (vs) {
    vs.querySelectorAll('button').forEach((b) => {
      b.onclick = () => setPvView(b.dataset.view);
    });
  }
  const cfgBtn = $('btnPvCfg');
  if (cfgBtn) {
    cfgBtn.onclick = (e) => { e.stopPropagation(); togglePvCfg(); };
  }
  const cfgPop = $('pvCfgPop');
  if (cfgPop) {
    cfgPop.onclick = (e) => e.stopPropagation();
  }
  document.querySelectorAll('input[name=pvFx]').forEach((r) => {
    r.onchange = () => setPvCfg('fx', r.value);
  });
  const cfgFont = $('pvCfgFont');
  if (cfgFont) cfgFont.onchange = () => setPvCfg('font', cfgFont.value);
  const cfgDist = $('pvCfgDist');
  if (cfgDist) cfgDist.onchange = () => setPvCfg('dist', cfgDist.value);
  document.addEventListener('click', () => {
    const p = $('pvCfgPop');
    if (p && !p.classList.contains('hidden')) p.classList.add('hidden');
  });

  document.querySelectorAll('#page-settings input').forEach((el) => {
    el.addEventListener('keydown', (e) => { if (e.key === 'Enter') saveSettings(); });
  });
}

function switchPage(name) {
  document.querySelectorAll('.nav-item').forEach((b) => b.classList.toggle('active', b.dataset.page === name));
  document.querySelectorAll('.page').forEach((p) => p.classList.toggle('active', p.id === 'page-' + name));
  if (name === 'settings') { loadSettingsForm(state.boot); loadTermOptions(); }
  if (name === 'dict') { const el = $('dictInput'); if (el) el.focus(); }
}

/* ---------------- 拖放文件 ----------------
   页面 JS 拿不到拖入文件的绝对路径，这里只负责高亮与阻止默认行为；
   真正的入队由 Python 侧的 document drop 监听完成（见 app/core/dnd.py）。 */
let dndDepth = 0;

function dndHasFiles(e) {
  const dt = e && e.dataTransfer;
  if (!dt) return false;
  const types = dt.types ? Array.prototype.slice.call(dt.types) : [];
  return types.indexOf('Files') >= 0;
}

function setDnd(on) {
  const dz = $('dropzone');
  if (dz) dz.classList.toggle('drag', !!on);
  const mask = $('dndMask');
  if (mask) mask.classList.toggle('show', !!on);
}

function initDnd() {
  document.addEventListener('dragenter', (e) => {
    if (!dndHasFiles(e)) return;
    e.preventDefault();
    dndDepth += 1;
    setDnd(true);
  });
  document.addEventListener('dragover', (e) => {
    if (!dndHasFiles(e)) return;
    e.preventDefault();
    if (e.dataTransfer) e.dataTransfer.dropEffect = 'copy';
    setDnd(true);
  });
  document.addEventListener('dragleave', (e) => {
    if (!dndHasFiles(e)) return;
    dndDepth = Math.max(0, dndDepth - 1);
    if (!dndDepth) setDnd(false);
  });
  document.addEventListener('drop', (e) => {
    if (!dndHasFiles(e)) return;
    e.preventDefault();
    dndDepth = 0;
    setDnd(false);
  });
}

/* ---------------- 术语库多选 ---------------- */
function setupTermSel(wrapId, btnId, popId, key, onChange) {
  const btn = $(btnId), pop = $(popId);
  btn.onclick = (e) => {
    e.stopPropagation();
    document.querySelectorAll('.ts-pop').forEach((p) => { if (p !== pop) p.classList.remove('open'); });
    pop.classList.toggle('open');
  };
  pop.onclick = (e) => e.stopPropagation();
  pop.addEventListener('change', (e) => {
    const cb = e.target;
    if (cb.type !== 'checkbox') return;
    const id = cb.value;
    const arr = state.sel[key];
    const i = arr.indexOf(id);
    if (cb.checked && i < 0) arr.push(id);
    if (!cb.checked && i >= 0) arr.splice(i, 1);
    renderTermPop(key, popId);
    updateTermButtons();
    if (onChange) onChange();
  });
  document.addEventListener('click', () => pop.classList.remove('open'));
  renderTermPop(key, popId);
}

function renderTermPop(key, popId) {
  const pop = $(popId);
  pop.innerHTML = state.termSets.map((s) => {
    const on = state.sel[key].includes(s.id) ? 'checked' : '';
    return `<label><input type="checkbox" value="${s.id}" ${on}>${esc(nm(s))}<span class="cnt">${s.count}</span></label>`;
  }).join('') || `<div class="dim" style="padding:8px">${L('暂无术语库', 'No glossaries')}</div>`;
}

function updateTermButtons() {
  const label = (arr) => {
    if (!arr.length) return L('术语库：未启用', 'Glossary: none');
    const names = arr.map((id) => nm(state.termSets.find((s) => s.id === id)) || id);
    return L('术语库：', 'Glossary: ') + names.join(' / ');
  };
  $('textTermsBtn').textContent = label(state.sel.text);
  $('docTermsBtn').textContent = label(state.sel.doc);
  $('pvTermsBtn').textContent = state.sel.pv.length ? label(state.sel.pv) : L('术语库', 'Glossary');
}

/* ---------------- 文本翻译 ---------------- */
function countText() {
  const s = $('srcText').value, t = $('tgtText').value;
  $('srcMeta').textContent = L(s.length + ' 字', s.length + ' chars');
  $('tgtMeta').textContent = L(t.length + ' 字', t.length + ' chars');
  const sl = s ? s.split('\n').length : 0;
  const tl = t ? t.split('\n').length : 0;
  $('srcLines').textContent = L(sl + ' 行', sl + (sl === 1 ? ' line' : ' lines'));
  $('tgtLines').textContent = L(tl + ' 行', tl + (tl === 1 ? ' line' : ' lines'));
}

function textPatch() {
  return {
    src: $('srcLang').value,
    tgt: $('tgtLang').value,
    style: $('textStyle').value,
    term_sets: state.sel.text.slice(),
    engine: $('textEngine').value,
  };
}

async function doTranslate() {
  const text = $('srcText').value.trim();
  if (!text) { toast(L('请输入要翻译的文本', 'Enter some text first')); return; }
  const btn = $('btnTranslate');
  if ($('srcLang').value === $('tgtLang').value) {
    toast(L('源语言与目标语言相同', 'Source and target languages are identical'), 'err');
    return;
  }
  btn.disabled = true;
  btn.innerHTML = '<span class="spin"></span> ' + L('翻译中', 'Translating');
  $('tgtEngine').textContent = '';
  try {
    const r = await api('translate_text', text, textPatch());
    if (!r.ok) { toast(r.error || L('翻译失败', 'Translation failed'), 'err'); return; }
    $('tgtText').value = r.text;
    $('tgtEngine').textContent = L('引擎：', 'Engine: ') + (r.engine || '-')
      + (r.term_note ? ' · ' + r.term_note : '');
    countText();
    if (r.term_note) toast(r.term_note, 'err');
  } catch (e) {
    toast(L('请求失败：', 'Request failed: ') + e.message, 'err');
  } finally {
    btn.disabled = false;
    btn.textContent = L('翻译', 'Translate');
  }
}

/* ---------------- 文档翻译 ---------------- */
async function addFiles() {
  const r = await api('add_files');
  if (r.skipped && r.skipped.length) toast(L('已跳过：', 'Skipped: ') + r.skipped.slice(0, 3).join(L('、', ', ')), 'err');
  if (r.jobs) syncJobs(r.jobs);
}

async function addFolder() {
  const r = await api('add_folder');
  if (r.error) { toast(r.error, 'err'); return; }
  if (!r.added) toast(L('文件夹内没有受支持的文档', 'No supported documents in that folder'));
  if (r.jobs) syncJobs(r.jobs);
}

function docPatch() {
  const mode = [...document.querySelectorAll('input[name=docMode]')].find((x) => x.checked);
  return {
    src: $('srcLang').value,
    tgt: $('tgtLang').value,
    style: $('docStyle').value,
    term_sets: state.sel.doc.slice(),
    mode: mode ? mode.value : 'target_only',
    engine: $('docEngine').value,
    skip_header_footer: !$('optHeader').checked,
  };
}

async function startJobs() {
  const patch = docPatch();
  if (patch.src === patch.tgt) {
    toast(L('源语言与目标语言相同', 'Source and target languages are identical'), 'err');
    return;
  }
  const r = await api('start_jobs', patch);
  if (!r.ok) { toast(r.error || L('无法开始', 'Cannot start'), 'err'); return; }
  if (r.jobs) syncJobs(r.jobs);
  toast(L('开始处理 ' + r.count + ' 个文件', `Processing ${r.count} file(s)`), 'ok');
}

function resolveTheme(pref) {
  if (pref === 'light' || pref === 'dark') return pref;
  try {
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  } catch (e) {
    return 'dark';
  }
}

function applyTheme(pref, persist) {
  const mode = resolveTheme(pref);
  document.body.dataset.theme = mode;
  state.theme = pref;
  document.querySelectorAll('#themeSeg button').forEach((b) => {
    b.classList.toggle('active', b.dataset.theme === pref);
  });
  if (persist) {
    if (state.boot) state.boot.settings = Object.assign({}, state.boot.settings, {
      ui: Object.assign({}, (state.boot.settings || {}).ui, { theme: pref }),
    });
    api('save_settings', { ui: { theme: pref } }).catch(() => {});
  }
}

function shortPath(p, max = 30) {
  const s = String(p || '');
  if (s.length <= max) return s;
  const parts = s.split(/[\\/]/).filter(Boolean);
  let tail = parts.slice(-2).join('\\');
  if (tail.length > max - 1) tail = tail.slice(-(max - 1));
  return '…\\' + tail;
}

function updateDirButtons() {
  const dir = state.outDir || ((state.boot || {}).output_dir || '');
  ['btnOutDir', 'btnSetOutDir'].forEach((id) => {
    const el = $(id);
    if (!el) return;
    el.textContent = shortPath(dir);
    el.title = L('点击打开：', 'Click to open: ') + dir;
  });
  const lbl = $('outDirLabel');
  if (lbl) { lbl.textContent = L('输出目录：', 'Output: ') + dir; lbl.title = dir; }
}

async function openOutDir() {
  const dir = state.outDir || ((state.boot || {}).output_dir || '');
  if (!dir) { toast(L('尚未设置输出目录', 'No output folder set'), 'err'); return; }
  const r = await api('open_path', dir);
  if (!r.ok) toast(r.error || L('无法打开该目录', 'Cannot open that folder'), 'err');
}

async function pickOutDir() {
  const r = await api('pick_output_dir');
  if (r.ok) {
    state.outDir = r.dir;
    if (state.boot) state.boot.output_dir = r.dir;
    updateDirButtons();
    toast(L('输出目录已更新', 'Output folder updated'), 'ok');
  }
}

function openAbout() {
  const b = state.boot || {};
  const vp = b.version_parts || {};
  $('abName').textContent = L(b.title || 'Gururu 翻译', 'Gururu Translate');
  $('abAuthor').textContent = L('作者：', 'Author: ') + (b.author || 'Gururu Nick');
  $('abVer').textContent = b.version || '—';
  $('abBuild').textContent = vp.date ? vp.date + ' ' + vp.time : '—';
  $('abEnv').textContent = b.runtime || '—';
  $('abData').textContent = b.data_dir || '—';
  $('abData').title = b.data_dir || '';
  const fm = (b.formats || [])
    .map((f) => `<span class="chip">${esc((f.exts || [f.ext]).map((e) => String(e).replace('.', '').toUpperCase()).join('/'))}</span>`)
    .join('');
  $('abFormats').innerHTML = fm || '<span class="dim">—</span>';
  $('about').classList.remove('hidden');
}

function syncJobs(list) {
  state.jobs.clear();
  list.forEach((j) => state.jobs.set(j.id, j));
  renderQueue();
}

function renderQueue() {
  const now = Date.now();
  if (now - state.lastRender < 120) return;
  state.lastRender = now;
  const q = $('queue');
  const jobs = [...state.jobs.values()];
  if (!jobs.length) {
    q.innerHTML = `<div class="queue-empty">${L('队列为空，先添加文件', 'Queue is empty — add files first')}</div>`;
    return;
  }
  q.innerHTML = jobs.map((j) => {
    const cls = j.status === 'done' ? 'st-done' : j.status === 'failed' ? 'st-failed' : '';
    const canPreview = j.status === 'done';
    const pct = Math.max(0, Math.min(100, j.percent || 0));
    return `<div class="qrow ${cls}" data-id="${j.id}">
      <div class="qmain">
        <div class="qname" title="${esc(j.path)}"><span class="ext">${esc(j.ext)}</span>${esc(j.name)}</div>
        <div class="qmsg" title="${esc(j.message)}">${esc(j.message || '')}</div>
      </div>
      <div><div class="bar"><i style="width:${pct}%"></i></div></div>
      <div><span class="badge ${j.status}">${statusText(j)}</span></div>
      <div class="qact">
        ${canPreview ? `<button class="iconbtn" data-act="pv" data-id="${j.id}" title="${L('预览调整', 'Review')}">✎</button>` : ''}
        ${canPreview ? `<button class="iconbtn" data-act="open" data-id="${j.id}" title="${L('打开译文', 'Open output')}">↗</button>` : ''}
        <button class="iconbtn del" data-act="del" data-id="${j.id}" title="${L('移出队列', 'Remove')}">×</button>
      </div>
    </div>`;
  }).join('');
  q.querySelectorAll('.iconbtn').forEach((b) => {
    b.onclick = (e) => {
      e.stopPropagation();
      const id = b.dataset.id, act = b.dataset.act;
      if (act === 'del') api('remove_job', id).then((r) => r.jobs && syncJobs(r.jobs));
      if (act === 'pv') openPreview(id);
      if (act === 'open') {
        const j = state.jobs.get(id);
        if (j && j.output) api('open_path', j.output);
      }
    };
  });
}

function statusText(j) {
  const map = {
    queued: L('排队', 'Queued'), running: L('处理中', 'Running'), done: L('完成', 'Done'),
    failed: L('失败', 'Failed'), cancelled: L('已取消', 'Cancelled'),
  };
  if (j.status === 'done') return (j.translated || 0) + '/' + (j.segments || 0);
  return map[j.status] || j.status;
}

/* ---------------- 事件轮询 ---------------- */
function pollLoop() {
  clearTimeout(state.timer);
  const tick = async () => {
    try {
      const r = await api('poll', state.seq);
      if (r.seq) state.seq = r.seq;
      let dirty = false;
      (r.events || []).forEach((e) => {
        if (e.type === 'progress') {
          const j = state.jobs.get(e.id);
          if (j) { j.percent = e.percent; j.message = e.message; j.status = 'running'; dirty = true; }
        } else if (e.type === 'job' || e.type === 'job_done') {
          if (e.job) { state.jobs.set(e.job.id, e.job); dirty = true; }
          if (e.type === 'job_done' && state.jobs.get(e.id)) { /* noop */ }
        } else if (e.type === 'queue') {
          if (e.jobs) { syncJobs(e.jobs); }
          dirty = false;
        } else if (e.type === 'dropped') {
          if (e.jobs && e.jobs.length) syncJobs(e.jobs);
          switchPage('docs');
          if (e.failed) {
            toast(L('未能读取拖入文件的路径，请改用「点击选择文件」',
                    'Cannot read the dropped file path — please use "Click to choose"'), 'err');
          } else if (e.added) {
            toast(L('已加入队列 ' + e.added + ' 个文件', `Added ${e.added} file(s)`), 'ok');
          } else {
            toast(L('拖入的内容没有受支持的文档', 'No supported documents were dropped'), 'err');
          }
          if (!e.failed && e.skipped && e.skipped.length) {
            toast(L('已跳过：', 'Skipped: ') + e.skipped.slice(0, 3).join(L('、', ', ')), 'err');
          }
          dirty = false;
        } else if (e.type === 'log' && e.level === 'error') {
          toast(e.msg, 'err');
        } else if (e.type === 'saved') {
          toast(L('已保存：', 'Saved: ') + (e.output || '').split(/[\\/]/).pop(), 'ok');
        }
      });
      if (dirty) renderQueue();
      if (r.events && r.events.some((e) => e.type === 'job_done')) {
        const jr = await api('jobs');
        if (jr.jobs) syncJobs(jr.jobs);
        const t = await api('tm_stats');
        refreshTm(t);
      }
    } catch (e) { /* 忽略轮询瞬时错误 */ }
    state.timer = setTimeout(tick, 320);
  };
  tick();
}

/* ---------------- 预览调整 ---------------- */
async function openPreview(jid) {
  let r;
  try {
    r = await api('preview', jid);
  } catch (e) {
    toast(L('预览失败：', 'Preview failed: ') + (e && e.message ? e.message : e), 'err');
    return;
  }
  if (!r || !r.ok) { toast((r && r.error) || L('无法预览', 'Cannot preview'), 'err'); return; }
  state.pvJid = jid;
  state.pvDoc = r.doc;
  state.pvShown = 0;
  state.pvSel = new Set();
  state.pvView = 'seg';
  updateSelInfo();
  const vs0 = $('pvViewSeg');
  if (vs0) vs0.querySelectorAll('button').forEach((b) => b.classList.toggle('active', b.dataset.view === 'seg'));
  $('pvName').textContent = r.job.name + ' · '
    + L(r.doc.segments.length + ' 段', r.doc.segments.length + ' seg');
  $('pvMode').value = r.mode || 'target_only';
  const activeEngine = (((state.boot || {}).settings || {}).engine || {}).active || 'public';
  const pe = $('pvEngine');
  if (pe) pe.value = activeEngine === 'llm' ? 'llm' : 'public';
  $('preview').classList.remove('hidden');
  $('pvBody').innerHTML = '';
  updateTermButtons();
  renderPv();
}

/* ---- 预览显示设置：效果 / 字体 / 分布方式 ---- */
const PV_FONTS = [
  ['', 'default'],
  ['msyh', '微软雅黑'],
  ['songti', '宋体'],
  ['heiti', '黑体'],
  ['kaiti', '楷体'],
  ['fangsong', '仿宋'],
  ['times', 'Times New Roman'],
  ['arial', 'Arial'],
  ['calibri', 'Calibri'],
  ['georgia', 'Georgia'],
];
const FONT_CSS = {
  msyh: '"Microsoft YaHei", "微软雅黑", sans-serif',
  songti: '"SimSun", "宋体", serif',
  heiti: '"SimHei", "黑体", sans-serif',
  kaiti: '"KaiTi", "楷体", serif',
  fangsong: '"FangSong", "仿宋", serif',
  times: '"Times New Roman", serif',
  arial: 'Arial, sans-serif',
  calibri: 'Calibri, sans-serif',
  georgia: 'Georgia, serif',
};
const FONT_KEY = { default: '', 微软雅黑: 'msyh', 宋体: 'songti', 黑体: 'heiti', 楷体: 'kaiti', 仿宋: 'fangsong' };

function cssFont(key) {
  return FONT_CSS[key] || (key && !key.includes(' ') && key !== 'default' ? key : '');
}

function fillPvFonts(cur) {
  const sel = $('pvCfgFont');
  if (!sel) return;
  sel.innerHTML = PV_FONTS.map(([k, n]) =>
    `<option value="${k}">${k === '' ? L('默认', 'Default') : n}</option>`).join('');
  sel.value = cur || '';
}

function applyPvCfgToForm() {
  const c = state.pvCfg || {};
  const fx = document.querySelector('input[name=pvFx][value="' + (c.fx || 'default') + '"]');
  if (fx) fx.checked = true;
  fillPvFonts(c.font);
  const d = $('pvCfgDist');
  if (d) d.value = c.dist || 'stack';
}

async function savePvCfg() {
  const r = await api('save_settings', { preview: { ...state.pvCfg } });
  if (r && r.ok && r.settings) state.boot.settings = r.settings;
}

function setPvCfg(k, v) {
  state.pvCfg = { ...(state.pvCfg || {}), [k]: v };
  if (state.pvView === 'full' && state.pvDoc) renderPv();
  savePvCfg();
}

function togglePvCfg(force) {
  const pop = $('pvCfgPop');
  if (!pop) return;
  const show = typeof force === 'boolean' ? force : pop.classList.contains('hidden');
  pop.classList.toggle('hidden', !show);
  if (show) applyPvCfgToForm();
}

function setPvView(v) {
  state.pvView = v === 'full' ? 'full' : 'seg';
  const vs = $('pvViewSeg');
  if (vs) {
    vs.querySelectorAll('button').forEach((b) => {
      b.classList.toggle('active', b.dataset.view === state.pvView);
    });
  }
  if (!state.pvDoc) return;
  state.pvShown = 0;
  $('pvBody').innerHTML = '';
  renderPv();
}

function closePreview() {
  togglePvCfg(false);
  $('preview').classList.add('hidden');
  state.pvDoc = null;
  state.pvJid = null;
}

function pvModeValue() {
  return $('pvMode').value;
}

function renderPv() {
  if (state.pvView === 'full') return renderPvFull();
  return renderPvSeg();
}

function renderPvSeg() {
  const doc = state.pvDoc;
  if (!doc) return;
  const body = $('pvBody');
  const segs = doc.segments;
  const show = Math.min(segs.length, state.pvShown + 400);
  const slice = segs.slice(state.pvShown, show);
  const bi = pvModeValue() === 'bilingual';
  const html = slice.map((s, k) => {
    const idx = state.pvShown + k;
    const selCls = state.pvSel.has(s.sid) ? ' sel' : '';
    return `<div class="pv-row st-${s.status}${selCls}" data-sid="${s.sid}" data-v="pv-row" data-i="${idx}">
      <div class="pv-src">${esc(s.src)}</div>
      <div class="pv-tgt" contenteditable="true" spellcheck="false">${esc(s.tgt)}</div>
      <i class="pv-dot" title="${esc(s.note || s.status)}"></i>
      <span class="pv-idx">${bi ? '' : idx + 1}</span>
    </div>`;
  }).join('');
  if (state.pvShown === 0) {
    body.innerHTML = `<div class="pv-head"><span>${L('原文', 'Source')}</span>`
      + `<span>${L('译文（可直接编辑）', 'Translation (editable)')}</span></div>` + html;
  } else {
    const more = body.querySelector('.more');
    if (more) more.remove();
    body.insertAdjacentHTML('beforeend', html);
  }
  updatePvStat();

  if (show < segs.length) {
    let more = body.querySelector('.more');
    if (!more) {
      more = document.createElement('div');
      more.className = 'more';
      more.innerHTML = `<button id="btnMore">`
        + L(`显示更多（已显示 ${show}/${segs.length}）`, `Show more (${show}/${segs.length})`)
        + `</button>`;
      body.appendChild(more);
      $('btnMore').onclick = () => { state.pvShown = show; renderPv(); };
    }
  }
  state.pvShown = show;
  bindPvEditing(slice);
}

function renderPvFull() {
  const doc = state.pvDoc;
  if (!doc) return;
  const body = $('pvBody');
  const segs = doc.segments;
  const bi = pvModeValue() === 'bilingual';
  const cfg = state.pvCfg || {};
  const cls = `pv-full pv-fx-${esc(cfg.fx || 'default')} pv-dist-${esc(cfg.dist || 'stack')}`;
  const fam = cfg.font ? `font-family:${cssFont(cfg.font)}` : '';
  let html = `<div class="${cls}"${fam ? ` style="${fam}"` : ''}>`;
  let lastGroup = null;
  segs.forEach((s, idx) => {
    const g = s.group || '';
    if (g !== lastGroup) {
      if (g) html += `<div class="pv-ft-group">${esc(g)}</div>`;
      lastGroup = g;
    }
    const selCls = state.pvSel.has(s.sid) ? ' sel' : '';
    const srcHtml = bi ? `<div class="pv-ft-src">${esc(s.src)}</div>` : '';
    html += `<div class="pv-ft-row st-${s.status} k-${esc(s.kind || 'para')}${selCls}"`
      + ` data-sid="${s.sid}" data-v="pv-ft-row">`
      + `<span class="pv-ft-idx">${idx + 1}</span>`
      + srcHtml
      + `<div class="pv-ft-tgt" contenteditable="true" spellcheck="false">${esc(s.tgt)}</div>`
      + `</div>`;
  });
  html += '</div>';
  body.innerHTML = html;
  updatePvStat();
  bindPvEditing(segs, '.pv-ft-row');
}

function syncTransName() {
  const el = $('docTransName') || $('setTransName');
  const on = !!el && el.checked;
  const sf = $('setSuffix');
  if (sf) {
    sf.disabled = on;
    sf.title = on ? L('已在「文档翻译」页启用「同时翻译文件名」，输出直接使用译名，后缀失效',
      '"Translate file names" is on — output uses the translated name, suffix ignored') : '';
    sf.style.opacity = on ? '.55' : '';
  }
  const hint = $('setSuffixHint');
  if (hint) hint.style.opacity = on ? '1' : '.7';
}

function updatePvStat() {
  const segs = state.pvDoc ? state.pvDoc.segments : [];
  const cnt = (st) => segs.filter((s) => s.status === st).length;
  $('pvStat').innerHTML =
    `<span>${L('共 ' + segs.length + ' 段', segs.length + ' segments')}</span>` +
    `<span style="color:var(--ok)">${L('完成 ', 'Done ')}${cnt('done')}</span>` +
    `<span style="color:var(--info)">${L('已改 ', 'Edited ')}${cnt('edited')}</span>` +
    `<span class="c-ai">${L('AI 润色 ', 'AI ')}${cnt('refined')}</span>` +
    `<span class="c-term">${L('术语 ', 'Term ')}${cnt('term_violation')}</span>` +
    `<span style="color:var(--err)">${L('失败 ', 'Failed ')}${cnt('failed')}</span>` +
    `<span class="dim">${L('修改后点「保存输出」写回文件', 'Click “Save output” to write changes')}</span>`;
}

function bindPvEditing(slice, rowSel = '.pv-row') {
  const body = $('pvBody');
  slice.forEach((s) => {
    const row = body.querySelector(`${rowSel}[data-sid="${s.sid}"]`);
    if (!row) return;
    const src = row.querySelector(rowSel === '.pv-ft-row' ? '.pv-ft-src' : '.pv-src');
    if (src) {
      src.addEventListener('click', () => {
        if (state.pvSel.has(s.sid)) state.pvSel.delete(s.sid);
        else state.pvSel.add(s.sid);
        row.classList.toggle('sel');
        updateSelInfo();
      });
    }
    const cell = row.querySelector(rowSel === '.pv-ft-row' ? '.pv-ft-tgt' : '.pv-tgt');
    let composing = false;
    cell.addEventListener('compositionstart', () => { composing = true; });
    cell.addEventListener('compositionend', () => { composing = false; scheduleEdit(row, cell); });
    cell.addEventListener('input', () => { if (!composing) scheduleEdit(row, cell, 500); });
  });
}

const editTimers = new Map();
function scheduleEdit(row, cell, delay = 0) {
  const sid = row.dataset.sid;
  clearTimeout(editTimers.get(sid));
  editTimers.set(sid, setTimeout(async () => {
    const text = cell.textContent;
    const seg = state.pvDoc.segments.find((x) => x.sid === sid);
    if (seg) { seg.tgt = text; seg.status = text.trim() ? 'edited' : seg.status; }
    const selCls = state.pvSel.has(sid) ? ' sel' : '';
    row.className = (row.dataset.v || 'pv-row') + ' st-' + (seg ? seg.status : 'done') + selCls;
    updatePvStat();
    try { await api('edit_segment', state.pvJid, sid, text); } catch (e) { /* 忽略 */ }
  }, delay));
}

async function pvRetranslateAll(askConfirm) {
  if (!state.pvJid) return;
  const doc = state.pvDoc;
  const sids = doc.segments.filter((s) => s.status !== 'edited').map((s) => s.sid);
  if (!sids.length) { toast(L('没有可重译的段落', 'Nothing to retranslate')); return; }
  if (askConfirm === true && sids.length > 60) {
    const q = L(`将重译 ${sids.length} 段（已手动修改的段落会保留），继续？`,
      `Retranslate ${sids.length} segments (manually edited ones are kept). Continue?`);
    if (!confirm(q)) return;
  }
  const btn = $('btnPvRetrans');
  btn.disabled = true;
  btn.innerHTML = '<span class="spin"></span> ' + L('重译中', 'Retranslating');
  try {
    const patch = {
      src: $('srcLang').value, tgt: $('tgtLang').value,
      style: $('pvStyle').value, term_sets: state.sel.pv.slice(),
      mode: pvModeValue(), engine: $('pvEngine').value,
    };
    const r = await api('retranslate', state.pvJid, [], patch);
    if (!r.ok) { toast(r.error || L('重译失败', 'Retranslation failed'), 'err'); return; }
    const map = new Map((r.segments || []).map((s) => [s.sid, s]));
    doc.segments.forEach((s) => {
      const n = map.get(s.sid);
      if (n) { s.tgt = n.tgt; s.status = n.status; s.note = n.note; }
    });
    state.pvShown = 0;
    $('pvBody').innerHTML = '';
    renderPv();
    toast(L('已重译 ' + r.count + ' 段', `Retranslated ${r.count} segments`), 'ok');
  } catch (e) {
    toast(L('重译失败：', 'Retranslation failed: ') + e.message, 'err');
  } finally {
    btn.disabled = false;
    btn.textContent = L('全部重译', 'Retranslate all');
  }
}

async function savePreview() {
  if (!state.pvJid) return;
  const btn = $('btnPvSave');
  btn.disabled = true;
  btn.innerHTML = '<span class="spin"></span> ' + L('保存中', 'Saving');
  try {
    const r = await api('save_preview', state.pvJid, pvModeValue());
    if (!r.ok) { toast(r.error || L('保存失败', 'Save failed'), 'err'); return; }
    toast(L('已保存：', 'Saved: ') + (r.output || '').split(/[\\/]/).pop(), 'ok');
    if (r.warnings && r.warnings.length) toast(r.warnings[0], 'err');
    const jr = await api('jobs');
    if (jr.jobs) syncJobs(jr.jobs);
  } catch (e) {
    toast(L('保存失败：', 'Save failed: ') + e.message, 'err');
  } finally {
    btn.disabled = false;
    btn.textContent = L('保存输出', 'Save output');
  }
}

function updateSelInfo() {
  const el = $('pvSelInfo');
  if (!el) return;
  const n = state.pvSel.size;
  el.textContent = n
    ? L(`已选中 ${n} 段，AI 只调整这些段落`, `${n} selected — AI applies to these only`)
    : L('点击左侧原文可选中段落，未选中时作用于全部',
        'Click a source line to select; nothing selected = apply to all');
}

function applySegUpdates(list) {
  if (!state.pvDoc) return;
  const map = new Map(list.map((s) => [s.sid, s]));
  state.pvDoc.segments.forEach((s) => {
    const n = map.get(s.sid);
    if (n) { s.tgt = n.tgt; s.status = n.status; s.note = n.note; }
  });
  list.forEach((n) => {
    const row = document.querySelector(`.pv-row[data-sid="${n.sid}"]`)
      || document.querySelector(`.pv-ft-row[data-sid="${n.sid}"]`);
    if (!row) return;
    row.className = (row.dataset.v || 'pv-row') + ' st-' + n.status
      + (state.pvSel.has(n.sid) ? ' sel' : '');
    const cell = row.querySelector('.pv-tgt, .pv-ft-tgt');
    if (cell && cell.textContent !== n.tgt) cell.textContent = n.tgt;
    const dot = row.querySelector('.pv-dot');
    if (dot) dot.setAttribute('title', n.note || n.status);
  });
  updatePvStat();
}

async function aiRefine() {
  if (!state.pvJid) return;
  const instr = $('pvInstr').value.trim();
  const sids = [...state.pvSel];
  const btn = $('btnPvAi');
  btn.disabled = true;
  btn.innerHTML = '<span class="spin"></span> ' + L('调整中', 'Adjusting');
  try {
    const patch = {
      src: $('srcLang').value, tgt: $('tgtLang').value,
      style: $('pvStyle').value, term_sets: state.sel.pv.slice(),
      mode: pvModeValue(), engine: 'llm',
    };
    const r = await api('ai_refine', state.pvJid, sids, instr, patch);
    if (!r.ok) { toast(r.error || L('AI 调整失败', 'AI adjustment failed'), 'err'); return; }
    applySegUpdates(r.segments || []);
    toast(L(`AI 已调整 ${r.changed}/${r.count} 段`, `AI adjusted ${r.changed}/${r.count}`), 'ok');
  } catch (e) {
    toast(L('AI 调整失败：', 'AI adjustment failed: ') + e.message, 'err');
  } finally {
    btn.disabled = false;
    btn.textContent = L('AI 调整', 'AI adjust');
  }
}

/* ---------------- 设置页 ---------------- */
function loadSettingsForm(b) {
  if (!b) return;
  const s = b.settings || {};
  const e = s.engine || {}, llm = e.llm || {}, tr = s.translate || {},
    out = s.output || {}, doc = s.doc || {}, tmCfg = s.tm || {};

  fillProviders();
  $('setProvider').value = llm.provider || 'deepseek';
  $('setBaseUrl').value = llm.base_url || '';
  $('setModel').value = llm.model || '';
  $('setTemp').value = llm.temperature != null ? llm.temperature : 0.2;
  $('setConc').value = llm.concurrency || 6;
  $('setBatch').value = llm.batch_chars || 1800;
  $('setApiKey').placeholder = b.has_key
    ? L('已配置（' + (b.key_mask || '') + '），留空不修改', 'Configured, leave blank to keep')
    : 'sk-…';

  document.querySelectorAll('input[name=setEngine]').forEach((r) => {
    r.checked = r.value === (e.active || 'public');
  });
  if (tr.style) $('setStyle').value = tr.style;
  $('setSuffix').value = out.suffix || '_译文';
  const pv = s.preview || {};
  state.pvCfg = { fx: pv.fx || 'default', font: pv.font || '', dist: pv.dist || 'stack' };
  applyPvCfgToForm();
  const dtn = $('docTransName');
  if (dtn) {
    dtn.checked = !!out.translate_name;
    dtn.onchange = async () => {
      syncTransName();
      const r = await api('save_settings', { output: { translate_name: dtn.checked } });
      if (r && r.ok && r.settings) state.boot.settings = r.settings;
    };
  }
  syncTransName();
  $('setStartPage').value = (s.ui && s.ui.start_page) || 'text';
  state.outDir = out.dir || b.output_dir || '';
  updateDirButtons();
  $('setTm').checked = !!tmCfg.enabled;
  $('optHeader').checked = !doc.skip_header_footer;
  $('optAutoSave').checked = out.auto_save !== false;
  $('textEngine').value = e.active === 'llm' ? 'llm' : 'public';
  $('docEngine').value = e.active === 'llm' ? 'llm' : 'public';
  loadTermOptions();
}

/* ---------------- 查词 ---------------- */
const DICT_NAMES = {
  youdao: { zh: '有道词典', en: 'Youdao' },
  freedict: { zh: 'Free Dictionary 英文释义', en: 'Free Dictionary (English)' },
  local: { zh: '内置离线词典', en: 'Built-in dictionary' },
};

function dictName(key) {
  const n = DICT_NAMES[key];
  return n ? n[state.lang === 'en' ? 'en' : 'zh'] : key;
}

function dictSuggest(word) {
  const el = $('dictInput');
  if (el) el.value = word;
  doLookup();
}

function renderDictLocal(res, word) {
  const box = $('dictBody');
  if (!res || !res.ok) {
    box.innerHTML = `<div class="dict-card"><div class="dict-src">${dictName('local')}</div>`
      + `<div class="dict-warn">${L('内置词典不可用，请重新安装程序。',
        'Built-in dictionary unavailable — please reinstall.')}</div></div>`;
    return;
  }
  if (!res.hit) {
    const sug = (res.suggestions || []).map(
      (s) => `<button data-w="${esc(s)}">${esc(s)}</button>`).join('');
    box.innerHTML = `<div class="dict-card"><div class="dict-src">${dictName('local')}</div>`
      + `<div class="dict-word">${esc(res.query)}</div>`
      + `<div class="dict-warn" style="margin-top:8px">${L('内置词典未收录该词', 'Not found in the built-in dictionary')}</div>`
      + (sug ? `<div class="dict-more">${sug}</div>` : '')
      + `</div>`;
  } else {
    const e = res.entry;
    const badges = [];
    if (e.collins) badges.push(`<span class="dict-badge hot">COLLINS ${e.collins}</span>`);
    if (e.oxford) badges.push('<span class="dict-badge">OXFORD</span>');
    (e.tag || '').split(/\s+/).filter(Boolean).slice(0, 4).forEach((t) => {
      badges.push(`<span class="dict-badge">${esc(t)}</span>`);
    });
    if (e.forms && e.forms.length) {
      badges.push(`<span class="dict-badge">${esc(e.forms.join(' / '))}</span>`);
    }
    box.innerHTML = `<div class="dict-card">
      <div class="dict-src">${dictName('local')}</div>
      <div class="dict-head">
        <span class="dict-word">${esc(e.word)}</span>
        ${e.phonetic ? `<span class="dict-phon">/${esc(e.phonetic)}/</span>` : ''}
        <span class="dict-badges">${badges.join('')}</span>
      </div>
      <div class="dict-senses">${e.senses.map((s) => `<div>${esc(s)}</div>`).join('')}</div>
    </div>`;
  }
  box.querySelectorAll('.dict-more button').forEach((b) => {
    b.onclick = () => dictSuggest(b.dataset.w);
  });
}

function renderDictOnline(res) {
  const box = $('dictBody');
  if (!box) return;
  const old = box.querySelectorAll('[data-online]');
  old.forEach((n) => n.remove());
  const src = (res && res.sources) || [];
  if (!src.length) {
    box.insertAdjacentHTML('beforeend',
      `<div class="dict-card" data-online="1"><div class="dict-warn">${
        L('未获取到在线释义（可能未联网或服务暂不可用）',
          'No online results (offline or service unavailable)')}</div></div>`);
    return;
  }
  src.forEach((item) => {
    const head = `<div class="dict-src">${esc(dictName(item.name))}</div>`;
    let body = '';
    if (item.senses) {
      body = `<div class="dict-head"><span class="dict-word">${esc($('dictInput').value.trim())}</span>`
        + (item.phonetic ? `<span class="dict-phon">${esc(item.phonetic)}</span>` : '')
        + `</div><div class="dict-senses">${item.senses.map((s) => `<div>${esc(s)}</div>`).join('')}</div>`;
    } else {
      const groups = (item.groups || []).map((g) => `
        <div class="dict-group">
          ${g.pos ? `<div class="dict-pos">${esc(g.pos)}</div>` : ''}
          <ul>${g.defs.map((d) => `<li>${esc(d)}</li>`).join('')}</ul>
        </div>`).join('');
      body = (item.phonetic ? `<div class="dict-phon">${esc(item.phonetic)}</div>` : '') + groups;
    }
    box.insertAdjacentHTML('beforeend',
      `<div class="dict-card" data-online="1">${head}${body}</div>`);
    if (item.encyclopedia) renderEncyclopedia(item.encyclopedia);
  });
}

let sugTimer = null;
let sugSeq = 0;
let sugItems = [];
let sugActive = -1;
let sugOpen = false;

function closeSug() {
  const box = $('dictSug');
  if (box) box.classList.add('hidden');
  sugOpen = false;
  sugActive = -1;
}

function renderSug(items) {
  const box = $('dictSug');
  sugItems = items;
  sugActive = -1;
  if (!items.length) { closeSug(); return; }
  box.innerHTML = items.map((it, i) => {
    const tag = it.src ? `<span class="dict-sug-src">${esc(it.src)}</span>` : '';
    return `<div class="dict-sug-item" data-i="${i}">`
      + `<span class="dict-sug-word">${esc(it.word)}</span>`
      + `<span class="dict-sug-brief">${esc(it.brief || '')}</span>${tag}</div>`;
  }).join('');
  box.classList.remove('hidden');
  sugOpen = true;
  box.querySelectorAll('.dict-sug-item').forEach((el) => {
    el.onmousedown = (e) => { e.preventDefault(); pickSug(Number(el.dataset.i)); };
  });
}

function pickSug(i) {
  const it = sugItems[i];
  if (!it) return;
  $('dictInput').value = it.word;
  closeSug();
  doLookup();
}

function setSugActive(i) {
  const nodes = $('dictSug').querySelectorAll('.dict-sug-item');
  if (!nodes.length) return;
  sugActive = (i + nodes.length) % nodes.length;
  nodes.forEach((n, k) => n.classList.toggle('active', k === sugActive));
  nodes[sugActive].scrollIntoView({ block: 'nearest' });
}

async function onDictInput() {
  const q = $('dictInput').value.trim();
  clearTimeout(sugTimer);
  if (q.length < 2) { closeSug(); return; }
  const seq = ++sugSeq;
  sugTimer = setTimeout(async () => {
    let local = [];
    try {
      const r = await api('dict_suggest', q);
      local = (r.items || []).map((x) => ({ ...x, src: L('本地', 'local') }));
    } catch (e) { local = []; }
    if (seq !== sugSeq) return;
    renderSug(local.slice(0, 8));

    let online = [];
    try {
      const o = await api('dict_suggest_online', q);
      online = (o.items || []).map((x) => ({ ...x, src: L('在线', 'online') }));
    } catch (e) { online = []; }
    if (seq !== sugSeq || !online.length) return;
    const exact = local.some((x) => x.word.toLowerCase() === q.toLowerCase());
    // 有精确命中时本地优先；否则在线（含拼写纠错）优先，去重保留首次出现
    const merged = exact ? [...local, ...online] : [...online, ...local];
    const seen = new Set();
    const out = [];
    merged.forEach((it) => {
      const key = it.word.toLowerCase();
      if (seen.has(key)) return;
      seen.add(key);
      out.push(it);
    });
    renderSug(out.slice(0, 8));
  }, 140);
}

function renderEncyclopedia(enc) {
  const box = $('dictBody');
  if (!box || !enc || (!enc.summary && !(enc.images || []).length)) return;
  const id = 'enc-' + Math.random().toString(36).slice(2, 8);
  box.insertAdjacentHTML('beforeend', `
    <div class="dict-card" data-online="1" id="${id}">
      <div class="dict-src">${L('百科（维基摘要）', 'Encyclopedia (Wikipedia)')}</div>
      <div class="dict-enc-images"></div>
      <div class="dict-enc-sum">${esc(enc.summary || '')}</div>
      <div class="dict-enc-tr hidden"></div>
    </div>`);
  const card = document.getElementById(id);
  if (!card) return;

  const imgBox = card.querySelector('.dict-enc-images');
  (enc.images || []).slice(0, 2).forEach((url) => {
    api('fetch_image', url).then((r) => {
      if (r && r.ok) {
        imgBox.insertAdjacentHTML('beforeend', `<img src="${r.data}" alt="">`);
      } else if (!imgBox.children.length) {
        imgBox.style.display = 'none';
      }
    }).catch(() => { imgBox.style.display = 'none'; });
  });

  if (enc.summary && enc.summary_lang !== 'zh' && state.lang === 'zh') {
    api('translate_text', enc.summary,
      { src: 'en', tgt: 'zh', style: 'general', term_sets: [], engine: 'public' })
      .then((r) => {
        if (r && r.ok && r.text) {
          const tr = card.querySelector('.dict-enc-tr');
          tr.textContent = r.text;
          tr.classList.remove('hidden');
        }
      }).catch(() => {});
  }
}

async function doLookup() {
  const word = $('dictInput').value.trim();
  const tip = $('dictTip');
  if (!word) { $('dictBody').innerHTML = ''; return; }
  closeSug();
  tip.textContent = L('查询中…', 'Searching…');
  const onlinePromise = api('dict_online', word).catch(() => null);
  let local = null;
  try {
    local = await api('dict_lookup', word);
  } catch (e) {
    local = null;
  }
  renderDictLocal(local, word);
  tip.textContent = '';
  const online = await onlinePromise;
  renderDictOnline(online);
  tip.textContent = '';
}

function fillProviders() {
  const prov = $('setProvider');
  if (!prov) return;
  const cur = prov.value;
  prov.innerHTML = Object.entries(state.providers)
    .map(([k, v]) => `<option value="${k}">${esc(L(v.label, v.label_en || v.label))}</option>`)
    .join('');
  if (cur) prov.value = cur;
}

function refillOptions() {
  fillStyles('textStyle', $('textStyle').value);
  fillStyles('docStyle', $('docStyle').value);
  fillStyles('pvStyle', $('pvStyle').value);
  fillStyles('setStyle', $('setStyle').value);
  fillProviders();
  loadTermOptions();
  renderTermPop('text', 'textTermsPop');
  renderTermPop('doc', 'docTermsPop');
  renderTermPop('pv', 'pvTermsPop');
  updateTermButtons();
}

function loadTermOptions() {
  const sel = $('setTermSet');
  const cur = sel.value;
  sel.innerHTML = state.termSets
    .map((s) => `<option value="${s.id}">${esc(nm(s))} (${s.count})</option>`).join('');
  if (cur) sel.value = cur;
  loadTermDetail();
}

async function loadTermDetail() {
  const id = $('setTermSet').value;
  if (!id) { $('termList').innerHTML = ''; return; }
  const r = await api('term_detail', id);
  if (!r.ok) return;
  const terms = (r.set.terms || []).slice(0, 300);
  $('termList').innerHTML = terms.map((t) =>
    `<div class="term-row"><span title="${esc(t.a)}">${esc(t.a)}</span>
     <span title="${esc(t.b)}">${esc(t.b)}</span>
     <button class="iconbtn del" data-a="${esc(t.a)}" title="${L('删除', 'Delete')}">×</button></div>`
  ).join('') || `<div class="dim" style="padding:10px">${L('暂无术语', 'No terms yet')}</div>`;
  $('termList').querySelectorAll('button[data-a]').forEach((b) => {
    b.onclick = async () => {
      await api('remove_term', id, b.dataset.a);
      loadTermDetail();
      refreshTermSets();
    };
  });
  $('btnDelSet').disabled = !!r.set.builtin;
}

async function refreshTermSets() {
  const r = await api('term_sets');
  if (r.ok) {
    state.termSets = r.sets;
    ['text', 'doc', 'pv'].forEach((k) => {
      const pop = { text: 'textTermsPop', doc: 'docTermsPop', pv: 'pvTermsPop' }[k];
      renderTermPop(k, pop);
    });
    loadTermOptions();
    updateTermButtons();
  }
}

async function newTermSet() {
  const name = prompt(L('新建术语库名称：', 'New glossary name:'));
  if (!name) return;
  const r = await api('create_term_set', name);
  if (!r.ok) { toast(r.error, 'err'); return; }
  await refreshTermSets();
  $('setTermSet').value = r.id;
  loadTermDetail();
  toast(L('已创建', 'Created'), 'ok');
}

async function delTermSet() {
  const id = $('setTermSet').value;
  const set = state.termSets.find((s) => s.id === id);
  if (!set || set.builtin) {
    toast(L('内置术语库不可删除', 'Built-in glossaries cannot be deleted'), 'err');
    return;
  }
  const setName = nm(set);
  if (!confirm(L('删除术语库「' + setName + '」？', `Delete glossary “${setName}”?`))) return;
  await api('delete_term_set', id);
  state.sel.text = state.sel.text.filter((x) => x !== id);
  state.sel.doc = state.sel.doc.filter((x) => x !== id);
  state.sel.pv = state.sel.pv.filter((x) => x !== id);
  await refreshTermSets();
  toast(L('已删除', 'Deleted'), 'ok');
}

async function addTerm() {
  const id = $('setTermSet').value;
  const a = $('newTermSrc').value.trim(), b = $('newTermTgt').value.trim();
  if (!id) { toast(L('请先选择术语库', 'Choose a glossary first'), 'err'); return; }
  const set = state.termSets.find((s) => s.id === id);
  if (set && set.builtin) {
    toast(L('内置术语库只读，请新建自定义库', 'Built-in glossaries are read-only — create your own'), 'err');
    return;
  }
  if (!a || !b) { toast(L('源词与译词都要填写', 'Both source and target terms are required'), 'err'); return; }
  const r = await api('upsert_terms', id, [{ a, b, s: $('srcLang').value, t: $('tgtLang').value }]);
  if (!r.ok) { toast(r.error, 'err'); return; }
  $('newTermSrc').value = ''; $('newTermTgt').value = '';
  await refreshTermSets();
  loadTermDetail();
  toast(L('已添加 ' + r.added + ' 条', `Added ${r.added} term(s)`), 'ok');
}

async function importTerms() {
  const id = $('setTermSet').value;
  const set = state.termSets.find((s) => s.id === id);
  if (set && set.builtin) {
    toast(L('内置术语库只读，请新建自定义库', 'Built-in glossaries are read-only — create your own'), 'err');
    return;
  }
  const r = await api('import_terms', id);
  if (!r.ok) { if (r.error) toast(r.error, 'err'); return; }
  await refreshTermSets();
  loadTermDetail();
  toast(L('已导入 ' + r.added + ' 条', `Imported ${r.added} term(s)`), 'ok');
}

function applyProvider() {
  const p = state.providers[$('setProvider').value];
  if (!p) return;
  if (p.base_url) $('setBaseUrl').value = p.base_url;
  if (p.models && p.models.length) $('setModel').value = p.models[0];
}

async function testEngine() {
  const msg = $('testMsg');
  msg.className = 'msg';
  const key = $('setApiKey').value.trim();
  const cfg = {
    base_url: $('setBaseUrl').value.trim(),
    model: $('setModel').value.trim(),
    temperature: parseFloat($('setTemp').value) || 0.2,
    json_mode: true,
  };
  if (key) {
    await api('set_api_key', key);
    $('setApiKey').value = '';
  }
  msg.className = 'msg show';
  msg.textContent = L('测试中…', 'Testing…');
  const r = await api('test_engine', cfg, null);
  msg.className = 'msg show ' + (r.ok ? 'ok' : 'err');
  msg.textContent = r.message;
}

async function saveSettings() {
  const engineActive = [...document.querySelectorAll('input[name=setEngine]')].find((r) => r.checked);
  const key = $('setApiKey').value.trim();
  if (key) await api('set_api_key', key);
  const patch = {
    engine: {
      active: engineActive ? engineActive.value : 'public',
      llm: {
        provider: $('setProvider').value,
        base_url: $('setBaseUrl').value.trim(),
        model: $('setModel').value.trim(),
        temperature: parseFloat($('setTemp').value) || 0.2,
        concurrency: parseInt($('setConc').value, 10) || 6,
        batch_chars: parseInt($('setBatch').value, 10) || 1800,
      },
    },
    translate: {
      src: $('srcLang').value,
      tgt: $('tgtLang').value,
      style: $('setStyle').value,
      term_sets: state.sel.text.slice(),
      mode: [...document.querySelectorAll('input[name=docMode]')].find((x) => x.checked).value,
    },
    output: {
      dir: $('btnSetOutDir').textContent.trim(),
      suffix: $('setSuffix').value || '_译文',
      translate_name: !!($('docTransName') || $('setTransName') || {}).checked,
      auto_save: $('optAutoSave').checked,
    },
    doc: { skip_header_footer: !$('optHeader').checked },
    tm: { enabled: $('setTm').checked },
    ui: { theme: state.theme, lang: state.lang, start_page: $('setStartPage').value },
  };
  const r = await api('save_settings', patch);
  if (!r.ok) { toast(r.error || L('保存失败', 'Save failed'), 'err'); return; }
  state.boot.settings = r.settings;
  state.boot.has_key = r.has_key;
  state.boot.key_mask = r.key_mask;
  refreshEngineChip();
  $('setApiKey').placeholder = r.has_key
    ? L('已配置（' + r.key_mask + '），留空不修改', 'Configured, leave blank to keep')
    : 'sk-…';
  $('textEngine').value = (r.settings.engine || {}).active === 'llm' ? 'llm' : 'public';
  $('docEngine').value = (r.settings.engine || {}).active === 'llm' ? 'llm' : 'public';
  updateDirButtons();
  toast(L('设置已保存', 'Settings saved'), 'ok');
}
