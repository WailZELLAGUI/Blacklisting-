"""Bridge between the website and our thesis code (sim.py, features.py, detectors2.py, detectors3.py).
Runs unchanged in normal Python and in the browser (Pyodide). Every function takes and returns JSON text."""
import json
import os

import numpy as np
import pandas as pd

import detectors2 as D2
import detectors3 as D3
from configs import TEST3_CFG
from detectors import b0, labels, score
from features import candidate_table
from sim import NEGATIVE_ROLES, POSITIVE_ROLES, generate_world

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = json.load(open(os.path.join(HERE, "rules.json")))
EXCH = "ABCDEFGH"
STATE = {}

# what a visitor may change when creating a world (everything else keeps the thesis test settings)
WORLD_KEYS = {
    "n_seeds": int, "k_min": int, "k_max": int, "split_spread": float, "mule_window_h": float,
    "cex_share": float, "p_collector": float, "p_framing": float, "p_p2p": float, "p_landlord": float,
    "typologies": list,
}


def _f(x, nd=4):
    x = float(x)
    return None if not np.isfinite(x) else round(x, nd)


def new_world(params="{}"):
    p = json.loads(params) if isinstance(params, str) else dict(params)
    seed = int(p.get("seed", np.random.SeedSequence().entropy % 10**6))
    kw = {}
    if "n_seeds" in p: kw["n_seeds"] = int(p["n_seeds"])
    if "k_min" in p or "k_max" in p:
        lo = int(p.get("k_min", 2)); hi = int(p.get("k_max", 10)); kw["k_range"] = (min(lo, hi), max(lo, hi))
    if "mule_window_h" in p or "split_spread" in p:          # fixed split for every fraud
        kw["split_random"] = False
        kw["send_window_scale"] = float(p.get("mule_window_h", 24.0)) / 24.0
        kw["split_spread"] = float(p.get("split_spread", 0.2))
    for k in ("cex_share", "p_collector", "p_framing", "p_p2p", "p_landlord"):
        if k in p: kw[k] = float(p[k])
    if p.get("typologies"): kw["typologies"] = tuple(p["typologies"])
    cfg = TEST3_CFG.with_(**kw)
    w = generate_world(cfg, np.random.default_rng(seed))
    df = D2.add_ms_columns(candidate_table(w, world_id=seed)).reset_index(drop=True)
    STATE.clear()
    STATE.update(w=w, df=df, seed=seed, cfg=cfg, params=p)
    roles = df.role.value_counts().to_dict()
    frauds = []
    for s, v in sorted(w.seeds.items()):
        d = df[df.seed == s]
        frauds.append(dict(id=int(s), pattern=v["typology"], F=_f(v["F"], 0), k=int(v["k"]),
                           collector=bool(v.get("collector", False)),
                           involved=int(d.role.isin(POSITIVE_ROLES).sum()), accounts=int((d.X >= 100).sum())))
    return json.dumps(dict(seed=seed, frauds=frauds, n_accounts=len(w.accounts), n_rows=len(df),
                           roles={k: int(v) for k, v in roles.items()},
                           settings=dict(n_seeds=cfg.n_seeds, k_range=list(cfg.k_range), split_random=cfg.split_random,
                                         split_spread=cfg.split_spread, mule_window_h=24 * cfg.send_window_scale,
                                         cex_share=cfg.cex_share, p_collector=cfg.p_collector,
                                         typologies=list(cfg.typologies))))


def _rule(spec):
    preset = spec.get("preset", "rev3")
    vis = spec.get("vis", "V3")
    base_name = spec.get("base") or (preset if preset in ("rev2", "rev3") else "rev2")
    base = dict(RULES[base_name][vis])
    for k in ("fan_k", "fan_dt", "fan_ratio"):
        base.setdefault(k, D3.Rule3.__dataclass_fields__[k].default)
    if base_name == "rev2":
        base["fan_k"] = 0
    for k, v in (spec.get("overrides") or {}).items():
        if k in base:
            if k in ("fan_dt", "fan_ratio", "sigma", "sigma_g1", "kappa", "pi", "ms_floor", "x_min", "sigma_dom"):
                base[k] = float(v)
            elif k in ("fan_k", "delta"):
                base[k] = int(v)
            else:
                base[k] = v
    return D3.Rule3(**base), vis


