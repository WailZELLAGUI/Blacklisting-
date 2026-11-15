"""The reasons shown on an account card must give the same grade as the grade itself.

For several worlds and every rule preset of the page, the grade is recomputed from the ticks of the card
(the same formula as renderCard in js/app.js) and compared with the grade returned by webapi.
Run from the repository root:  PYTHONDONTWRITEBYTECODE=1 python3 tests/test_reasons.py"""
import json
import os
import sys
import warnings

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "py"))
warnings.simplefilter("ignore")
import webapi

WORLDS = [dict(seed=s, n_seeds=20, **extra) for s in (1, 2, 3, 4, 5, 7)
          for extra in ({}, dict(blacklist="alert", eval_days=90))] + [dict(seed=2027, blacklist="alert", eval_days=90)]
RULES = [(p, v, {}) for p in ("10k", "rev5", "rev3") for v in ("V1", "V3")] + \
        [("rev5", "V3", dict(sigma=0.05, kappa=0.9, pi=0.5, fan_k=2, fan_dt=24, fan_ratio=1.5)),
         ("rev3", "V1", dict(sigma=0.3, kappa=0.3, pi=0.9, fan_k=0))]


def card_grade(r, fan_on):
    """Grade read from the ticks of the card."""
    g1 = r["amount_ok"] and (r["share_g1"] or r["big_amount"] or r["common_destination"])
    share2 = r["share_g2"] or r["big_amount"] or r["common_destination"]
    behaviour = r["concentration_ok"] or r["pass_through_ok"]
    g2 = g1 and ((share2 and behaviour) or (fan_on and r["fan_route"])) and not r["victim"]
    g3 = g2 and (r["same_person_other_exchange"] or r["second_seed"]
                 or (r["common_destination"] and (r["share_g1"] or r["big_amount"])))
    return int(g1) + int(g2) + int(g3)


def test_reasons():
    n = 0
    bad = []
    for params in WORLDS:
        w = json.loads(webapi.new_world(json.dumps(params)))
        for preset, vis, overrides in RULES:
            base = "rev5" if preset == "10k" else preset
            g = json.loads(webapi.grade(json.dumps(dict(preset=preset, vis=vis, base=base, overrides=overrides))))
            whole = webapi.RULES[base][vis].get("whole_fraud", True)
            for f in w["frauds"]:
                graph = json.loads(webapi.fraud_graph(f["id"]))
                F_known = graph["nodes"][0]["F_known"]
                for node in graph["nodes"]:
                    if node["kind"] != "account":
                        continue
                    n += 1
                    r = node["reasons"]
                    where = (params["seed"], params.get("blacklist", "old"), preset, vis, bool(overrides), f["id"], node["aid"])
                    if card_grade(r, g["rule"]["fan_k"] > 0) != node["grade"]:
                        bad.append(("card and grade differ", where, node["grade"], r))
                    if r["whole_fraud"] != whole:
                        bad.append(("whole_fraud flag", where))
                    # the label of the amount line: ">= EUR 10,000" unless the rule keeps the whole-fraud branch
                    if not r["whole_fraud"] and vis == "V1" and r["big_amount"] != (node["X"] >= 10000):
                        bad.append(("amount line ticked below EUR 10,000", where, node["X"]))
                    if r["whole_fraud"] and vis == "V1" and r["big_amount"] != (node["X"] >= min(10000, F_known)) \
                            and abs(node["X"] - min(10000, F_known)) > 1:      # X and F are rounded to the euro
                        bad.append(("amount line and min(10k, fraud size)", where, node["X"], F_known))
    assert n > 3000, n
    assert not bad, f"{len(bad)} contradictions out of {n} cards, first ones:\n" + "\n".join(map(str, bad[:8]))
    return n


if __name__ == "__main__":
    print(f"ok: {test_reasons()} account cards agree with their grade")
