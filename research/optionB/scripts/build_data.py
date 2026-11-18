"""Build the website's data files from our result files (no number typed by hand)."""
import json, os, shutil, sys
import numpy as np, pandas as pd
ROOT = '/home/claude/fraudster_plus1'
SITE = f'{ROOT}/site'
sys.path.insert(0, ROOT); sys.path.insert(0, f'{ROOT}/realdata/analysis')

def f(x, nd=4):
    try:
        x = float(x)
    except Exception:
        return None
    return None if not np.isfinite(x) else round(x, nd)

out = {}
# ---------- simulation: test worlds E with the collector settings measured on BigQuery (experiments7.py, frozen rules),
#            and worlds D (revision 2 run)
def main_table(path, keep):
    m = pd.read_csv(path).set_index('detector')
    return {v: dict(precision=f(m.loc[k, 'precision']), prec_lo=f(m.loc[k, 'prec_lo']), prec_hi=f(m.loc[k, 'prec_hi']),
                    recall=f(m.loc[k, 'recall']), rec_lo=f(m.loc[k, 'rec_lo']), rec_hi=f(m.loc[k, 'rec_hi']),
                    value_recall=f(m.loc[k, 'value_recall']), fp_per_fraud=f(m.loc[k, 'fp_per_seed'])) for k, v in keep.items()}
# 17 Nov 2026 (option B): the final test of the frozen rule "Revision 2" on new worlds 18000-18019, with the corrected
# generator (budget_cap="all": a fraud never sends more than it stole). Setting 1 (median EUR 30,000) -> results19/,
# setting 4 (amounts of the real phishing sample) -> results19/s4/ (experiments27.py). Earlier numbers are kept under 'history'.
R = f'{ROOT}/results19'
keep = {'B0 10k per exchange': 'ten_k', 'B0 paper': 'ten_k_paper', 'Rev3 V1 G2+': 'rev3_V1', 'Rev3 V3 G2+': 'rev3_V3', 'Rev5 V1 G2+': 'rev5_V1', 'Rev5 V3 G2+': 'rev5_V3',
        'Rev4 V3 G2+': 'rev4_V3', 'Rev3 V3 G3': 'rev3_V3_G3', 'Rev5 V3 G3': 'rev5_V3_G3', 'Rev5 V3 G1+': 'rev5_V3_G1'}
DAYS = {'tau1': 1, 'tau7': 7, 'tau30': 30, 'tau90': 90, 'end': 365}

def block_from(d, worlds_label):
    b = {}
    m = pd.read_csv(f'{d}/site_main.csv').set_index('detector')
    b['main_E'] = main_table(f'{d}/site_main.csv', {k: v for k, v in keep.items() if k in m.index})
    vis = pd.read_csv(f'{d}/visible.csv')
    vis = vis[(vis.blacklist == 'alert') & (vis.date == 'tau90')].involved_reached.iloc[0]
    b['headline'] = dict(blacklist='alert', days=90, accounts_reached=f(vis), worlds=20, frauds=int(20 * 40), test_worlds=worlds_label)
    br = pd.read_csv(f'{d}/site_by_role.csv').set_index('group')
    b['by_role_E'] = {g: dict(n=int(br.loc[g, 'n']), ten_k=f(br.loc[g, 'B0 10k per exchange']),
                              rev3=f(br.loc[g, 'Rev3 V3 G2+']), rev5=f(br.loc[g, 'Rev5 V3 G2+'])) for g in br.index}
    bp = pd.read_csv(f'{d}/site_by_pattern.csv').set_index('typology')
    b['by_pattern_E'] = {t: dict(ten_k=f(bp.loc[t, 'B0 10k per exchange']),
                                 rev3=f(bp.loc[t, 'Rev3 V3 G2+']), rev5=f(bp.loc[t, 'Rev5 V3 G2+'])) for t in bp.index}
    cv = pd.read_csv(f'{d}/site_curve.csv')
    b['curve'] = [dict(blacklist=r.blacklist, days=DAYS[r.date], detector=r.detector, precision=f(r.precision), recall=f(r.recall),
                       fp_per_fraud=f(r.fp_per_seed)) for r in cv.itertuples()]
    return b

