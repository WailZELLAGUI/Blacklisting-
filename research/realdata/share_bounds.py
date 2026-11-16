"""Real-data bounds for the stress scenarios of experiments19 (15 Nov 2026).
Input: realdata/bq/results/real_candidates.csv (pairs seed x deposit address, on-chain, two hops; X in EUR,
sigma2 = X / F, F = max(money sent, money received) by the seed). Pairs with X >= EUR 100 (the G1 floor).
No labels on-chain: every number here mixes involved and innocent accounts, so it is an UPPER bound for innocents.
  1. share of pairs by share band;
  2. for thresholds s: share of seeds with >= 1 pair at >= s, and with >= 2 pairs at >= s (an innocent besides the
     fraud's main account), over the seeds that reach a deposit address and over all 1,448 seeds;
  3. common destination: NOT measurable on-chain (a CEX account's withdrawals leave from the exchange's hot wallets),
     stated in the output.
Output: realdata/out/share_bounds.json."""
import json
import numpy as np, pandas as pd

cd = pd.read_csv("realdata/bq/results/real_candidates.csv")
cd = cd[cd.X >= 100]
N_SEEDS_ALL = 1448                      # phishing seeds of the query set (realdata/bq/README.md)
bins = [0, 0.01, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50, 1.000001]
lab = ["<1%", "1-5%", "5-10%", "10-15%", "15-20%", "20-30%", "30-50%", ">=50%"]
out = dict(pairs=int(len(cd)), seeds_reaching_a_deposit=int(cd.seed.nunique()), seeds_all=N_SEEDS_ALL,
           pairs_by_share=pd.cut(cd.sigma2, bins, right=False, labels=lab).value_counts(normalize=True).reindex(lab).round(4).to_dict())
per = {}
for s in (0.10, 0.15, 0.20, 0.30, 0.50):
    n = cd[cd.sigma2 >= s].groupby("seed").size()
    per[f">= {int(s*100)} %"] = dict(
        seeds_with_1plus=int((n >= 1).sum()), seeds_with_2plus=int((n >= 2).sum()),
        share_of_reaching_seeds_1plus=round(float((n >= 1).sum() / cd.seed.nunique()), 4),
        share_of_reaching_seeds_2plus=round(float((n >= 2).sum() / cd.seed.nunique()), 4),
        share_of_all_seeds_2plus=round(float((n >= 2).sum() / N_SEEDS_ALL), 4))
out["seeds_by_threshold"] = per
out["common_destination"] = ("not measurable on-chain: withdrawals from a CEX account leave from the exchange's hot "
                             "wallets, so two accounts paying the same address cannot be seen without exchange data "
                             "(grades_real.py already drops this clue)")
json.dump(out, open("realdata/out/share_bounds.json", "w"), indent=1)
print(json.dumps(out, indent=1))

# ---- 15 Nov 2026 addition (review of the other session) ----
# B: among seeds with >= 2 deposit addresses at >= 10 % of their money, how many have two of them at DIFFERENT exchanges
# (necessary condition for the "same person on >= 2 exchanges" clue; same exchange does not trigger it)?
# A: pass-through within 24 h of the main account is NOT measurable on-chain (deposits are swept into the exchange's
# hot wallets; the account's own withdrawals are not visible), so only the unconditional bound applies.
big = cd[cd.sigma2 >= 0.10]
g = big.groupby("seed").agg(n=("da", "size"), n_ex=("exchange", lambda x: x.fillna("unknown").nunique()))
two = g[g.n >= 2]
out["B_two_accounts_ge10pct"] = dict(seeds=int(len(two)), on_two_or_more_exchanges=int((two.n_ex >= 2).sum()),
                                      share_of_reaching_seeds=round(float((two.n_ex >= 2).sum() / cd.seed.nunique()), 4),
                                      exchange_label_missing_pairs=int(big.exchange.isna().sum()))
out["A_bounds_ge20pct"] = dict(upper_bound_no_assumption=round(float((cd[cd.sigma2 >= 0.2].seed.nunique()) / cd.seed.nunique()), 4),
                               pass_through_24h="not measurable on-chain")
json.dump(out, open("realdata/out/share_bounds.json", "w"), indent=1)
print(json.dumps({k: out[k] for k in ("B_two_accounts_ge10pct", "A_bounds_ge20pct")}, indent=1))
