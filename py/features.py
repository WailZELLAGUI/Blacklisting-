"""Indicators for every (seed, account) pair with traced exposure.

Tracing rule: direct deposits from a detected seed-cluster address are
traced; inside an account, value is followed with FIFO lots, so a
customer's earlier balance leaves before the traced value does.
"""
from __future__ import annotations

from collections import deque, defaultdict

import numpy as np
import pandas as pd

from sim import DAY, World

DELTAS = (1.0, 24.0, 168.0)          # exit delays for pass-through, hours
KAPPA_HALF_WINDOW = 15 * DAY
EPS = 1e-9


def _fifo_account(world: World, aid: int, keep_timeline: bool = False):
    a = world.accounts[aid]
    evs = sorted(world.events.get(aid, []))
    lots = deque()
    bal = float(a.get("prior", 0.0))
    if bal > 0:
        lots.append([bal, None, -1e9])
    per_seed = {}
    paid_seed = {}
    in_t, in_v = [], []
    for t, _prio, _o, kind, amt, info in evs:
        if kind in ("in", "in_seed"):
            tag = None
            if kind == "in_seed":
                s, detected = info
                if detected:
                    tag = s
                    d = per_seed.setdefault(s, dict(X=0.0, t_first=t, n_tx=0,
                                                    exited={dd: 0.0 for dd in DELTAS},
                                                    fiat=0.0, crypto=0.0, dests=set(),
                                                    rec=[], ex=[]))
                    d["X"] += amt
                    d["rec"].append((t, amt))
                    d["n_tx"] += 1
                    d["t_first"] = min(d["t_first"], t)
            lots.append([amt, tag, t])
            bal += amt
            in_t.append(t)
            in_v.append(amt)
            continue
        # exits
        if kind == "exit_frac":
            amount = bal * amt
            dest, etype = info
        elif kind == "exit_amt":
            amount = min(amt, bal)
            dest, etype = info
        elif kind == "pay_seed":
            s, etype = info
            dest = f"seed{s}"
            amount = min(amt, bal)
            paid_seed.setdefault(s, t)
        else:
            raise ValueError(kind)
        amount = min(amount, bal)
        bal -= amount
        while amount > EPS and lots:
            lot = lots[0]
            take = min(lot[0], amount)
            if lot[1] is not None:
                d = per_seed[lot[1]]
                d["ex"].append((t, take, t - lot[2]))
                age = t - lot[2]
                for dd in DELTAS:
                    if age <= dd:
                        d["exited"][dd] += take
                if etype == "fiat":
                    d["fiat"] += take
                else:
                    d["crypto"] += take
                    if dest is not None:
                        d["dests"].add(dest)
            lot[0] -= take
            amount -= take
            if lot[0] <= EPS:
                lots.popleft()
    in_t = np.asarray(in_t)
    in_v = np.asarray(in_v)
    order = np.argsort(in_t)
    in_t, cum = in_t[order], np.concatenate([[0.0], np.cumsum(in_v[order])])
    rows = []
    for s, d in per_seed.items():
        lo = np.searchsorted(in_t, d["t_first"] - KAPPA_HALF_WINDOW, "left")
        hi = np.searchsorted(in_t, d["t_first"] + KAPPA_HALF_WINDOW, "right")
        inflow = cum[hi] - cum[lo]
        rec_t = np.array([r[0] for r in d["rec"]]); rec_v = np.array([r[1] for r in d["rec"]])
        in_win = np.abs(rec_t - d["t_first"]) <= KAPPA_HALF_WINDOW
        x_win = float(rec_v[in_win].sum())
        bins = defaultdict(float)
        for tt, vv in d["rec"]:
            bins[int(tt // (30 * DAY))] += vv
        ex_age = np.array([e[2] for e in d["ex"]]) if d["ex"] else np.zeros(0)
        ex_val = np.array([e[1] for e in d["ex"]]) if d["ex"] else np.zeros(0)
        extra = {f"pi_{int(dd)}": float(ex_val[ex_age <= dd].sum()) / d["X"] for dd in (336.0, 720.0)}
        if keep_timeline:
            extra["timeline_rec"] = tuple(d["rec"])
            extra["timeline_ex"] = tuple((e[0], e[1]) for e in d["ex"])
        rows.append(dict(
            kappa2=x_win / max(inflow, EPS),
            n_months=sum(1 for v in bins.values() if v >= 100.0),
            **extra,
            seed=s, aid=aid, X=d["X"], n_tx=d["n_tx"], t_first=d["t_first"],
            kappa=d["X"] / max(inflow, EPS),
            **{f"pi_{int(dd)}": d["exited"][dd] / d["X"] for dd in DELTAS},
            fiat_share=d["fiat"] / d["X"],
            v=int(s in paid_seed and paid_seed[s] < d["t_first"]),
            age_days=(d["t_first"] - a["open_t"]) / DAY,
            dests=frozenset(d["dests"]),
        ))
    return rows


def _groups(keys):
    """Union-find over records sharing any key. keys: list of lists."""
    parent = list(range(len(keys)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    first = {}
    for i, ks in enumerate(keys):
        for k in ks:
            if k in first:
                ri, rj = find(i), find(first[k])
                if ri != rj:
                    parent[ri] = rj
            else:
                first[k] = i
    return [find(i) for i in range(len(keys))]


def candidate_table(world: World, world_id: int = 0, x_min: float = 100.0, keep_timeline: bool = False) -> pd.DataFrame:
    """One row per (seed, account) with traced value > 0."""
    rows = []
    involved = {aid for (_, aid) in world.truth}
    for aid in involved:
        rows.extend(_fifo_account(world, aid, keep_timeline))
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    acc = world.accounts
    df["exch"] = df.aid.map(lambda a: acc[a]["exch"])
    df["iid"] = df.aid.map(lambda a: acc[a]["iid"])
    df["pid"] = df.aid.map(lambda a: acc[a]["pid"])
    df["key2"] = df.aid.map(lambda a: acc[a]["key2"])
    df["profile"] = df.aid.map(lambda a: acc[a]["profile"])
    df["role"] = [world.truth.get((s, a), "UNKNOWN") for s, a in zip(df.seed, df.aid)]
    sd = world.seeds
    df["F"] = df.seed.map(lambda s: sd[s]["F"])
    df["F_known"] = df.seed.map(lambda s: sd[s]["F_known"])
    df["typology"] = df.seed.map(lambda s: sd[s]["typology"])
    df["out"] = df.seed.map(lambda s: sd[s]["out"])
    df["theta_f"] = np.minimum(10_000.0, df.F_known)
    df["sigma"] = df.X / df.out
    df["out2"] = np.maximum(df.out, df.F_known)          # second test: max(money sent, known fraud total)
    df["sigma2"] = df.X / df.out2
    df["t_dist"] = df.seed.map(lambda s: sd[s]["t_dist"])
    df["collector"] = df.seed.map(lambda s: sd[s].get("collector", False))
    df["coll_found"] = df.seed.map(lambda s: sd[s].get("intermediary_detected", True))
    df["world"] = world_id

    # identity aggregation per seed under each visibility regime
    df["g_V2"] = df.seed.astype(str) + "|" + df.pid                       # paper: same document hash
    gid = np.empty(len(df), dtype=object)
    for s, idx in df.groupby("seed").groups.items():
        sub = df.loc[idx]
        g = _groups([[p, k] for p, k in zip(sub.pid, sub.key2)])
        gid[df.index.get_indexer(idx)] = [f"{s}|{x}" for x in g]
    df["g_V3"] = gid                                                         # document OR second key
    df["g_V4"] = df.seed.astype(str) + "|" + df.iid.astype(str)            # true identity (oracle)
    for v in ("V2", "V3", "V4"):
        g = df.groupby(f"g_{v}")
        df[f"X_{v}"] = g.X.transform("sum")
        df[f"nex_{v}"] = g.exch.transform("nunique")
    df["X_V1"] = df.X
    df["nex_V1"] = 1

    # multi-seed exposure (local to the account)
    big = df[(df.sigma >= 0.02) & (df.X >= x_min)]
    ms = big.groupby("aid").seed.nunique()
    df["ms_count"] = df.aid.map(ms).fillna(0).astype(int)
    big1 = df[(df.sigma2 >= 0.01) & (df.X >= x_min)]               # second test: 1% floor
    df["ms_count1"] = df.aid.map(big1.groupby("aid").seed.nunique()).fillna(0).astype(int)

    # convergence: shared unlabelled crypto destination with another recipient of the same seed
    labelled = {lab for lab, is_lab in world.popular if is_lab}
    df["conv_V1"] = 0
    df["conv_V3"] = 0
    elig = df.X >= x_min
    for s, idx in df[elig].groupby("seed").groups.items():
        sub = df.loc[idx]
        dest_owners = defaultdict(list)
        for i, aid, ex, ds in zip(sub.index, sub.aid, sub.exch, sub.dests):
            for d in ds:
                if d not in labelled:
                    dest_owners[d].append((i, aid, ex))
        for owners in dest_owners.values():
            if len({o[1] for o in owners}) < 2:
                continue
            for i, aid, ex in owners:
                df.at[i, "conv_V3"] = 1
                if any(o[2] == ex and o[1] != aid for o in owners):
                    df.at[i, "conv_V1"] = 1
    df["conv_V2"] = df.conv_V1
    df["conv_V4"] = df.conv_V3
    return df.drop(columns=["dests"])


def world_tables(cfg, seeds, x_min=100.0, keep_timeline=False, return_plus2=False):
    from sim import generate_world
    out, p2 = [], []
    for i, sd in enumerate(seeds):
        w = generate_world(cfg, np.random.default_rng(sd))
        out.append(candidate_table(w, world_id=sd, x_min=x_min, keep_timeline=keep_timeline))
        if return_plus2 and w.plus2:
            t = pd.DataFrame(w.plus2)
            t["world"] = sd
            t["src_exch"] = t.src.map(lambda a: w.accounts[a]["exch"])
            p2.append(t)
    df = pd.concat(out, ignore_index=True)
    if return_plus2:
        return df, (pd.concat(p2, ignore_index=True) if p2 else pd.DataFrame())
    return df
