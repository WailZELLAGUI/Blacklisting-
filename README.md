# Fraudster +1

**Following stolen crypto into exchange accounts, to find the people behind a fraud.**
*Suivre les cryptos volées jusque dans les comptes des plateformes d'échange, pour retrouver les personnes derrière une fraude.*

Interactive website (English / French): open `index.html` through GitHub Pages.

## What is in the site

| Section | Content |
|---|---|
| The idea | The method in four steps and the meaning of the grades G0-G3 |
| Simulator | Our thesis simulator running **in the browser** (Python via Pyodide): create new worlds, change the rule and its thresholds, see one fraud as a network, click an account to see why it got its grade |
| Results | Precision and recall on 20 test worlds never used for tuning, by role, by fraud pattern, robustness |
| Real data | Ethereum phishing addresses (Jul 2022 - Feb 2023, Google BigQuery public dataset): where the money went, exchange deposit accounts reached, grades, check over time |
| Data explained | Every column the grades use, example rows, fraud patterns and roles |
| Sources | Data sets and studies used |

An optional "Ask Claude" box drives the simulator in plain language. It uses the visitor's own
Anthropic API key, which stays in the visitor's browser.

## Files

- `index.html`, `css/`, `js/`: the page (no build step).
- `py/`: the Python code of the thesis that the page runs (`sim.py`, `features.py`, `detectors*.py`),
  the frozen rules (`rules.json`) and the bridge to the page (`webapi.py`).
- `data/thesis.json`: our measured results, built from the result files of the experiments.
- `data/world_default.json`: one world generated in advance (seed 2027), shown while Python loads
  or if it cannot start.

## Run locally

```
python3 -m http.server 8000
```
then open http://localhost:8000.
