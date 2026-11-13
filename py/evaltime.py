"""Candidate table seen at a given evaluation date: tau_s + offset for each fraud s.

The main experiments grade every account once, at the end of the 180-day horizon, so the rule sees
flows that happen long after the address is blacklisted. Here each fraud s is graded at
t_e(s) = tau_s + offset: only events up to t_e(s) are used (seed transfers, the account's other
inflows for concentration, exits for pass-through). Everything else is computed as in features.py.

The seed's total sent (denominator of the share sigma) is also cut at t_e(s): traced payments made
before t_e(s), plus the money sent through routes we do not follow in the same proportion
(sim.add_lump). Revisions up to 12 Nov 2026 used the final total here.

Simplification: when an account is also paid by other frauds, their transfers before t_e(s) are
visible even if those frauds are not yet blacklisted (second-seed clue slightly optimistic).
"""
from __future__ import annotations

from copy import copy

import numpy as np
import pandas as pd

import detectors2 as D2
from features import candidate_table
from sim import DAY, generate_world


def out_at(sd: dict, cut: float) -> float:
    """Money sent by the seed up to time `cut`."""
    ev = sd.get("out_ev", [])
    tot = sum(a for _, a in ev)
    tr = sum(a for t, a in ev if t <= cut)
    frac = tr / tot if tot > 0 else float(cut >= sd["t_dist"])
    return tr + sd.get("out_lump", 0.0) * frac


def candidate_table_at(world, offset_h: float, world_id: int = 0, x_min: float = 100.0) -> pd.DataFrame:
    by_seed = {}
    for (s, aid) in world.truth:
        by_seed.setdefault(s, set()).add(aid)
    parts = []
    for s, aids in by_seed.items():
        cut = world.seeds[s]["tau"] + offset_h
        w = copy(world)
        w.events = {a: [e for e in world.events.get(a, []) if e[0] <= cut] for a in aids}
        w.truth = {k: v for k, v in world.truth.items() if k[1] in aids}
        w.seeds = dict(world.seeds)
        w.seeds[s] = dict(world.seeds[s], out=out_at(world.seeds[s], cut))
        df = candidate_table(w, world_id=world_id, x_min=x_min)
        if df.empty:
            continue
        parts.append(df[df.seed == s])
    out = pd.concat(parts, ignore_index=True)
    return D2.add_ms_columns(out)


def _one(args):
    cfg, sd, offset_h = args
    w = generate_world(cfg, np.random.default_rng(sd))
    return candidate_table_at(w, offset_h, world_id=sd)


def tables_at(cfg, seeds, offset_h, procs=8):
    from multiprocessing import Pool
    with Pool(procs) as pool:
        out = pool.map(_one, [(cfg, s, offset_h) for s in seeds])
    return pd.concat(out, ignore_index=True)
