# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary: the thesis jury. Examiners judging whether the method is sound, whether the results are measured honestly, and whether the candidate understands the limits. The site is mostly shown **live**, driven by the author on a projector during the defense or a talk; being opened alone from a link is secondary.

Secondary: researchers and curious readers who reach it from the thesis or GitHub.

## Product Purpose

"Fraudster +1" explains and demonstrates a thesis method for finding the people behind a crypto fraud. Starting from a blacklisted address, stolen money is traced into customer accounts at crypto exchanges, and each receiving account is graded G0–G3 from how it received and moved the money. Success: within a short live demo, the jury sees that the method finds far more of the people involved than today's €10,000 rule, understands why each account got its grade, and sees what the results do not prove.

## Positioning

Today exchanges look at accounts that received a large amount (the €10,000 rule), which misses most people involved. This method grades every receiving account on behaviour (share of the fraud money, concentration, pass-through within 24 h, fan-out to several mules at once) and adds a sharing protocol so exchanges can link the same person across exchanges without revealing customers. Headline from the 20 held-out test worlds: the €10k rule finds about 8 % of involved accounts, the grades about 61 %.

## Operating Context

- Shown on a projector in a defense room, with the author navigating; also opened later from a shared link.
- Sections: The idea, Simulator, Results, Real data (Ethereum, Jul 2022 – Feb 2023, Google BigQuery public dataset), Data explained, Sources.
- The simulator runs the actual thesis Python code in the browser; world seed 2027 reproduces the thesis runs exactly.
- Optional "Ask Claude" box drives the simulator in plain language with the visitor's own Anthropic API key, kept in the browser.

## Capabilities and Constraints

- Static site on GitHub Pages: plain HTML/CSS/JS, no build step, no server.
- The simulator must keep running the real thesis code through Pyodide (numpy, pandas), with a pre-generated world (`data/world_default.json`) shown while Python loads or if it cannot start.
- Every text exists in English and French (`js/i18n.js`).
- Terminology: grades G0 (no action), G1 (watch), G2 (review), G3 (strong case); detection rules "€10k rule", "Revision 2", "Revision 3"; visibility "One exchange alone" (V1) vs "With our sharing protocol" (V3); fraud patterns T1–T9 (no T6); roles such as mule, professional launderer, paid accomplice, framed customer.
- Precision and recall are measured only in simulation; real data allows indirect checks only.

## Evidence on Hand

- `data/thesis.json`: measured results (precision, recall, money caught, false alerts, by role, by pattern, robustness, 95 % bootstrap intervals over 20 test worlds).
- Real-data results: phishing addresses, exchange deposit accounts reached, their grades, the 90-day check over time, G3 deposit addresses with Etherscan links.
- `py/`: thesis code (`sim.py`, `features.py`, `detectors*.py`), frozen rules (`rules.json`).
- No testimonials, adoption by any exchange, or external validation exist; none may be implied.

## Product Principles

1. The argument comes first: the gap between the €10k rule and the grades must be visible within seconds of a live demo.
2. Every grade is explainable: any account can be opened to see the exact rules it passed or failed.
3. Honesty is part of the design: simulation vs real data, limits and intervals are always visible, never hidden.
4. Real accounts are indicators, not accusations: real addresses are shown with framing that makes clear only an exchange can confirm involvement.
5. Same seed, same numbers: the in-browser simulator must reproduce the thesis results.

## Accessibility & Inclusion

Readable from the back of a room on a projector (large type, strong contrast, colour never the only cue). Bilingual EN/FR throughout.
