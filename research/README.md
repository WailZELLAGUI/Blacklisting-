# Research files behind the "How far the results hold" section

These are the scripts and result files that `tools/build_stress.py` reads to build `data/stress.json` (Tables 3 to 6
of the Results page), and those of the final test (`optionB/`), which `data/thesis.json` reads (Tables 1 and 2). They are kept here so that a later session can check or rebuild every number without the full
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

## Generator changes of 17 and 18 Nov 2026 (py/sim.py)

- `budget_cap` (17 Nov): `"all"`, the default since then, makes a fraud never send more than it stole (out <= F).
  `"off"` reproduces every earlier result. `tests/test_budget.py` checks the money of every fraud.
- `streams` (18 Nov): `"shared"`, the default, is one random stream for the whole world, as in every earlier result;
  changing an option that draws random numbers shifts the draws, so two settings with the same world number do not
  hold the same frauds. `"paired"` gives each fraud's parameters their own stream and the rest of each fraud a stream of
  its own, so the frauds stay the same from one setting to the next. `tests/test_paired.py` checks it.

## The final test (option B, 17 Nov 2026)

Plan written before any run: `preregistration_optionB.md` (with its dated corrections). Scripts in `optionB/scripts/`
(they import modules of the full research folder: `experiments5`, `experiments7`, `experiments8`, `experiments10`,
`experiments17`, `experiments17b`, `experiments18`; they are kept here so that what was run can be read).

| Script | What it does | Worlds | Output |
|---|---|---|---|
| `experiments26.py` | calibration on 12 settings, then one test of the rule chosen (the current rule was kept) | 17000-17019, 18000-18019 | `optionB/results18/` |
| `experiments27.py` | the site's results (Table 1, figures) for setting 1 and setting 4 | 18000-18019 | `optionB/results19/`, `optionB/results19/s4/` |
| `experiments28.py` | speed and number-of-mules sweeps, paired (`FP1_STREAMS=paired`, `FP1_SWEEP_W0=44000`) | 44000-44009 | `optionB/results19/sweeps.csv` |
| `validate_timing.py` | simulated blacklisting timing against the real one (`FP1_OPTION_B=1`) | 18000-18019 | `optionB/results19/timing_validation.csv` |
| `experiments29.py` | diagnostic of world 12 against world 5 (changes no rule) | 18000-18019, 42000-42019 | `optionB/results18/diag_world12.csv` |
| `experiments22.py` to `experiments25.py` | payments between customers, customer activity (`preregistration_activity.md`), budget cap, Table 5 with the cap | 15000-15019, 16000-16019, 19000-19019 | in the research folder |

The 12 settings of the final test use `streams="shared"` (they are frozen as run): they are not drawn on the same
frauds, which the Results page says. Every calculation made after it uses `streams="paired"`.

Since 18 Nov 2026 the breaking points (Tables 3 to 6) are rerun with the corrected, paired generator on worlds
43000-43019 (`FP1_W0=43000 FP1_STREAMS=paired`); `results/` holds them, and `results_v16nov/` the earlier ones
(worlds 15000-15019 and 16000-16019, generator without the cap).

## Worlds already used

- 14000-14019: calibration (hard settings); 15000-15019: test and every stress test until 16 Nov; 16000-16019: the
  preregistered P2P sweep; 19000-19019: customer-activity sweep; 20000-20009 and 30000-30009 (and the other blocks of
  100 above them): earlier speed and mules sweeps.
- 17000-17019: option B calibration; 18000-18019: final test (frozen).
- 41000-41019: breaking points with the unpaired generator, stopped before any number was read.
- 42000-42019: diagnostic of world 12. 43000-43019: breaking points (paired). 44000-44009: paired sweeps.
- 99000-99199 and 99500: dry runs and tests.
