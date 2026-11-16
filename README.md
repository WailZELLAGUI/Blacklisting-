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
| Results | Precision and recall on 20 test worlds never used for tuning (collector settings measured on our BigQuery data), by role, by fraud pattern, robustness; what the simulator assumes and how far the results hold when innocent accounts are added (stress tests) |
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
- `data/stress.json`: the stress tests of the Results page ("How far the results hold"), built from the result
  files of the experiments by `tools/build_stress.py` (`python3 tools/build_stress.py research/results`).
- `research/`: the stress-test and fraud-size scripts, their result files, and the preregistration of the fraud-size
  and peer-to-peer sweep (see `research/README.md`).
- `data/world_default.json`: one world generated in advance (seed 2027), shown while Python loads
  or if it cannot start; rebuilt by `tools/build_world_default.py`.
- `tests/`: checks that run without the network (see `tests/README.md`).

## Collector settings in every new world

Two settings about the fraudster's collector wallet come from our BigQuery data (1,448 phishing seeds):

- each world draws the share of frauds that use a collector between 26.7% and 71.2%: the share of seeds that send
  at least 99% (resp. 50%) of their money to one address; no source fixes this cutoff, so the world draws it;
- when there is a collector, the trace stops there for 8.9% of frauds (26 of 293 seeds, 95% CI 5.8-12.3%;
  7.1% to 9.3% for any cutoff from 50% to 99%). Such a collector is drawn dashed, "Collector not traced".

## Headline results (since 14 Nov 2026)

The Results page and the opening paragraph use 20 test worlds that were never used to choose a value, with the
early-warning list (ScamSniffer timing), each fraud graded 90 days after blacklisting (by then 93 % of the involved
accounts have received money). Recall counts every involved account that receives at least one traced payment; the
accounts behind a collector we cannot trace are left out (the Results page gives both counts). The default world 2027
uses the same settings.

**The baseline is the plain €10,000 rule**: an account is flagged when it received at least €10,000. Our earlier paper
used "at least €10,000, or the whole fraud if it is smaller"; that version is kept in `data/thesis.json`
(`main_E.ten_k_paper`) and quoted in a note under the results table.

**How far the results hold.** The Results page states the four settings of the simulator that no public source
measures, and shows stress tests on the same 20 test worlds with the frozen rule (`data/stress.json`): innocent accounts
that receive a large share of a fraud (an ordinary customer, or a seller who resells within hours), the same innocent
person paid at two exchanges, and more or fewer mules sending the money on to one shared address. These are breaking
points, not predictions.

**World settings, sourced on 14 Nov 2026.**
- Half of a fraud's money reaches our exchanges (`cex_share` 0.50): Chainalysis (Money Laundering and Cryptocurrency,
  2024) reports that over 50 % of illicit funds end at centralized exchanges (figure from the gated report, quoted by
  the press). The results also hold at 0.30 and 0.86 (Griffin & Mei, version 1, February 2024: $4.3B traced to
  exchanges out of more than $5B).
- 25-50 % of mule accounts are opened for the fraud, drawn per world: RUSI 2025 (Lloyds data: most mule accounts are
  older than a year) and FCA, Money mules: mule activity and cashing out findings (23 Sep 2026): 47.1 % of the accounts
  whose tenure is known (114,984) were closed within their first year.
- The number of exchange accounts and of innocent accounts paid by each fraud has no public source; it stays an
  assumption of the simulator (2 to 10 payments to the fraud's handlers).
- Fraud size is set by hand (median €30,000). Our sample of 1,448 real phishing addresses (Ethereum, ScamSniffer list,
  Jul 2022 - Feb 2023) sends a median of €1,874; other kinds of fraud are larger. On 20 new worlds (16000-16019) drawn
  from that sample, G2 or G3 keeps about the same false alerts per fraud (0.06 to 0.09) but finds fewer involved
  accounts, so its precision is 88.0 to 91.6 %; peer-to-peer resale lowers it further (Table 5 of the Results page).
  The sweep was fixed before it was run (`preregistration_p2p.md` and `experiments21.py` in the research code).

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

- every number on the site is read from the result files of the experiments (`data/thesis.json`, `data/stress.json`),
  not typed by hand;
- the page re-runs world 2027 in the browser and checks that it gives the same result as the stored run;
- every threshold is either taken from a cited source or chosen by a search on calibration worlds and tested
  on separate test worlds, as the site explains.

## License and citation

Code and text by Wail Zellagui. To cite this work, please cite the author's PhD thesis (LORIA, Université de Lorraine).

