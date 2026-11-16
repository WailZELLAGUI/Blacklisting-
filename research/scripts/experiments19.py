"""experiments19.py (15 Nov 2026): stress tests of the lead rule (rev5, V3) on the 20 test worlds 15000-15019,
alert timing, graded at tau + 90 d. The rule is frozen; nothing is tuned here.

  A. An innocent customer who receives a large share of the fraud (one account).
  B. An innocent customer paid by the same fraud at two exchanges (same identity).
  C. Recall with and without the common-destination clue; world-side sweep of p_mule_crypto_exit.
  D. The EUR 10k baseline as coded (X >= min(10k, F)) and pure (X >= 10k), in every table.

A and B are planted AFTER the base world is generated, with their own random stream: the base world is
unchanged, so every scenario is paired with the base. The planted amount is chosen so that the innocent's
share of the seed's money (X / max(out, F_known), as the rule computes it, at the end) equals the target.

Usage: python3 experiments19.py PY_DIR OUT_DIR [n_worlds] [procs]
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
R5 = dict(RULES["rev5"]["V3"]); R5["fan_k"] = 0
RULE = D3.Rule3(**R5)
RULE_NOCONV = D3.Rule3(**{**R5, "conv_entry": False})

P_A = (0.1, 0.3, 0.5, 1.0)
S_A = (0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50)
P_B = (0.05, 0.1, 0.3)
S_B = (0.10, 0.16, 0.20, 0.24, 0.30, 0.40)
SCEN = [("base", 0.0, 0.0)] + [("A", p, s) for p in P_A for s in S_A] + [("B", p, s) for p in P_B for s in S_B]
CFGS = [("C_exit", x, BASE.with_(p_mule_crypto_exit=x)) for x in (0.0, 0.25, 0.75, 1.0)] + \
       [("X_framing_cfg_20_50", 0.3, BASE.with_(framing_share=(0.20, 0.50)))]


def plant(w, kind, p, share, rng):
    """In a fraction p of frauds, the seed also pays one innocent customer `share` of its money:
    kind A = one account; kind B = two accounts of the same identity at two exchanges, half each."""
    planted = set()
    u = dict(zip(sorted(w.seeds), rng.random(len(w.seeds))))
    for s in sorted(w.seeds):                 # nested: a fraud selected at p is also selected at any larger p
        v = w.seeds[s]
        if u[s] >= p:
            continue
        out, fk = v["out"], v["F_known"]
        a = share / (1 - share) * out
        if out + a < fk:
            a = share * fk
        iid = w.new_identity()
        exs = rng.permutation(w.cfg.n_exchanges)[:2 if kind == "B" else 1]
        for ex in exs:
            aid = w.new_account(rng, iid, int(ex), "legit")
            sim.legit_profile(w, rng, aid)
            w.truth[(s, aid)] = "FRAMED"
            sim.seed_transfer(w, s, aid, v["t_dist"] + rng.uniform(0, 5) * DAY + sim.payout_shift(w, s),
                              a / len(exs), rng=rng)
            planted.add((s, aid))
    return planted


def measure(w, sd, planted=frozenset()):
    df = candidate_table_at(w, OFFSET, world_id=sd)
    pos, neg = (m.values for m in labels(df))
    isp = np.array([(s, a) in planted for s, a in zip(df.seed, df.aid)], bool)
    g1, g2, g3, ch = D3.parts(df, RULE, "V3")
    _, g2n, g3n, _ = D3.parts(df, RULE_NOCONV, "V3")
    _, g2v1, _, _ = D3.parts(df, RULE, "V1")
    g3_nocd = g2 & (ch["same_person"] | ch["second_seed"])          # G3 without the common-destination clue
    flags = {"G2+": g2, "G3": g3, "G2+_V1": g2v1, "G2+_noconv": g2n, "G3_noconv": g3n, "G3_nocd": g3_nocd,
             "10k_coded": b0(df).values, "10k_pure": (df.X >= 10_000).values, "G1": g1}
    r = dict(n_pos=int(pos.sum()), n_neg=int(neg.sum()),
             n_all=sum(1 for v in w.truth.values() if v in POSITIVE_ROLES),
             n_frauds=int(df.seed.nunique()), n_planted=int(isp.sum()),
             planted_share_med=float(np.median((df.X_V3.values / df.out2.values)[isp])) if isp.any() else np.nan)
    for k, f in flags.items():
        r[f"tp_{k}"] = int((f & pos).sum()); r[f"fp_{k}"] = int((f & neg).sum())
        r[f"pl_{k}"] = int((f & isp).sum())
    sig = df.X_V3.values / df.out2.values
    direct = (sig >= RULE.sigma) | (df.X_V3.values >= 10_000)
    r["tp_G2+_only_conv"] = int((g2 & pos & ~direct).sum())
    return r


def one_world(sd):
    rows = []
    w0 = generate_world(BASE, np.random.default_rng(sd))
    blob = pickle.dumps(w0)
    for kind, p, s in SCEN:
        w = pickle.loads(blob)
        planted = plant(w, kind, p, s, np.random.default_rng([sd, 9919])) if kind != "base" else frozenset()
        rows.append(dict(scen=kind, p=p, s=s, world=sd, **measure(w, sd, planted)))
    for name, x, cfg in CFGS:
        w = generate_world(cfg, np.random.default_rng(sd))
        rows.append(dict(scen=name, p=x, s=0.0, world=sd, **measure(w, sd)))
    return rows


def summarise(raw):
    rng = np.random.default_rng(0)
    out = []
    for (scen, p, s), g in raw.groupby(["scen", "p", "s"], sort=False):
        g = g.sort_values("world")
        ix = rng.integers(len(g), size=(4000, len(g)))
        row = dict(scen=scen, p=p, s=s, n_worlds=len(g), n_pos=int(g.n_pos.sum()), n_all=int(g.n_all.sum()),
                   n_frauds=int(g.n_frauds.sum()), n_planted=int(g.n_planted.sum()),
                   planted_share_med=round(float(g.planted_share_med.median()), 4) if g.n_planted.sum() else None)
        for k in ("G2+", "G3", "G2+_V1", "G2+_noconv", "G3_noconv", "G3_nocd", "10k_coded", "10k_pure", "G1"):
            tp, fp = g[f"tp_{k}"].values, g[f"fp_{k}"].values
            row[f"prec_{k}"] = round(tp.sum() / max(tp.sum() + fp.sum(), 1), 4)
            b = tp[ix].sum(1) / np.maximum(tp[ix].sum(1) + fp[ix].sum(1), 1)
            row[f"prec_{k}_p05"], row[f"prec_{k}_lo"], row[f"prec_{k}_hi"] = (round(float(x), 4) for x in np.percentile(b, [5, 2.5, 97.5]))
            row[f"found_{k}"] = round(tp.sum() / g.n_pos.sum(), 4)          # / involved accounts reached (site definition)
            row[f"found_all_{k}"] = round(tp.sum() / g.n_all.sum(), 4)      # / every involved pair of the world
            row[f"tp_{k}"], row[f"fp_{k}"] = int(tp.sum()), int(fp.sum())
            row[f"fa_per_fraud_{k}"] = round(fp.sum() / g.n_frauds.sum(), 4)
            row[f"planted_flagged_{k}"] = int(g[f"pl_{k}"].sum())
        row["tp_G2+_only_conv"] = int(g["tp_G2+_only_conv"].sum())
        out.append(row)
    return pd.DataFrame(out)


if __name__ == "__main__":
    from multiprocessing import Pool
    t = time.time()
    seeds = list(range(15000, 15000 + N_WORLDS))
    with Pool(PROCS) as pool:
        res = pool.map(one_world, seeds, chunksize=1)
    raw = pd.DataFrame(list(itertools.chain.from_iterable(res)))
    raw.to_csv(f"{OUT_DIR}/exp19_raw.csv", index=False)
    summ = summarise(raw)
    summ.to_csv(f"{OUT_DIR}/exp19_summary.csv", index=False)
    print(f"done in {time.time() - t:.0f} s; {len(raw)} rows")
