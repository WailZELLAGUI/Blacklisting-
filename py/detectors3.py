"""Evidence grades, revision 3: an optional fan-out route to G2.

Declared before any run on fresh worlds (see README, "Revision 3"):
  - Why: on test worlds D, 578 mules passed the behaviour test but were stopped by the G2 seed-share
    floor (15 %), because the fraud was split between several mules (critique_diagnostics.md).
  - What: an account at G1 that passes the behaviour test and is not a victim also reaches G2 if at
    least `fan_k` OTHER accounts of the same seed received a similar amount (larger / smaller <= fan_ratio)
    within `fan_dt` hours of it. Sources: fraud proceeds are "broken into smaller amounts and dispersed
    across multiple accounts" (Vocalink/Mastercard, The rise of the mule, 2019) and "split into smaller
    transactions" (FCA multi-firm review of mule activity, 2026); fast fan-in/fan-out is the first trait of
    laundering agents in real bank data (MonLAD, Sun et al. 2022).
  - Who sees the siblings: one exchange alone (V1) and identity sharing (V2) see only siblings at the same
    exchange; our protocol (V3) and the oracle (V4) see all exchanges, which requires the protocol to share,
    per case pseudonym, the amount and time of each receipt.
  - The three numbers are not fixed by hand: fan_k, fan_dt and fan_ratio are chosen by the same search as
    the other thresholds (highest G2 recall with precision >= 90 % on calibration worlds), with "no route"
    as an option. Search ranges: fan_dt 1 h - 7 days (sources describe moves within minutes to hours and
    a dispersion tree over 18.5 h; Elliptic describes "staggered settlement" across time windows);
    fan_ratio 1.1 - 3 (no quantitative source; the one documented dispersion tree shows unequal amounts).
"""
from __future__ import annotations

import itertools
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

import detectors2 as D2
from detectors import THETA, labels, score

FAN_GRID = dict(fan_k=[1, 2, 3], fan_dt=[1, 6, 24, 72, 168], fan_ratio=[1.1, 1.3, 1.5, 2.0, 3.0])


@dataclass(frozen=True)
class Rule3(D2.Rule):
    fan_k: int = 0          # 0 = no fan-out route
    fan_dt: float = 24.0    # hours
    fan_ratio: float = 1.3  # larger amount / smaller amount


def rule2_part(p: Rule3) -> D2.Rule:
    d = asdict(p)
    for k in ("fan_k", "fan_dt", "fan_ratio"):
        d.pop(k)
    return D2.Rule(**d)


def fan_counts(df: pd.DataFrame, vis: str, dt: float, ratio: float, x_min=100.0, s_floor=0.01) -> np.ndarray:
    """For each row: number of OTHER accounts of the same seed (same exchange under V1/V2) that received
    at least x_min and at least s_floor of the seed's money, within dt hours and within `ratio` in amount."""
    sig = df[f"X_{vis}"].values / df.out2.values
    el = (df.X.values >= x_min) & (sig >= s_floor)
    keys = ["world", "seed"] if vis in ("V3", "V4") else ["world", "seed", "exch"]
    n = np.zeros(len(df), dtype=int)
    t_all, x_all = df.t_first.values, df.X.values
    pos_index = {ix: i for i, ix in enumerate(df.index)}
    for _, idx in df[el].groupby(keys).groups.items():
        if len(idx) < 2:
            continue
        ii = np.fromiter((pos_index[j] for j in idx), int, len(idx))
        t, x = t_all[ii], x_all[ii]
        m = (np.abs(t[:, None] - t[None, :]) <= dt) & \
            (np.maximum(x[:, None], x[None, :]) / np.minimum(x[:, None], x[None, :]) <= ratio)
        np.fill_diagonal(m, False)
        n[ii] = m.sum(1)
    return n


_FAN_CACHE: dict = {}


def fan_mask(df, p: Rule3, vis):
    if p.fan_k <= 0:
        return np.zeros(len(df), bool)
    key = (id(df), len(df), float(np.nansum(df.t_first.values)), vis, p.fan_dt, p.fan_ratio, p.x_min,
           p.sigma_g1 if p.sigma_g1 is not None else p.sigma)
    if key not in _FAN_CACHE:
        _FAN_CACHE[key] = fan_counts(df, vis, p.fan_dt, p.fan_ratio, p.x_min, key[-1])
    return _FAN_CACHE[key] >= p.fan_k


def parts(df: pd.DataFrame, p: Rule3, vis: str):
    g1, g2, g3, ch = D2._parts(df, rule2_part(p), vis)
    if p.fan_k > 0:
        beh = (df.kappa2.values >= p.kappa) | (df[f"pi_{p.delta}"].values >= p.pi) if p.mode == "OR" else \
              (df.kappa2.values >= p.kappa) & (df[f"pi_{p.delta}"].values >= p.pi)
        nv = (df.v.values == 0) if p.use_v else np.ones(len(df), bool)
        fan = g1 & beh & nv & fan_mask(df, p, vis)
        g2 = g2 | fan
        g3 = g2 & (ch["same_person"] | ch["second_seed"] | ch["common_dest"] | ch["repetition"])
        ch = {**ch, "fan_route": fan}
    return g1, g2, g3, ch


