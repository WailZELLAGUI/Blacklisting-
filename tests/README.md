# Tests

Three checks, all run from the repository root, without the network. Python needs `numpy` and `pandas`.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_world_default.py   # about 10 s
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_reasons.py         # about 1 min
node tests/check_static.js                                      # instant
```

| Test | What it checks |
|---|---|
| `test_world_default.py` | `data/world_default.json` (the world shown before Python has loaded) equals a fresh build of world 2027 by `tools/build_world_default.py`. |
| `test_reasons.py` | Over several worlds and every rule of the page, the ticks of an account card give the same grade as the grade itself. |
| `check_static.js` | English and French texts have the same keys; every text key and every element id used by the scripts exists; no internal revision name in a visible text. `--unused` also lists the texts nothing refers to. |

After a change to the Python code in `py/`, rebuild the stored world:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/build_world_default.py
```
