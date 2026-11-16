"""experiments19b.py (15 Nov 2026): extension of experiments19.py.
  - three plausible worlds: cex_share 0.30 / 0.50 / 0.86 (test worlds 15000-15019, alert timing, tau + 90 d);
  - lead rule (rev5, V3) and revision 3 (fan-out), both frozen;
  - innocent planted on one account (A), on two exchanges (B), and on two exchanges with fast resale on both
    accounts, like a P2P/OTC seller (Bp);
  - candidate fixes for the G3 clue 'same person at >= 2 exchanges', TESTED ONLY, not adopted:
      P1  the clue counts only if every account of that person paid by the fraud passes the behaviour test (kappa OR pi)
      P1b same, with the pass-through test alone (>= 90 % passed on within 24 h on every account)
      P4  the clue is dropped (G3 = second seed OR common destination)
Recall is divided by the involved accounts with at least one traced payment over the whole world (site definition).
Usage: python3 experiments19b.py PY_DIR OUT_DIR [n_worlds] [procs]
"""
import sys, json, pickle, time, itertools
PY_DIR, OUT_DIR = sys.argv[1], sys.argv[2]
N_WORLDS = int(sys.argv[3]) if len(sys.argv) > 3 else 20
PROCS = int(sys.argv[4]) if len(sys.argv) > 4 else 4
sys.path.insert(0, PY_DIR)
import numpy as np, pandas as pd
import sim, detectors3 as D3
from detectors import b0, labels
from configs import TEST3_CFG
from evaltime import candidate_table_at
from sim import generate_world, DAY, POSITIVE_ROLES

OFFSET = 90 * DAY
BASE = TEST3_CFG.with_(blacklist_model="alert", horizon_days=365.0)
RULES = json.load(open(f"{PY_DIR}/rules.json"))
R5 = D3.Rule3(**{**RULES["rev5"]["V3"], "fan_k": 0})
R3 = D3.Rule3(**RULES["rev3"]["V3"])
CEX = (0.30, 0.50, 0.86)
SCEN = [("base", 0.0, 0.0)] + [("A", p, s) for p in (0.1, 0.3) for s in (0.10, 0.20, 0.30)] + \
       [(k, p, s) for k in ("B", "Bp") for p in (0.05, 0.1, 0.3) for s in (0.20, 0.40)]


def plant(w, kind, p, share, rng):
    planted = set()
    u = dict(zip(sorted(w.seeds), rng.random(len(w.seeds))))
    for s in sorted(w.seeds):
        v = w.seeds[s]
        if u[s] >= p:
            continue
        out, fk = v["out"], v["F_known"]
        a = share / (1 - share) * out
        if out + a < fk:
            a = share * fk
        iid = w.new_identity()
        exs = rng.permutation(w.cfg.n_exchanges)[:1 if kind == "A" else 2]
        for ex in exs:
            aid = w.new_account(rng, iid, int(ex), "legit")
            sim.legit_profile(w, rng, aid)
            if kind == "Bp":
                w.accounts[aid]["ramp"] = True          # resells every deposit within hours (P2P/OTC seller)
            w.truth[(s, aid)] = "FRAMED"
            sim.seed_transfer(w, s, aid, v["t_dist"] + rng.uniform(0, 5) * DAY + sim.payout_shift(w, s),
                              a / len(exs), rng=rng)
            planted.add((s, aid))
    return planted


def n_traced(w):
    n = 0
    for (s, a), v in w.truth.items():
        if v in POSITIVE_ROLES and any(e[3] == "in_seed" and e[5][0] == s and e[5][1] for e in w.events.get(a, [])):
            n += 1
    return n


