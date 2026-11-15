"""data/world_default.json must be exactly what the Python code produces for world 2027.
Run from the repository root:  PYTHONDONTWRITEBYTECODE=1 python3 tests/test_world_default.py"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build_world_default as B


def differences(a, b, path=""):
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(f"{path}/{k}: only in the {'file' if k in a else 'build'}")
            else:
                out += differences(a[k], b[k], f"{path}/{k}")
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{path}: {len(a)} items in the file, {len(b)} in the build"]
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in differences(x, y, f"{path}[{i}]")]
    return [] if a == b and type(a) == type(b) else [f"{path}: file {a!r}, build {b!r}"]


def test_world_default():
    stored = json.load(open(B.OUT, encoding="utf-8"))
    built = json.loads(json.dumps(B.build()))
    diff = differences(stored, built)
    assert not diff, f"{len(diff)} differences, first ones:\n" + "\n".join(diff[:10])
    assert stored["world"]["seed"] == B.SEED and len(stored["world"]["frauds"]) == 40
    assert sorted(stored["grades"]) == sorted(f"{p}|{v}" for p in B.PRESETS for v in B.VISIBILITIES)


if __name__ == "__main__":
    test_world_default()
    print("ok: data/world_default.json equals a fresh build of world 2027")
