"""experiments26.py (17 Nov 2026): option B, the last recalibration, exactly as written in preregistration_optionB.md
before any run. Generator corrected by default (budget_cap = "all"); 12 settings; calibration on worlds 17000-17019;
choice of the final rule from the calibration alone (saved before any test world is generated); one test on worlds
18000-18019.
Usage: python3 experiments26.py PY_DIR OUT_DIR calibrate|test [procs]
"""
import sys, json, time, itertools
PY_DIR, OUT_DIR, STEP = sys.argv[1], sys.argv[2], sys.argv[3]
PROCS = int(sys.argv[4]) if len(sys.argv) > 4 else 2
sys.path.insert(0, PY_DIR)
sys.path.insert(1, "/home/claude/fraudster_plus1")
import numpy as np, pandas as pd
import sim, detectors3 as D3, detectors2 as D2
from detectors import labels
from configs import TEST3_CFG
from evaltime import candidate_table_at
from sim import DAY, POSITIVE_ROLES, NEGATIVE_ROLES
import experiments8 as E8, experiments17b as E17b

BASE = TEST3_CFG.with_(blacklist_model="alert", horizon_days=365.0, budget_cap="all")
REAL = dict(F_source="real")
SETTINGS = {
    1: dict(), 2: dict(cex_share=0.30), 3: dict(cex_share=0.86),
    4: dict(REAL), 5: dict(REAL, cex_share=0.30), 6: dict(REAL, cex_share=0.86),
    7: dict(REAL, p2p_volume=0.10), 8: dict(REAL, innocent_amounts="fraud"),
    9: dict(REAL, legit_amount_scale=0.5, legit_rate_scale=0.5), 10: dict(REAL, legit_amount_scale=2.0, legit_rate_scale=2.0),
    11: dict(REAL, user_transfers=0.3),
    12: dict(REAL, cex_share=0.30, p2p_volume=0.10, legit_amount_scale=0.5, legit_rate_scale=0.5),
}
import os
CAL, TEST = (range(99000, 99003), range(99100, 99102)) if os.environ.get("FP1_DRY") else (range(17000, 17020), range(18000, 18020))
RULES = json.load(open(f"{PY_DIR}/rules.json"))
CUR = {**RULES["rev5"]["V3"], "fan_k": 0}
GRID = E17b.GRID
KEYS = list(GRID)
SB = E8.BASE4
rng = np.random.default_rng(2026)


def budget_ok(w):
    for s, v in w.seeds.items():
        tot = sum(a for _, a in v.get("out_ev", [])) + v.get("out_lump", 0.0)
        if abs(tot - v["out"]) > 1e-6 * max(1.0, v["out"]) or v["out"] > v["F"] * (1 + 1e-9):
            return False
    return True


def n_traced(w):
    return sum(1 for (s, a), v in w.truth.items() if v in POSITIVE_ROLES and
               any(e[3] == "in_seed" and e[5][0] == s and e[5][1] for e in w.events.get(a, [])))


def one(args):
    k, sd, offsets = args
    w = sim.generate_world(BASE.with_(**SETTINGS[k]), np.random.default_rng(sd))
    assert budget_ok(w), f"budget check failed: setting {k}, world {sd}"
    out = {}
    for off in offsets:
        df = candidate_table_at(w, off * DAY, world_id=sd)
        df["setting"] = k
        out[off] = df
    return k, sd, n_traced(w), len(w.seeds), out


def tables(worlds, offsets):
    from multiprocessing import Pool
    jobs = [(k, sd, offsets) for k in SETTINGS for sd in worlds]
    with Pool(PROCS) as p:
        res = p.map(one, jobs, chunksize=1)
    T = {k: {off: [] for off in offsets} for k in SETTINGS}
    n_pos = {k: 0 for k in SETTINGS}; n_fr = {k: 0 for k in SETTINGS}
    for k, sd, npos, nfr, out in res:
        n_pos[k] += npos; n_fr[k] += nfr
        for off, df in out.items():
            T[k][off].append(df)
    return {k: {off: pd.concat(v, ignore_index=True) for off, v in d.items()} for k, d in T.items()}, n_pos, n_fr


