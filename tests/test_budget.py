"""17 Nov 2026: automatic check of the money of every seed.
Run from the repository root:  PYTHONDONTWRITEBYTECODE=1 python3 tests/test_budget.py
For every fraud of every world checked: the seed's dated traced outflows plus its untraced routes equal `out`
(the total the evaluation uses), the traced payments received by the accounts equal the seed's dated outflows, and with budget_cap="all" the seed never sends more than it stole (out <= F).
Worlds: the test worlds 15000-15019 and the sweep worlds 16000-16019 under the sweep settings used in Table 5."""
import os
import sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "py"))
import numpy as np
import sim
from configs import TEST3_CFG
BASE = TEST3_CFG.with_(blacklist_model="alert", horizon_days=365.0)
SETTINGS = [("default (budget all since 17 Nov)", range(15000, 15020), {}),
            ("budget off (earlier results)", range(15000, 15020), dict(budget_cap="off")),
            ("budget all, sample amounts, P2P 20 % one buyer", range(16000, 16020),
             dict(budget_cap="all", F_source="real", p2p_volume=0.2, p2p_buyers=1)),
            ("budget all, sample amounts, buyer at two exchanges 10 %", range(16000, 16020),
             dict(budget_cap="all", F_source="real", p2p_volume=0.2, p2p_buyers=1, p2p_two_platforms=0.1)),
            ("budget all, payments between customers 30 %", range(15000, 15005), dict(budget_cap="all", user_transfers=0.3))]
bad = 0
for name, worlds, kw in SETTINGS:
    n = over = incons = 0
    for sd in worlds:
        w = sim.generate_world(BASE.with_(**kw), np.random.default_rng(sd))
        for s, v in w.seeds.items():
            n += 1
            tot = sum(a for _, a in v.get("out_ev", [])) + v.get("out_lump", 0.0)
            if abs(tot - v["out"]) > 1e-6 * max(1.0, v["out"]):
                incons += 1
            # the payments the accounts actually received (traced ones) match the seed's dated outflows
            H = w.cfg.horizon_days * sim.DAY
            sent = sum(a for t, a in v.get("out_ev", []) if t <= H)
            got = sum(e[4] for (ss, a) in w.truth if ss == s for e in w.events.get(a, []) if e[3] == "in_seed" and e[5][0] == s and e[5][1])
            if abs(sent - got) > 1e-6 * max(1.0, sent):
                incons += 1
            if v["out"] > v["F"] * (1 + 1e-9):
                over += 1
    capped = BASE.with_(**kw).budget_cap == "all"
    ok = incons == 0 and (over == 0 or not capped)
    bad += not ok
    print(f"{'OK  ' if ok else 'FAIL'} {name}: {n} frauds, outflows inconsistent with out: {incons}, out > F: {over}"
          + ("" if capped else " (expected without the cap)"))
sys.exit(1 if bad else 0)
