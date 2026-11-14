"""Evidence grades, second test (realistic parameters).

Differences with the pilot rule (detectors.py), all decided before this test:
  - seed share divides by max(money the seed sent, known fraud total)   (sigma2 / out2)
  - concentration counts fraud money and income over the same +-15 days (kappa2)
  - second-seed floor 1% instead of 2%                                    (ms_count1)
  - repetition: >= EUR 100 from the same seed in `rep_months` separate months, G3 clue only
    (an optional G2 route, rep_route, is reported separately)
  - candidate G2 route "amount": X >= min(10k, fraud total) AND pass-through
  - longer pass-through windows (14 and 30 days) and lower seed-share values in the search
"""
from __future__ import annotations

import itertools
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from detectors import THETA, labels, score


@dataclass(frozen=True)
class Rule:
    sigma: float = 0.01
    kappa: float = 0.5
    pi: float = 0.7
    delta: int = 168
    mode: str = "AND"
    x_min: float = 100.0
    sigma_dom: float = 0.2
    amount_route: bool = False
    rep_months: int = 2
    use_sigma: bool = True
    use_kappa: bool = True
    use_pi: bool = True
    use_v: bool = True
    use_dom: bool = True
    conv_entry: bool = True
    g3_rep: bool = True
    rep_route: bool = False        # option: repetition + pass-through opens G2
    # revision 2 (declared after test worlds C, evaluated on fresh worlds D)
    sigma_g1: float | None = None  # fixed G1 floor (1%); `sigma` then becomes the G2 share requirement
    ms_floor: float = 0.01         # second-seed floor, chosen on calibration worlds
    # revision 4 (supervisor review, 12 Nov 2026): the amount branch is X >= 10k only, without 'or the whole fraud'
    whole_fraud: bool = True
    # 14 Nov 2026: G2 share relative to the seed's money that reaches our exchanges (add_rel_columns), not to all it sent
    rel_share: bool = False


def amount_ok(Xv, df, p) -> np.ndarray:
    """Amount branch: X >= min(10k, known fraud total) (revisions 1-3) or X >= 10k (revision 4)."""
    floor = np.minimum(THETA, df.F_known.values) if getattr(p, "whole_fraud", True) else THETA
    return Xv >= floor


def ms_column(p: Rule) -> str:
    return "ms_count1" if p.ms_floor == 0.01 else f"ms_{int(round(p.ms_floor * 100))}"


def add_ms_columns(df: pd.DataFrame, floors=(0.02, 0.05, 0.10), x_min=100.0) -> pd.DataFrame:
    """Number of different seeds that each paid the account at least `floor` of their money."""
    for f in floors:
        big = df[(df.sigma2 >= f) & (df.X >= x_min)]
        n = big.groupby(["world", "aid"]).seed.nunique()
        df[f"ms_{int(round(f * 100))}"] = pd.MultiIndex.from_arrays([df.world, df.aid]).map(n).fillna(0).astype(int).values
    return df


def add_rel_columns(df: pd.DataFrame) -> pd.DataFrame:
    """cex_V3: money of the seed that reaches all our exchanges (known through the sharing protocol);
    cex_V1: money of the seed that reaches the account's own exchange."""
    df = df.copy()
    df["cex_V3"] = df.groupby(["world", "seed"]).X.transform("sum").values
    df["cex_V1"] = df.groupby(["world", "seed", "exch"]).X.transform("sum").values
    return df


def _parts(df: pd.DataFrame, p: Rule, vis: str):
    Xv = df[f"X_{vis}"].values
    sig1 = Xv / df.out2.values
    sig = (Xv / df[f"cex_{'V3' if vis in ('V2', 'V3', 'V4') else 'V1'}"].values) if getattr(p, "rel_share", False) else sig1
    x_ok = df.X.values >= p.x_min
    theta_b = amount_ok(Xv, df, p)
    s_g1 = p.sigma if p.sigma_g1 is None else p.sigma_g1
    g1a = ((sig1 >= s_g1) if p.use_sigma else np.zeros(len(df), bool)) | theta_b
    share2 = ((sig >= (p.sigma if getattr(p, "rel_share", False) else max(p.sigma, s_g1))) if p.use_sigma else np.zeros(len(df), bool)) | theta_b
    conv = df[f"conv_{vis}"].values == 1
    g1 = x_ok & (g1a | (conv & p.conv_entry))
    g2_share = share2 | (conv & p.conv_entry)
    pi_ok = df[f"pi_{p.delta}"].values >= p.pi
    k_ok = df.kappa2.values >= p.kappa
    if p.use_kappa and p.use_pi:
        beh = (k_ok & pi_ok) if p.mode == "AND" else (k_ok | pi_ok)
    elif p.use_kappa:
        beh = k_ok
    elif p.use_pi:
        beh = pi_ok
    else:
        beh = np.ones(len(df), bool)
    nv = (df.v.values == 0) if p.use_v else np.ones(len(df), bool)
    rep = df.n_months.values >= p.rep_months
    dom = (sig >= p.sigma_dom) & pi_ok if p.use_dom else np.zeros(len(df), bool)
    amt = theta_b & pi_ok if p.amount_route else np.zeros(len(df), bool)
    rr = rep & pi_ok if p.rep_route else np.zeros(len(df), bool)
    g2 = g1 & g2_share & (beh | dom | amt | rr) & nv
    ch = dict(same_person=df[f"nex_{vis}"].values >= 2,
              second_seed=df[ms_column(p)].values >= 2,
              common_dest=conv & g1a,
              repetition=rep & p.g3_rep)
    g3 = g2 & (ch["same_person"] | ch["second_seed"] | ch["common_dest"] | ch["repetition"])
    return g1, g2, g3, ch


