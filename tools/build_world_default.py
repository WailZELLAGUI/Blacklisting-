"""Rebuild data/world_default.json: the world the site shows before Python has loaded (seed 2027).

Usage (from the repository root):
    PYTHONDONTWRITEBYTECODE=1 python3 tools/build_world_default.py            # rewrite the file
    PYTHONDONTWRITEBYTECODE=1 python3 tools/build_world_default.py --check    # compare only, exit 1 if different

The file holds what js/app.js reads when the Python engine is not ready:
    world   the answer of webapi.new_world, plus the `params` it was created with
    grades  webapi.grade for each rule of the page ("10k", "rev3", "rev5") and each visibility ("V1", "V3")
    graphs  webapi.fraud_graph of every fraud, for each of these six rules
    rows    webapi.sample_rows, graded with the lead rule (rev5, V3)
Numbers depend on the numpy and pandas versions only through floating-point rounding; the stored values are
rounded (see webapi._f), and tests/test_world_default.py checks that this build equals the committed file.
"""
import json
import os
import sys
import warnings

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "world_default.json")
SEED = 2027
PARAMS = {"blacklist": "alert", "eval_days": 90}      # measured blacklisting dates, graded 90 days later
PRESETS = ("10k", "rev3", "rev5")
VISIBILITIES = ("V1", "V3")


def build():
    sys.path.insert(0, os.path.join(ROOT, "py"))
    warnings.simplefilter("ignore")
    import webapi

    def spec(preset, vis):
        return json.dumps(dict(preset=preset, vis=vis, base="rev5" if preset == "10k" else preset, overrides={}))

    world = json.loads(webapi.new_world(json.dumps({"seed": SEED, **PARAMS})))
    world["params"] = dict(PARAMS)
    grades, graphs = {}, {}
    for preset in PRESETS:
        for vis in VISIBILITIES:
            key = f"{preset}|{vis}"
            grades[key] = json.loads(webapi.grade(spec(preset, vis)))
            graphs[key] = {str(f["id"]): json.loads(webapi.fraud_graph(f["id"])) for f in world["frauds"]}
    webapi.grade(spec("rev5", "V3"))
    rows = json.loads(webapi.sample_rows())
    return dict(world=world, grades=grades, graphs=graphs, rows=rows)


def main():
    text = json.dumps(build())
    if "--check" in sys.argv:
        same = open(OUT, encoding="utf-8").read() == text
        print("data/world_default.json is up to date" if same else "data/world_default.json differs from this build")
        sys.exit(0 if same else 1)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"wrote {OUT} ({len(text):,} bytes)")


if __name__ == "__main__":
    main()