def sweeps_from(path):
    sw = pd.read_csv(path)
    s1 = sw[sw.setting == 'split'].groupby(['mule_window_h', 'detector'])[['precision', 'recall']].mean().reset_index()
    s2 = sw[sw.setting != 'split']
    return dict(sweep_speed=[dict(window_h=f(r.mule_window_h, 1), detector=r.detector, precision=f(r.precision), recall=f(r.recall)) for r in s1.itertuples()],
                sweep_k=[dict(k=int(r.k), detector=r.detector, precision=f(r.precision), recall=f(r.recall)) for r in s2.itertuples()])

out.update(block_from(R, '18000-18019'))
out['main_E_sample'] = main_table(f'{R}/s4/site_main.csv', {'B0 10k per exchange': 'ten_k', 'Rev5 V3 G2+': 'rev5_V3', 'Rev5 V3 G3': 'rev5_V3_G3', 'Rev5 V3 G1+': 'rev5_V3_G1'})
out.update(sweeps_from(f'{R}/sweeps.csv'))
# configuration of experiments28.py as run (FP1_STREAMS=paired, FP1_SWEEP_W0=44000): the same 10 worlds for every setting
out['sweep_meta'] = dict(worlds='44000-44009', n=10, paired=True)
out['generator'] = dict(budget_cap='all', test_worlds='18000-18019', since='2026-11-17')
# option B: the twelve preregistered settings, graded 90 days after blacklisting (experiments26.py, results18/)
OB = json.load(open(f'{ROOT}/results18/optionB_test.json'))
ot = pd.read_csv(f'{ROOT}/results18/optionB_test.csv')
ot = ot[ot.when == 'tau+90']
SETTING_KEYS = {1: dict(F='median', cex=0.5), 2: dict(F='median', cex=0.3), 3: dict(F='median', cex=0.86),
                4: dict(F='sample', cex=0.5), 5: dict(F='sample', cex=0.3), 6: dict(F='sample', cex=0.86),
                7: dict(F='sample', cex=0.5, extra='p2p10'), 8: dict(F='sample', cex=0.5, extra='versionB'),
                9: dict(F='sample', cex=0.5, extra='activity05'), 10: dict(F='sample', cex=0.5, extra='activity2'),
                11: dict(F='sample', cex=0.5, extra='transfers30'), 12: dict(F='sample', cex=0.3, extra='hard')}
RULES = {'10k': 'ten_k', 'final G2+': 'G2', 'final G3': 'G3'}
def row(k):
    d = dict(setting=k, n_pos=int(OB['n_pos'][str(k)]), n_frauds=int(OB['n_frauds'][str(k)]), **SETTING_KEYS[k])
    for r, name in RULES.items():
        x = ot[(ot.setting == k) & (ot.rule == r)].iloc[0]
        ci = OB['results'][str(k)]['tau+90'][r]['precision_ci_lo5_hi']
        d[name] = dict(precision=f(x.precision), prec_lo5=f(x.precision_lo5), prec_lo=f(ci[0]), prec_hi=f(ci[2]), precision_c=f(x.precision_complementary),
                       prec_c_lo5=f(x.precision_complementary_lo5), found=f(x.found), fp_per_fraud=f(x.false_alerts_per_fraud),
                       p2p_per_fraud=f(x.p2p_flagged_per_fraud))
    return d
out['option_b'] = dict(rule=OB['final_rule'], how=OB['how'], worlds='18000-18019', calibration_worlds='17000-17019', days=90,
                       settings=[row(k) for k in sorted(SETTING_KEYS)])
# diagnostic after the test, changes no rule (experiments29.py): world 12 vs world 5 on 20 other worlds
dg = pd.read_csv(f'{ROOT}/results18/diag_world12.csv')
dg = dg[(dg.rule == 'G2')]
out['option_b']['diag_world12'] = [dict(worlds=r.worlds, setting=r.setting, precision=f(r.precision), lo5=f(r.lo5), hi=f(r.hi), found=f(r.found))
                                   for r in dg.itertuples()]
