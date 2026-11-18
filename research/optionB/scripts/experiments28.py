"""experiments28.py (17 Nov 2026): the sweeps of experiments18s rerun on the corrected generator of option B
(budget_cap = "all", now the default), with the final rule; same settings and seeds. Output: results19/sweeps.csv.

Original docstring: Sensitivity sweeps of the website (mule speed x split spread; handler payments per fraud) in the sourced world of
experiments18 (alert timing, graded at tau + 90 d, found = of all accounts ever paid). Same settings and seeds as
experiments7 (20000+, 30000+, 10 worlds each); revision 5 (shown as Revision 2), revision 3, revision 4.
Output: results19/sweeps.csv."""
import os, pickle
import pandas as pd
import detectors2 as D2, detectors3 as D3, experiments5 as E5, experiments7 as E7, experiments17 as E17, experiments18 as E18
from detectors import labels
from evaltime import tables_at
from sim import DAY

BASE = E17.CFG.with_(budget_cap="all", streams=os.environ.get("FP1_STREAMS", "shared"))   # TEST3 settings + measured + cex 0.5 + mule range, alert, 365 d
# 18 Nov 2026: FP1_STREAMS=paired and FP1_SWEEP_W0 (same 10 worlds for every setting) make the sweep paired
SW0 = os.environ.get("FP1_SWEEP_W0")


def get(cfg, seeds, tag):
    end = E17.cached(f"sw{'P' + str(SW0) if BASE.streams == 'paired' else 'B'}_{tag}_end", lambda: E5.tables(cfg, seeds)[0])
    t90 = E17.cached(f"sw{'P' + str(SW0) if BASE.streams == 'paired' else 'B'}_{tag}_tau90", lambda: tables_at(cfg, seeds, 90 * DAY, procs=2))
    return end, t90


def scores(end, t90):
    rev4, rev5, rev3 = E18.rules()
    n_all = int(labels(end)[0].sum())
    out = {}
    for name, f in (("Rev5 V3 G2+", D2.grades(t90, rev5["V3"], "V3") >= 2), ("Rev4 V3 G2+", D2.grades(t90, rev4["V3"], "V3") >= 2),
                    ("Rev3 V3 G2+", D3.grades(t90, rev3["V3"], "V3") >= 2)):
        pos, neg = labels(t90)
        tp, fp = int((f & pos).sum()), int((f & neg).sum())
        out[name] = dict(precision=tp / (tp + fp) if tp + fp else float("nan"), recall=tp / n_all,
                         fp_per_seed=fp / end.groupby(["world", "seed"]).ngroups)
    return out


def main():
    rows = []
    settings = [(s, w) for s in (0.0, 0.2, 0.5, 0.8) for w in (1 / 24, 1.0, 3.0, 7.0)]
    for i, (spread, wsc) in enumerate(settings):
        cfg = BASE.with_(split_random=False, split_spread=spread, send_window_scale=wsc)
        seeds = list(range(int(SW0), int(SW0) + 10)) if SW0 else list(range(20000 + 100 * i, 20000 + 100 * i + 10))
        for name, s in scores(*get(cfg, seeds, f"s{spread}_w{wsc:.3f}")).items():
            rows.append(dict(setting="split", spread=spread, mule_window_h=24 * wsc, detector=name, **s))
        print("split", spread, wsc, flush=True)
    for j, k in enumerate((2, 3, 5, 10)):
        cfg = BASE.with_(k_fixed=k)
        seeds = list(range(int(SW0), int(SW0) + 10)) if SW0 else list(range(30000 + 100 * j, 30000 + 100 * j + 10))
        for name, s in scores(*get(cfg, seeds, f"k{k}")).items():
            rows.append(dict(setting="handlers per fraud", k=k, detector=name, **s))
        print("k", k, flush=True)
    sw = pd.DataFrame(rows); sw.to_csv("results19/sweeps.csv", index=False)   # 18 Nov 2026: was E18.OUT (results9), which overwrote the earlier sweeps; restored from the cache by rerunning experiments18s.py
    print(sw.groupby(["setting", "detector"])[["precision", "recall"]].mean().round(3))


if __name__ == "__main__":
    main()
