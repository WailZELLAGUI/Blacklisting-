# Research files behind the "How far the results hold" section

These are the scripts and result files that `tools/build_stress.py` reads to build `data/stress.json` (Tables 2 to 5
of the Results page). They are kept here so that a later session can check or rebuild every number without the full
research folder. The simulator itself is `py/sim.py` (same file as the research code).

## Rebuild data/stress.json

```sh
python3 tools/build_stress.py research/results
```

No number is typed in the script: every value is read from the files in `research/results/`.

## Rerun an experiment

Every script takes the folder that holds the simulator as first argument, here `py/`, and an output folder:

```sh
python3 research/scripts/experiments21.py py research/results 20 2     # about 30 min on 2 cores
```

| Script | What it tests | Worlds | Output in `results/` |
|---|---|---|---|
| `experiments19.py` | one innocent with a large share (A), one innocent at two exchanges (B), shared destination swept | 15000-15019 | `exp19_summary.csv` |
| `experiments19b.py` | A and B in the three worlds (30 / 50 / 86 % to exchanges), P2P seller at two exchanges, G3 fixes tested only | 15000-15019 | `exp19b_summary.csv` |
| `experiments19c.py` | P2P seller on one account | 15000-15019 | `exp19c_summary.csv` |
| `innocents.py` | share of a fraud received by each innocent role | 15000-15019 | `innocents.csv` |
| `experiments20.py`, `experiments20b.py` | first look at fraud size (median moved), innocents paid fixed or proportional amounts | 15000-15019 | `exp20_summary.csv`, `exp20b_summary.csv` |
| `experiments21.py` | **preregistered** sweep of fraud size and P2P resale (`preregistration_p2p.md`, written before the run) | 16000-16019 | `exp21_summary.csv`, `exp21_roles.csv`, `exp21_raw.csv` |

`innocents.py` has a hard-coded path to `py/`; change its first line before running it.

## Real-data files

`share_bounds.json`, `fraud_size.json` and `real_F.json` come from our BigQuery extract of Ethereum phishing addresses
(Jul 2022 - Feb 2023), which is not in this repository. `realdata/share_bounds.py` and `realdata/fraud_size.py` are the
scripts that made them; they need that extract. `real_F.json` (the money sent by each of the 1,448 seeds, in EUR) is
also copied to `py/realdata/out/`, where `py/sim.py` reads it for `F_source = "real"`.

## Simulator options added on 16 Nov 2026 (py/sim.py)

`innocent_amounts`, `F_source`, `p2p_volume`, `p2p_buyers`, `p2p_fast`, `p2p_two_platforms`. Their defaults give
exactly the worlds of every earlier result (checked on worlds 14003, 15000, 15007, 15011), so the site's own
simulator and `data/world_default.json` do not change.

## Worlds already used

- 14000-14019: calibration (hard settings); 15000-15019: test and every stress test; 16000-16019: the preregistered sweep.
- 17000-17019 (calibration) and 18000-18019 (final test) are reserved for the one further calibration that
  `preregistration_p2p.md` allows. Do not generate them for anything else.
