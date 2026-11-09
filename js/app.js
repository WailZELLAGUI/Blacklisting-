/* Main page logic: exhibit tabs, languages, simulator, charts. */
const APP = (() => {
  const S = { lang: 'en', thesis: null, def: null, world: null, res: null, graph: null, preset: 'rev3', vis: 'V3', overrides: {},
    colorBy: 'grade', mistakes: true, fraud: null, selected: null, engine: 'idle', engineVersion: '', worker: null,
    pending: {}, nextId: 1, charts: {}, busy: false, rows: null, page: 'story' };
  const $ = (q) => document.querySelector(q);
  const $$ = (q) => [...document.querySelectorAll(q)];
  const esc = (s) => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const t = (k, vars) => {
    let s = I18N[S.lang][k]; if (s === undefined) s = I18N.en[k]; if (s === undefined) return k;
    if (vars && typeof s === 'string') for (const v in vars) s = s.split('{' + v + '}').join(vars[v]);
    return s;
  };
  const loc = () => S.lang === 'fr' ? 'fr-FR' : 'en-GB';
  const pct = (x, d = 1) => x === null || x === undefined ? '–' : (100 * x).toFixed(d).replace('.', S.lang === 'fr' ? ',' : '.') + ' %';
  const eur = (x) => x === null || x === undefined ? '–' : (S.lang === 'fr' ? Math.round(x).toLocaleString('fr-FR') + ' €' : '€' + Math.round(x).toLocaleString('en-GB'));
  const num = (x) => Math.round(x).toLocaleString(loc());
  const meur = (x) => S.lang === 'fr' ? (x / 1e6).toFixed(1).replace('.', ',') + ' M€' : '€' + (x / 1e6).toFixed(1) + 'M';
  const hours = (h) => h > 48 ? t('days_approx', { d: Math.round(h / 24) }) : `${num(h)} h`;
  const patName = (k) => { const p = t('patterns')[k]; return p ? p.split(' · ').slice(1).join(' · ') + ` (${k})` : k; };
  const reduceMotion = () => window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------------------------------------------------------------- Python engine (web worker), started on demand */
  function ensureEngine() { if (S.engine === 'idle') startEngine(); }
  function startEngine() {
    S.engine = 'loading'; engineStatus();
    try {
      S.worker = new Worker('js/py-worker.js');
    } catch (e) { engineFailed(String(e)); return; }
    S.worker.onmessage = (ev) => {
      const m = ev.data;
      if (m.type === 'progress') { $('#engine-msg').textContent = t({ python: 'engine_python', packages: 'engine_packages', code: 'engine_code' }[m.step]); return; }
      if (m.type === 'failed') { engineFailed(m.error); return; }
      if (m.type === 'ready') {
        S.engineVersion = m.version;
        // load the same world the page shows, so every later call works on it
        call('new_world', JSON.stringify({ seed: S.world.seed, ...(S.world.params || {}) }), true)
          .then(() => call('grade', JSON.stringify({ preset: 'rev3', vis: 'V3', base: 'rev3', overrides: {} }), true))
          .then((g) => {
            const ref = S.def.grades['rev3|V3'].selected;
            S.identical = g.selected.found === ref.found && g.selected.false_alerts === ref.false_alerts;
            S.engine = 'ready'; engineStatus(); setControls(); renderPatterns();
            call('sample_rows').then(r => { S.rows = r; renderData(); }).catch(() => {});
          }).catch(e => engineFailed(String(e)));
        return;
      }
      const p = S.pending[m.id]; if (!p) return; delete S.pending[m.id];
      m.ok ? p.resolve(JSON.parse(m.result)) : p.reject(new Error(m.error));
    };
    S.worker.onerror = (e) => engineFailed(e.message || 'worker error');
  }
  function engineFailed(err) { S.engine = 'failed'; S.engineError = err; engineStatus(); setControls(); }
  function engineStatus() {
    const box = $('#engine');
    box.className = 'engine ' + (S.engine === 'ready' ? 'ok' : S.engine === 'failed' ? 'bad' : '');
    $('#engine-msg').textContent = S.engine === 'ready' ? t('engine_ready', { v: 'Pyodide ' + S.engineVersion }) + (S.identical === undefined ? '' : ' ' + t(S.identical ? 'engine_same' : 'engine_diff'))
      : S.engine === 'failed' ? t('engine_failed', { e: (S.engineError || '').slice(0, 120) })
      : S.engine === 'idle' ? t('engine_idle') : t('engine_loading');
  }
  function call(fn, arg, force) {
    if (S.engine !== 'ready' && !force) return Promise.reject(new Error('engine not ready'));
    return new Promise((resolve, reject) => {
      const id = S.nextId++; S.pending[id] = { resolve, reject };
      S.worker.postMessage({ id, fn, arg });
    });
  }
  // grade and graph: Python when ready, else the precomputed world (tuned presets only)
  async function engGrade(spec) {
    if (S.engine === 'ready') return call('grade', JSON.stringify(spec));
    return S.def.grades[`${spec.preset}|${spec.vis}`];
  }
  async function engGraph(id) {
    if (S.engine === 'ready') return call('fraud_graph', id);
    return S.def.graphs[`${S.preset}|${S.vis}`][String(id)];
  }

  /* ---------------------------------------------------------------- URL state: rule, fraud and account survive a reload or a shared link */
  function readUrl() {
    const q = new URLSearchParams(location.search);
    if (['10k', 'rev2', 'rev3'].includes(q.get('rule'))) S.preset = q.get('rule');
    if (['V1', 'V3'].includes(q.get('vis'))) S.vis = q.get('vis');
    if (q.get('fraud')) S.urlFraud = +q.get('fraud');
    if (q.get('acc')) S.urlAcc = q.get('acc');
  }
  function writeUrl() {
    if (!S.world) return;
    const q = new URLSearchParams();
    q.set('rule', S.preset); q.set('vis', S.vis);
    if (S.fraud !== null && S.world.seed === S.def.world.seed) q.set('fraud', S.fraud);
    if (S.selected && S.world.seed === S.def.world.seed) q.set('acc', S.selected);
    history.replaceState(null, '', `?${q}${location.hash}`);
  }

  /* ---------------------------------------------------------------- language and navigation */
  function applyLang() {
    document.documentElement.lang = S.lang;
    document.title = t('doc_title');
    $$('[data-i18n]').forEach(e => { const v = t(e.dataset.i18n); if (typeof v === 'string') e.textContent = v; });
    $$('.lang button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.lang === S.lang)));
    $('.lang').setAttribute('aria-label', t('lang_label'));
    $('#vis').setAttribute('aria-label', t('vis_label'));
    $('#nav').setAttribute('aria-label', t('nav_label'));
    $('#ask-in').placeholder = t('ask_ph');
    const cap = { 'cap-main': ['fig', 'B-1', 'res_main_h'], 'cap-role': ['fig', 'B-2', 'res_role_h'], 'cap-pattern': ['fig', 'B-3', 'res_pattern_h'],
      'cap-speed': ['fig', 'B-4', 'res_speed_h'], 'cap-k': ['fig', 'B-5', 'res_k_h'], 'cap-flow': ['fig', 'C-1', 'real_flow_h'], 'cap-ex': ['fig', 'C-2', 'real_ex_h'],
      'cap-check': ['fig', 'C-3', 'real_check_h'] };
    for (const id in cap) { const [k, n, h] = cap[id]; $('#' + id).textContent = `${t(k)} ${n} · ${t(h)}`; }
    engineStatus(); renderStory(); renderPatterns(); renderSim(); renderData(); renderSources();
    if (S.chartsDrawn) { renderResults(); renderReal(); }
  }
  function route() {
    const id = (location.hash || '#story').slice(1);
    const el = document.getElementById(id);
    const page = el && el.classList.contains('page') ? id : 'story';
    const changed = page !== S.page; S.page = page;
    $$('.page').forEach(p => { p.classList.toggle('on', p.id === page); p.classList.toggle('turn', changed && p.id === page); });
    $$('#nav a').forEach(a => { if (a.getAttribute('href') === '#' + page) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current'); });
    if (['simulator', 'results', 'real-data', 'data'].includes(page)) document.body.setAttribute('data-wide', ''); else document.body.removeAttribute('data-wide');
    if (page === 'simulator') { ensureEngine(); if (changed && S.graph) renderSim(); } // redraw once visible, so labels scale to the real width
    if ((page === 'results' || page === 'real-data') && !S.chartsDrawn && S.thesis) { S.chartsDrawn = true; renderResults(); renderReal(); }
    const active = $(`#nav a[href="#${page}"]`); if (active && active.scrollIntoView && window.innerWidth <= 900) active.scrollIntoView({ block: 'nearest', inline: 'center' });
    if (changed) { window.scrollTo(0, 0); $('#main').focus({ preventScroll: true }); }
  }

  /* ---------------------------------------------------------------- the report */
  function renderStory() {
    if (!S.thesis) return;
    const m = S.thesis.main_E;
    $('#p1').innerHTML = t('p1', { a: `<mark>${pct(m.ten_k.recall, 0)}</mark>`, b: `<mark>${pct(m.rev3_V3.recall, 0)}</mark>` }) +
      ` <a class="cite" href="#results">${esc(t('cite_b1'))}</a>`;
    const k = [['ten_k', 'key_rule10'], ['rev2_V3', 'key_rev2'], ['rev3_V3', 'key_rev3']];
    $('#kpis').innerHTML = `<table class="t"><caption>${t('tbl')} R-1 · ${esc(t('key_tbl'))}</caption><thead><tr><th scope="col">${t('col_rule')}</th><th scope="col" class="n">${t('key_found')}</th><th scope="col" class="n">${t('key_prec')}</th></tr></thead><tbody>` +
      k.map(([key, lab]) => `<tr><th scope="row" style="font-weight:${key === 'rev3_V3' ? 800 : 500}">${t(lab)}</th><td class="n">${pct(m[key].recall, 0)}</td><td class="n">${pct(m[key].precision)}</td></tr>`).join('') + '</tbody></table>';
    const c = S.thesis.real.check_90d;
    $('#key-real').textContent = t('key_real', { g3: pct(c.G3.either, 0), g0: pct(c['grade 0'].either, 0) });
  }

  /* ---------------------------------------------------------------- simulator */
  function renderPatterns() {
    const box = $('#pat-boxes'); const sel = new Set((S.world && S.world.settings.typologies) || ['T1', 'T2', 'T3', 'T4', 'T5', 'T7', 'T8', 'T9']);
    const prev = new Set($$('#pat-boxes input:checked').map(i => i.value));
    const use = prev.size ? prev : sel;
    box.innerHTML = Object.entries(t('patterns')).map(([k, v]) => `<label class="check"><input type="checkbox" value="${k}" ${use.has(k) ? 'checked' : ''}> ${esc(v)}</label>`).join('');
    $$('#pat-boxes input').forEach(i => i.disabled = S.engine !== 'ready' || S.busy);
  }
  function setControls() {
    const ready = S.engine === 'ready';
    const tuneOff = S.preset === '10k';
    ['#new-world', '#sl-frauds', '#sl-kmin', '#sl-kmax', '#sel-window', '#sl-spread', '#sl-cex']
      .forEach(q => { $(q).disabled = !ready || S.busy; });
    ['#sl-sigma', '#sl-kappa', '#sl-pi', '#cb-fan', '#sl-fank', '#sl-fandt', '#sl-fanr', '#reset']
      .forEach(q => { $(q).disabled = !ready || S.busy || tuneOff; });
    $('#tune-off').hidden = !tuneOff;
    $('#adv-sub').textContent = ready ? t('adv_sub') : t('needs_python');
    $$('#pat-boxes input').forEach(i => i.disabled = !ready || S.busy);
    const fixedWindow = $('#sel-window').value !== 'random';
    $('#sl-spread').disabled = !ready || S.busy || !fixedWindow;
    $('#lab-spread').classList.toggle('off', !fixedWindow);
  }
  function syncSliders() {
    const r = S.res.rule;
    $('#sl-sigma').value = r.g2_share; $('#sl-kappa').value = r.concentration; $('#sl-pi').value = r.pass_through;
    $('#cb-fan').checked = r.fan_k > 0; $('#sl-fank').value = Math.max(1, r.fan_k); $('#sl-fandt').value = r.fan_window_h; $('#sl-fanr').value = r.fan_ratio;
    sliderLabels();
    $('#custom-note').hidden = !Object.keys(S.overrides).length;
  }
  function sliderLabels() {
    $('#v-sigma').textContent = pct(+$('#sl-sigma').value, 0); $('#v-kappa').textContent = pct(+$('#sl-kappa').value, 0); $('#v-pi').textContent = pct(+$('#sl-pi').value, 0);
    $('#v-fank').textContent = $('#sl-fank').value; $('#v-fandt').textContent = $('#sl-fandt').value + ' h'; $('#v-fanr').textContent = '×' + (+$('#sl-fanr').value).toFixed(1);
    $('#v-frauds').textContent = $('#sl-frauds').value; $('#v-mules').textContent = `${$('#sl-kmin').value} – ${$('#sl-kmax').value}`;
    $('#v-spread').textContent = (+$('#sl-spread').value).toFixed(1); $('#v-cex').textContent = pct(+$('#sl-cex').value, 0);
  }
  async function regrade(keepFraud = true) {
    const spec = { preset: S.preset, vis: S.vis, base: S.preset === '10k' ? 'rev2' : S.preset, overrides: S.overrides };
    S.res = await engGrade(spec);
    if (!keepFraud || S.fraud === null) S.fraud = pickFraud();
    S.graph = await engGraph(S.fraud);
    if (S.selected && !S.graph.nodes.some(n => n.id === S.selected)) S.selected = null;
    syncSliders(); renderSim();
    if (S.engine === 'ready') { S.rows = await call('sample_rows'); renderData(); }
  }
  function pickFraud() {
    if (S.urlFraud !== undefined && S.world.frauds.some(f => f.id === S.urlFraud)) { const f = S.urlFraud; S.urlFraud = undefined; return f; }
    const fr = S.world.frauds.filter(f => ['T4', 'T5', 'T3'].includes(f.pattern)).sort((a, b) => b.accounts - a.accounts);
    return (fr[0] || S.world.frauds[0]).id;
  }
  function fraudHead() {
    const f = S.world.frauds.find(x => x.id === S.fraud); if (!f) return '';
    const seed = S.graph.nodes.find(n => n.id === 'seed');
    return `${t('fraud_pick')} ${f.id} · ${patName(f.pattern)} · ${eur(f.F)} · ` + t('fraud_involved', { i: f.involved, n: f.accounts }) +
      (seed ? ' · ' + t('fraud_day', { d: Math.round(seed.blacklisted_h / 24) }) : '') +
      (f.collector ? ` · ${f.collector_traced === false || S.graph.nodes.some(n => n.id === 'collector' && n.found === false) ? t('coll_untraced') : t('legend_coll')}` : '');
  }
  function renderSim() {
    if (!S.res || !S.graph) return;
    $$('#presets button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.preset === S.preset)));
    $$('#vis button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.vis === S.vis)));
    $$('#colorby button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.c === S.colorBy)));
    const sel = $('#sel-fraud');
    sel.innerHTML = S.world.frauds.map(f => `<option value="${f.id}" ${f.id === S.fraud ? 'selected' : ''}>${esc(t('fraud_opt', { id: f.id, p: patName(f.pattern), e: eur(f.F), n: f.accounts }))}</option>`).join('');
    $('#fraud-head').textContent = fraudHead();
    const accts = S.graph.nodes.filter(n => n.kind === 'account');
    const nEx = new Set(accts.map(a => a.exchange)).size;
    $('#net').setAttribute('aria-label', t('net_label', { id: S.fraud, n: accts.length, e: nEx }));
    $('#net-hint').textContent = t('net_hint', { e: nEx });
    const o = { colorBy: S.colorBy, mistakes: S.mistakes, preset: S.preset, t, lang: S.lang, selected: S.selected, eur,
      onSelect: (n) => { S.selected = n.id; renderSim(); const c = $('#card'); if (window.innerWidth <= 1180 && c.scrollIntoView) c.scrollIntoView({ block: 'nearest', behavior: reduceMotion() ? 'auto' : 'smooth' }); } };
    NET.draw($('#net'), S.graph, o); NET.legend($('#legend'), o, S.graph);
    if (S.focusAcc) { const g = $(`#net [data-id="${S.focusAcc}"]`); if (g) g.focus(); S.focusAcc = null; }
    renderAccList(accts); renderCard(); renderStrip(); renderMetrics();
    const w = S.world;
    if (!S.busy && !$('#world-info .errdetails')) $('#world-info').textContent = t('world_info', { seed: w.seed, frauds: w.frauds.length, accounts: num(w.n_accounts), rows: num(w.n_rows) });
    setControls(); writeUrl();
  }
  function gradeOf(n) { return S.preset === '10k' ? (n.ten_k ? t('flag_10k') : '–') : `<span class="chip c${n.grade}">G${n.grade}</span>`; }
  function renderAccList(accts) {
    const rows = [...accts].sort((a, b) => b.X - a.X);
    $('#acc-table').innerHTML = `<table class="t"><thead><tr><th scope="col">${t('card_h')}</th><th scope="col">${t('exch')}</th><th scope="col" class="n">${t('card_x')}</th><th scope="col">${S.preset === '10k' ? t('preset_10k') : t('card_grade')}</th><th scope="col">${t('card_role')}</th><th></th></tr></thead><tbody>` +
      rows.map(a => `<tr><td>${a.aid}</td><td>${esc(a.exchange)}</td><td class="n">${eur(a.X)}</td><td>${gradeOf(a)}</td><td>${esc(t('roles')[a.role] || a.role)}</td><td><button class="link" data-open="${a.id}">${t('acc_open')}</button></td></tr>`).join('') + '</tbody></table>';
    $$('#acc-table [data-open]').forEach(b => b.addEventListener('click', () => { S.selected = b.dataset.open; renderSim(); $('#card').focus && $('#card h2') && $('#card h2').focus(); }));
  }
  function renderCard() {
    const box = $('#card');
    const n = S.graph.nodes.find(x => x.id === S.selected);
    if (!n) { box.innerHTML = `<h2>${t('card_h')}</h2><p class="note">${t('card_empty')}</p>`; return; }
    const r = n.reasons, rule = S.res.rule;
    const inv = NET.INVOLVED.has(n.role);
    const mark = (ok) => ok ? '<svg viewBox="0 0 14 14" aria-hidden="true"><path d="M2 7.5l3.2 3.2L12 3.5"/></svg>' : '<svg viewBox="0 0 14 14" aria-hidden="true"><path d="M3 3l8 8M11 3l-8 8"/></svg>';
    const li = (ok, txt) => `<li class="${ok ? 'y' : 'n'}">${mark(ok)}<span><span class="sr-only">${ok ? t('yes') : t('no')}: </span>${esc(txt)}</span></li>`;
    const or = S.lang === 'fr' ? ' ou ' : ' or ';
    const g1 = li(r.amount_ok, t('r_amount')) + li(r.share_g1 || r.big_amount || r.common_destination,
      [t('r_share1', { v: pct(rule.g1_share, 0) }), t('r_big'), t('r_conv')].join(or));
    const g2 = li(r.share_g2 || r.big_amount || r.common_destination, t('r_share2', { v: pct(rule.g2_share, 0) }) + (S.lang === 'fr' ? ' (ou montant / destination)' : ' (or amount / destination)')) +
      li(r.concentration_ok || r.pass_through_ok, t('r_kappa', { v: pct(rule.concentration, 0) }) + or + t('r_pi', { v: pct(rule.pass_through, 0) })) +
      (rule.fan_k > 0 ? li(r.fan_route, t('r_fan', { n: r.fan_siblings, h: rule.fan_window_h, k: rule.fan_k })) : '') +
      li(!r.victim, t('r_victim'));
    const g3 = li(r.same_person_other_exchange, t('r_same')) + li(r.second_seed, t('r_second')) + li(r.common_destination && (r.share_g1 || r.big_amount), t('r_conv'));
    box.innerHTML = `<h2 tabindex="-1">${t('card_h')} ${n.aid}</h2><p class="cardsub">${t('exch')} ${esc(n.exchange)}</p>
      <table>
        <tr><td>${t('card_role')}</td><td style="color:${inv ? 'var(--g3)' : 'var(--ink-2)'}">${esc(t('roles')[n.role] || n.role)} (${inv ? t('involved') : t('innocent')})</td></tr>
        <tr><td>${t('card_10k')}</td><td>${n.ten_k ? t('yes') : t('no')}</td></tr>
        <tr><td>${t('card_grade')}</td><td><span class="chip c${n.grade}">G${n.grade}</span></td></tr>
        <tr><td>${t('card_x')}</td><td>${eur(n.X)}</td></tr>
        <tr><td>${t('card_share')}</td><td>${pct(n.share)}</td></tr>
        <tr><td>${t('card_kappa')}</td><td>${pct(n.concentration, 0)}</td></tr>
        <tr><td>${t('card_pi')}</td><td>${pct(n.pass_24h, 0)}</td></tr>
        <tr><td>${t('card_pi7')}</td><td>${pct(n.pass_7d, 0)}</td></tr>
        <tr><td>${t('card_age')}</td><td>${num(n.age_days)} ${t('days')}</td></tr>
        <tr><td>${t('card_tx')}</td><td>${n.n_tx}</td></tr>
      </table>
      ${S.preset === '10k' ? `<p class="note" style="margin-top:10px">${t('card_10k_note')}</p>` : ''}
      <h3>${t('card_why')}</h3>
      <b class="why"><span class="chip c1">G1</span></b><ul class="why">${g1}</ul><b class="why"><span class="chip c2">G2</span></b><ul class="why">${g2}</ul><b class="why"><span class="chip c3">G3</span></b><ul class="why">${g3}</ul>`;
  }
  function renderStrip() {
    const sel = S.res.selected, ten = S.res.ten_k, m = S.thesis.main_E;
    const custom = Object.keys(S.overrides).length;
    const ruleName = custom ? t('custom_rule') : t('preset_' + S.preset);
    const row = (name, rec, found, prec, fa, hl) => `<tr${hl ? ' style="font-weight:700"' : ''}><th scope="row" style="font-weight:inherit">${esc(name)}</th><td class="n">${hl ? `<mark>${rec}</mark>` : rec}</td><td class="n">${found}</td><td class="n">${prec}</td><td class="n">${fa}</td></tr>`;
    const other = S.preset === '10k'
      ? row(t('strip_rev3'), pct(m.rev3_V3.recall, 0), '–', pct(m.rev3_V3.precision, 0), '–', false)
      : row(t('met_vs10k'), pct(ten.recall, 0), `${ten.found} / ${ten.involved}`, pct(ten.precision, 0), ten.false_alerts, false);
    $('#strip').innerHTML = `<table class="t"><caption>${t('tbl')} A-1 · ${esc(t('met_h'))}</caption><thead><tr><th scope="col">${t('col_rule')}</th><th scope="col" class="n">${t('met_found')}</th><th scope="col" class="n">${t('col_accounts')}</th><th scope="col" class="n">${t('met_prec')}</th><th scope="col" class="n">${t('met_fa')}</th></tr></thead><tbody>` +
      row(ruleName, pct(sel.recall, 0), `${sel.found} / ${sel.involved}`, pct(sel.precision, 0), sel.false_alerts, true) + other + '</tbody></table>';
  }
  function renderMetrics() {
    const r = S.res, sel = r.selected;
    const key = S.preset === '10k' ? 'ten_k' : `${S.preset}_${S.vis}`;
    const ref = !Object.keys(S.overrides).length && S.thesis.main_E[key];
    const refTxt = (k) => ref ? `<div class="r">${t('met_thesis')}: ${pct(ref[k])}</div>` : '';
    $('#metrics').innerHTML = [
      [t('met_found'), pct(sel.recall), `${sel.found} / ${sel.involved}`, refTxt('recall')],
      [t('met_prec'), pct(sel.precision), `${sel.false_alerts} ${t('met_fa').toLowerCase()}`, refTxt('precision')],
      [t('met_value'), pct(sel.value_recall), '', refTxt('value_recall')],
      [t('met_frauds'), pct(r.frauds_with_one_found), '', ''],
      [t('met_g3'), S.preset === '10k' ? '–' : pct(r.g3.precision), S.preset === '10k' ? '' : `${r.g3.found + r.g3.false_alerts} G3`, ''],
      [t('met_vs10k'), pct(r.ten_k.recall), `${t('met_prec')} ${pct(r.ten_k.precision)}`, ''],
    ].map(([l, v, s, ref]) => `<div class="m"><div class="l">${esc(l)}</div><div class="v">${v}</div><div class="s">${esc(s)}</div>${ref}</div>`).join('');
    const pos = ['SELF', 'MULE', 'FACILITATOR', 'ACCOMPLICE'], neg = ['P2P', 'VICTIM', 'FRAMED', 'LANDLORD', 'SERVICE', 'BAIT'];
    const row = (rk, cls) => { const b = r.by_role[rk]; if (!b) return '';
      return `<div>${esc(t('roles')[rk])} <span class="note">(${b.flagged}/${b.n})</span><div class="bar ${cls}" role="img" aria-label="${pct(b.rate || 0, 0)}"><i style="width:${100 * (b.rate || 0)}%"></i></div></div>`; };
    $('#roles').innerHTML = `<div class="h">${t('role_h')}</div>` + pos.map(x => row(x, '')).join('') + neg.map(x => row(x, 'neg')).join('');
  }
  async function newWorld(params) {
    if (S.engine !== 'ready') throw new Error('Python not ready');
    S.busy = true; setControls(); $('#world-info').textContent = t('world_busy');
    try {
      const p = params || readWorldControls();
      if (p.seed === undefined) p.seed = Math.floor(Math.random() * 900000) + 100000;
      const w = await call('new_world', JSON.stringify(p));
      w.params = p; S.world = w; S.fraud = null; S.selected = null;
      await regrade(false);
      return w;
    } finally { S.busy = false; setControls(); renderSim(); }
  }
  // A short, translated message; the Python traceback stays available behind "Technical details".
  function worldError(e) {
    const box = $('#world-info');
    box.textContent = '';
    const msg = document.createElement('span');
    msg.className = 'warn'; msg.textContent = t('world_failed');
    const det = document.createElement('details');
    det.className = 'errdetails';
    const sum = document.createElement('summary'); sum.textContent = t('error_details');
    const pre = document.createElement('pre'); pre.textContent = String(e && e.message || e);
    det.append(sum, pre);
    box.append(msg, det);
  }
  function readWorldControls() {
    const p = { n_seeds: +$('#sl-frauds').value, k_min: +$('#sl-kmin').value, k_max: +$('#sl-kmax').value, cex_share: +$('#sl-cex').value,
      typologies: $$('#pat-boxes input:checked').map(i => i.value) };
    if (!p.typologies.length) p.typologies = ['T4'];
    const w = $('#sel-window').value;
    if (w !== 'random') { p.mule_window_h = +w; p.split_spread = +$('#sl-spread').value; }
    return p;
  }

  /* ---------------------------------------------------------------- results (charts, each with a text table) */
  const C = { r3: '#2a5db0', r2: '#8fb0de', k10: '#8a8a84', red: '#b3261e' };
  function srTable(canvas, cfg) {
    const old = canvas.parentNode.querySelector('div.sr-only'); if (old) old.remove();
    const d = cfg.data, fmt = cfg.fmt || (v => v === null || v === undefined ? '–' : (+v).toFixed(1) + (cfg.unit === undefined ? ' %' : cfg.unit));
    const wrap = document.createElement('div'); wrap.className = 'sr-only';
    const tb = document.createElement('table'); wrap.appendChild(tb);
    tb.innerHTML = `<caption>${esc(t('fig_data'))}</caption><tr><th></th>${d.datasets.map(s => `<th scope="col">${esc(s.label)}</th>`).join('')}</tr>` +
      d.labels.map((l, i) => `<tr><th scope="row">${esc(l)}</th>${d.datasets.map(s => `<td>${fmt(s.data[i])}</td>`).join('')}</tr>`).join('');
    canvas.parentNode.appendChild(wrap);
  }
  function chart(id, cfg) {
    if (S.charts[id]) S.charts[id].destroy();
    const cv = document.getElementById(id);
    const fig = cv.closest('figure'); const cap = fig && fig.querySelector('figcaption b');
    cv.setAttribute('role', 'img'); cv.setAttribute('aria-label', cap ? cap.textContent : id);
    cfg.options = cfg.options || {}; cfg.options.animation = reduceMotion() ? false : { duration: 500 };
    cfg.options.maintainAspectRatio = true; cfg.options.aspectRatio = cfg.aspect || (window.innerWidth < 600 ? 1.1 : 1.6);
    S.charts[id] = new Chart(cv, cfg); srTable(cv, cfg);
  }
  const pctAxis = { min: 0, max: 100, ticks: { callback: v => v + ' %' }, grid: { color: '#ecece8' } };
  function renderResults() {
    if (!S.thesis || typeof Chart === 'undefined') return;
    Chart.defaults.font.family = '"Libre Franklin", system-ui, sans-serif'; Chart.defaults.font.size = 13; Chart.defaults.color = '#33332f';
    const m = S.thesis.main_E;
    const L = { ten_k: t('preset_10k'), rev2_V1: `${t('preset_rev2')} · ${t('vis_v1')}`, rev2_V3: `${t('preset_rev2')} · ${t('vis_v3')}`,
      rev3_V1: `${t('preset_rev3')} · ${t('vis_v1')}`, rev3_V3: `${t('preset_rev3')} · ${t('vis_v3')}` };
    const ks = Object.keys(L);
    const rows = ks.concat(['rev2_V3_G3', 'rev3_V3_G3']);
    const lab = (k) => L[k] || (k.startsWith('rev2') ? `${t('preset_rev2')} · G3` : `${t('preset_rev3')} · G3`);
    const ci = (lo, hi) => `<span class="ci">[${(100 * lo).toFixed(0)}–${(100 * hi).toFixed(0)}]</span>`;
    $('#res-table').innerHTML = `<table class="t"><caption>${t('tbl')} B-1 · ${esc(t('res_table_h'))}</caption><thead><tr><th scope="col">${t('col_rule')}</th><th scope="col" class="n">${t('col_rec')}</th><th scope="col" class="n">${t('col_prec')}</th><th scope="col" class="n">${t('col_val')}</th><th scope="col" class="n">${t('col_fa')}</th></tr></thead><tbody>` +
      rows.map(k => `<tr${k === 'rev3_V3' ? ' style="font-weight:700"' : ''}><th scope="row" style="font-weight:inherit">${esc(lab(k))}</th><td class="n">${k === 'ten_k' || k === 'rev3_V3' ? `<mark>${pct(m[k].recall)}</mark>` : pct(m[k].recall)} ${ci(m[k].rec_lo, m[k].rec_hi)}</td><td class="n">${pct(m[k].precision)} ${ci(m[k].prec_lo, m[k].prec_hi)}</td><td class="n">${pct(m[k].value_recall)}</td><td class="n">${(m[k].fp_per_fraud).toFixed(2)}</td></tr>`).join('') + '</tbody></table>';
    chart('ch-main', { type: 'bar', data: { labels: ks.map(k => L[k]), datasets: [
      { label: t('col_rec'), data: ks.map(k => 100 * m[k].recall), backgroundColor: C.r3 },
      { label: t('col_prec'), data: ks.map(k => 100 * m[k].precision), backgroundColor: C.r2 }] },
      aspect: window.innerWidth < 600 ? 0.8 : 1.25,
      options: { indexAxis: 'y', scales: { x: pctAxis, y: { grid: { display: false } } }, plugins: { tooltip: { callbacks: { label: c => `${c.dataset.label}: ${c.raw.toFixed(1)} %` } } } } });
    const br = S.thesis.by_role_E;
    const rl = [['own account (SELF)', t('roles').SELF], ['mule', t('roles').MULE], ['mule, without T7', t('roles').MULE + ' (≠T7)'], ['facilitator', t('roles').FACILITATOR], ['all involved', t('all_involved')]];
    const three = (src, keys) => [
      { label: t('preset_10k'), data: keys.map(x => 100 * src(x).ten_k), backgroundColor: C.k10 },
      { label: t('preset_rev2'), data: keys.map(x => 100 * src(x).rev2), backgroundColor: C.r2 },
      { label: t('preset_rev3'), data: keys.map(x => 100 * src(x).rev3), backgroundColor: C.r3 }];
    chart('ch-role', { type: 'bar', aspect: window.innerWidth < 600 ? 0.8 : 1.25, data: { labels: rl.map(x => x[1]), datasets: three(x => br[x], rl.map(x => x[0])) }, options: { indexAxis: 'y', scales: { x: pctAxis, y: { grid: { display: false } } } } });
    const bp = S.thesis.by_pattern_E, pk = Object.keys(bp);
    chart('ch-pattern', { type: 'bar', aspect: window.innerWidth < 600 ? 0.8 : 2.4, data: { labels: pk.map(k => patName(k)), datasets: three(k => bp[k], pk) }, options: { indexAxis: 'y', scales: { x: pctAxis, y: { grid: { display: false } } } } });
    const sp = S.thesis.sweep_speed, wins = [...new Set(sp.map(x => x.window_h))].sort((a, b) => a - b);
    const ser = (det, k) => wins.map(w => 100 * sp.find(x => x.window_h === w && x.detector === det)[k]);
    const wl = wins.map(w => w <= 72 ? w + ' h' : (S.lang === 'fr' ? '7 jours' : '7 days'));
    const lines = (f) => [
      { label: `${t('col_rec')} · ${t('preset_rev3')}`, data: f('Rev3 V3 G2+', 'recall'), borderColor: C.r3, backgroundColor: C.r3, borderWidth: 3 },
      { label: `${t('col_rec')} · ${t('preset_rev2')}`, data: f('Rev2 frozen V3 G2+', 'recall'), borderColor: C.r2, backgroundColor: C.r2, borderWidth: 3 },
      { label: `${t('col_prec')} · ${t('preset_rev3')}`, data: f('Rev3 V3 G2+', 'precision'), borderColor: C.r3, borderDash: [6, 4], backgroundColor: C.r3, borderWidth: 2 },
      { label: `${t('col_prec')} · ${t('preset_rev2')}`, data: f('Rev2 frozen V3 G2+', 'precision'), borderColor: C.r2, borderDash: [6, 4], backgroundColor: C.r2, borderWidth: 2 }];
    chart('ch-speed', { type: 'line', data: { labels: wl, datasets: lines(ser) }, options: { scales: { y: pctAxis } } });
    const sk = S.thesis.sweep_k, kk = [...new Set(sk.map(x => x.k))];
    const kser = (det, k) => kk.map(v => 100 * sk.find(x => x.k === v && x.detector === det)[k]);
    chart('ch-k', { type: 'line', data: { labels: kk.map(v => v + ' mules'), datasets: lines(kser) }, options: { scales: { y: pctAxis } } });
  }

  /* ---------------------------------------------------------------- real data */
  function renderReal() {
    if (!S.thesis || typeof Chart === 'undefined') return;
    const r = S.thesis.real;
    $('#real-kpis').innerHTML = `<table class="t"><caption>${t('tbl')} C-1 · ${esc(t('real_facts_h'))}</caption><tbody>` + [
      [num(r.phishing_active), t('real_seeds')], [meur(r.total_out_eur), t('real_sent')],
      [num(r.deposit_addresses), t('real_deposits')], [pct(r.fraud_eur_to_deposits / r.total_out_eur), t('real_reach')]]
      .map(([v, l]) => `<tr><td class="n" style="font-weight:800;width:7em">${v}</td><td>${esc(l)}</td></tr>`).join('') + '</tbody></table>';
    const fk = Object.keys(r.flows_share).sort((a, b) => r.flows_share[b] - r.flows_share[a]);
    chart('ch-flow', { type: 'bar', data: { labels: fk.map(k => t('flows')[k] || k), datasets: [{ label: '%', data: fk.map(k => 100 * r.flows_share[k]), backgroundColor: C.r3 }] },
      options: { indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: pctAxis, y: { grid: { display: false } } } } });
    $('#real-roles').innerHTML = `<table class="t"><caption>${t('tbl')} C-2 · ${esc(t('real_roles_h'))}</caption><thead><tr><th></th><th scope="col" class="n">${t('col_n')}</th><th scope="col" class="n">${t('col_eur')}</th></tr></thead><tbody>` +
      Object.entries(r.hop1_roles).map(([k, v]) => `<tr><th scope="row" style="font-weight:500">${esc(t('hop')[k])}</th><td class="n">${num(v.n)}</td><td class="n">${meur(v.eur)}</td></tr>`).join('') + '</tbody></table>';
    const ek = Object.keys(r.by_exchange);
    chart('ch-ex', { type: 'bar', fmt: v => num(v), data: { labels: ek, datasets: [{ label: t('col_accounts'), data: ek.map(k => r.by_exchange[k]), backgroundColor: C.r2 }] }, options: { plugins: { legend: { display: false } }, scales: { x: { grid: { display: false } } } } });
    $('#real-grades').innerHTML = `<table class="t"><caption>${t('tbl')} C-3 · ${esc(t('real_grades_h'))}</caption><thead><tr><th></th><th scope="col" class="n">${t('col_accounts')}</th><th scope="col" class="n">${t('col_med')}</th><th scope="col" class="n">${t('col_tot')}</th><th scope="col" class="n">${t('col_kappa')}</th></tr></thead><tbody>` +
      Object.entries(r.grades).map(([g, v]) => `<tr><th scope="row"><span class="chip c${g[1]}">${g}</span></th><td class="n">${v.n}</td><td class="n">${eur(v.X_median)}</td><td class="n">${meur(v.X_total)}</td><td class="n">${pct(v.kappa_median, 0)}</td></tr>`).join('') +
      `<tr><th scope="row" style="font-weight:500">${t('preset_10k')}</th><td class="n">${r.rule10k}</td><td colspan="3" class="note">${S.lang === 'fr'
        ? `${r.overlap.both} en commun avec G2/G3 ; ${r.overlap.grades_only} G2/G3 sous 10 k€ ; ${r.overlap.ten_k_only} ≥ 10 k€ mais pas G2`
        : `${r.overlap.both} shared with G2/G3; ${r.overlap.grades_only} G2/G3 below €10k; ${r.overlap.ten_k_only} ≥ €10k but not G2`}</td></tr></tbody></table>`;
    const cg = ['grade 0', 'G1', 'G2', 'G3', '10k rule'];
    chart('ch-check', { type: 'bar', data: { labels: cg.map(g => `${t('check_groups')[g]} (${r.check_90d[g].accounts})`), datasets: [
      { label: t('col_either'), data: cg.map(g => 100 * r.check_90d[g].either), backgroundColor: cg.map(g => g === 'G3' ? C.red : g === '10k rule' ? C.k10 : C.r3) }] },
      options: { plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => { const g = r.check_90d[cg[c.dataIndex]];
        return `${c.raw.toFixed(1)} % [${(100 * g.lo).toFixed(0)}–${(100 * g.hi).toFixed(0)} %] · ${t('col_same')} ${(100 * g.same).toFixed(1)} % · ${t('col_new')} ${(100 * g.new).toFixed(1)} %`; } } } },
        indexAxis: 'y', scales: { x: { min: 0, max: 80, ticks: { callback: v => v + ' %' }, grid: { color: '#ecece8' } }, y: { grid: { display: false } } } } });
    const f = r.fanout;
    $('#real-fan').textContent = t('real_fan_p', { gap: hours(f.median_gap_h), ratio: f.median_ratio.toFixed(1), fires: f.seeds_route_fires, multi: f.seeds_multi });
    $('#real-g3').innerHTML = `<table class="t"><caption>${t('tbl')} C-4 · ${esc(t('real_g3_h'))}</caption><thead><tr><th scope="col">${t('col_addr')}</th><th scope="col">${t('col_ex')}</th><th scope="col" class="n">${t('col_x')}</th><th scope="col" class="n">${t('col_seeds')}</th><th scope="col" class="n">${t('col_kappa1')}</th></tr></thead><tbody>` +
      r.g3_examples.map(g => `<tr><td><a href="https://etherscan.io/address/${esc(g.address)}" target="_blank" rel="noopener">${esc(g.address.slice(0, 10))}…${esc(g.address.slice(-6))}<span class="sr-only"> (Etherscan)</span></a></td><td>${esc(g.exchange)}</td><td class="n">${eur(g.X)}</td><td class="n">${g.seeds}</td><td class="n">${pct(g.kappa, 0)}</td></tr>`).join('') + '</tbody></table>';
    $('#real-limits').innerHTML = t('real_limits').map(x => `<li>${esc(x)}</li>`).join('');
  }

  /* ---------------------------------------------------------------- data explained, sources */
  function renderData() {
    $('#cols').innerHTML = `<table class="t"><caption>${t('tbl')} D-1 · ${esc(t('data_cols_h'))}</caption><thead><tr><th scope="col">${t('data_col')}</th><th scope="col">${t('data_mean')}</th><th scope="col">${t('data_src')}</th></tr></thead><tbody>` +
      t('cols').map(([c, m, s]) => `<tr><th scope="row">${esc(c)}</th><td>${esc(m)}</td><td>${esc(s)}</td></tr>`).join('') + '</tbody></table>';
    const rows = S.rows || (S.def && S.def.rows) || [];
    const H = S.lang === 'fr' ? ['part', 'concentration', 'renvoi 24 h', 'victime', 'âge', 'deuxième seed', 'grade', 'rôle'] : ['share', 'concentration', 'pass-through 24 h', 'victim', 'age', 'second seed', 'grade', 'role'];
    $('#rows').innerHTML = `<table class="t"><caption>${t('tbl')} D-2 · ${esc(t('data_rows_h'))}</caption><thead><tr><th scope="col">${t('fraud_pick')}</th><th scope="col">${t('card_h')}</th><th scope="col">${t('exch')}</th><th scope="col" class="n">X</th>${H.slice(0, 3).map(h => `<th scope="col" class="n">${h}</th>`).join('')}<th scope="col">${H[3]}</th><th scope="col" class="n">${H[4]}</th><th scope="col" class="n">${H[5]}</th><th scope="col">${H[6]}</th><th scope="col">${H[7]}</th></tr></thead><tbody>` +
      rows.map(r => `<tr><td>${r.fraud}</td><td>${r.account}</td><td>${esc(r.exchange)}</td><td class="n">${eur(r.X)}</td><td class="n">${pct(r.share)}</td><td class="n">${pct(r.concentration, 0)}</td><td class="n">${pct(r.pass_24h, 0)}</td><td>${r.victim ? t('yes') : t('no')}</td><td class="n">${num(r.age_days)}</td><td class="n">${r.second_seed}</td><td>${r.grade === null ? '–' : `<span class="chip c${r.grade}">G${r.grade}</span>`}</td><td>${esc(t('roles')[r.role] || r.role)}</td></tr>`).join('') + '</tbody></table>';
    $('#pat-list').innerHTML = Object.values(t('patterns')).map(x => `<li>${esc(x)}</li>`).join('');
    $('#role-list').innerHTML = Object.entries(t('roles')).map(([k, v]) => `<li><span style="color:${NET.ROLE_COLORS[k]}" aria-hidden="true">●</span> ${esc(v)}: <span class="note">${NET.INVOLVED.has(k) ? t('involved') : k === 'ACCOMPLICE' ? t('secondary') : t('innocent')}</span></li>`).join('');
  }
  const SOURCES = [
    ['Google BigQuery, public Ethereum dataset (goog_blockchain_ethereum_mainnet_us)', 'https://cloud.google.com/blockchain-analytics/docs/dataset-ethereum'],
    ['ScamSniffer scam database (blacklisted addresses)', 'https://github.com/scamsniffer/scam-database'],
    ['Forta labelled datasets (Etherscan phishing labels)', 'https://github.com/forta-network/labelled-datasets'],
    ['Etherscan labels (exchange hot wallets), brianleect/etherscan-labels', 'https://github.com/brianleect/etherscan-labels'],
    ['Al-E\'mari et al., Labeled Transactions-based Dataset of Ethereum Network (BLTE)', 'https://github.com/salam-ammari/Labeled-Transactions-based-Dataset-of-Ethereum-Network'],
    ['Coin Metrics community data (daily ETH price)', 'https://github.com/coinmetrics/data'],
    ['US Federal Reserve H.10 exchange rates (EUR/USD), via datasets/exchange-rates', 'https://github.com/datasets/exchange-rates'],
    ['RUSI, Following the Fraud: The Role of Money Mules (Lloyds data)', 'https://www.rusi.org/explore-our-research/publications/emerging-insights/following-fraud-role-money-mules'],
    ['Vocalink / Mastercard, The rise of the mule (2nd ed., 2019)', 'https://b2b.mastercard.com/media/1fsooyfv/the-rise-of-the-mule-second-edition.pdf'],
    ['FCA, Proceeds of fraud – detecting and preventing money mules', 'https://www.fca.org.uk/publications/multi-firm-reviews/proceeds-fraud-detecting-preventing-money-mules'],
    ['Sun et al., MonLAD: Money Laundering Agents Detection in Transaction Streams (WSDM 2022)', 'https://arxiv.org/abs/2201.10051'],
    ['Altman et al., Realistic Synthetic Financial Transactions for AML Models (NeurIPS 2023)', 'https://arxiv.org/abs/2306.16424'],
    ['Griffin & Mei, How Do Crypto Flows Finance Slavery? The Economics of Pig Butchering', 'https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4742235'],
    ['Pyodide (Python in the browser)', 'https://pyodide.org'],
  ];
  function renderSources() { $('#src-list').innerHTML = SOURCES.map(([n, u]) => `<li><a href="${u}" target="_blank" rel="noopener">${esc(n)}</a></li>`).join(''); }

  /* ---------------------------------------------------------------- events */
  function wire() {
    $$('.lang button').forEach(b => b.addEventListener('click', () => { S.lang = b.dataset.lang; try { localStorage.setItem('f1-lang', S.lang); } catch (e) {} applyLang(); }));
    window.addEventListener('hashchange', route);
    $$('#presets button').forEach(b => b.addEventListener('click', () => { S.preset = b.dataset.preset; S.overrides = {}; regrade(); }));
    $$('#vis button').forEach(b => b.addEventListener('click', () => { S.vis = b.dataset.vis; S.overrides = {}; regrade(); }));
    $$('#colorby button').forEach(b => b.addEventListener('click', () => { S.colorBy = b.dataset.c; renderSim(); }));
    $('#cb-mist').addEventListener('change', e => { S.mistakes = e.target.checked; renderSim(); });
    $('#sel-fraud').addEventListener('change', async e => { S.fraud = +e.target.value; S.selected = null; S.graph = await engGraph(S.fraud); renderSim(); });
    $('#next-fraud').addEventListener('click', async () => { const ids = S.world.frauds.map(f => f.id); S.fraud = ids[(ids.indexOf(S.fraud) + 1) % ids.length]; S.selected = null; S.graph = await engGraph(S.fraud); renderSim(); });
    $('#play').addEventListener('click', () => NET.play(reduceMotion()));
    $('#net').addEventListener('keydown', e => { const g = e.target.closest && e.target.closest('[data-id]'); if (g && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); S.focusAcc = g.dataset.id; S.selected = g.dataset.id; renderSim(); } });
    const demo = async (e) => {
      e.preventDefault(); S.preset = '10k'; S.overrides = {}; S.selected = null;
      location.hash = '#simulator'; await regrade(); NET.play(reduceMotion());
    };
    $('#demo').addEventListener('click', demo); $('#cite-a').addEventListener('click', demo);
    let timer = null;
    const slid = () => {
      sliderLabels();
      S.overrides = { sigma: +$('#sl-sigma').value, kappa: +$('#sl-kappa').value, pi: +$('#sl-pi').value,
        fan_k: $('#cb-fan').checked ? +$('#sl-fank').value : 0, fan_dt: +$('#sl-fandt').value, fan_ratio: +$('#sl-fanr').value };
      clearTimeout(timer); timer = setTimeout(() => regrade().catch(() => {}), 250);
    };
    ['#sl-sigma', '#sl-kappa', '#sl-pi', '#sl-fank', '#sl-fandt', '#sl-fanr'].forEach(q => $(q).addEventListener('input', slid));
    $('#cb-fan').addEventListener('change', slid);
    $('#reset').addEventListener('click', () => { S.overrides = {}; regrade(); });
    ['#sl-frauds', '#sl-kmin', '#sl-kmax', '#sl-spread', '#sl-cex'].forEach(q => $(q).addEventListener('input', () => {
      if (+$('#sl-kmin').value > +$('#sl-kmax').value) $('#sl-kmax').value = $('#sl-kmin').value; sliderLabels(); }));
    $('#sel-window').addEventListener('change', setControls);
    $('#new-world').addEventListener('click', () => newWorld().catch(worldError));
    let rt = null; window.addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(() => { if (S.chartsDrawn) { renderResults(); renderReal(); } if (S.page === 'simulator' && S.graph) renderSim(); }, 300); });
  }

  async function init() {
    let saved = null; try { saved = localStorage.getItem('f1-lang'); } catch (e) {}
    S.lang = saved || ((navigator.language || '').toLowerCase().startsWith('fr') ? 'fr' : 'en');
    readUrl(); wire(); route();
    const [th, def] = await Promise.all([fetch('data/thesis.json').then(r => r.json()), fetch('data/world_default.json').then(r => r.json())]);
    S.thesis = th; S.def = def; S.world = def.world; S.world.params = {};
    if (S.urlAcc) { S.selected = S.urlAcc; S.urlAcc = undefined; }
    applyLang();
    await regrade(false);
    route();
  }
  // used by the Claude box
  const api = {
    state: () => S, t, newWorld, call, ensureEngine,
    async setRule({ preset, visibility, overrides }) {
      if (preset) S.preset = preset; if (visibility) S.vis = visibility;
      S.overrides = overrides || {}; await regrade(); return S.res;
    },
    async showFraud(id) { S.fraud = +id; S.selected = null; S.graph = await engGraph(S.fraud); renderSim(); location.hash = '#simulator'; return S.graph; },
    selectAccount(id) { S.selected = 'a' + id; renderSim(); return S.graph.nodes.find(n => n.id === S.selected) || null; },
  };
  document.addEventListener('DOMContentLoaded', init);
  return api;
})();