def scan(df):
    """experiments16.scan, plus: false alerts without P2P buyers (complementary definition), P2P buyers flagged."""
    pos, neg = (m.values for m in labels(df))
    p2p = (df.role == "P2P").values
    w = pd.factorize(df.world)[0]; nw = w.max() + 1
    Xv = df.X_V3.values; sig = Xv / df.out2.values
    theta = D2.amount_ok(Xv, df, SB); conv = df.conv_V3.values == 1
    live = (df.X.values >= SB.x_min) & (df.v.values == 0) & ((sig >= SB.sigma_g1) | theta | conv)
    kap = df.kappa2.values; pis = {d: df[f"pi_{d}"].values for d in GRID["delta"]}
    C, TP, FPc, FP, PP = [], [], [], [], []
    for vals in itertools.product(*(GRID[k] for k in KEYS)):
        p = dict(zip(KEYS, vals))
        s_ok = (sig >= max(p["sigma"], SB.sigma_g1)) | theta | conv
        pi_ok = pis[p["delta"]] >= p["pi"]; k_ok = kap >= p["kappa"]
        f = ((k_ok & pi_ok) if p["mode"] == "AND" else (k_ok | pi_ok)) | ((sig >= p["sigma_dom"]) & pi_ok)
        if p["amount_route"]:
            f = f | (theta & pi_ok)
        f = live & s_ok & f
        C.append(p)
        TP.append(np.bincount(w[f & pos], minlength=nw)); FP.append(np.bincount(w[f & neg], minlength=nw))
        FPc.append(np.bincount(w[f & neg & ~p2p], minlength=nw)); PP.append(int((f & p2p).sum()))
    C = pd.DataFrame(C); TP, FP, FPc = np.array(TP), np.array(FP), np.array(FPc)
    C["tp"], C["fp"], C["fp_noP2P"], C["p2p_flagged"] = TP.sum(1), FP.sum(1), FPc.sum(1), PP
    Wb = rng.multinomial(nw, np.ones(nw) / nw, size=1000).T
    tpb, fpb = TP @ Wb, FPc @ Wb
    with np.errstate(invalid="ignore", divide="ignore"):
        C["prec_c_lo5"] = np.nanpercentile(tpb / (tpb + fpb), 5, axis=1)
    return C


def dist(row):
    return sum(row[k] != CUR[k] for k in KEYS)


