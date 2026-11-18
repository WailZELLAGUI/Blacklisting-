"""Do the simulated worlds reproduce the measured timing? (blacklist_model alert / freeze, test worlds E)

Real values (realdata/bq/README.md, timing section):
  alert (ScamSniffer): first traced arrival at a deposit account - listing: median +8.6 d;
         pairs arrived by tau / tau+7 / tau+30: 34.8 / 47.9 / 73.7 %; EUR sent by the seeds after listing: 66.2 %
  freeze (Tether, addresses that paid out): pay-outs end before the freeze by construction; real: 84.4 % of the USDT
         received was sent before the freeze, the rest stayed and was frozen
"""
import numpy as np, pandas as pd
from multiprocessing import Pool
import experiments7 as E7
import experiments17 as E17
import os, experiments5 as E5
from features import candidate_table
from sim import DAY, generate_world, POSITIVE_ROLES

H = 365.0


# 14 Nov 2026: by default the sourced world of experiments17/18 (cex_share 0.50, new mule accounts 25-50 %), test seeds
# 15000-15019 -> results9/timing_validation.csv; FP1_OLD_WORLD=1 gives the 13 Nov run (results6/).
if os.environ.get("FP1_OLD_WORLD"):
    CFG, SEEDS, OUTF = E7.TEST3_CFG, E5.TESTE_SEEDS, "results6/timing_validation.csv"
elif os.environ.get("FP1_OPTION_B"):     # 17 Nov 2026: corrected generator, final test worlds 18000-18019
    CFG, SEEDS, OUTF = E17.CFG.with_(budget_cap="all"), list(range(18000, 18020)), "results19/timing_validation.csv"
else:
    CFG, SEEDS, OUTF = E17.CFG.with_(budget_cap="off"), E17.TEST, "results9/timing_validation.csv"


def one(args):
    model, sd = args
    w = generate_world(CFG.with_(blacklist_model=model, horizon_days=H), np.random.default_rng(sd))
    df = candidate_table(w, world_id=sd)
    df["tau"] = df.seed.map(lambda s: w.seeds[s]["tau"])
    rows = []
    for s, d in w.seeds.items():
        ev = d.get("out_ev", []); tot = sum(a for _, a in ev)
        rows.append(dict(world=sd, seed=s, tau=d["tau"], traced=tot,
                         after=sum(a for t, a in ev if t >= d["tau"]), lump=d.get("out_lump", 0.0)))
    return df[["world", "seed", "aid", "role", "t_first", "tau", "X"]], pd.DataFrame(rows)


def main():
    out = []
    for model in ("old", "alert", "freeze"):
        with Pool(4) as p:
            res = p.map(one, [(model, sd) for sd in SEEDS])
        df = pd.concat([r[0] for r in res]); sd = pd.concat([r[1] for r in res])
        pos = df[df.role.isin(POSITIVE_ROLES)]
        lag = (pos.t_first - pos.tau) / DAY
        after = sd.after.sum() / sd.traced.sum()
        out.append(dict(model=model, pairs=len(pos), median_arrival_minus_tau_d=round(lag.median(), 1),
                        arrived_by_tau=round((lag <= 0).mean(), 3), by_tau7=round((lag <= 7).mean(), 3),
                        by_tau30=round((lag <= 30).mean(), 3), traced_sent_after_tau=round(after, 3),
                        traced_sent_before_tau=round(1 - after, 3)))
        print(out[-1], flush=True)
    pd.DataFrame(out).to_csv(OUTF, index=False)


if __name__ == "__main__":
    import os; os.makedirs("results6", exist_ok=True); main()
