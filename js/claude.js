/* "Ask Claude" box: the visitor's own Anthropic API key, kept in this browser only.
   Claude can drive the simulator through the tools below (same functions as the buttons). */
(() => {
  const $ = (q) => document.querySelector(q);
  const MODEL = 'claude-sonnet-5-5';
  const history = [];
  let key = '';
  try { key = localStorage.getItem('f1-anthropic-key') || ''; } catch (e) {}

  const TOOLS = [
    { name: 'create_world', description: 'Generate a new simulated world with our thesis simulator (Python, running in the page) and grade it with the current rule. Every setting is optional; omitted settings keep the values of our test worlds.',
      input_schema: { type: 'object', properties: {
        n_frauds: { type: 'integer', minimum: 5, maximum: 100, description: 'number of frauds (default 40)' },
        mules_min: { type: 'integer', minimum: 1, maximum: 10 }, mules_max: { type: 'integer', minimum: 1, maximum: 10 },
        payment_window_hours: { type: 'number', minimum: 0.5, maximum: 168, description: 'time over which each fraud pays its mules; omit to draw it per fraud (1 h to 7 days) as in our tests' },
        amount_spread: { type: 'number', minimum: 0, maximum: 0.8, description: 'how different the amounts paid to each mule are (0 = equal); only used with payment_window_hours' },
        share_reaching_exchanges: { type: 'number', minimum: 0.05, maximum: 1 },
        patterns: { type: 'array', items: { type: 'string', enum: ['T1', 'T2', 'T3', 'T4', 'T5', 'T7', 'T8', 'T9'] } },
        seed: { type: 'integer', description: 'random seed, to reproduce a world' } } } },
    { name: 'set_rule', description: 'Choose the detection rule and visibility, optionally with custom thresholds, and grade the current world. Returns precision, recall and results by role.',
      input_schema: { type: 'object', properties: {
        preset: { type: 'string', enum: ['10k', 'rev5', 'rev3'], description: 'rev5 = our lead rule, shown to visitors as "Revision 2" (G2 share 20 %); rev3 = Revision 3, adds a fan-out route (finds more, less precise)' }, visibility: { type: 'string', enum: ['V1', 'V3'], description: 'V1 = one exchange alone, V3 = with our sharing protocol' },
        g2_share: { type: 'number' }, concentration: { type: 'number' }, pass_through_24h: { type: 'number' },
        fan_out_accounts: { type: 'integer', description: '0 switches the fan-out route off' }, fan_out_window_hours: { type: 'number' }, fan_out_ratio: { type: 'number' } } } },
    { name: 'show_fraud', description: 'Display one fraud of the current world in the network view and return its accounts (role, grade, amounts, reasons).',
      input_schema: { type: 'object', properties: { fraud_id: { type: 'integer' } }, required: ['fraud_id'] } },
    { name: 'thesis_results', description: 'Our measured thesis results (20 test worlds, real Ethereum data), to compare with the current world.',
      input_schema: { type: 'object', properties: {} } },
  ];

  function compact(res) {
    if (!res) return null;
    return { rule: res.rule, visibility: res.vis, preset: res.preset, selected: res.selected, g3: res.g3, ten_k_rule: res.ten_k,
      counts: res.counts, by_role: res.by_role, by_pattern: res.by_pattern, frauds_with_one_found: res.frauds_with_one_found };
  }
  async function runTool(name, input) {
    const S = APP.state();
    if (name === 'create_world') {
      APP.ensureEngine();
      for (let i = 0; i < 240 && APP.state().engine === 'loading'; i++) await new Promise(r => setTimeout(r, 500));
      if (APP.state().engine !== 'ready') return { error: 'Python is not ready in this browser; new worlds are not available.' };
      const p = {};
      if (input.n_frauds) p.n_seeds = input.n_frauds;
      if (input.mules_min) p.k_min = input.mules_min; if (input.mules_max) p.k_max = input.mules_max;
      if (input.payment_window_hours) { p.mule_window_h = input.payment_window_hours; p.split_spread = input.amount_spread ?? 0.2; }
      if (input.share_reaching_exchanges) p.cex_share = input.share_reaching_exchanges;
      if (input.patterns && input.patterns.length) p.typologies = input.patterns;
      if (input.seed !== undefined) p.seed = input.seed;
      const w = await APP.newWorld(p);
      location.hash = '#simulator';
      return { world: { seed: w.seed, frauds: w.frauds.length, accounts: w.n_accounts, receiving_accounts: w.n_rows, roles: w.roles, settings: w.settings,
        frauds_list: w.frauds.slice(0, 60) }, grading: compact(APP.state().res) };
    }
    if (name === 'set_rule') {
      const ov = {};
      if (input.g2_share !== undefined) ov.sigma = input.g2_share;
      if (input.concentration !== undefined) ov.kappa = input.concentration;
      if (input.pass_through_24h !== undefined) ov.pi = input.pass_through_24h;
      if (input.fan_out_accounts !== undefined) ov.fan_k = input.fan_out_accounts;
      if (input.fan_out_window_hours !== undefined) ov.fan_dt = input.fan_out_window_hours;
      if (input.fan_out_ratio !== undefined) ov.fan_ratio = input.fan_out_ratio;
      if (Object.keys(ov).length && S.engine !== 'ready') return { error: 'Custom thresholds need Python, which is not ready; only the tuned presets are available.' };
      const res = await APP.setRule({ preset: input.preset, visibility: input.visibility, overrides: ov });
      location.hash = '#simulator';
      return compact(res);
    }
    if (name === 'show_fraud') {
      const g = await APP.showFraud(input.fraud_id);
      return { fraud: g.fraud, nodes: g.nodes.map(n => n.kind === 'account'
        ? { account: n.aid, exchange: n.exchange, role: n.role, grade: n.grade, ten_k_rule: n.ten_k, received_eur: n.X, share: n.share,
            concentration: n.concentration, passed_on_24h: n.pass_24h, reasons: n.reasons } : n) };
    }
    if (name === 'thesis_results') { const th = S.thesis; return { simulation_test_worlds: th.main_E, by_role: th.by_role_E, by_pattern: th.by_pattern_E, speed_sweep: th.sweep_speed, mules_sweep: th.sweep_k, real_ethereum: th.real }; }
    return { error: 'unknown tool' };
  }

  function system() {
    const S = APP.state();
    return `You are the assistant of the "Fraudster +1" website, a research simulator about finding the accounts involved in a crypto fraud.
Answer in ${S.lang === 'fr' ? 'French' : 'English'}, briefly and plainly, for a general audience. Use the tools to create worlds, change the rule, or show a fraud; never invent numbers.
Method: a blacklisted fraud address (seed) sends money, possibly through a collector wallet, to customer accounts at exchanges. Each receiving account gets a grade.
G1: received >= EUR 100 and a share of the fraud >= 1 % (or >= EUR 10,000, or a common destination). G2: G1, not a victim, and a large enough share (or amount), and relay behaviour (fraud money >= a set share of the account's money over +-15 days, or passed on within 24 h); our lead rule is called revision 2 on the site (preset id rev5); revision 3 adds a fan-out route: several accounts of the same fraud paid similar amounts at about the same time. G3: G2 plus independent evidence (same person at another exchange, or a second fraud paying the account).
V1 = one exchange alone; V3 = exchanges sharing evidence through our privacy-preserving protocol. The EUR 10k rule flags accounts that received >= EUR 10,000 (or the whole fraud if smaller).
Roles in the simulation (truth): involved = fraudster's own account (SELF), mule, professional launderer (FACILITATOR); innocent = shops, peer-to-peer sellers, victims receiving refunds, dust, framed customers, bait, landlords; paid accomplices are a secondary target.
Recall = share of involved accounts found; precision = share of alerts (G2 or more) that are involved. One world has about 40 frauds, so its numbers vary; our thesis numbers come from 20 test worlds (use thesis_results).
Current state: world seed ${S.world.seed}, ${S.world.frauds.length} frauds; rule ${S.preset} ${S.vis}${Object.keys(S.overrides).length ? ' with custom thresholds' : ''}; showing fraud #${S.fraud}. Python engine: ${S.engine}.`;
  }

  function log(cls, text) { const d = document.createElement('div'); d.className = 'msg ' + cls; d.textContent = text; $('#ask-log').appendChild(d); $('#ask-log').scrollTop = 1e9; return d; }

  async function ask(question) {
    const T = APP.t;
    if (!key) { log('t', T('ask_need_key')); return; }
    history.push({ role: 'user', content: question });
    log('u', question);
    const thinking = log('t', T('ask_thinking'));
    try {
      for (let step = 0; step < 8; step++) {
        const r = await fetch('https://api.anthropic.com/v1/messages', {
          method: 'POST',
          headers: { 'content-type': 'application/json', 'x-api-key': key, 'anthropic-version': '2023-06-01', 'anthropic-dangerous-direct-browser-access': 'true' },
          body: JSON.stringify({ model: MODEL, max_tokens: 1500, system: system(), tools: TOOLS, messages: history }) });
        const data = await r.json();
        if (!r.ok) throw new Error((data.error && data.error.message) || r.statusText);
        history.push({ role: 'assistant', content: data.content });
        const text = data.content.filter(c => c.type === 'text').map(c => c.text).join('\n').trim();
        if (text) log('a', text);
        const uses = data.content.filter(c => c.type === 'tool_use');
        if (!uses.length || data.stop_reason !== 'tool_use') break;
        const results = [];
        for (const u of uses) {
          log('t', T('ask_tool', { t: u.name }));
          let out; try { out = await runTool(u.name, u.input || {}); } catch (e) { out = { error: String(e.message || e) }; }
          results.push({ type: 'tool_result', tool_use_id: u.id, content: JSON.stringify(out).slice(0, 60000) });
        }
        history.push({ role: 'user', content: results });
      }
    } catch (e) {
      log('t', 'Error: ' + (e.message || e));
      history.pop();
    } finally { thinking.remove(); }
  }

  document.addEventListener('DOMContentLoaded', () => {
    $('#ask-key').value = key;
    try { $('#ask-remember').checked = !!localStorage.getItem('f1-anthropic-key'); } catch (e) {}
    const open = () => { $('#ask').hidden = false; $('#ask-open').setAttribute('aria-expanded', 'true'); (key ? $('#ask-in') : $('#ask-key')).focus(); };
    const close = () => { $('#ask').hidden = true; $('#ask-open').setAttribute('aria-expanded', 'false'); $('#ask-open').focus(); };
    $('#ask-open').addEventListener('click', () => { $('#ask').hidden ? open() : close(); });
    $('#ask-close').addEventListener('click', close);
    $('#ask').addEventListener('keydown', e => { if (e.key === 'Escape') { e.preventDefault(); close(); } });
    $('#ask-key').addEventListener('input', e => { key = e.target.value.trim(); if ($('#ask-remember').checked) { try { localStorage.setItem('f1-anthropic-key', key); } catch (x) {} } });
    $('#ask-remember').addEventListener('change', e => { try { e.target.checked ? localStorage.setItem('f1-anthropic-key', key) : localStorage.removeItem('f1-anthropic-key'); } catch (x) {} });
    $('#ask-form').addEventListener('submit', e => { e.preventDefault(); const q = $('#ask-in').value.trim(); if (!q) return;
      if (!key) { log('t', APP.t('ask_need_key')); $('#ask-key').focus(); return; } // keep the question until a key is entered
      $('#ask-in').value = ''; ask(q); });
    $('#ask-in').addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); $('#ask-form').requestSubmit(); } });
  });
})();