def measure(w, sd, planted=frozenset()):
    df = candidate_table_at(w, OFFSET, world_id=sd)
    pos, neg = (m.values for m in labels(df))
    isp = np.array([(s, a) in planted for s, a in zip(df.seed, df.aid)], bool)
    g1, g2, g3, ch = D3.parts(df, R5, "V3")
    _, g2r3, g3r3, _ = D3.parts(df, R3, "V3")
    pi_ok = df[f"pi_{R5.delta}"].values >= R5.pi
    beh = (df.kappa2.values >= R5.kappa) | pi_ok
    grp = df.g_V3.values
    all_beh = pd.Series(beh).groupby(grp).transform("min").values.astype(bool)
    all_pi = pd.Series(pi_ok).groupby(grp).transform("min").values.astype(bool)
    other = ch["second_seed"] | ch["common_dest"]
    flags = {"G2+": g2, "G3": g3, "G3_P1": g2 & ((ch["same_person"] & all_beh) | other),
             "G3_P1b": g2 & ((ch["same_person"] & all_pi) | other), "G3_P4": g2 & other,
             "rev3_G2+": g2r3, "rev3_G3": g3r3, "10k_coded": b0(df).values, "10k_pure": (df.X >= 10_000).values}
    r = dict(n_pos=n_traced(w), n_frauds=int(df.seed.nunique()), n_planted=int(isp.sum()))
    for k, f in flags.items():
        r[f"tp_{k}"] = int((f & pos).sum()); r[f"fp_{k}"] = int((f & neg).sum()); r[f"pl_{k}"] = int((f & isp).sum())
    return r


def one(args):
    cex, sd = args
    rows = []
    blob = pickle.dumps(generate_world(BASE.with_(cex_share=cex), np.random.default_rng(sd)))
    for kind, p, s in SCEN:
        w = pickle.loads(blob)
        planted = plant(w, kind, p, s, np.random.default_rng([sd, 9919])) if kind != "base" else frozenset()
        rows.append(dict(cex=cex, scen=kind, p=p, s=s, world=sd, **measure(w, sd, planted)))
    return rows


def summarise(raw):
    rng = np.random.default_rng(0)
    out = []
    keys = [c[3:] for c in raw.columns if c.startswith("tp_")]
    for (cex, scen, p, s), g in raw.groupby(["cex", "scen", "p", "s"], sort=False):
        g = g.sort_values("world")
        ix = rng.integers(len(g), size=(4000, len(g)))
        row = dict(cex=cex, scen=scen, p=p, s=s, n_pos=int(g.n_pos.sum()), n_frauds=int(g.n_frauds.sum()), n_planted=int(g.n_planted.sum()))
        for k in keys:
            tp, fp = g[f"tp_{k}"].values, g[f"fp_{k}"].values
            row[f"prec_{k}"] = round(tp.sum() / max(tp.sum() + fp.sum(), 1), 4)
            b = tp[ix].sum(1) / np.maximum(tp[ix].sum(1) + fp[ix].sum(1), 1)
            row[f"prec_{k}_p05"], row[f"prec_{k}_lo"], row[f"prec_{k}_hi"] = (round(float(x), 4) for x in np.percentile(b, [5, 2.5, 97.5]))
            row[f"found_{k}"] = round(tp.sum() / g.n_pos.sum(), 4)
            row[f"tp_{k}"], row[f"fp_{k}"] = int(tp.sum()), int(fp.sum())
            row[f"fa_per_fraud_{k}"] = round(fp.sum() / g.n_frauds.sum(), 4)
            row[f"planted_flagged_{k}"] = int(g[f"pl_{k}"].sum())
        out.append(row)
    return pd.DataFrame(out)


if __name__ == "__main__":
    from multiprocessing import Pool
    t = time.time()
    jobs = [(c, sd) for sd in range(15000, 15000 + N_WORLDS) for c in CEX]
    with Pool(PROCS) as pool:
        res = pool.map(one, jobs, chunksize=1)
    raw = pd.DataFrame(list(itertools.chain.from_iterable(res)))
    raw.to_csv(f"{OUT_DIR}/exp19b_raw.csv", index=False)
    summarise(raw).to_csv(f"{OUT_DIR}/exp19b_summary.csv", index=False)
    print(f"done in {time.time() - t:.0f} s; {len(raw)} rows")
