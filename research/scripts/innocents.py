import sys, os, json; PY = sys.argv[1] if len(sys.argv) > 1 else "/home/user/Blacklisting-/py"; sys.path.insert(0, PY)
W0 = int(os.environ.get("FP1_W0", "15000"))
import numpy as np, pandas as pd
from multiprocessing import Pool
from configs import TEST3_CFG
from evaltime import candidate_table_at
from sim import generate_world, DAY, NEGATIVE_ROLES
import detectors3 as D3
BASE = TEST3_CFG.with_(blacklist_model="alert", horizon_days=365.0, streams=__import__("os").environ.get("FP1_STREAMS", "shared"))   # 18 Nov 2026: "paired" for the reruns
R5 = D3.Rule3(**{**json.load(open(f"{PY}/rules.json"))["rev5"]["V3"], "fan_k": 0})
def one(sd):
    df = candidate_table_at(generate_world(BASE, np.random.default_rng(sd)), 90 * DAY, world_id=sd)
    g1, g2, g3, ch = D3.parts(df, R5, "V3")
    df["sig"] = df.X_V3.values / df.out2.values; df["g2"] = g2
    return df[df.role.isin(NEGATIVE_ROLES)][["role", "sig", "g2", "X"]]
if __name__ == "__main__":
    with Pool(2) as p: d = pd.concat(p.map(one, range(W0, W0 + 20)))
    d.to_csv(sys.argv[2] if len(sys.argv) > 2 else "innocents.csv", index=False); d = d[d.X >= 100]
    print(len(d), (d.sig < .10).mean(), d.sig.quantile([.5, .9, .99]).round(4).to_dict())
    g = d.groupby("role"); print(pd.DataFrame(dict(n=g.size(), max=g.sig.max().round(3), ge20=g.sig.apply(lambda x: (x >= .2).mean()).round(4), n_ge20=g.sig.apply(lambda x: int((x >= .2).sum())), g2_among_ge20=g.apply(lambda x: int((x.g2 & (x.sig >= .2)).sum())))))
