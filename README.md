# Fraudster +1

**Following stolen crypto into exchange accounts, to find the people behind a fraud.**
*Suivre les cryptos volées jusque dans les comptes des plateformes d'échange, pour retrouver les personnes derrière une fraude.*

Interactive website (English / French): open `index.html` through GitHub Pages.

**Author:** Wail Zellagui, PhD candidate in cybersecurity, LORIA, Université de Lorraine.
This site accompanies the chapter "Fraudster +1" of the author's PhD thesis on fraud in cryptocurrencies.

## What is in the site

| Section | Content |
|---|---|
| The idea | The method in four steps and the meaning of the grades G0-G3 |
| Simulator | Our thesis simulator running **in the browser** (Python via Pyodide): create new worlds (patterns, mules, collector, blacklisting timing, grading date), change the rule and its thresholds, see one fraud as a network or the whole world as one interactive network (drag, zoom, hover), click an account to see why it got its grade |
| Results | Precision and recall on 20 test worlds never used for tuning (collector settings measured on our BigQuery data), by role, by fraud pattern, robustness |
| Real data | Ethereum phishing addresses (Jul 2022 - Feb 2023, Google BigQuery public dataset): where the money went, exchange deposit accounts reached, grades, check over time; when scam addresses get blacklisted (ScamSniffer alerts, Tether freezes) and how many exchange accounts are already reached by then |
| Data explained | Every column the grades use, example rows, fraud patterns and roles |
| Sources | Data sets and studies used |

An optional "Ask Claude" box drives the simulator in plain language. It uses the visitor's own
Anthropic API key, which stays in the visitor's browser. It is a feature of the page, not part of the method.

## Files

- `index.html`, `css/`, `js/`: the page (no build step).
- `py/`: the Python code of the thesis that the page runs (`sim.py`, `features.py`, `detectors*.py`),
  the frozen rules (`rules.json`) and the bridge to the page (`webapi.py`).
- `data/thesis.json`: our measured results, built from the result files of the experiments.
- `data/world_default.json`: one world generated in advance (seed 2027), shown while Python loads
  or if it cannot start.

## Collector settings in every new world

Two settings about the fraudster's collector wallet come from our BigQuery data (1,448 phishing seeds):

- each world draws the share of frauds that use a collector between 26.7% and 71.2%: the share of seeds that send
  at least 99% (resp. 50%) of their money to one address; no source fixes this cutoff, so the world draws it;
- when there is a collector, the trace stops there for 8.9% of frauds (26 of 293 seeds, 95% CI 5.8-12.3%;
  7.1% to 9.3% for any cutoff from 50% to 99%). Such a collector is drawn dashed, "Collector not traced".

## Headline results (since 14 Nov 2026)

The Results page and the opening paragraph use 20 test worlds that were never used to choose a value, with the
early-warning list (ScamSniffer timing), each fraud graded 90 days after blacklisting (by then 93 % of the involved
accounts have received money). Recall counts every account the fraud will ever pay. The default world 2027 uses the
same settings.

**World settings, sourced on 14 Nov 2026.**
- Half of a fraud's money reaches our exchanges (`cex_share` 0.50): Chainalysis (Money Laundering and Cryptocurrency,
  2024) reports that over 50 % of illicit funds end at centralized exchanges (figure from the gated report, quoted by
  the press). The results also hold at 0.30 and 0.86 (Griffin & Mei: $4.3B of over $5B of pig-butchering money traced
  to exchanges).
- 25-50 % of mule accounts are opened for the fraud, drawn per world: RUSI 2025 (Lloyds data: most mule accounts are
  older than a year) and the FCA multi-firm review of Sep 2026 (47.1 % of offboarded mule accounts closed within their
  first year).
- The number of exchange accounts and of innocent accounts paid by each fraud has no public source; it stays an
  assumption of the simulator (2 to 10 payments to the fraud's handlers).

**The lead rule, shown as "Revision 2"** (`rev5` in the code: G2 share 20 %, concentration 50 %, 90 % passed on within
24 h, either one). The thresholds are not one "right" point: the site's box "Stable values" shows the value sets that keep
at least 90 % precision, with a margin for chance, in all three plausible worlds (30 %, 50 %, 86 % of the money
reaching our exchanges): G2 share 20 % and a 24 h window are fixed, concentration and the share passed on can be anything
from 50 % to 90 % (`experiments17c.py`). Revision 3 adds the fan-out route: it finds more but raises more than twice the
false alerts (0.18 per fraud against 0.08), and on real data two exchange accounts paid by the same scammer are a median
of 25 days apart, so its 6-hour route would rarely fire.

Earlier headlines are kept in `data/thesis.json` for comparison: `main_E_handset` (hand-set timing, end of a 180-day
period).

## Blacklisting date in every new world

When a world is created you choose how fast the scam addresses are blacklisted, and when each fraud is graded:

- **hand-set** (earlier results, 180 days): blacklisted 2 to 20 days after the first money, payments in one burst;
- **early-warning list**, measured on 551 ScamSniffer scam addresses (Jul 2022 - Feb 2023): blacklisted a median
  6 days after the first money, and most payments to exchange accounts come after that date (365 days simulated);
- **late freeze**, measured on 261 addresses frozen by Tether (USDT, 2023): a median 26 days after the first money,
  once most of it has already left (365 days simulated).

Grading at 1, 7, 30 or 90 days after blacklisting uses only the money moved by then; the counts are then over the
accounts already reached. The Real data page compares the measured delays with the simulator (table 5 and figure 4 of that page).

## Run locally

```
python3 -m http.server 8000
```
then open http://localhost:8000.

## How this work was made

The research questions, the method (the evidence grades G0-G3, the fan-out route and the cross-exchange
protocol), the choice of data sources, every threshold and the reading of the results are the author's.

Parts of the implementation, mainly this website's interface and parts of the simulator and data-processing
scripts, were written with the help of Claude Code (Anthropic), an AI coding assistant, under the author's
direction. The code was reviewed, run and tested by the author, and the results are reproducible:

- every number on the site is read from the result files of the experiments (`data/thesis.json`), not typed by hand;
- the page re-runs world 2027 in the browser and checks that it gives the same result as the stored run;
- every threshold is either taken from a cited source or chosen by a search on calibration worlds and tested
  on separate test worlds, as the site explains.

## License and citation

Code and text by Wail Zellagui. To cite this work, please cite the author's PhD thesis (LORIA, Université de Lorraine).

