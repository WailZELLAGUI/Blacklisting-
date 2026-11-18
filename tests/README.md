# Tests

Seven checks, all run from the repository root, without the network. Python needs `numpy` and `pandas`.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_world_default.py   # about 10 s
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_reasons.py         # about 1 min
node tests/check_static.js                                      # instant
python3 tests/test_option_b.py                                  # instant
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_webapi_budget.py   # about 20 s
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_paired.py          # about 2 min
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_budget.py          # about 5 min
```

| Test | What it checks |
|---|---|
| `test_world_default.py` | `data/world_default.json` (the world shown before Python has loaded) equals a fresh build of world 2027 by `tools/build_world_default.py`. |
| `test_reasons.py` | Over several worlds and every rule of the page, the ticks of an account card give the same grade as the grade itself, and the €10k rule flags exactly the accounts that received at least €10,000. |
| `test_option_b.py` | The sentences of the Results page that compare worlds (Table 2, the hardest world, world 12, the Table 3 reading) hold in `data/thesis.json` and `data/stress.json`. |
| `test_webapi_budget.py` | "Create a world", as the browser runs it (`py/webapi.py`), uses the corrected generator: no fraud sends more than it stole, for random seeds and extreme slider values. |
| `test_paired.py` | With `streams="paired"` the frauds (amount, pattern, handlers, dates) stay the same under 10 changes of setting; the default `"shared"` is not paired. |
| `test_budget.py` | For each of 3,400 frauds in five settings, the dated outflows plus the untraced routes equal what the evaluation uses, the payments received match them, and with the cap the fraud never sends more than it stole. |
| `check_static.js` | English and French texts have the same keys; every text key and every element id used by the scripts exists; no internal revision name in a visible text; every value the page reads in `data/thesis.json` and `data/stress.json` exists. `--unused` also lists the texts nothing refers to. |

After a change to the Python code in `py/`, rebuild the stored world:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/build_world_default.py
```
