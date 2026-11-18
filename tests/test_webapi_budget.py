"""Create a world" in the browser runs py/webapi.new_world. Check that the frauds it creates never send more than
they stole (budget_cap = "all", the default since 17 Nov 2026), for random seeds and the extreme slider values.
Run from the repository root:  PYTHONDONTWRITEBYTECODE=1 python3 tests/test_webapi_budget.py"""
import json
import os
import sys
import warnings

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "py"))
warnings.simplefilter("ignore")
import numpy as np
import webapi

CASES = [dict(seed=int(s)) for s in np.random.default_rng(7).integers(100000, 999999, 4)] + [
    dict(seed=123456, cex_share=1.0, k_min=10, k_max=10, blacklist="alert", eval_days=90),
    dict(seed=654321, cex_share=0.1, k_min=2, k_max=2, mule_window_h=1, split_spread=0.8, blacklist="freeze", eval_days=7),
]


def test_webapi_budget():
    for p in CASES:
        webapi.new_world(json.dumps(p))
        w = webapi.STATE["w"]
        assert w.cfg.budget_cap == "all", p
        for s, v in w.seeds.items():
            tot = sum(a for _, a in v.get("out_ev", [])) + v.get("out_lump", 0.0)
            assert abs(tot - v["out"]) <= 1e-6 * max(1.0, v["out"]), (p, s)
            assert v["out"] <= v["F"] * (1 + 1e-9), (p, s, v["out"], v["F"])


if __name__ == "__main__":
    test_webapi_budget()
    print(f"ok: {len(CASES)} worlds created as in the browser, no fraud sends more than it stole")
