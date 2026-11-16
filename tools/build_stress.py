"""Builds data/stress.json (the "How far the results hold" tables of the Results page) from the result files of
experiments19.py, experiments19b.py, experiments19c.py (stress tests on the 20 test worlds, tau + 90 d, frozen rules),
innocents.csv (shares received by innocent accounts in the base worlds) and realdata/out/share_bounds.json;
and, since 16 Nov 2026, exp21_summary.csv (experiments21.py: fraud size and P2P resale on the new worlds 16000-16019,
preregistration_p2p.md) and fraud_size.json (realdata/analysis/fraud_size.py).

Usage: python3 tools/build_stress.py DIR      (DIR holds exp19_summary.csv, exp19b_summary.csv, exp19c_summary.csv,
                                               innocents.csv, share_bounds.json, exp21_summary.csv,
                                               fraud_size.json)
No number is typed here: every value is read from those files."""
import sys, json, pathlib
import pandas as pd

D = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "stress.json"
a, b, c = (pd.read_csv(D / f"exp19{x}_summary.csv") for x in ("", "b", "c"))
a["cex"] = 0.5


def prec(r, k):
    return round(r[f"tp_{k}"] / (r[f"tp_{k}"] + r[f"fp_{k}"]), 6)


def found(r, k):
    return round(r[f"tp_{k}"] / N, 6)


base_a = a[a.scen == "base"].iloc[0]
N = int(b[b.scen == "base"].n_pos.iloc[0])                 # involved accounts with a traced payment (site definition)

base = {}
for _, r in b[b.scen == "base"].iterrows():
    base[str(r.cex)] = dict(
        g2=dict(precision=prec(r, "G2+"), lo=r["prec_G2+_lo"], hi=r["prec_G2+_hi"], found=found(r, "G2+")),
        g3=dict(precision=prec(r, "G3"), found=found(r, "G3")),
        g3_no_same=dict(precision=prec(r, "G3_P4"), found=found(r, "G3_P4")),
        rev3=dict(precision=prec(r, "rev3_G2+"), found=found(r, "rev3_G2+")),
        ten_k=dict(precision=prec(r, "10k_pure"), found=found(r, "10k_pure")))

one, seen = [], set()
for df, kinds in ((c, {"A": "ordinary", "Ap": "seller"}), (b, {"A": "ordinary"}), (a, {"A": "ordinary"})):
    for _, r in df[df.scen.isin(kinds)].iterrows():
        key = (float(r.cex), kinds[r.scen], float(r.p), float(r.s))
        if key in seen:
            continue
        seen.add(key)
        one.append(dict(cex=key[0], kind=key[1], p=key[2], s=key[3], g2=prec(r, "G2+"), g2_p05=r["prec_G2+_p05"],
                        g3=prec(r, "G3"), ten_k=prec(r, "10k_pure"), found=found(r, "G2+")))
two = [dict(cex=float(r.cex), kind={"B": "ordinary", "Bp": "seller"}[r.scen], p=float(r.p), s=float(r.s),
            g2=prec(r, "G2+"), g3=prec(r, "G3"), g3_no_same=prec(r, "G3_P4"), ten_k=prec(r, "10k_pure"),
            found_g3_no_same=found(r, "G3_P4"))
       for _, r in b[b.scen.isin(["B", "Bp"])].iterrows()]
dest = [dict(share=0.5 if r.scen == "base" else float(r.p), g2=prec(r, "G2+"), lo=r["prec_G2+_lo"], hi=r["prec_G2+_hi"],
             found=found(r, "G2+"), found_g3=found(r, "G3"))
        for _, r in a[a.scen.isin(["base", "C_exit"])].iterrows()]
dest.sort(key=lambda x: x["share"])

inn = pd.read_csv(D / "innocents.csv")
inn = inn[inn.X >= 100]
g = inn.groupby("role")
innocents = dict(accounts=int(len(inn)), under_10pct=round(float((inn.sig < 0.10).mean()), 4),
                 q90=round(float(inn.sig.quantile(0.9)), 4), q99=round(float(inn.sig.quantile(0.99)), 4),
                 by_role={k: dict(n=int(len(x)), max=round(float(x.sig.max()), 4), ge20=int((x.sig >= 0.2).sum()),
                                  ge20_flagged=int((x.g2 & (x.sig >= 0.2)).sum())) for k, x in g})
sb = json.load(open(D / "share_bounds.json"))
real = dict(seeds=sb["seeds_reaching_a_deposit"],
            one_account_ge20=sb["seeds_by_threshold"][">= 20 %"]["share_of_reaching_seeds_1plus"],
            two_accounts_ge20=sb["seeds_by_threshold"][">= 20 %"]["share_of_reaching_seeds_2plus"],
            two_exchanges_ge10=sb["B_two_accounts_ge10pct"]["share_of_reaching_seeds"])
out = dict(meta=dict(worlds=int(base_a.n_worlds), days=90, involved=N, involved_all=int(base_a.n_all),
                     found_all=round(base_a["tp_G2+"] / base_a.n_all, 4)),
           base=base, one_account=one, two_exchanges=two,
           common_destination=dict(rows=dest, found_total=int(base_a["tp_G2+"]), found_only_by_it=int(base_a["tp_G2+_only_conv"]),
                                   without_clue=dict(precision=prec(base_a, "G2+_noconv"), found=found(base_a, "G2+_noconv"))),
           innocents=innocents, real=real)

# fraud size and P2P resale (Table 6 of the Results page)
e = pd.read_csv(D / "exp21_summary.csv").set_index("case")
fs = json.load(open(D / "fraud_size.json"))
CASES = [("reference", "reference"), ("sample_fixed", "grid F=real v=0.0 buyers=2-10 fixed"),
         ("sample_prop", "grid F=real v=0.0 buyers=2-10 fraud"),
         ("p2p_10", "p2p frequency=0.1"), ("p2p_25", "p2p frequency=0.25"), ("p2p_50", "grid F=real v=0.2 buyers=1 fixed"),
         ("two_5", "two platforms=0.05"), ("two_10", "two platforms=0.1")]
size = dict(worlds="16000-16019", real_median_eur=round(fs["real"]["quantiles_eur"]["0.5"]), real_seeds=fs["real"]["n_seeds"],
            sim_median_eur=fs["sim"]["F_median_setting"],
            rows=[dict(id=k, g2=float(e.loc[c, "prec_G2+"]), g2_lo=float(e.loc[c, "prec_G2+_lo"]), g2_hi=float(e.loc[c, "prec_G2+_hi"]),
                       g2_fa=float(e.loc[c, "fa_per_fraud_G2+"]), g2_found=float(e.loc[c, "found_G2+"]),
                       g3=float(e.loc[c, "prec_G3"]), g3_lo=float(e.loc[c, "prec_G3_lo"])) for k, c in CASES],
            g3_min_all=float(e["prec_G3"].min()), g3_min_but_two10=float(e.drop("two platforms=0.1")["prec_G3"].min()),
            cases=int(len(e)))
out["size_p2p"] = size
json.dump(out, open(OUT, "w"), indent=1)
print(f"wrote {OUT}: {len(one)} one-account rows, {len(two)} two-exchange rows, {len(dest)} destination rows")