def grades(df, p: Rule3, vis="V3") -> pd.Series:
    g1, g2, g3, _ = parts(df, p, vis)
    return pd.Series(g1.astype(int) + g2.astype(int) + g3.astype(int), index=df.index)


def calibrate(df, vis="V3", target_precision=0.90, base: Rule3 = Rule3(), grid=None, fan_grid=FAN_GRID):
    """Revision 3 search: the revision-2 grid times the fan-out grid (plus 'no route').
    Highest G2 recall subject to precision >= target on calibration worlds."""
    grid = grid or D2.GRID
    keys = list(grid)
    pos_all, neg_all = (m.values for m in labels(df))
    npos = pos_all.sum()
    Xv = df[f"X_{vis}"].values
    sig_all = Xv / df.out2.values
    theta_all = Xv >= np.minimum(THETA, df.F_known.values)
    conv_all = df[f"conv_{vis}"].values == 1
    nv_all = (df.v.values == 0) if base.use_v else np.ones(len(df), bool)
    g1floor = base.sigma_g1 if base.sigma_g1 is not None else min(grid["sigma"])
    live = (df.X.values >= base.x_min) & ((sig_all >= min(min(grid["sigma"]), g1floor)) | theta_all | conv_all) \
        & nv_all & (pos_all | neg_all)
    d = df[live]
    pos, neg = pos_all[live], neg_all[live]
    sig = sig_all[live]; theta_b = theta_all[live]; conv = conv_all[live] & base.conv_entry
    kap = d.kappa2.values
    pis = {dl: d[f"pi_{dl}"].values for dl in grid["delta"]}
    rep = d.n_months.values >= base.rep_months
    g1row = (sig >= g1floor) | theta_b | conv                      # G1 with the fixed floor
    # fan-out settings: one row of the matrix per (k, dt, ratio)
    fan_settings = [(0, 24.0, 1.3)] + list(itertools.product(fan_grid["fan_k"], fan_grid["fan_dt"], fan_grid["fan_ratio"]))
    counts = {}
    for _, dt, r in fan_settings[1:]:
        if (dt, r) not in counts:
            counts[(dt, r)] = fan_counts(df, vis, dt, r, base.x_min, g1floor)[live]
    FM = np.zeros((len(fan_settings), len(d)), bool)
    for i, (k, dt, r) in enumerate(fan_settings):
        if k > 0:
            FM[i] = counts[(dt, r)] >= k
    best, best_key = None, None
    for vals in itertools.product(*(grid[k] for k in keys)):
        p = D2.Rule(**{**{k: v for k, v in asdict(base).items() if k in D2.Rule.__dataclass_fields__}, **dict(zip(keys, vals))})
        s_eff = p.sigma if p.sigma_g1 is None else max(p.sigma, p.sigma_g1)
        share2 = (sig >= s_eff) | theta_b | conv
        pi_ok = pis[p.delta] >= p.pi
        k_ok = kap >= p.kappa
        beh = (k_ok & pi_ok) if p.mode == "AND" else (k_ok | pi_ok)
        f = beh.copy()
        if p.use_dom:
            f = f | ((sig >= p.sigma_dom) & pi_ok)
        if p.amount_route:
            f = f | (theta_b & pi_ok)
        base_g2 = g1row & share2 & f
        fan_g2 = g1row & beh
        G = base_g2[None, :] | (fan_g2[None, :] & FM)
        tp = (G & pos[None, :]).sum(1); fp = (G & neg[None, :]).sum(1)
        tot = tp + fp
        ok = (tot > 0)
        prec = np.where(ok, tp / np.maximum(tot, 1), 0.0); rec = tp / npos
        for i in np.where(ok & (prec >= target_precision))[0]:
            k, dt, r = fan_settings[i]
            # ties: recall, precision, simpler rule (no amount route, no fan route), middle window,
            # then the strictest fan-out (more siblings, shorter window, closer amounts)
            key = (round(rec[i], 4), round(prec[i], 4), -int(p.amount_route), -int(k > 0), -abs(p.delta - 168), k, -dt, -r)
            if best_key is None or key > best_key:
                best_key = key
                best = Rule3(**{**asdict(p), "fan_k": k, "fan_dt": dt, "fan_ratio": r})
    if best is None:
        return None
    s = score(df, grades(df, best, vis) >= 2)
    assert abs(s["recall"] - best_key[0]) < 1e-3, f"fast path disagrees with grades(): {s['recall']} vs {best_key[0]}"
    return best, s


def choose_ms_floor(df, p: Rule3, vis="V3", floors=(0.01, 0.02, 0.05, 0.10), target=0.99):
    """Same rule as revision 2: lowest second-seed floor whose G3 channel reaches 99 % on calibration worlds."""
    pos, _ = labels(df)
    for f in floors:
        q = Rule3(**{**asdict(p), "ms_floor": f})
        ch = parts(df, q, vis)[3]["second_seed"] & (parts(df, q, vis)[1])
        if ch.sum() == 0 or pos[ch].mean() >= target:
            return q, (int(ch.sum()), float(pos[ch].mean()) if ch.sum() else float("nan"))
    return Rule3(**{**asdict(p), "ms_floor": floors[-1]}), None