# ---------- history: the numbers shown before 17 Nov 2026 (generator without the budget cap, test worlds 15000-15019)
H = block_from(f'{ROOT}/results10', '15000-15019')
H.update(sweeps_from(f'{ROOT}/results9/sweeps.csv'))
zr = json.load(open(f'{ROOT}/results8/zone_robust.json'))
H['zone'] = dict(values={k: zr['values'][k] for k in ('sigma', 'kappa', 'pi', 'delta', 'mode')}, size=zr['zone_size'],
                 worlds=[0.30, 0.50, 0.86], test_tau90=zr['test_tau90'])
H['main_E_handset'] = main_table(f'{ROOT}/results4/main_results_E_measured.csv',
                                 {'B0 10k per exchange': 'ten_k', 'Rev2 frozen V3 G2+': 'rev2_V3', 'Rev3 V3 G2+': 'rev3_V3'})
mD = pd.read_csv(f'{ROOT}/results2/D/main_results.csv').set_index('detector')
H['main_D'] = {v: dict(precision=f(mD.loc[k, 'precision']), recall=f(mD.loc[k, 'recall']), value_recall=f(mD.loc[k, 'value_recall']))
               for k, v in {'B0 10k per exchange': 'ten_k', 'Grades V3 G2+': 'rev2_V3', 'Grades V3 G3': 'rev2_V3_G3'}.items()}
H['generator'] = dict(budget_cap='off', test_worlds='15000-15019', until='2026-11-16')
out['history'] = {'v16nov': H}
rules = json.load(open(f'{ROOT}/webapp/rules.json'))
out['rules'] = rules

# ---------- real Ethereum data
from common import labels as elabels, label_cat, seeds as eseeds, to_eur
from hop import load, classify_hop1
comb, s, hack, bad, allseeds, a, b = load()
o = a[a.kind == 'out'].copy()
o['cat'] = o.counterparty.map(lambda x: label_cat(x, comb, allseeds | hack))
flows = o.groupby('cat').eur.sum()
out['real'] = dict(
    seeds_listed=int(len(s)), seeds_excluded_token_contracts=18, hack_seeds=int(len(hack)),
    phishing_active=int(a.seed.nunique()), phishing_sending=int(o.seed.nunique()), transfers_out=int(o.n.sum()),
    total_out_eur=f(o.eur.sum(), 0), flows_share={k: f(v / flows.sum()) for k, v in flows.items()},
)
role1 = pd.read_csv(f'{ROOT}/realdata/bq/results/hop1_roles.csv', index_col=0).role
direct = o[o.counterparty.isin(role1.index)].assign(role=lambda d: d.counterparty.map(role1)).groupby('role').eur.sum()
out['real']['hop1_roles'] = {r: dict(n=int((role1 == r).sum()), eur=f(direct.get(r, 0), 0)) for r in ['deposit', 'collector', 'busy', 'holder']}
acc = pd.read_csv(f'{ROOT}/realdata/bq/results/real_accounts.csv', index_col=0)
cd = pd.read_csv(f'{ROOT}/realdata/bq/results/real_candidates.csv')
out['real']['deposit_addresses'] = int(len(acc))
out['real']['by_exchange'] = {k: int(v) for k, v in acc.exchange.fillna('other').value_counts().head(8).items()}
out['real']['fraud_eur_to_deposits'] = f(cd.X.sum(), 0)
out['real']['grades'] = {f'G{g}': dict(n=int((acc.grade == g).sum()), X_median=f(acc[acc.grade == g].X.median(), 0),
                                       X_total=f(acc[acc.grade == g].X.sum(), 0), kappa_median=f(acc[acc.grade == g].kappa.median(), 3))
                         for g in range(4)}
out['real']['rule10k'] = int(acc.rule10k.sum())
out['real']['overlap'] = dict(both=int((acc.rule10k & (acc.grade >= 2)).sum()), grades_only=int(((acc.grade >= 2) & ~acc.rule10k).sum()),
                             ten_k_only=int((acc.rule10k & (acc.grade < 2)).sum()))
rs = pd.read_csv(f'{ROOT}/realdata/bq/results/real_rolling_summary2.csv').set_index('group')
out['real']['check_90d'] = {g: dict(accounts=int(rs.loc[g, 'accounts']), same=f(rs.loc[g, 'same']), new=f(rs.loc[g, 'new']),
                                    either=f(rs.loc[g, 'either']), lo=f(rs.loc[g, 'either_lo']), hi=f(rs.loc[g, 'either_hi'])) for g in rs.index}
