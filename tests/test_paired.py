"""18 Nov 2026: with streams="paired", the frauds are the same from one setting to the next. For the same world number,
every fraud keeps its amount stolen, pattern, number of handlers and dates when an option that does not concern the
fraud itself changes (share reaching exchanges, P2P resale, customer activity, innocents' amounts, payments between
customers, budget cap). With the real-sample amounts only the amount changes. With streams="shared" (the default, every
earlier result) this does not hold, which is why the 12 worlds of the final test are not paired.
Run from the repository root:  PYTHONDONTWRITEBYTECODE=1 python3 tests/test_paired.py"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "py"))
import numpy as np
import sim
from configs import TEST3_CFG

BASE = TEST3_CFG.with_(blacklist_model="alert", horizon_days=365.0)
SAME_FRAUDS = [dict(cex_share=0.3), dict(cex_share=0.86), dict(p2p_volume=0.1), dict(p2p_volume=0.2, p2p_buyers=1, p2p_two_platforms=0.1),
               dict(legit_amount_scale=0.5, legit_rate_scale=0.5), dict(legit_amount_scale=2.0, legit_rate_scale=2.0),
               dict(innocent_amounts="fraud"), dict(user_transfers=0.3), dict(budget_cap="off"),
               dict(cex_share=0.3, p2p_volume=0.1, legit_amount_scale=0.5, legit_rate_scale=0.5)]


def frauds(cfg, seed, with_F=True):
    w = sim.generate_world(cfg, np.random.default_rng(seed))
    return [((v["F"],) if with_F else ()) + (v["typology"], v["k"], v["tau"], v["t_col0"], v["t_dist"]) for s, v in sorted(w.seeds.items())]


def test_paired():
    for seed in (18000, 99500):
        for F_source in ("lognormal", "real"):
            ref_cfg = BASE.with_(streams="paired", F_source=F_source)
            ref = frauds(ref_cfg, seed)
            for kw in SAME_FRAUDS:
                assert frauds(ref_cfg.with_(**kw), seed) == ref, (seed, F_source, kw)
        a = frauds(BASE.with_(streams="paired"), seed, with_F=False)
        b = frauds(BASE.with_(streams="paired", F_source="real"), seed, with_F=False)
        assert a == b, seed
    # the shared stream (default) is not paired: a change of customer activity changes the frauds
    sh = BASE.with_(F_source="real")
    assert frauds(sh, 18000) != frauds(sh.with_(legit_amount_scale=0.5, legit_rate_scale=0.5), 18000)


if __name__ == "__main__":
    test_paired()
    print(f"ok: with paired streams the frauds stay the same under {len(SAME_FRAUDS)} changes of setting")