def grade(spec="{}"):
    spec = json.loads(spec) if isinstance(spec, str) else dict(spec)
    df = STATE["df"]
    rule, vis = _rule(spec)
    g1, g2, g3, ch = D3.parts(df, rule, vis)
    grades = g1.astype(int) + g2.astype(int) + g3.astype(int)
    ten = b0(df).values
    flag = ten if spec.get("preset") == "10k" else grades >= 2
    pos, neg = (m.values for m in labels(df))
    sig = df[f"X_{vis}"].values / df.out2.values
    fan_n = D3.fan_counts(df, vis, rule.fan_dt, rule.fan_ratio, rule.x_min,
                          rule.sigma_g1 if rule.sigma_g1 is not None else rule.sigma) if rule.fan_k > 0 else np.zeros(len(df), int)
    STATE.update(rule=rule, vis=vis, grades=grades, flag=flag, ch=ch, sig=sig, fan_n=fan_n, ten=ten,
                 preset=spec.get("preset", "rev3"))

    def metrics(f):
        s = score(df, pd.Series(f, index=df.index))
        return dict(precision=_f(s["precision"]), recall=_f(s["recall"]), value_recall=_f(s["value_recall"]),
                    found=int(s["tp"]), false_alerts=int(s["fp"]), involved=int(pos.sum()))
    by_role = {}
    for r in list(POSITIVE_ROLES) + ["ACCOMPLICE"] + list(NEGATIVE_ROLES):
        m = (df.role == r).values
        if m.any():
            by_role[r] = dict(n=int(m.sum()), flagged=int(flag[m].sum()), rate=_f(flag[m].mean()))
    by_pattern = {}
    for t, d in df[pos].groupby("typology"):
        by_pattern[t] = dict(n=len(d), rate=_f(flag[d.index].mean()))
    fr = pd.DataFrame(dict(seed=df.seed, f=flag & pos, p=pos))
    fr = fr[fr.p].groupby("seed").f.max()
    return json.dumps(dict(rule=_rule_public(rule), vis=vis, preset=spec.get("preset", "rev3"),
                           selected=metrics(flag), g3=metrics(grades >= 3), ten_k=metrics(ten),
                           counts={f"G{i}": int((grades == i).sum()) for i in range(4)},
                           by_role=by_role, by_pattern=by_pattern,
                           frauds_with_one_found=_f(fr.mean()) if len(fr) else None))


def _rule_public(r):
    return dict(g1_share=r.sigma_g1, g2_share=r.sigma, concentration=r.kappa, pass_through=r.pi,
                window_h=r.delta, behaviour_mode=r.mode, second_seed_floor=r.ms_floor,
                fan_k=r.fan_k, fan_window_h=r.fan_dt, fan_ratio=r.fan_ratio, min_amount=r.x_min)


def _reasons(i):
    df, r, vis = STATE["df"], STATE["rule"], STATE["vis"]
    row = df.iloc[i]
    sig = STATE["sig"][i]
    theta = row[f"X_{vis}"] >= min(10_000.0, row.F_known)
    conv = row[f"conv_{vis}"] == 1
    k_ok = row.kappa2 >= r.kappa
    p_ok = row[f"pi_{r.delta}"] >= r.pi
    return dict(
        amount_ok=bool(row.X >= r.x_min), share_g1=bool(sig >= (r.sigma_g1 or r.sigma)), big_amount=bool(theta),
        common_destination=bool(conv), share_g2=bool(sig >= r.sigma), concentration_ok=bool(k_ok),
        pass_through_ok=bool(p_ok), victim=bool(row.v == 1),
        dominant=bool(sig >= r.sigma_dom and p_ok), fan_siblings=int(STATE["fan_n"][i]),
        fan_route=bool(STATE["ch"].get("fan_route", np.zeros(len(df), bool))[i]),
        same_person_other_exchange=bool(row[f"nex_{vis}"] >= 2), second_seed=bool(row[D2.ms_column(r)] >= 2))


