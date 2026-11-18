"""experiments27.py (17 Nov 2026): website results of the FINAL TEST of option B (preregistration_optionB.md): corrected
generator (budget_cap = "all"), test worlds 18000-18019 never used before option B, final rule = Revision 2 (rev5).
Run twice: setting 1 (median EUR 30,000) -> results19/, setting 4 (real phishing sample amounts) -> results19/s4/
(FP1_SETTING=4; alert timing only). Copy of experiments18p otherwise.

Original docstring of experiments18p: Website results in the sourced world, with the PLAIN 10k rule as reference (15 Nov 2026; copy of experiments18).
"B0 10k per exchange" = account received >= EUR 10,000 (as applied in practice); "B0 paper" = >= min(EUR 10,000, F)
(our earlier paper, used in results9). Everything else identical to experiments18. Outputs: results10/.

Original docstring:
World: test settings (worlds E), measured collectors, ScamSniffer ("alert") / Tether ("freeze") / hand-set ("old")
blacklisting dates, cex_share 0.50 (Chainalysis), new mule accounts drawn in 25-50 % per world (RUSI, FCA).
Test worlds: seeds 15000-15019 (experiments17), never used to choose a value.
Rules: revision 5 = revision 4 with sigma_2 = 20 % in V3/V4 (V1/V2 already 20 %): the robust zone of experiments17c;
shown on the website as "Revision 2". Revision 3 (fan-out route) as before. Revision 4 kept for comparison.
Headline: alert timing, graded 90 days after blacklisting; found = of all accounts the fraud will ever pay.
Outputs: results9/site_main.csv, site_by_role.csv, site_by_pattern.csv, site_curve.csv, visible.csv."""
from __future__ import annotations
import os, pickle
from dataclasses import replace
import numpy as np, pandas as pd
import detectors2 as D2, detectors3 as D3, experiments5 as E5, experiments17 as E17
from detectors import b0, score, labels
from evaltime import tables_at
from experiments10 import on_end
from sim import DAY

SETTING = int(os.environ.get("FP1_SETTING", "1"))
OUT = "results19" if SETTING == 1 else "results19/s4"; os.makedirs(OUT, exist_ok=True)
CFG_B = E17.CFG.with_(budget_cap="all", **({} if SETTING == 1 else {"F_source": "real"}))
TEST_B = list(range(18000, 18020))
MODELS = ("old", "alert", "freeze") if SETTING == 1 else ("alert",)
DATES = {"tau1": 1, "tau7": 7, "tau30": 30, "tau90": 90, "end": None}
HEADLINE = ("alert", "tau90")


def cfg(model):
    return CFG_B.with_(blacklist_model=model)


def table(model, date):
    off = DATES[date]
    tag = f"optionB_final_s{SETTING}_{model}"
    if off is None:
        return E17.cached(f"{tag}_end", lambda: E5.tables(cfg(model), TEST_B)[0])
    return E17.cached(f"{tag}_tau{off}", lambda: tables_at(cfg(model), TEST_B, off * DAY, procs=2))


def rules():
    R = pickle.load(open("results3/rules.pkl", "rb"))
    rev4 = {v: replace(R["rev2"][v], whole_fraud=False) for v in ("V1", "V3")}
    rev5 = {v: replace(rev4[v], sigma=max(rev4[v].sigma, 0.2)) for v in ("V1", "V3")}
    return rev4, rev5, R["rev3"]


def flagset(df):
    rev4, rev5, rev3 = rules()
    f = {"B0 10k per exchange": df.X >= 10_000, "B0 paper": b0(df)}
    for vis in ("V1", "V3"):
        g5, g4, g3 = D2.grades(df, rev5[vis], vis), D2.grades(df, rev4[vis], vis), D3.grades(df, rev3[vis], vis)
        f[f"Rev5 {vis} G2+"], f[f"Rev5 {vis} G3"] = g5 >= 2, g5 >= 3
        f[f"Rev4 {vis} G2+"], f[f"Rev4 {vis} G3"] = g4 >= 2, g4 >= 3
        f[f"Rev3 {vis} G2+"], f[f"Rev3 {vis} G3"] = g3 >= 2, g3 >= 3
        f[f"Rev5 {vis} G1+"] = g5 >= 1
    return f


def main():
    rows, vis = [], []
    for model in MODELS:
        end = table(model, "end"); pos_end = labels(end)[0]
        for date in DATES:
            df = end if date == "end" else table(model, date)
            fl = on_end(end, df, flagset(df))
            # share of the (fraud, account) pairs of the end table already paid at this date
            vis.append(dict(blacklist=model, date=date, visible=round(len(df) / len(end), 4),
                            involved_reached=round(float(labels(df)[0].sum() / pos_end.sum()), 4)))
            if (model, date) == HEADLINE:
                E5.evaluate(end, fl).to_csv(f"{OUT}/site_main.csv", index=False)
                keyf = {k: fl[k] for k in ["B0 10k per exchange", "B0 paper", "Rev5 V3 G2+", "Rev3 V3 G2+", "Rev4 V3 G2+"]}
                E5.by_role(end, keyf).to_csv(f"{OUT}/site_by_role.csv", index=False)
                E5.by_pattern(end, keyf).to_csv(f"{OUT}/site_by_pattern.csv")
            for name in ["B0 10k per exchange", "B0 paper", "Rev5 V3 G2+", "Rev5 V3 G3", "Rev3 V3 G2+", "Rev4 V3 G2+"]:
                s = score(end, fl[name])
                rows.append(dict(blacklist=model, date=date, detector=name, precision=s["precision"], recall=s["recall"],
                                 fp_per_seed=s["fp_per_seed"], value_recall=s.get("value_recall")))
            print(model, date, flush=True)
    pd.DataFrame(rows).to_csv(f"{OUT}/site_curve.csv", index=False)
    pd.DataFrame(vis).to_csv(f"{OUT}/visible.csv", index=False)
    m = pd.read_csv(f"{OUT}/site_main.csv")
    print(m[["detector", "precision", "prec_lo", "prec_hi", "recall", "rec_lo", "rec_hi", "value_recall", "fp_per_seed"]].round(3).to_string())
    print(pd.DataFrame(rows)[lambda d: d.blacklist == "alert"].round(3).to_string())
    print(pd.DataFrame(vis).to_string())


if __name__ == "__main__":
    main()
