"""Baselines (the paper's EUR 10,000 rule) and the proposed evidence tiers."""
from __future__ import annotations

import itertools
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd

from sim import POSITIVE_ROLES, NEGATIVE_ROLES

THETA = 10_000.0


# ---------------------------------------------------------------- baselines
def b0(df: pd.DataFrame, theta: float = THETA) -> pd.Series:
    """Paper, intra-exchange: account receives >= min(theta, F) from the seed."""
    return df.X >= np.minimum(theta, df.F_known)


def b1(df: pd.DataFrame, theta: float = THETA) -> pd.Series:
    """Paper, inter-exchange: PID (same document hash) total >= min(theta, F)."""
    return df.X_V2 >= np.minimum(theta, df.F_known)


def b2(df: pd.DataFrame) -> pd.Series:
    """Flag every exposed account (recall ceiling, precision floor)."""
    return df.X > 0


# ---------------------------------------------------------------- tiers
@dataclass(frozen=True)
class TierParams:
    sigma: float = 0.05
    kappa: float = 0.3
    pi: float = 0.5
    delta: int = 24
    mode: str = "AND"          # how kappa and pi combine at G2
    x_min: float = 100.0
    use_sigma: bool = True
    use_kappa: bool = True
    use_pi: bool = True
    use_v: bool = True
    conv_entry: bool = True    # convergence can open G1 (multi-identity splits)
    g3_channels: bool = True
    sigma_dom: float = 1.01    # revision 1: a dominant recipient that passes value on
                               # reaches G2 without the concentration test (>1 = off)


def grades(df: pd.DataFrame, p: TierParams, vis: str = "V3") -> pd.Series:
    """Return the grade 0..3 for every candidate under visibility regime vis."""
    Xv = df[f"X_{vis}"]
    sigma_v = Xv / df.out
    x_ok = df.X >= p.x_min
    conv = df[f"conv_{vis}"] == 1
    g1_amount = (sigma_v >= p.sigma) if p.use_sigma else pd.Series(False, index=df.index)
    g1_amount = g1_amount | (Xv >= np.minimum(THETA, df.F_known))
    g1_conv = conv if p.conv_entry else pd.Series(False, index=df.index)
    g1 = x_ok & (g1_amount | g1_conv)
    k_ok = df.kappa >= p.kappa if p.use_kappa else None
    p_ok = df[f"pi_{p.delta}"] >= p.pi if p.use_pi else None
    if k_ok is None and p_ok is None:
        beh = pd.Series(True, index=df.index)
    elif k_ok is None:
        beh = p_ok
    elif p_ok is None:
        beh = k_ok
    else:
        beh = (k_ok & p_ok) if p.mode == "AND" else (k_ok | p_ok)
    not_victim = (df.v == 0) if p.use_v else pd.Series(True, index=df.index)
    dominant = (sigma_v >= p.sigma_dom) & (df[f"pi_{p.delta}"] >= p.pi)
    g2 = g1 & (beh | dominant) & not_victim
    if p.g3_channels:
        pid_cross = df[f"nex_{vis}"] >= 2
        multi = df.ms_count >= 2
        # convergence counts at G3 only if G1 was not opened by convergence alone
        conv_g3 = conv & g1_amount
        g3 = g2 & (pid_cross | multi | conv_g3)
    else:
        g3 = pd.Series(False, index=df.index)
    return g1.astype(int) + g2.astype(int) + g3.astype(int)


# ---------------------------------------------------------------- scoring
def labels(df):
    pos = df.role.isin(POSITIVE_ROLES)
    neg = df.role.isin(NEGATIVE_ROLES)
    return pos, neg


def score(df: pd.DataFrame, flagged: pd.Series) -> dict:
    pos, neg = labels(df)
    tp = int((flagged & pos).sum())
    fp = int((flagged & neg).sum())
    n_pos = int(pos.sum())
    prec = tp / (tp + fp) if tp + fp else np.nan
    rec = tp / n_pos if n_pos else np.nan
    vrec = df.X[flagged & pos].sum() / df.X[pos].sum() if n_pos else np.nan
    seeds = df.groupby(["world", "seed"]).ngroups
    out = dict(precision=prec, recall=rec, value_recall=vrec, tp=tp, fp=fp,
               alerts_per_seed=(tp + fp) / seeds,
               fp_per_seed=fp / seeds)
    acc = df.role == "ACCOMPLICE"
    out["accomplice_rate"] = float(flagged[acc].mean()) if acc.any() else np.nan
    for r in NEGATIVE_ROLES:
        m = df.role == r
        out[f"fpr_{r}"] = float(flagged[m].mean()) if m.any() else np.nan
    return out


# ---------------------------------------------------------------- calibration
GRID = dict(
    sigma=[0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3],
    kappa=[0.05, 0.1, 0.2, 0.3, 0.5, 0.7],
    pi=[0.3, 0.5, 0.7, 0.9],
    delta=[1, 24, 168],
    mode=["AND", "OR"],
    sigma_dom=[0.2, 0.3, 0.5, 1.01],
)


def calibrate(df: pd.DataFrame, vis: str, target_precision: float = 0.90,
              base: TierParams = TierParams(), grid=GRID, keep=None):
    """Pick the tier thresholds that maximise recall at G2 subject to a precision target.

    Ties are broken towards higher precision, then towards the middle delta (stability).
    `keep` lists fields that stay at their value in `base` (for ablations).
    Vectorised re-implementation of grades() >= 2; checked against it below.
    """
    keys = [k for k in grid if not (keep and k in keep)]
    pos, neg = (m.values for m in labels(df))
    Xv = df[f"X_{vis}"].values
    sig = Xv / df.out.values
    x_ok = df.X.values >= base.x_min
    theta_b = Xv >= np.minimum(THETA, df.F_known.values)
    conv = (df[f"conv_{vis}"].values == 1) & base.conv_entry
    kap = df.kappa.values
    pis = {d: df[f"pi_{d}"].values for d in grid["delta"]}
    nv = (df.v.values == 0) if base.use_v else np.ones(len(df), bool)
    npos = pos.sum()
    best, best_key = None, None
    for vals in itertools.product(*(grid[k] for k in keys)):
        p = TierParams(**{**asdict(base), **dict(zip(keys, vals))})
        g1a = ((sig >= p.sigma) if p.use_sigma else False) | theta_b
        g1 = x_ok & (g1a | conv)
        pi_ok = pis[p.delta] >= p.pi
        k_ok = kap >= p.kappa
        if p.use_kappa and p.use_pi:
            beh = (k_ok & pi_ok) if p.mode == "AND" else (k_ok | pi_ok)
        elif p.use_kappa:
            beh = k_ok
        elif p.use_pi:
            beh = pi_ok
        else:
            beh = np.ones(len(df), bool)
        dom = (sig >= p.sigma_dom) & pi_ok
        f = g1 & (beh | dom) & nv
        tp = (f & pos).sum(); fp = (f & neg).sum()
        if tp + fp == 0:
            continue
        prec, rec = tp / (tp + fp), tp / npos
        if prec < target_precision:
            continue
        key = (round(rec, 4), round(prec, 4), -abs(p.delta - 24))
        if best_key is None or key > best_key:
            best, best_key = p, key
    if best is None:
        return None
    s = score(df, grades(df, best, vis) >= 2)
    assert abs(s["recall"] - best_key[0]) < 1e-3, "fast path disagrees with grades()"
    return best, s
