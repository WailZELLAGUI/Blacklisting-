"""The sentences of the Results page about the final test (Table 2) state facts that the data must support:
G2 has a better precision than the EUR 10,000 rule in every world, and finds more involved accounts; the hardest world for
G2 is world 5 (the text explains it and compares world 12 with it); world 12 holds world 5's settings plus others;
the false alerts per fraud of world 5 and world 4 are equal (the text says they "stay the same"); and the Table 3 reading.
Run from the repository root:  python3 tests/test_option_b.py"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_option_b_claims():
    ob = json.load(open(os.path.join(ROOT, "data", "thesis.json"), encoding="utf-8"))["option_b"]
    rows = {r["setting"]: r for r in ob["settings"]}
    assert sorted(rows) == list(range(1, 13))
    for k, r in rows.items():
        assert r["G2"]["precision"] > r["ten_k"]["precision"], k
        assert r["G2"]["found"] > r["ten_k"]["found"], k
    worst = min(rows.values(), key=lambda r: r["G2"]["precision"])
    assert worst["setting"] == 5
    assert rows[5]["F"] == rows[4]["F"] == "sample" and rows[5]["cex"] == 0.3 and rows[4]["cex"] == 0.5
    assert rows[12]["F"] == "sample" and rows[12]["cex"] == 0.3 and rows[12]["extra"] == "hard"
    assert rows[5]["G2"]["fp_per_fraud"] == rows[4]["G2"]["fp_per_fraud"]
    assert rows[5]["ten_k"]["precision"] < rows[5]["G2"]["precision"]
    dg = {(d["worlds"].split()[0], d["setting"]): d for d in ob["diag_world12"]}
    # "each addition on its own does not raise precision" (same test worlds)
    for k in ("5+P2P", "5+activity"):
        assert dg[("test", k)]["precision"] <= dg[("test", "5")]["precision"], k
    # "on 20 other worlds the gap shrinks ... within chance": the two intervals overlap
    a, b = dg[("new", "5")], dg[("new", "12")]
    assert b["precision"] - a["precision"] < rows[12]["G2"]["precision"] - rows[5]["G2"]["precision"]
    assert a["hi"] >= b["lo5"]


def test_stress_claims():
    """Results page, Table 3 reading: "in every scenario tested up to one fraud in ten, G2 stays above the EUR 10,000 rule"."""
    st = json.load(open(os.path.join(ROOT, "data", "stress.json"), encoding="utf-8"))
    for r in st["one_account"] + st["two_exchanges"]:
        if r["p"] <= 0.1:
            assert r["g2"] > r["ten_k"], r


if __name__ == "__main__":
    test_option_b_claims()
    test_stress_claims()
    print("ok: the sentences about the final test match data/thesis.json")
