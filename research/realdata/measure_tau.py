"""Blacklisting delay measured on our own seeds: ScamSniffer listing date vs on-chain activity.
Inputs: bq/seeds_all.csv (ss_listed), bq/results/a_seed_flows.csv (query a), bq/results/real_candidates.csv."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "../bq")
from real_common import price_table, seeds_table, load_a
DAY = 86400
W0, W1 = pd.Timestamp("2022-07-01").timestamp(), pd.Timestamp("2023-03-01").timestamp()
p = price_table(); s = seeds_table()
s = s[(s.kind == "phishing") & s.ss_listed.notna()].copy()
s["tau"] = (pd.to_datetime(s.ss_listed) - pd.Timestamp("1970-01-01")).dt.total_seconds().astype("int64")     # start of the listing day (UTC)
out, inn = load_a(p)
first_in = inn.groupby("seed").t.min()
# keep seeds whose first inflow is clearly inside the query window (not cut at its start) and listed inside it
s = s.join(first_in.rename("t_in0"), how="inner")
s = s[(s.t_in0 > W0 + 7 * DAY) & (s.tau < W1)]
s["delay_d"] = (s.tau - s.t_in0) / DAY
q = s.delay_d.quantile([.1, .25, .5, .75, .9]).round(1)
bins = [-1e9, 0, 7, 30, 180, 1e9]; lab = ["listed before first inflow", "0-7 d", "8-30 d", "31-180 d", ">180 d"]
buck = pd.cut(s.delay_d, bins, labels=lab).value_counts(normalize=True).reindex(lab).round(3)
print("seeds:", len(s)); print("delay first inflow -> listing (days) quantiles:\n", q.to_string()); print(buck.to_string())

o = out[out.seed.isin(s.index)].merge(s[["tau"]], left_on="seed", right_index=True)
o["after"] = o.t >= o.tau
print("\nshare of EUR sent by the seeds after listing:", round(o.loc[o.after, "eur"].sum() / o.eur.sum(), 3))
print("share of seeds still sending after listing:", round(o[o.after].seed.nunique() / o.seed.nunique(), 3))

c = pd.read_csv("../bq/results/real_candidates.csv")
c = c[c.seed.isin(s.index)].merge(s[["tau"]], left_on="seed", right_index=True)
c["lag_d"] = (c.t_first - c.tau) / DAY
print("\ncandidate pairs (seed, deposit account):", len(c))
print("first traced arrival - listing (days) quantiles:\n", c.lag_d.quantile([.1, .25, .5, .75, .9]).round(1).to_string())
for d in (0, 7, 30):
    print(f"share of pairs whose first traced money arrives <= tau+{d} d:", round((c.lag_d <= d).mean(), 3),
          "| share of traced EUR (X) arriving to these pairs:", round(c.loc[c.lag_d <= d, 'X'].sum() / c.X.sum(), 3))
s[["t_in0", "tau", "delay_d"]].to_csv("delay_per_seed.csv"); c[["seed", "da", "t_first", "tau", "lag_d", "X", "grade"]].to_csv("arrival_vs_tau.csv", index=False)

# how long a seed stays active (first to last inflow, all assets), for the simulator's collection window
act = inn.groupby("seed").agg(t0=("t", "min"), t1=("t_last", "max"))
act = act[act.index.isin(s.index)]
dur = (act.t1 - act.t0) / DAY
print("\nseed active span, first to last inflow (days) quantiles:\n", dur.quantile([.1, .25, .5, .75, .9]).round(1).to_string())
