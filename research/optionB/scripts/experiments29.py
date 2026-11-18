"""experiments29.py (17 Nov 2026, diagnostic, after the option B test; changes no rule): why is world 12 (sample amounts,
30 %, P2P 10 %, activity 0.5) better for G2 precision than world 5 (sample amounts, 30 %)?
The generator draws the frauds from the same random stream as the customers' activity and the P2P plan, so world 5 and
world 12 with the same seed number do NOT contain the same frauds. We measure (a) the decomposition 5 / 5+P2P /
5+activity / 12 on the test worlds 18000-18019, and (b) settings 5 and 12 again on 20 new worlds 42000-42019.
Final rule, tau + 90 d. Output: results18/diag_world12.csv
Usage: python3 experiments29.py PY_DIR"""
import sys
sys.argv = [sys.argv[0], sys.argv[1], "results18", "none", "2"]
import numpy as np, pandas as pd, json
import experiments26 as E
from detectors import labels
import detectors3 as D3
R = E.REAL
E.SETTINGS = {"5": dict(R, cex_share=0.30), "5+P2P": dict(R, cex_share=0.30, p2p_volume=0.10),
              "5+activity": dict(R, cex_share=0.30, legit_amount_scale=0.5, legit_rate_scale=0.5),
              "12": dict(R, cex_share=0.30, p2p_volume=0.10, legit_amount_scale=0.5, legit_rate_scale=0.5)}
final = {**E.CUR, **json.load(open("results18/optionB_choice.json"))["choice"]["final"]}
rows = []
for label, worlds, keys in (("test 18000-18019", range(18000, 18020), list(E.SETTINGS)),
                            ("new 42000-42019", range(42000, 42020), ["5", "12"])):
    full = E.SETTINGS
    E.SETTINGS = {k: full[k] for k in keys}
    T, n_pos, n_fr = E.tables(worlds, (90,))
    E.SETTINGS = full
    for k in keys:
        df = T[k][90]; pos, neg = (m.values for m in labels(df)); p2p = (df.role == "P2P").values
        _, g2, g3, _ = D3.parts(df, D3.Rule3(**final), "V3")
        for rule, f in (("G2", g2), ("10k", (df.X >= 10_000).values)):
            m = E.metrics(df, f, pos, neg, p2p, n_pos[k], n_fr[k])
            rows.append(dict(worlds=label, setting=k, rule=rule, n_pos=n_pos[k], tp=m["tp"], fp=m["fp"], precision=m["precision"],
                             lo5=m["precision_ci_lo5_hi"][1], hi=m["precision_ci_lo5_hi"][2], found=m["found"],
                             fa_per_fraud=m["false_alerts_per_fraud"]))
        print(label, k, "done", flush=True)
pd.DataFrame(rows).to_csv("results18/diag_world12.csv", index=False)
print(pd.DataFrame(rows).to_string())