def calibrate():
    t0 = time.time()
    T, n_pos, n_fr = tables(CAL, (90,))
    log = dict(settings={str(k): v for k, v in SETTINGS.items()}, n_pos=n_pos, n_frauds=n_fr, budget_check="passed")
    S = {}
    for k in SETTINGS:
        df = T[k][90]
        C = scan(df)
        C["recall"] = C.tp / n_pos[k]
        C["p2p_per_fraud"] = C.p2p_flagged / n_fr[k]
        ten = (df.X >= 10_000).values & labels(df)[0].values
        C["floor"] = 2 * ten.sum() / n_pos[k]
        S[k] = C
        print(f"setting {k} scanned ({time.time() - t0:.0f} s)", flush=True)
    ref = S[1][KEYS]
    is_cur = np.all([ref[k] == CUR[k] for k in KEYS], axis=0)
    assert is_cur.sum() == 1, "current rule not in the grid"
    ic = int(np.flatnonzero(is_cur)[0])
    # sanity check: the scan reproduces detectors3's G2 for the current rule (setting 1)
    g2 = D3.parts(T[1][90], D3.Rule3(**CUR), "V3")[1]
    pos, neg = (m.values for m in labels(T[1][90]))
    assert int((g2 & pos).sum()) == int(S[1].tp[ic]) and int((g2 & neg).sum()) == int(S[1].fp[ic]), "scan != detectors3"
    lo = np.array([S[k].prec_c_lo5.values for k in SETTINGS]); rec = np.array([S[k].recall.values for k in SETTINGS])
    pp = np.array([S[k].p2p_per_fraud.values for k in SETTINGS]); fl = np.array([S[k].floor.values for k in SETTINGS])
    p2p_ok = np.all(pp <= pp[:, [ic]] + 1e-12, axis=0); floor_ok = np.all(rec >= fl, axis=0)
    prec_ok = np.all(lo >= 0.90, axis=0)
    mean_rec = rec.mean(0); worst_lo = lo.min(0)
    C = ref.copy(); C["mean_recall"] = mean_rec; C["worst_lo5"] = worst_lo
    C["prec_ok"], C["p2p_ok"], C["floor_ok"] = prec_ok, p2p_ok, floor_ok
    C["dist"] = C.apply(dist, axis=1)
    C.to_csv(f"{OUT_DIR}/calibration_scan.csv", index=False)
    cur = dict(mean_recall=float(mean_rec[ic]), worst_lo5=float(worst_lo[ic]), prec_ok=bool(prec_ok[ic]),
               by_setting={str(k): dict(lo5_complementary=round(float(lo[i, ic]), 4), recall=round(float(rec[i, ic]), 4),
                                        p2p_per_fraud=round(float(pp[i, ic]), 4), floor=round(float(fl[i, ic]), 4))
                           for i, k in enumerate(SETTINGS)})
    ok = C[C.prec_ok & C.p2p_ok & C.floor_ok]
    choice = dict(current=cur, passing_all=int(len(ok)))
    if len(ok):
        Z = ok[ok.mean_recall >= ok.mean_recall.max() - 0.02]
        choice["zone_size"] = int(len(Z))
        choice["zone_values"] = {k: sorted(set(Z[k].tolist()), key=str) for k in KEYS}
        if ic in Z.index:
            final, how = ic, "current rule in the zone: kept"
        else:
            best = Z[Z.mean_recall == Z.mean_recall.max()]
            final, how = best.sort_values(["dist"], kind="stable").index[0], "best mean recall in the zone"
        fallback = None
    else:
        cand = C[(C.mean_recall >= mean_rec[ic] - 0.03) & C.p2p_ok & C.floor_ok]
        if len(cand):
            best = cand[cand.worst_lo5 == cand.worst_lo5.max()]
            fallback = best.sort_values(["dist"], kind="stable").index[0]
            final, how = fallback, "no zone: fallback rule (best worst-case lower bound)"
        else:
            final, how, fallback = ic, "no zone and no fallback: current rule kept", None
    choice["how"] = how
    choice["final"] = {k: (v.item() if hasattr(v, "item") else v) for k, v in C.loc[final, KEYS].items()}
    choice["final_calibration"] = dict(mean_recall=round(float(mean_rec[final]), 4), worst_lo5=round(float(worst_lo[final]), 4),
                                       by_setting={str(k): dict(lo5_complementary=round(float(lo[i, final]), 4),
                                                                recall=round(float(rec[i, final]), 4),
                                                                p2p_per_fraud=round(float(pp[i, final]), 4))
                                                   for i, k in enumerate(SETTINGS)})
    choice["fallback_rule_also_tested"] = fallback is not None
    # G3 check on calibration (declared, not a constraint): flag settings where its lower bound is below 95 %
    g3 = {}
    for k in SETTINGS:
        df = T[k][90]; pos, neg = (m.values for m in labels(df))
        for name, r in (("final", choice["final"]), ("current", {k2: CUR[k2] for k2 in KEYS})):
            g = D3.parts(df, D3.Rule3(**{**CUR, **r}), "V3")[2]
            wv = pd.factorize(df.world)[0]; nw = wv.max() + 1
            tp = np.bincount(wv[g & pos], minlength=nw); fp = np.bincount(wv[g & neg], minlength=nw)
            Wb = rng.multinomial(nw, np.ones(nw) / nw, size=1000).T
            b = (tp @ Wb) / np.maximum((tp + fp) @ Wb, 1)
            g3.setdefault(name, {})[str(k)] = round(float(np.percentile(b, 5)), 4)
    choice["g3_lo5_calibration"] = g3
    choice["g3_flags_below_95"] = {n: [k for k, v in d.items() if v < 0.95] for n, d in g3.items()}
    choice["seconds"] = round(time.time() - t0)
    log["choice"] = choice
    json.dump(log, open(f"{OUT_DIR}/optionB_choice.json", "w"), indent=1)
    print(json.dumps(choice, indent=1))


