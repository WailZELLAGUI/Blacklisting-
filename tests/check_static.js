/* Static checks of the page, without a browser or the network.
   Run from the repository root:  node tests/check_static.js
   1. the English and French texts have the same keys, the same shape and the same {placeholders};
   2. every text key used in index.html (data-i18n) or in the scripts (t('key')) exists in both languages;
   3. every element id the scripts look up exists in index.html, and no id is used twice;
   4. visitors never see the internal revision names;
   5. every value js/app.js reads in data/thesis.json and data/stress.json exists.
   With --unused it also lists the text keys that nothing refers to (information only). */
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..');
const read = (f) => fs.readFileSync(path.join(ROOT, f), 'utf8');
const html = read('index.html'), i18nSrc = read('js/i18n.js');
const I18N = new Function(i18nSrc + '; return I18N;')();
const scripts = ['app.js', 'claude.js', 'net.js', 'world.js'];
const js = scripts.map(f => read('js/' + f)).join('\n');
const problems = [];
const bad = (m) => problems.push(m);

// 1. same keys and shape in both languages
const en = I18N.en, fr = I18N.fr;
for (const k of Object.keys(en)) if (!(k in fr)) bad(`text "${k}" is in English only`);
for (const k of Object.keys(fr)) if (!(k in en)) bad(`text "${k}" is in French only`);
const holes = (s) => (s.match(/\{\w+\}/g) || []).sort().join(' ');
for (const k of Object.keys(en)) {
  const a = en[k], b = fr[k];
  if (b === undefined) continue;
  if (typeof a !== typeof b || Array.isArray(a) !== Array.isArray(b)) bad(`text "${k}": different types in English and French`);
  else if (Array.isArray(a)) { if (a.length !== b.length) bad(`text "${k}": ${a.length} items in English, ${b.length} in French`); }
  else if (typeof a === 'object') {
    const d = Object.keys(a).filter(x => !(x in b)).concat(Object.keys(b).filter(x => !(x in a)));
    if (d.length) bad(`text "${k}": sub-keys differ (${d.join(', ')})`);
  } else if (holes(a) !== holes(b)) bad(`text "${k}": placeholders differ (${holes(a)} | ${holes(b)})`);
}