g3 = acc[acc.grade >= 3].sort_values('X', ascending=False)
out['real']['g3_examples'] = [dict(address=i, exchange=r.exchange, X=f(r.X, 0), seeds=int(r.nseeds), kappa=f(r.kappa, 2)) for i, r in g3.iterrows()]
# fan-out measurement
import itertools
c2 = cd[cd.X >= 100]; pairs = []; per = []
for sd_, d in c2.groupby('seed'):
    if d.da.nunique() < 2: continue
    t = d.t_first.values / 3600; x = d.X.values
    dt = np.abs(t[:, None] - t[None, :]); r = np.maximum(x[:, None], x[None, :]) / np.minimum(x[:, None], x[None, :])
    iu = np.triu_indices(len(d), 1); pairs += list(zip(dt[iu], r[iu]))
    np.fill_diagonal(dt, np.inf); per.append(((dt <= 6) & (r <= 2)).sum(1).max() >= 2)
pp = np.array(pairs)
out['real']['fanout'] = dict(seeds_multi=len(per), seeds_total=int(c2.seed.nunique()), median_gap_h=f(np.median(pp[:, 0]), 0),
                             median_ratio=f(np.median(pp[:, 1]), 2), pairs_6h_x2=f(((pp[:, 0] <= 6) & (pp[:, 1] <= 2)).mean()),
                             seeds_route_fires=int(np.sum(per)))
# ---------- blacklisting date: real timing (realdata/timing) vs simulator (results19/timing_validation.csv, corrected generator, worlds 18000-18019)
TD = f'{ROOT}/realdata/timing'
ss = pd.read_csv(f'{TD}/delay_per_seed.csv', index_col=0)
av = pd.read_csv(f'{TD}/arrival_vs_tau.csv')
te = pd.read_csv(f'{TD}/e_tether_blacklist.csv'); te = te[te.first_in.notna() & (te.cut_left == False)]
tb = te[te.in_before_usd > 0]
BINS = [-1e9, 0, 7, 30, 180, 1e9]; BL = ['before', '0-7', '8-30', '31-180', '>180']
buck = lambda x: {k: f(v) for k, v in pd.Series(pd.cut(np.asarray(x), BINS, labels=BL)).value_counts(normalize=True).reindex(BL).items()}
rng = np.random.default_rng(0)                      # old simulator: tau - first money = U(2,10) + U(0,10) days
old = rng.uniform(2, 10, 200000) + rng.uniform(0, 10, 200000)
val = pd.read_csv(f'{ROOT}/results19/timing_validation.csv').set_index('model')
val_old = pd.read_csv(f'{ROOT}/results9/timing_validation.csv').set_index('model')
out['real']['timing'] = dict(
    scamsniffer=dict(seeds=int(len(ss)), median_delay=f(ss.delay_d.median(), 1), buckets=buck(ss.delay_d),
                     reached={d: f((av.lag_d <= d).mean()) for d in (0, 7, 30)}, pairs=int(len(av))),
    tether=dict(addresses=int(len(te)), median_delay=f(te.delay_days.median(), 1), buckets=buck(te.delay_days),
                gone_before=f(tb.out_before_usd.fillna(0).clip(upper=tb.in_before_usd).sum() / tb.in_before_usd.sum())),
    old_sim=dict(median_delay=f(np.median(old), 1), buckets=buck(old)),
    sim_reached={m: {0: f(val.loc[m, 'arrived_by_tau']), 7: f(val.loc[m, 'by_tau7']), 30: f(val.loc[m, 'by_tau30'])}
                 for m in ('old', 'alert', 'freeze')})
out['history']['v16nov']['timing_sim_reached'] = {m: {0: f(val_old.loc[m, 'arrived_by_tau']), 7: f(val_old.loc[m, 'by_tau7']), 30: f(val_old.loc[m, 'by_tau30'])}
                                                  for m in ('old', 'alert', 'freeze')}
json.dump(out, open(f'{SITE}/data/thesis.json', 'w'), indent=1)
print(json.dumps(out['real'], indent=1)[:2500])
