"""experiments23.py (17 Nov 2026): the sweep of ordinary activity fixed in preregistration_activity.md (written before
any run). New worlds 19000-19019, alert timing, tau + 90 d, frozen lead rule (Revision 2 on the site = rev5, V3, no fan-out).
Usage: python3 experiments21.py PY_DIR OUT_DIR [n_worlds] [procs]   (PY_DIR must hold the sim.py of 17 Nov 2026, with user_transfers)
"""
import sys, json, time, itertools
PY_DIR, OUT_DIR = sys.argv[1], sys.argv[2]
N_WORLDS = int(sys.argv[3]) if len(sys.argv) > 3 else 20
PROCS = int(sys.argv[4]) if len(sys.argv) > 4 else 2
sys.path.insert(0, PY_DIR)
import numpy as np, pandas as pd
import detectors3 as D3
from detectors import labels
from configs import TEST3_CFG
from evaltime import candidate_table_at
from sim import generate_world, DAY, POSITIVE_ROLES, NEGATIVE_ROLES

OFFSET = 90 * DAY
BASE = TEST3_CFG.with_(blacklist_model="alert", horizon_days=365.0)
R5 = D3.Rule3(**{**json.load(open(f"{PY_DIR}/rules.json"))["rev5"]["V3"], "fan_k": 0})
WORLDS = range(19000, 19000 + N_WORLDS)


def case(name, **kw):
    return dict(case=name, **kw)


CASES = []
for ut in (0.0, 0.3):
    for a in (0.5, 1.0, 1.5, 2.0):
        CASES.append(case(f"activity={a} user_transfers={ut}", block="reference" if (a == 1.5 and ut == 0) else "grid",
                          legit_amount_scale=a, legit_rate_scale=a, user_transfers=ut))


def n_traced(w):
    return sum(1 for (s, a), v in w.truth.items() if v in POSITIVE_ROLES and
               any(e[3] == "in_seed" and e[5][0] == s and e[5][1] for e in w.events.get(a, [])))


def one(args):
    c, sd = args
    kw = {k: v for k, v in c.items() if k not in ("case", "block")}
    w = generate_world(BASE.with_(**kw), np.random.default_rng(sd))
    df = candidate_table_at(w, OFFSET, world_id=sd)
    pos, neg = (m.values for m in labels(df))
    p2p = (df.role == "P2P").values
    g1, g2, g3, ch = D3.parts(df, R5, "V3")
    flags = {"G1": g1, "G2+": g2, "G3": g3, "10k": (df.X >= 10_000).values}
    r = dict(case=c["case"], block=c["block"], world=sd, n_pos=n_traced(w), n_frauds=len(w.seeds),
             n_frauds_reaching=int(df[df.X >= 100].seed.nunique()))
    for k, f in flags.items():
        r[f"tp_{k}"] = int((f & pos).sum()); r[f"fp_{k}"] = int((f & neg).sum())
    r["fp_G2+_noP2P"] = int((g2 & neg & ~p2p).sum())
    roles3 = df[g3 & neg].role.value_counts().to_dict()
    for role in NEGATIVE_ROLES:
        r[f"fpG3_{role}"] = int(roles3.get(role, 0))
    roles = df[g2 & neg].role.value_counts().to_dict()
    for role in NEGATIVE_ROLES:
        r[f"fpG2_{role}"] = int(roles.get(role, 0))
    return r


def summarise(raw):
    rng = np.random.default_rng(0)
    out = []
    for name, g in raw.groupby("case", sort=False):
        g = g.sort_values("world"); ix = rng.integers(len(g), size=(4000, len(g)))
        row = dict(case=name, block=g.block.iloc[0], n_worlds=len(g), n_pos=int(g.n_pos.sum()),
                   n_frauds=int(g.n_frauds.sum()), n_frauds_reaching=int(g.n_frauds_reaching.sum()))
        defs = [(k, f"fp_{k}") for k in ("G1", "G2+", "G3", "10k")] + [("G2+_P2Pexcluded", "fp_G2+_noP2P")]
        for k, fpc in defs:
            tp = g[f"tp_{k.split('_P2P')[0]}"].values; fp = g[fpc].values
            row[f"tp_{k}"], row[f"fp_{k}"] = int(tp.sum()), int(fp.sum())
            row[f"prec_{k}"] = round(tp.sum() / max(tp.sum() + fp.sum(), 1), 4)
            b = tp[ix].sum(1) / np.maximum(tp[ix].sum(1) + fp[ix].sum(1), 1)
            row[f"prec_{k}_p05"], row[f"prec_{k}_lo"], row[f"prec_{k}_hi"] = (round(float(x), 4) for x in np.percentile(b, [5, 2.5, 97.5]))
            row[f"found_{k}"] = round(tp.sum() / g.n_pos.sum(), 4)
            row[f"fa_per_fraud_{k}"] = round(fp.sum() / g.n_frauds.sum(), 4)
            row[f"fa_per_reaching_fraud_{k}"] = round(fp.sum() / max(g.n_frauds_reaching.sum(), 1), 4)
        row["too_few_G2_alerts"] = bool(row["tp_G2+"] + row["fp_G2+"] < 100)
        for role in NEGATIVE_ROLES:
            row[f"fpG2_{role}"] = int(g[f"fpG2_{role}"].sum())
            row[f"fpG3_{role}"] = int(g[f"fpG3_{role}"].sum())
        out.append(row)
    return pd.DataFrame(out)


if __name__ == "__main__":
    from multiprocessing import Pool
    t = time.time()
    jobs = [(c, sd) for c in CASES for sd in WORLDS]
    print(len(CASES), "cases,", len(jobs), "worlds", flush=True)
    with Pool(PROCS) as p:
        raw = pd.DataFrame(p.map(one, jobs, chunksize=2))
    raw.to_csv(f"{OUT_DIR}/exp23_raw.csv", index=False)
    summ = summarise(raw)
    summ.to_csv(f"{OUT_DIR}/exp23_summary.csv", index=False)
    summ[["case"] + [c for c in summ.columns if c.startswith("fpG2_") or c.startswith("fpG3_")]].to_csv(f"{OUT_DIR}/exp23_roles.csv", index=False)
    print(f"done in {time.time() - t:.0f} s")