// 2. keys in use. Keys built at run time, t('prefix_' + x), are listed here with every value x can take.
const DYNAMIC = {
  preset_: ['10k', 'rev5', 'rev3'],            // t('preset_' + S.preset), t('preset_' + k.slice(0, 4))
  bl_: ['old', 'alert', 'freeze'],             // t('bl_' + settings.blacklist)
  eval_: ['1', '7', '30', '90', 'end'],        // t('eval_' + settings.eval_days)
  hold_c_: ['reference', 'sample_fixed', 'sample_prop'],   // t('hold_c_' + id), Table 5 of the Results page
};
const used = new Set();
for (const m of html.matchAll(/data-i18n="([^"]+)"/g)) used.add(m[1]);
for (const m of js.matchAll(/\b[tT]\(\s*'([A-Za-z0-9_]+)'\s*[,)]/g)) used.add(m[1]);
for (const m of js.matchAll(/\b[tT]\(\s*'([A-Za-z0-9_]+)'\s*\+/g)) {
  if (!DYNAMIC[m[1]]) bad(`t('${m[1]}' + …) builds a key at run time: list its values in DYNAMIC (tests/check_static.js)`);
}
for (const p in DYNAMIC) for (const v of DYNAMIC[p]) used.add(p + v);
for (const k of used) {
  if (!(k in en)) bad(`text "${k}" is used but missing in English`);
  if (!(k in fr)) bad(`text "${k}" is used but missing in French`);
}

// 3. element ids
const idList = [...html.matchAll(/\bid="([^"]+)"/g)].map(m => m[1]);
const ids = new Set(idList);
for (const d of new Set(idList.filter((x, i) => idList.indexOf(x) !== i))) bad(`id "${d}" appears twice in index.html`);
const CREATED = new Set(['key3', 'key3-note']);            // elements the scripts create themselves before using them
const wanted = new Set();
for (const m of js.matchAll(/\$\$?\(\s*[`']#([A-Za-z][\w-]*)/g)) wanted.add(m[1]);
for (const m of js.matchAll(/getElementById\(\s*'([^']+)'\s*\)/g)) wanted.add(m[1]);
for (const m of js.matchAll(/'#([A-Za-z][\w-]*)'/g)) if (!/^([0-9a-f]{3}|[0-9a-f]{6}|[0-9a-f]{8})$/i.test(m[1])) wanted.add(m[1]);                     // lists such as ['#sl-sigma', …]
for (const m of js.matchAll(/\bchart\(\s*'([^']+)'/g)) wanted.add(m[1]);
for (const m of js.matchAll(/'(cap-[a-z]+)'\s*:/g)) wanted.add(m[1]);
for (const id of wanted) if (!ids.has(id) && !CREATED.has(id)) bad(`the scripts look for #${id}, which is not in index.html`);
for (const m of html.matchAll(/href="#([^"]+)"/g)) if (!ids.has(m[1])) bad(`link to #${m[1]}, which is not in index.html`);

// 4. internal revision names must not reach the visitor (texts and page; code identifiers are fine)
const visible = [];
const walk = (v) => { if (typeof v === 'string') visible.push(v); else if (v && typeof v === 'object') Object.values(v).forEach(walk); };
walk(en); walk(fr);
visible.push(html.replace(/<script[\s\S]*?<\/script>/g, '').replace(/\b(data-preset|data-i18n|id|class|href|value)="[^"]*"/g, ''));
for (const s of visible) {
  const m = s.match(/\brev ?[0-9]\b|r[eé]vision\s*[45]\b/i);
  if (m) bad(`internal revision name "${m[0]}" in a visible text: ${s.slice(Math.max(0, m.index - 40), m.index + 40)}`);
}

// 5. every value js/app.js reads in data/thesis.json and data/stress.json exists
const thesis = JSON.parse(read('data/thesis.json')), stress = JSON.parse(read('data/stress.json'));
const app = read('js/app.js');
const at = (root, parts) => parts.reduce((o, k) => (o && typeof o === 'object' && !Array.isArray(o) ? o[k] : undefined), root);
// 5a. chains written in full in the code, such as S.thesis.real.check_90d (they stop at the first list or number)
for (const m of app.matchAll(/\bS\.(thesis|stress)((?:\.[A-Za-z_]\w*)+)/g)) {
  let o = m[1] === 'thesis' ? thesis : stress;
  for (const k of m[2].slice(1).split('.')) {
    if (o === null || typeof o !== 'object' || Array.isArray(o)) break;       // a method (map, find…) or a property of a value
    if (!(k in o)) { bad(`js/app.js reads ${m[0]}, but "${k}" is not in data/${m[1]}.json`); break; }
    o = o[k];
  }
}
// 5b. values read through a short name (m = S.thesis.main_E …): listed by hand, "a|b" = each of them
const need = (name, root, paths) => { for (const p of paths) {
  const expand = (parts) => parts.length ? parts[0].split('|').flatMap(h => expand(parts.slice(1)).map(t => [h, ...t])) : [[]];
  for (const parts of expand(p.split('.'))) if (at(root, parts.map(x => x.replace(/_dot_/g, '.'))) === undefined) bad(`data/${name}.json has no ${parts.join('.').replace(/_dot_/g, '.')} (read by js/app.js)`);
} };
need('thesis', thesis, [
  'main_E.ten_k|rev5_V1|rev5_V3|rev3_V1|rev3_V3|rev5_V3_G3|rev3_V3_G3.precision|recall|value_recall|fp_per_fraud|prec_lo|prec_hi|rec_lo|rec_hi',
  'main_E.ten_k_paper.precision', 'headline.days|accounts_reached', 'zone.size', 'zone.values.sigma|kappa|pi|delta',
  'curve', 'sweep_speed', 'sweep_k', 'by_pattern_E',
  'by_role_E.own account (SELF)|mule|mule, without T7|facilitator|all involved.ten_k|rev5|rev3',
  'real.phishing_active|total_out_eur|deposit_addresses|fraud_eur_to_deposits|flows_share|hop1_roles|by_exchange|grades|rule10k|g3_examples',
  'real.overlap.both|grades_only|ten_k_only', 'real.fanout.median_gap_h|median_ratio|seeds_route_fires|seeds_multi',
  'real.check_90d.grade 0|G1|G2|G3|10k rule.accounts|either|lo|hi|same|new',
  'real.timing.scamsniffer|tether|old_sim.median_delay|buckets', 'real.timing.scamsniffer.seeds|reached', 'real.timing.tether.addresses|gone_before',
  'real.timing.sim_reached.alert|freeze|old',
]);
need('stress', stress, [
  'meta.involved|involved_all', 'base.0_dot_5.g2|g3|g3_no_same|ten_k.precision', 'base.0_dot_5.g3|g3_no_same.found',
  'common_destination.rows|found_total|found_only_by_it', 'innocents.accounts|under_10pct', 'innocents.by_role.LANDLORD|P2P.ge20|ge20_flagged',
  'real.seeds|one_account_ge20|two_exchanges_ge10',
]);
// 5c. the rows the tables and the reading text look up
const row = (list, what, q, fields) => { const r = list.find(x => Object.keys(q).every(k => x[k] === q[k]));
  if (!r) bad(`data/${what}: no row ${JSON.stringify(q)}`); else for (const f of fields) if (typeof r[f] !== 'number') bad(`data/${what}: row ${JSON.stringify(q)} has no ${f}`); };
for (const kind of ['ordinary', 'seller']) {
  for (const p of [0.05, 0.1, 0.3]) for (const s of [0.1, 0.2, 0.3]) row(stress.one_account, 'stress.json one_account', { cex: 0.5, kind, p, s }, ['g2', 'ten_k']);
  for (const p of [0.05, 0.1]) row(stress.two_exchanges, 'stress.json two_exchanges', { cex: 0.5, kind, p, s: 0.2 }, ['g2', 'g3', 'g3_no_same']);
}
row(stress.one_account, 'stress.json one_account', { cex: 0.3, kind: 'seller', p: 0.05, s: 0.2 }, ['g2']);
for (const r of stress.common_destination.rows) for (const f of ['share', 'g2', 'found', 'found_g3']) if (typeof r[f] !== 'number') bad(`data/stress.json common_destination: a row has no ${f}`);
for (const detector of ['Rev5 V3 G2+', 'Rev5 V3 G3', 'B0 10k per exchange']) for (const days of [7, 30, 90, 365]) row(thesis.curve, 'thesis.json curve', { blacklist: 'alert', detector, days }, ['recall', 'precision']);
// the sentence "G2 stays above the EUR 10,000 rule in every scenario tested up to one fraud in ten" must stay true
for (const r of stress.one_account.concat(stress.two_exchanges)) if (r.p <= 0.1 && !(r.g2 > r.ten_k)) bad(`data/stress.json: G2 (${r.g2}) is not above the EUR 10k rule (${r.ten_k}) in ${JSON.stringify(r)}; the reading text of the Results page says it is`);

if (process.argv.includes('--unused')) {
  const unused = Object.keys(en).filter(k => !used.has(k) && !new RegExp(`['"\`.]${k}\\b`).test(js) && !html.includes(k));
  console.log(`texts nothing refers to (${unused.length}):`, unused.join(', ') || 'none');
}
if (problems.length) { console.error(problems.join('\n')); console.error(`\n${problems.length} problem(s)`); process.exit(1); }
console.log(`ok: ${Object.keys(en).length} texts in both languages, ${used.size} keys in use, ${wanted.size} element ids found, data files hold every value the page reads`);