def fraud_graph(fraud_id):
    """Nodes and links for one fraud: the blacklisted address, its collector if any, every account that
    received at least 100 EUR from it, and one summary node for the smaller receivers."""
    df, w = STATE["df"], STATE["w"]
    s = int(fraud_id)
    sd = w.seeds[s]
    d = df[df.seed == s]
    big = d[d.X >= 100]
    small = d[d.X < 100]
    nodes = [dict(id="seed", kind="seed", pattern=sd["typology"], F=_f(sd["F"], 0), F_known=_f(sd["F_known"], 0),
                  sent=_f(sd["out"], 0), k=int(sd["k"]), blacklisted_h=_f(sd["tau"], 1),
                  collector=bool(sd.get("collector", False)))]
    links = []
    src = "seed"
    if sd.get("collector", False):
        nodes.append(dict(id="collector", kind="collector", found=bool(sd.get("intermediary_detected", True))))
        links.append(dict(source="seed", target="collector"))
        src = "collector"
    groups = {}
    for i in big.index:
        row = df.loc[i]
        g = int(STATE["grades"][i])
        nodes.append(dict(
            id=f"a{int(row.aid)}", kind="account", aid=int(row.aid), exchange=EXCH[int(row.exch)], role=row.role,
            grade=g, ten_k=bool(STATE["ten"][i]), X=_f(row.X, 0), share=_f(STATE["sig"][i]), concentration=_f(row.kappa2),
            pass_24h=_f(row.pi_24), pass_7d=_f(row.pi_168), t_first_h=_f(row.t_first, 1), age_days=_f(row.age_days, 0),
            n_tx=int(row.n_tx), months=int(row.n_months), fiat_share=_f(row.fiat_share),
            reasons=_reasons(df.index.get_loc(i))))
        links.append(dict(source=src, target=f"a{int(row.aid)}", amount=_f(row.X, 0)))
        groups.setdefault(row[f"g_{STATE['vis']}"] if STATE["vis"] != "V1" else row.aid, []).append(f"a{int(row.aid)}")
    if len(small):
        nodes.append(dict(id="small", kind="small", n=int(len(small)), total=_f(small.X.sum(), 0),
                          roles={k: int(v) for k, v in small.role.value_counts().items()}))
        links.append(dict(source=src, target="small"))
    same_person = [ids for ids in groups.values() if len(ids) > 1]
    return json.dumps(dict(fraud=s, nodes=nodes, links=links, same_person=same_person))


def sample_rows(n=12, seed=0):
    df = STATE["df"]
    rng = np.random.default_rng(seed)
    pick = []
    for r in ["SELF", "MULE", "FACILITATOR", "P2P", "VICTIM", "SERVICE", "ACCOMPLICE", "DUST", "FRAMED", "LANDLORD"]:
        idx = df.index[(df.role == r).values]
        if len(idx):
            pick.append(int(rng.choice(idx)))
    pick = pick[:n]
    out = []
    for i in pick:
        row = df.loc[i]
        out.append(dict(fraud=int(row.seed), account=int(row.aid), exchange=EXCH[int(row.exch)], X=_f(row.X, 0),
                        share=_f(row.sigma2), concentration=_f(row.kappa2), pass_24h=_f(row.pi_24),
                        victim=int(row.v), age_days=_f(row.age_days, 0), second_seed=int(row.ms_5),
                        grade=int(STATE["grades"][i]) if "grades" in STATE else None, role=row.role))
    return json.dumps(out)