def metrics(df, f, pos, neg, p2p, n_pos, n_fr):
    w = pd.factorize(df.world)[0]; nw = w.max() + 1
    tp = np.bincount(w[f & pos], minlength=nw); fp = np.bincount(w[f & neg], minlength=nw)
    fpc = np.bincount(w[f & neg & ~p2p], minlength=nw)
    Wb = np.random.default_rng(0).multinomial(nw, np.ones(nw) / nw, size=4000).T
    def bs(t, q):
        b = (t @ Wb) / np.maximum((t + q) @ Wb, 1)
        return [round(float(x), 4) for x in np.percentile(b, [2.5, 5, 97.5])]
    X = df.X.values
    return dict(tp=int(tp.sum()), fp=int(fp.sum()), precision=round(tp.sum() / max(tp.sum() + fp.sum(), 1), 4),
                precision_ci_lo5_hi=bs(tp, fp), precision_complementary=round(tp.sum() / max(tp.sum() + fpc.sum(), 1), 4),
                precision_complementary_ci_lo5_hi=bs(tp, fpc), found=round(tp.sum() / n_pos, 4),
                money_covered=round(float(X[f & pos].sum() / max(X[pos].sum(), 1e-9)), 4),
                false_alerts_per_fraud=round(fp.sum() / n_fr, 4), p2p_flagged_per_fraud=round(int((f & p2p).sum()) / n_fr, 4),
                false_alerts_by_role={r: int((f & neg & (df.role == r).values).sum()) for r in NEGATIVE_ROLES})


def test():
    ch = json.load(open(f"{OUT_DIR}/optionB_choice.json"))["choice"]
    rules = {"final": {**CUR, **ch["final"]}, "current": CUR}
    T, n_pos, n_fr = tables(TEST, (1, 7, 30, 90))
    out = dict(final_rule=ch["final"], how=ch["how"], n_pos=n_pos, n_frauds=n_fr, results={})
    for k in SETTINGS:
        out["results"][str(k)] = {}
        for off in (1, 7, 30, 90):
            df = T[k][off]; pos, neg = (m.values for m in labels(df)); p2p = (df.role == "P2P").values
            r = {"10k": metrics(df, (df.X >= 10_000).values, pos, neg, p2p, n_pos[k], n_fr[k])}
            for name, rr in rules.items():
                g1, g2, g3, _ = D3.parts(df, D3.Rule3(**rr), "V3")
                for gn, f in (("G1", g1), ("G2+", g2), ("G3", g3)):
                    r[f"{name} {gn}"] = metrics(df, f, pos, neg, p2p, n_pos[k], n_fr[k])
            out["results"][str(k)][f"tau+{off}"] = r
    json.dump(out, open(f"{OUT_DIR}/optionB_test.json", "w"), indent=1)
    rows = []
    for k, d in out["results"].items():
        for off, r in d.items():
            for name, m in r.items():
                rows.append(dict(setting=int(k), when=off, rule=name, **{a: b for a, b in m.items() if not isinstance(b, (list, dict))},
                                 precision_lo5=m["precision_ci_lo5_hi"][1], precision_complementary_lo5=m["precision_complementary_ci_lo5_hi"][1]))
    pd.DataFrame(rows).to_csv(f"{OUT_DIR}/optionB_test.csv", index=False)
    print("test done")


if __name__ == "__main__":
    {"calibrate": calibrate, "test": test}[STEP]()
