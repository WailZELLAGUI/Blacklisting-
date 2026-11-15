"""Builds data/stress.json (the "How far the results hold" tables of the Results page) from the result files of
experiments19.py, experiments19b.py, experiments19c.py (stress tests on the 20 test worlds, tau + 90 d, frozen rules),
innocents.csv (shares received by innocent accounts in the base worlds) and realdata/out/share_bounds.json.

Usage: python3 tools/build_stress.py DIR      (DIR holds exp19_summary.csv, exp19b_summary.csv, exp19c_summary.csv,
                                               innocents.csv, share_bounds.json)
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
json.dump(out, open(OUT, "w"), indent=1)
print(f"wrote {OUT}: {len(one)} one-account rows, {len(two)} two-exchange rows, {len(dest)} destination rows")
