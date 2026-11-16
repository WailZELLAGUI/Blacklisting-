"""Point 1 of the 16 Nov 2026 audit: does the simulator's fraud size F, and the number of exchange accounts each
fraud pays, look like our real Ethereum phishing seeds?
Real side: the 1,448 phishing seeds that send money (BigQuery, Jul 2022 - Feb 2023), total sent in EUR (daily prices),
and `out/split_params.json` (422 seeds reaching an exchange: number of deposit addresses >= EUR 100, share of the
seed's money they receive, two hops).
Simulated side: the 20 test worlds 15000-15019 (TEST3_CFG + sourced settings), graded at tau + 90 d.
Output: realdata/out/fraud_size.json
"""
import sys, json
sys.path.insert(0, '/home/claude/fraudster_plus1'); sys.path.insert(0, '/home/claude/fraudster_plus1/realdata/analysis')
import numpy as np, pandas as pd
from hop import load
comb, s, hack, bad, allseeds, a, b = load()
o = a[a.kind == 'out']
real_out = o.groupby('seed').eur.sum()
q = [0.1, 0.25, 0.5, 0.75, 0.9, 0.99]
def lnfit(x):
    x = np.log(x[x > 0]); return dict(median=float(np.exp(np.median(x))), sigma=float(x.std()))
sp = np.array(json.load(open('/home/claude/fraudster_plus1/realdata/out/split_params.json'))['seeds'])
res = dict(real=dict(
    n_seeds=int(len(real_out)), total_eur=float(real_out.sum()), mean_eur=float(real_out.mean()),
    quantiles_eur={str(k): float(v) for k, v in real_out.quantile(q).items()},
    share_below_500=float((real_out < 500).mean()),
    lognormal_fit_all=lnfit(real_out.values), lognormal_fit_ge500=lnfit(real_out[real_out >= 500].values),
    reaching_seeds=int(len(sp)), deposit_accounts_quantiles={str(k): float(np.quantile(sp[:, 0], k)) for k in q},
    one_deposit_account=float((sp[:, 0] == 1).mean()), share_to_deposits_median=float(np.median(sp[:, 1]))))
# simulated
import experiments17 as E17, sim
rng = np.random.default_rng(0)
F = np.clip(np.exp(np.log(E17.CFG.F_median) + E17.CFG.F_sigma * rng.standard_normal(200000)), 500, 2e6)
t = E17.table(E17.CFG, E17.TEST, 90, 'test')
t = t[t.X >= 100]
per = t.groupby(['world', 'seed'])
n_acc = per.aid.nunique()
share = per.X.sum() / per.out2.first()
res['sim'] = dict(F_median_setting=E17.CFG.F_median, F_sigma_setting=E17.CFG.F_sigma,
    F_quantiles_eur={str(k): float(np.quantile(F, k)) for k in q}, F_mean_eur=float(F.mean()),
    reaching_frauds=int(len(n_acc)), accounts_quantiles={str(k): float(np.quantile(n_acc, k)) for k in q},
    one_account=float((n_acc == 1).mean()), share_to_accounts_median=float(np.median(share)))
json.dump(res, open('/home/claude/fraudster_plus1/realdata/out/fraud_size.json', 'w'), indent=1)
print(json.dumps(res, indent=1))
