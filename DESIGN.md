# Design: Fraudster +1

The locked system. Every design run reads this first and every view shares it. Change it on purpose; the file is the rule. It replaces the earlier "exhibit binder" system, which was retired in the Hallmark redesign.

## System
- Genre: editorial
- Shape of the report view: Map / Diagram (the fraud network carries the page); the simulator is an app screen
- Theme: Studio (cool proof paper with an ink dot grid, Hedvig Letters Serif over Geist, crop marks, orange construction lines)
- Axes: light/roman-serif/warm · posture: restrained

## Tokens
`css/tokens.css` is the source of truth; `css/style.css` adds the page tokens below. The roles:
```css
:root {
  --color-paper: oklch(97.2% 0.006 215);  --color-paper-2: oklch(94% 0.009 215);  --color-paper-3: oklch(90.5% 0.011 215);  --color-paper-hi: oklch(99% 0.004 215);
  --color-ink: oklch(16% 0.032 250);  --color-ink-2: oklch(34% 0.022 245);  --color-muted: oklch(49% 0.018 240);  --color-rule: oklch(84% 0.010 225);
  --color-accent: oklch(68% 0.172 50);  --color-accent-ink: oklch(16% 0.032 250);  --color-focus: oklch(52% 0.15 48);
  --font-display: "Hedvig Letters Serif", ui-serif, Georgia, serif;  --font-body: "Geist", ui-sans-serif, system-ui, sans-serif;
  --radius-card: 3px;  --radius-pill: 3px;  --rule-hair: 1px;  --shadow-card: none;
  /* page tokens (css/style.css): the grade ramp on the accent hue */
  --g0: #d5dce1;  --g1: #f7cfa6;  --g2: #ec8b3f;  --g3: #a6420f;
}
```
The spacing scale, the type scale, the easings and the durations are the scaffold's and live in `css/tokens.css`.

## The network encoding (shared by the hero, the path diagram, the simulator and the whole-world view)
- An account is a dot: fill from the grade ramp (`--g0` to `--g3`), and its grade drawn as line form as well: G1 one ring, G2 two rings, G3 two heavy rings. Grades must read in grayscale.
- Under the €10k rule a flagged account takes `--g3` with heavy rings; everything else `--g0`.
- Mistakes: an innocent account flagged gets a dashed `--color-error` ring; an involved account missed gets a solid ink ring.
- The blacklisted address is an ink disc with a paper cross; a collector is a muted square, dashed and marked "not traced" when the trace stops there.
- In the whole world, an account paid by two frauds or more gets a `--g2` ring; hovering lights its links in the accent.

## Controls
- Primary: orange fill (`--color-accent`), ink text, 1px ink border with a second rule inset 2px, 2px radius, 48px tall. One per view.
- Secondary: paper fill, same border, radius and height. Toggles: a segmented control, the pressed state in ink.

## Rules this system keeps
- Orange is a signal and a construction line, never a wash: no orange behind text or figures.
- No eyebrows, no tracked capitals, no middle-dot strings; labels are Geist a step smaller, sentence case.
- Crop marks only on printed pieces (a sheet, the real-data notice); the dot grid only on the hero and the world preview.
- Real accounts are indicators, never accusations.

## Motion
- Character: calm. One settle when a view opens; the money flow plays on demand; hover changes colour, not size. Under reduced motion everything ends at once.

## Exports
`css/tokens.css` in this project.