def grades(df: pd.DataFrame, p: Rule, vis: str = "V3") -> pd.Series:
    g1, g2, g3, _ = _parts(df, p, vis)
    return pd.Series(g1.astype(int) + g2.astype(int) + g3.astype(int), index=df.index)


def g3_channels(df, p, vis="V3"):
    _, _, g3, ch = _parts(df, p, vis)
    return {k: g3 & v for k, v in ch.items()}


GRID = dict(
    sigma=[0.005, 0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3],
    kappa=[0.05, 0.1, 0.2, 0.3, 0.5, 0.7],
    pi=[0.3, 0.5, 0.7, 0.9],
    delta=[1, 24, 168, 336, 720],
    mode=["AND", "OR"],
    sigma_dom=[0.1, 0.15, 0.2, 0.3, 0.5, 1.01],
    amount_route=[False, True],
)


def calibrate(df: pd.DataFrame, vis: str = "V3", target_precision: float = 0.90,
              base: Rule = Rule(), grid=GRID, keep=()):
    """Highest G2 recall subject to the precision target (vectorised; checked against grades())."""
    keys = [k for k in grid if k not in keep]
    pos_all, neg_all = (m.values for m in labels(df))
    npos = pos_all.sum()
    # rows that can never reach G2 do not change the result: drop them once
    Xv = df[f"X_{vis}"].values
    sig_all = Xv / df.out2.values
    theta_all = amount_ok(Xv, df, base)
    conv_all = df[f"conv_{vis}"].values == 1
    nv_all = (df.v.values == 0) if base.use_v else np.ones(len(df), bool)
    smin = min(grid["sigma"]) if "sigma" in keys else base.sigma
    live = (df.X.values >= base.x_min) & ((sig_all >= smin) | theta_all | conv_all) & nv_all & (pos_all | neg_all)
    d = df[live]
    pos, neg = pos_all[live], neg_all[live]
    sig = sig_all[live]; theta_b = theta_all[live]; conv = conv_all[live] & base.conv_entry
    kap = d.kappa2.values
    pis = {dl: d[f"pi_{dl}"].values for dl in grid["delta"]}
    rep = d.n_months.values >= base.rep_months
    best, best_key = None, None
    for vals in itertools.product(*(grid[k] for k in keys)):
        p = Rule(**{**asdict(base), **dict(zip(keys, vals))})
        s_eff = p.sigma if p.sigma_g1 is None else max(p.sigma, p.sigma_g1)
        g1a = ((sig >= s_eff) if p.use_sigma else False) | theta_b
        g1 = g1a | conv
        pi_ok = pis[p.delta] >= p.pi
        k_ok = kap >= p.kappa
        if p.use_kappa and p.use_pi:
            beh = (k_ok & pi_ok) if p.mode == "AND" else (k_ok | pi_ok)
        elif p.use_kappa:
            beh = k_ok
        elif p.use_pi:
            beh = pi_ok
        else:
            beh = np.ones(len(d), bool)
        f = beh
        if p.use_dom:
            f = f | ((sig >= p.sigma_dom) & pi_ok)
        if p.amount_route:
            f = f | (theta_b & pi_ok)
        if p.rep_route:
            f = f | (rep & pi_ok)
        f = g1 & f
        tp = (f & pos).sum(); fp = (f & neg).sum()
        if tp + fp == 0:
            continue
        prec, rec = tp / (tp + fp), tp / npos
        if prec < target_precision:
            continue
        # ties: higher precision, then the simpler rule (no amount route), then the middle window
        key = (round(rec, 4), round(prec, 4), -int(p.amount_route), -abs(p.delta - 168))
        if best_key is None or key > best_key:
            best, best_key = p, key
    if best is None:
        return None
    s = score(df, grades(df, best, vis) >= 2)
    assert abs(s["recall"] - best_key[0]) < 1e-3, "fast path disagrees with grades()"
    return best, s


def calibrate_g3(df, p: Rule, vis="V3", target=0.99, months=(2, 3)):
    """Choose the repetition month count: highest G3 recall with G3 precision >= target."""
    best, key = None, None
    for m in months:
        q = Rule(**{**asdict(p), "rep_months": m})
        s = score(df, grades(df, q, vis) == 3)
        if s["precision"] >= target and (key is None or (s["recall"], s["precision"]) > key):
            best, key = q, (s["recall"], s["precision"])
    return best or Rule(**{**asdict(p), "rep_months": max(months)})


def choose_ms_floor(df, p: Rule, vis="V3", floors=(0.01, 0.02, 0.05, 0.10), target=0.99):
    """Lowest second-seed floor whose G3 channel reaches the precision target on calibration worlds."""
    pos, _ = labels(df)
    for f in floors:
        q = Rule(**{**asdict(p), "ms_floor": f})
        ch = g3_channels(df, q, vis)["second_seed"]
        if ch.sum() == 0 or pos[ch].mean() >= target:
            return q, (int(ch.sum()), float(pos[ch].mean()) if ch.sum() else float("nan"))
    return Rule(**{**asdict(p), "ms_floor": floors[-1]}), None
