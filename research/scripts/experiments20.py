"""experiments20.py (16 Nov 2026): sensitivity of the frozen lead rule (rev5, V3) to the fraud size F.
Real check (realdata/analysis/fraud_size.py): our 1,448 real phishing seeds send a median EUR 1,874 (EUR 6,621 for the
seeds sending >= EUR 500, log-sigma 1.93), while the simulator draws F with median EUR 30,000 (sigma 1.2), set by hand.
Here the 20 test worlds 15000-15019 (alert timing, tau + 90 d, cex_share 0.50) are regenerated with F drawn as the real
seeds >= EUR 500 (and an intermediate setting). Nothing is tuned: the rule is frozen.
Recall is divided by the involved accounts with at least one traced payment (site definition), as in experiments19.
Usage: python3 experiments20.py PY_DIR OUT_DIR [n_worlds] [procs]
"""
import sys, json, time, itertools
PY_DIR, OUT_DIR = sys.argv[1], sys.argv[2]
N_WORLDS = int(sys.argv[3]) if len(sys.argv) > 3 else 20
PROCS = int(sys.argv[4]) if len(sys.argv) > 4 else 4
sys.path.insert(0, PY_DIR)
import numpy as np, pandas as pd
import detectors3 as D3
from detectors import b0, labels
from configs import TEST3_CFG
from evaltime import candidate_table_at
from sim import generate_world, DAY, POSITIVE_ROLES

OFFSET = 90 * DAY
BASE = TEST3_CFG.with_(blacklist_model="alert", horizon_days=365.0)
R5 = D3.Rule3(**{**json.load(open(f"{PY_DIR}/rules.json"))["rev5"]["V3"], "fan_k": 0})
SIZES = [("sim (hand) 30000 / 1.2", 30000.0, 1.2), ("between 15000 / 1.5", 15000.0, 1.5), ("real >= 500: 6621 / 1.93", 6621.0, 1.93)]


def n_traced(w):
    return sum(1 for (s, a), v in w.truth.items() if v in POSITIVE_ROLES and
               any(e[3] == "in_seed" and e[5][0] == s and e[5][1] for e in w.events.get(a, [])))


def one(args):
    name, med, sig, sd = args
    w = generate_world(BASE.with_(F_median=med, F_sigma=sig), np.random.default_rng(sd))
    df = candidate_table_at(w, OFFSET, world_id=sd)
    pos, neg = (m.values for m in labels(df))
    g1, g2, g3, ch = D3.parts(df, R5, "V3")
    flags = {"G1": g1, "G2+": g2, "G3": g3, "10k_pure": (df.X >= 10_000).values, "10k_coded": b0(df).values}
    r = dict(size=name, world=sd, n_pos=n_traced(w), n_frauds=int(df.seed.nunique()),
             F_median_world=float(np.median([v["F"] for v in w.seeds.values()])))
    for k, f in flags.items():
        r[f"tp_{k}"] = int((f & pos).sum()); r[f"fp_{k}"] = int((f & neg).sum())
    return r


if __name__ == "__main__":
    from multiprocessing import Pool
    t = time.time()
    jobs = [(n, m, s, sd) for n, m, s in SIZES for sd in range(15000, 15000 + N_WORLDS)]
    with Pool(PROCS) as p:
        raw = pd.DataFrame(p.map(one, jobs, chunksize=1))
    raw.to_csv(f"{OUT_DIR}/exp20_raw.csv", index=False)
    rng = np.random.default_rng(0); out = []
    for name, g in raw.groupby("size", sort=False):
        g = g.sort_values("world"); ix = rng.integers(len(g), size=(4000, len(g)))
        row = dict(size=name, n_pos=int(g.n_pos.sum()), n_frauds=int(g.n_frauds.sum()), F_median=round(float(g.F_median_world.median())))
        for k in ("G1", "G2+", "G3", "10k_pure", "10k_coded"):
            tp, fp = g[f"tp_{k}"].values, g[f"fp_{k}"].values
            row[f"prec_{k}"] = round(tp.sum() / max(tp.sum() + fp.sum(), 1), 4)
            b = tp[ix].sum(1) / np.maximum(tp[ix].sum(1) + fp[ix].sum(1), 1)
            row[f"prec_{k}_lo"], row[f"prec_{k}_hi"] = (round(float(x), 4) for x in np.percentile(b, [2.5, 97.5]))
            row[f"found_{k}"] = round(tp.sum() / g.n_pos.sum(), 4)
            row[f"fa_per_fraud_{k}"] = round(fp.sum() / g.n_frauds.sum(), 4)
        out.append(row)
    pd.DataFrame(out).to_csv(f"{OUT_DIR}/exp20_summary.csv", index=False)
    print(pd.DataFrame(out).T.to_string()); print(f"done in {time.time() - t:.0f} s")
