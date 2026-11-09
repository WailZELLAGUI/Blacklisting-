/* Main page logic: navigation, languages, simulator, charts. */
const APP = (() => {
  const S = { lang: 'en', thesis: null, def: null, world: null, res: null, graph: null, preset: 'rev3', vis: 'V3', overrides: {},
    colorBy: 'grade', mistakes: true, fraud: null, selected: null, engine: 'loading', engineVersion: '', worker: null,
    pending: {}, nextId: 1, charts: {}, busy: false, rows: null };
  const $ = (q) => document.querySelector(q);
  const $$ = (q) => [...document.querySelectorAll(q)];
  const t = (k, vars) => {
    let s = I18N[S.lang][k]; if (s === undefined) s = I18N.en[k]; if (s === undefined) return k;
    if (vars && typeof s === 'string') for (const v in vars) s = s.split('{' + v + '}').join(vars[v]);
    return s;
  };
  const pct = (x, d = 1) => x === null || x === undefined ? '–' : (100 * x).toFixed(d).replace('.', S.lang === 'fr' ? ',' : '.') + ' %';
  const eur = (x) => x === null || x === undefined ? '–' : '€' + Math.round(x).toLocaleString(S.lang === 'fr' ? 'fr-FR' : 'en-GB');
  const num = (x) => Math.round(x).toLocaleString(S.lang === 'fr' ? 'fr-FR' : 'en-GB');
  const meur = (x) => '€' + (x / 1e6).toFixed(1).replace('.', S.lang === 'fr' ? ',' : '.') + (S.lang === 'fr' ? ' M' : 'M');

  /* ---------------------------------------------------------------- Python engine (web worker) */
  function startEngine() {
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
      : S.engine === 'failed' ? t('engine_failed', { e: (S.engineError || '').slice(0, 120) }) : t('engine_loading');
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

  /* ---------------------------------------------------------------- language and navigation */
  function applyLang() {
    document.documentElement.lang = S.lang;
    $$('[data-i18n]').forEach(e => { const v = t(e.dataset.i18n); if (typeof v === 'string') e.textContent = v; });
    $$('.lang button').forEach(b => b.classList.toggle('on', b.dataset.lang === S.lang));
    $('#ask-in').placeholder = t('ask_ph');
    engineStatus(); renderStory(); renderPatterns(); renderSim(); renderData(); renderSources();
    if (S.chartsDrawn) { renderResults(); renderReal(); }
  }
  function route() {
    const id = (location.hash || '#story').slice(1);
    const page = document.getElementById(id) && document.getElementById(id).classList.contains('page') ? id : 'story';
    $$('.page').forEach(p => p.classList.toggle('on', p.id === page));
    $$('#nav a').forEach(a => a.classList.toggle('on', a.getAttribute('href') === '#' + page));
    if ((page === 'results' || page === 'real-data') && !S.chartsDrawn) { S.chartsDrawn = true; renderResults(); renderReal(); }
    window.scrollTo(0, 0);
  }

  /* ---------------------------------------------------------------- the idea */
  function renderStory() {
    if (!S.thesis) return;
    const m = S.thesis.main_E;
    const k = [['ten_k', 'key_rule10'], ['rev2_V3', 'key_rev2'], ['rev3_V3', 'key_rev3']];
    $('#kpis').innerHTML = k.map(([key, lab], i) => `<div class="kpi ${i === 2 ? 'hl' : ''}"><div class="l">${t(lab)}</div>
      <div class="v">${pct(m[key].recall, 0)}</div><div class="s">${t('key_found')}</div>
      <div class="s">${t('key_prec')}: <b>${pct(m[key].precision)}</b></div></div>`).join('');
    const c = S.thesis.real.check_90d;
    $('#key-real').textContent = t('key_real', { g3: pct(c.G3.either, 0), g0: pct(c['grade 0'].either, 0) });
  }

  /* ---------------------------------------------------------------- simulator */
  function renderPatterns() {
    const box = $('#pat-boxes'); const sel = new Set((S.world && S.world.settings.typologies) || ['T1', 'T2', 'T3', 'T4', 'T5', 'T7', 'T8', 'T9']);
    const prev = new Set($$('#pat-boxes input:checked').map(i => i.value));
    const use = prev.size ? prev : sel;
    box.innerHTML = Object.entries(t('patterns')).map(([k, v]) => `<label><input type="checkbox" value="${k}" ${use.has(k) ? 'checked' : ''}> ${v}</label>`).join('');
    $$('#pat-boxes input').forEach(i => i.disabled = S.engine !== 'ready');
  }
  function setControls() {
    const ready = S.engine === 'ready';
    ['#new-world', '#sl-frauds', '#sl-kmin', '#sl-kmax', '#sel-window', '#sl-spread', '#sl-cex', '#sl-sigma', '#sl-kappa', '#sl-pi', '#cb-fan', '#sl-fank', '#sl-fandt', '#sl-fanr', '#reset']
      .forEach(q => { $(q).disabled = !ready || S.busy; });
    $$('#pat-boxes input').forEach(i => i.disabled = !ready || S.busy);
    $('#lab-spread').style.opacity = $('#sel-window').value === 'random' ? 0.45 : 1;
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
    $('#v-window').textContent = '';
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
    const fr = S.world.frauds.filter(f => ['T4', 'T5', 'T3'].includes(f.pattern)).sort((a, b) => b.accounts - a.accounts);
    return (fr[0] || S.world.frauds[0]).id;
  }
  function fraudHead() {
    const f = S.world.frauds.find(x => x.id === S.fraud); if (!f) return '';
    const seed = S.graph.nodes.find(n => n.id === 'seed');
    return `${t('fraud_pick')} #${f.id} · ${t('patterns')[f.pattern] || f.pattern} · ${eur(f.F)} · ` +
      (S.lang === 'fr' ? `${f.involved} impliqués parmi ${f.accounts} comptes ayant reçu ≥ 100 €` : `${f.involved} involved among ${f.accounts} accounts that received ≥ €100`) +
      (seed ? ` · ${S.lang === 'fr' ? 'blacklistée au jour' : 'blacklisted on day'} ${Math.round(seed.blacklisted_h / 24)}` : '') +
      (f.collector ? ` · ${t('legend_coll')}` : '');
  }
  function renderSim() {
    if (!S.res || !S.graph) return;
    $$('#presets button').forEach(b => b.classList.toggle('on', b.dataset.preset === S.preset));
    $$('#vis button').forEach(b => b.classList.toggle('on', b.dataset.vis === S.vis));
    $$('#colorby button').forEach(b => b.classList.toggle('on', b.dataset.c === S.colorBy));
    const sel = $('#sel-fraud');
    sel.innerHTML = S.world.frauds.map(f => `<option value="${f.id}" ${f.id === S.fraud ? 'selected' : ''}>#${f.id} · ${f.pattern} · ${eur(f.F)} · ${f.accounts}</option>`).join('');
    $('#fraud-head').textContent = fraudHead();
    const o = { colorBy: S.colorBy, mistakes: S.mistakes, preset: S.preset, t, lang: S.lang, selected: S.selected, onSelect: (n) => { S.selected = n.id; renderSim(); } };
    NET.draw($('#net'), S.graph, o); NET.legend($('#legend'), o, S.graph);
    renderCard(); renderMetrics();
    const w = S.world;
    $('#world-info').textContent = t('world_info', { seed: w.seed, frauds: w.frauds.length, accounts: num(w.n_accounts), rows: num(w.n_rows) });
    setControls();
  }
  function renderCard() {
    const box = $('#card');
    const n = S.graph.nodes.find(x => x.id === S.selected);
    if (!n) { box.innerHTML = `<h3>${t('card_h')}</h3><p class="note">${t('card_empty')}</p>`; return; }
    const r = n.reasons, rule = S.res.rule;
    const inv = NET.INVOLVED.has(n.role);
    const li = (ok, txt) => `<li class="${ok ? 'y' : 'n'}">${ok ? '✓' : '✗'} ${txt}</li>`;
    const g1 = li(r.amount_ok, t('r_amount')) + li(r.share_g1 || r.big_amount || r.common_destination,
      [t('r_share1', { v: pct(rule.g1_share, 0) }), t('r_big'), t('r_conv')].join(S.lang === 'fr' ? ' ou ' : ' or '));
    const g2 = li(r.share_g2 || r.big_amount || r.common_destination, t('r_share2', { v: pct(rule.g2_share, 0) }) + (S.lang === 'fr' ? ' (ou montant / destination)' : ' (or amount / destination)')) +
      li(r.concentration_ok || r.pass_through_ok, t('r_kappa', { v: pct(rule.concentration, 0) }) + (S.lang === 'fr' ? ' ou ' : ' or ') + t('r_pi', { v: pct(rule.pass_through, 0) })) +
      (rule.fan_k > 0 ? li(r.fan_route, t('r_fan', { n: r.fan_siblings, h: rule.fan_window_h, k: rule.fan_k })) : '') +
      li(!r.victim, t('r_victim'));
    const g3 = li(r.same_person_other_exchange, t('r_same')) + li(r.second_seed, t('r_second')) + li(r.common_destination && (r.share_g1 || r.big_amount), t('r_conv'));
    box.innerHTML = `<h3>${t('card_h')} ${n.aid} · ${t('exch')} ${n.exchange}</h3>
      <table>
        <tr><td>${t('card_role')}</td><td style="color:${inv ? '#b03a2e' : '#5b6475'}">${t('roles')[n.role] || n.role} (${inv ? t('involved') : t('innocent')})</td></tr>
        <tr><td>${t('card_grade')}</td><td><span class="chip c${n.grade}">G${n.grade}</span></td></tr>
        <tr><td>${t('card_10k')}</td><td>${n.ten_k ? t('yes') : t('no')}</td></tr>
        <tr><td>${t('card_x')}</td><td>${eur(n.X)}</td></tr>
        <tr><td>${t('card_share')}</td><td>${pct(n.share)}</td></tr>
        <tr><td>${t('card_kappa')}</td><td>${pct(n.concentration, 0)}</td></tr>
        <tr><td>${t('card_pi')}</td><td>${pct(n.pass_24h, 0)}</td></tr>
        <tr><td>${t('card_pi7')}</td><td>${pct(n.pass_7d, 0)}</td></tr>
        <tr><td>${t('card_age')}</td><td>${num(n.age_days)} ${t('days')}</td></tr>
        <tr><td>${t('card_tx')}</td><td>${n.n_tx}</td></tr>
      </table>
      <h3>${t('card_why')}</h3>
      <b>G1</b><ul class="why">${g1}</ul><b>G2</b><ul class="why">${g2}</ul><b>G3</b><ul class="why">${g3}</ul>`;
  }
  function renderMetrics() {
    const r = S.res, sel = r.selected, ten = r.ten_k;
    const key = S.preset === '10k' ? 'ten_k' : `${S.preset}_${S.vis}`;
    const ref = !Object.keys(S.overrides).length && S.thesis.main_E[key];
    const refTxt = (k) => ref ? `<div class="ref">${t('met_thesis')}: ${pct(ref[k])}</div>` : '';
    $('#metrics').innerHTML = [
      [t('met_found'), pct(sel.recall), `${sel.found} / ${sel.involved}`, refTxt('recall')],
      [t('met_prec'), pct(sel.precision), `${sel.false_alerts} ${t('met_fa').toLowerCase()}`, refTxt('precision')],
      [t('met_value'), pct(sel.value_recall), '', refTxt('value_recall')],
      [t('met_frauds'), pct(r.frauds_with_one_found), '', ''],
      [t('met_g3'), S.preset === '10k' ? '–' : pct(r.g3.precision), S.preset === '10k' ? '' : `${r.g3.found + r.g3.false_alerts} G3`, ''],
      [t('met_vs10k'), pct(ten.recall), `${t('met_prec')} ${pct(ten.precision)}`, ''],
    ].map(([l, v, s, ref]) => `<div class="m"><div class="l">${l}</div><div class="v">${v}</div><div class="ref">${s}</div>${ref}</div>`).join('');
    const pos = ['SELF', 'MULE', 'FACILITATOR', 'ACCOMPLICE'], neg = ['P2P', 'VICTIM', 'FRAMED', 'LANDLORD', 'SERVICE', 'BAIT'];
    const row = (rk, cls) => { const b = r.by_role[rk]; if (!b) return '';
      return `<div>${t('roles')[rk]} <span class="note">(${b.flagged}/${b.n})</span><div class="bar ${cls}"><i style="width:${100 * (b.rate || 0)}%"></i></div></div>`; };
    $('#roles').innerHTML = `<div style="grid-column:1/-1"><b>${t('role_h')}</b></div>` + pos.map(x => row(x, '')).join('') + neg.map(x => row(x, 'neg')).join('');
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
  function readWorldControls() {
    const p = { n_seeds: +$('#sl-frauds').value, k_min: +$('#sl-kmin').value, k_max: +$('#sl-kmax').value, cex_share: +$('#sl-cex').value,
      typologies: $$('#pat-boxes input:checked').map(i => i.value) };
    if (!p.typologies.length) p.typologies = ['T4'];
    const w = $('#sel-window').value;
    if (w !== 'random') { p.mule_window_h = +w; p.split_spread = +$('#sl-spread').value; }
    return p;
  }

  /* ---------------------------------------------------------------- results (charts) */
  const C = { a: '#9DB9D3', b: '#1F5F99', c: '#E59866', d: '#7d8a99' };
  function chart(id, cfg) { if (S.charts[id]) S.charts[id].destroy(); S.charts[id] = new Chart(document.getElementById(id), cfg); }
  const pctAxis = { min: 0, max: 100, ticks: { callback: v => v + ' %' } };
  function renderResults() {
    if (!S.thesis || typeof Chart === 'undefined') return;
    const m = S.thesis.main_E;
    const L = { ten_k: t('preset_10k'), rev2_V1: `${t('preset_rev2')} · ${t('vis_v1')}`, rev2_V3: `${t('preset_rev2')} · ${t('vis_v3')}`,
      rev3_V1: `${t('preset_rev3')} · ${t('vis_v1')}`, rev3_V3: `${t('preset_rev3')} · ${t('vis_v3')}` };
    const ks = Object.keys(L);
    chart('ch-main', { type: 'bar', data: { labels: ks.map(k => L[k]), datasets: [
      { label: t('col_rec'), data: ks.map(k => 100 * m[k].recall), backgroundColor: C.b },
      { label: t('col_prec'), data: ks.map(k => 100 * m[k].precision), backgroundColor: C.a }] },
      options: { scales: { y: pctAxis }, plugins: { tooltip: { callbacks: { label: c => `${c.dataset.label}: ${c.raw.toFixed(1)} %` } } } } });
    const br = S.thesis.by_role_E;
    const rl = [['own account (SELF)', t('roles').SELF], ['mule', t('roles').MULE], ['mule, without T7', t('roles').MULE + ' (≠T7)'], ['facilitator', t('roles').FACILITATOR], ['all involved', S.lang === 'fr' ? 'Tous impliqués' : 'All involved']];
    chart('ch-role', { type: 'bar', data: { labels: rl.map(x => x[1]), datasets: [
      { label: t('preset_10k'), data: rl.map(x => 100 * br[x[0]].ten_k), backgroundColor: C.c },
      { label: t('preset_rev2'), data: rl.map(x => 100 * br[x[0]].rev2), backgroundColor: C.a },
      { label: t('preset_rev3'), data: rl.map(x => 100 * br[x[0]].rev3), backgroundColor: C.b }] }, options: { scales: { y: pctAxis } } });
    const bp = S.thesis.by_pattern_E, pk = Object.keys(bp);
    chart('ch-pattern', { type: 'bar', data: { labels: pk.map(k => t('patterns')[k] || k), datasets: [
      { label: t('preset_10k'), data: pk.map(k => 100 * bp[k].ten_k), backgroundColor: C.c },
      { label: t('preset_rev2'), data: pk.map(k => 100 * bp[k].rev2), backgroundColor: C.a },
      { label: t('preset_rev3'), data: pk.map(k => 100 * bp[k].rev3), backgroundColor: C.b }] }, options: { indexAxis: 'y', scales: { x: pctAxis } } });
    const sp = S.thesis.sweep_speed, wins = [...new Set(sp.map(x => x.window_h))].sort((a, b) => a - b);
    const ser = (det, k) => wins.map(w => 100 * sp.find(x => x.window_h === w && x.detector === det)[k]);
    const wl = wins.map(w => w < 24 ? w + ' h' : w === 24 ? '24 h' : w === 72 ? '72 h' : (S.lang === 'fr' ? '7 jours' : '7 days'));
    chart('ch-speed', { type: 'line', data: { labels: wl, datasets: [
      { label: `${t('col_rec')} · ${t('preset_rev3')}`, data: ser('Rev3 V3 G2+', 'recall'), borderColor: C.b, backgroundColor: C.b },
      { label: `${t('col_rec')} · ${t('preset_rev2')}`, data: ser('Rev2 frozen V3 G2+', 'recall'), borderColor: C.a, backgroundColor: C.a },
      { label: `${t('col_prec')} · ${t('preset_rev3')}`, data: ser('Rev3 V3 G2+', 'precision'), borderColor: C.b, borderDash: [6, 4], backgroundColor: C.b },
      { label: `${t('col_prec')} · ${t('preset_rev2')}`, data: ser('Rev2 frozen V3 G2+', 'precision'), borderColor: C.a, borderDash: [6, 4], backgroundColor: C.a }] },
      options: { scales: { y: pctAxis } } });
    const sk = S.thesis.sweep_k, kk = [...new Set(sk.map(x => x.k))];
    const kser = (det, k) => kk.map(v => 100 * sk.find(x => x.k === v && x.detector === det)[k]);
    chart('ch-k', { type: 'line', data: { labels: kk.map(v => v + (S.lang === 'fr' ? ' mules' : ' mules')), datasets: [
      { label: `${t('col_rec')} · ${t('preset_rev3')}`, data: kser('Rev3 V3 G2+', 'recall'), borderColor: C.b, backgroundColor: C.b },
      { label: `${t('col_rec')} · ${t('preset_rev2')}`, data: kser('Rev2 frozen V3 G2+', 'recall'), borderColor: C.a, backgroundColor: C.a },
      { label: `${t('col_prec')} · ${t('preset_rev3')}`, data: kser('Rev3 V3 G2+', 'precision'), borderColor: C.b, borderDash: [6, 4], backgroundColor: C.b },
      { label: `${t('col_prec')} · ${t('preset_rev2')}`, data: kser('Rev2 frozen V3 G2+', 'precision'), borderColor: C.a, borderDash: [6, 4], backgroundColor: C.a }] },
      options: { scales: { y: pctAxis } } });
    const rows = ks.concat(['rev2_V3_G3', 'rev3_V3_G3']);
    const lab = (k) => L[k] || (k.startsWith('rev2') ? `${t('preset_rev2')} · G3` : `${t('preset_rev3')} · G3`);
    $('#res-table').innerHTML = `<table class="t"><tr><th>${t('col_rule')}</th><th>${t('col_prec')}</th><th>${t('col_rec')}</th><th>${t('col_val')}</th><th>${t('col_fa')}</th></tr>` +
      rows.map(k => `<tr><td>${lab(k)}</td><td>${pct(m[k].precision)} <span class="note">[${(100 * m[k].prec_lo).toFixed(0)}–${(100 * m[k].prec_hi).toFixed(0)}]</span></td><td>${pct(m[k].recall)} <span class="note">[${(100 * m[k].rec_lo).toFixed(0)}–${(100 * m[k].rec_hi).toFixed(0)}]</span></td><td>${pct(m[k].value_recall)}</td><td>${(m[k].fp_per_fraud).toFixed(2)}</td></tr>`).join('') + '</table>';
  }

  /* ---------------------------------------------------------------- real data */
  function renderReal() {
    if (!S.thesis || typeof Chart === 'undefined') return;
    const r = S.thesis.real;
    $('#real-kpis').innerHTML = [
      [num(r.phishing_active), t('real_seeds')], [meur(r.total_out_eur), t('real_sent')],
      [num(r.deposit_addresses), t('real_deposits')], [pct(r.fraud_eur_to_deposits / r.total_out_eur), t('real_reach')]]
      .map(([v, l]) => `<div class="kpi"><div class="v">${v}</div><div class="l">${l}</div></div>`).join('');
    const fk = Object.keys(r.flows_share).sort((a, b) => r.flows_share[b] - r.flows_share[a]);
    chart('ch-flow', { type: 'bar', data: { labels: fk.map(k => t('flows')[k] || k), datasets: [{ label: '%', data: fk.map(k => 100 * r.flows_share[k]), backgroundColor: C.b }] },
      options: { indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: pctAxis } } });
    $('#real-roles').innerHTML = `<table class="t"><tr><th></th><th>${t('col_n')}</th><th>${t('col_eur')}</th></tr>` +
      Object.entries(r.hop1_roles).map(([k, v]) => `<tr><td>${t('hop')[k]}</td><td>${num(v.n)}</td><td>${meur(v.eur)}</td></tr>`).join('') + '</table>';
    const ek = Object.keys(r.by_exchange);
    chart('ch-ex', { type: 'bar', data: { labels: ek, datasets: [{ label: t('col_accounts'), data: ek.map(k => r.by_exchange[k]), backgroundColor: C.a }] }, options: { plugins: { legend: { display: false } } } });
    $('#real-grades').innerHTML = `<table class="t"><tr><th></th><th>${t('col_accounts')}</th><th>${t('col_med')}</th><th>${t('col_tot')}</th><th>${t('col_kappa')}</th></tr>` +
      Object.entries(r.grades).map(([g, v]) => `<tr><td><span class="chip c${g[1]}">${g}</span></td><td>${v.n}</td><td>${eur(v.X_median)}</td><td>${meur(v.X_total)}</td><td>${pct(v.kappa_median, 0)}</td></tr>`).join('') +
      `<tr><td>${t('preset_10k')}</td><td>${r.rule10k}</td><td colspan="3" class="note">${S.lang === 'fr'
        ? `${r.overlap.both} en commun avec G2/G3 ; ${r.overlap.grades_only} G2/G3 sous 10 k€ ; ${r.overlap.ten_k_only} ≥ 10 k€ mais pas G2`
        : `${r.overlap.both} shared with G2/G3; ${r.overlap.grades_only} G2/G3 below €10k; ${r.overlap.ten_k_only} ≥ €10k but not G2`}</td></tr></table>`;
    const cg = ['grade 0', 'G1', 'G2', 'G3', '10k rule'];
    chart('ch-check', { type: 'bar', data: { labels: cg.map(g => `${t('check_groups')[g]} (${r.check_90d[g].accounts})`), datasets: [
      { label: t('col_either'), data: cg.map(g => 100 * r.check_90d[g].either), backgroundColor: cg.map(g => g === 'G3' ? '#c0392b' : g === '10k rule' ? C.c : C.b) }] },
      options: { plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => { const g = r.check_90d[cg[c.dataIndex]];
        return `${c.raw.toFixed(1)} % [${(100 * g.lo).toFixed(0)}–${(100 * g.hi).toFixed(0)} %] · ${t('col_same')} ${(100 * g.same).toFixed(1)} % · ${t('col_new')} ${(100 * g.new).toFixed(1)} %`; } } } }, scales: { y: { min: 0, max: 80, ticks: { callback: v => v + ' %' } } } } });
    const f = r.fanout;
    $('#real-fan').textContent = t('real_fan_p', { gap: num(f.median_gap_h), ratio: f.median_ratio.toFixed(1), fires: f.seeds_route_fires, multi: f.seeds_multi });
    $('#real-g3').innerHTML = `<table class="t"><tr><th>${t('col_addr')}</th><th>${t('col_ex')}</th><th>${t('col_x')}</th><th>${t('col_seeds')}</th><th>${t('col_kappa1')}</th></tr>` +
      r.g3_examples.map(g => `<tr><td><a href="https://etherscan.io/address/${g.address}" target="_blank" rel="noopener">${g.address.slice(0, 10)}…${g.address.slice(-6)}</a></td><td>${g.exchange}</td><td>${eur(g.X)}</td><td>${g.seeds}</td><td>${pct(g.kappa, 0)}</td></tr>`).join('') + '</table>';
    $('#real-limits').innerHTML = t('real_limits').map(x => `<li>${x}</li>`).join('');
  }

  /* ---------------------------------------------------------------- data explained, sources */
  function renderData() {
    $('#cols').innerHTML = `<table class="t"><tr><th>${t('data_col')}</th><th>${t('data_mean')}</th><th>${t('data_src')}</th></tr>` +
      t('cols').map(([c, m, s]) => `<tr><td><b>${c}</b></td><td style="text-align:left">${m}</td><td>${s}</td></tr>`).join('') + '</table>';
    const rows = S.rows || (S.def && S.def.rows) || [];
    $('#rows').innerHTML = `<table class="t"><tr><th>${t('fraud_pick')}</th><th>${t('card_h')}</th><th>${t('exch')}</th><th>X</th><th>${S.lang === 'fr' ? 'part' : 'share'}</th><th>concentration</th><th>${S.lang === 'fr' ? 'renvoi 24 h' : 'pass-through 24 h'}</th><th>${S.lang === 'fr' ? 'victime' : 'victim'}</th><th>${S.lang === 'fr' ? 'âge' : 'age'}</th><th>${S.lang === 'fr' ? 'deuxième seed' : 'second seed'}</th><th>grade</th><th>${S.lang === 'fr' ? 'rôle' : 'role'}</th></tr>` +
      rows.map(r => `<tr><td>#${r.fraud}</td><td>${r.account}</td><td>${r.exchange}</td><td>${eur(r.X)}</td><td>${pct(r.share)}</td><td>${pct(r.concentration, 0)}</td><td>${pct(r.pass_24h, 0)}</td><td>${r.victim ? t('yes') : t('no')}</td><td>${num(r.age_days)}</td><td>${r.second_seed}</td><td>${r.grade === null ? '–' : 'G' + r.grade}</td><td>${t('roles')[r.role] || r.role}</td></tr>`).join('') + '</table>';
    $('#pat-list').innerHTML = Object.values(t('patterns')).map(x => `<li>${x}</li>`).join('');
    $('#role-list').innerHTML = Object.entries(t('roles')).map(([k, v]) => `<li><span style="color:${NET.ROLE_COLORS[k]}">●</span> ${v} — <span class="note">${NET.INVOLVED.has(k) ? t('involved') : k === 'ACCOMPLICE' ? (S.lang === 'fr' ? 'cible secondaire' : 'secondary target') : t('innocent')}</span></li>`).join('');
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
  function renderSources() { $('#src-list').innerHTML = SOURCES.map(([n, u]) => `<li><a href="${u}" target="_blank" rel="noopener">${n}</a></li>`).join(''); }

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
    $('#play').addEventListener('click', () => NET.play());
    let timer = null;
    const slid = () => {
      sliderLabels();
      if (S.preset === '10k') S.preset = 'rev2';
      S.overrides = { sigma: +$('#sl-sigma').value, kappa: +$('#sl-kappa').value, pi: +$('#sl-pi').value,
        fan_k: $('#cb-fan').checked ? +$('#sl-fank').value : 0, fan_dt: +$('#sl-fandt').value, fan_ratio: +$('#sl-fanr').value };
      clearTimeout(timer); timer = setTimeout(() => regrade(), 250);
    };
    ['#sl-sigma', '#sl-kappa', '#sl-pi', '#sl-fank', '#sl-fandt', '#sl-fanr'].forEach(q => $(q).addEventListener('input', slid));
    $('#cb-fan').addEventListener('change', slid);
    $('#reset').addEventListener('click', () => { S.overrides = {}; regrade(); });
    ['#sl-frauds', '#sl-kmin', '#sl-kmax', '#sl-spread', '#sl-cex'].forEach(q => $(q).addEventListener('input', () => {
      if (+$('#sl-kmin').value > +$('#sl-kmax').value) $('#sl-kmax').value = $('#sl-kmin').value; sliderLabels(); }));
    $('#sel-window').addEventListener('change', setControls);
    $('#new-world').addEventListener('click', () => newWorld().catch(e => { $('#world-info').textContent = String(e); }));
  }

  async function init() {
    let saved = null; try { saved = localStorage.getItem('f1-lang'); } catch (e) {}
    S.lang = saved || ((navigator.language || '').toLowerCase().startsWith('fr') ? 'fr' : 'en');
    wire(); route();
    const [th, def] = await Promise.all([fetch('data/thesis.json').then(r => r.json()), fetch('data/world_default.json').then(r => r.json())]);
    S.thesis = th; S.def = def; S.world = def.world; S.world.params = {};
    applyLang();
    await regrade(false);
    startEngine();
  }
  // used by the Claude box
  const api = {
    state: () => S, t, newWorld, call,
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
