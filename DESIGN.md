---
name: Fraudster +1
description: A thesis method presented as a forensic expert report, with numbered claims on one bond sheet and every claim cited to an exhibit tab.
colors:
  desk: "#e4e4df"
  bond: "#ffffff"
  ink: "#111111"
  ink-2: "#33332f"
  muted: "#5a5a55"
  rule: "#d4d4cf"
  rule-2: "#ecece8"
  margin-red: "#d47a7a"
  exhibit-blue: "#2a5db0"
  exhibit-blue-ink: "#1f4687"
  exhibit-yellow: "#f2c230"
  highlighter: "#f7d65a"
  exhibit-green: "#2c6e45"
  exhibit-grey-light: "#cfcfca"
  exhibit-grey-dark: "#5c5c5c"
  grade-g0: "#d8d8d4"
  grade-g1: "#f2c230"
  grade-g2: "#e07b1f"
  grade-g3: "#b3261e"
  ok: "#2c6e45"
  bad: "#b3261e"
  chart-blue-light: "#8fb0de"
  chart-grey: "#8a8a84"
  diagram-box: "#f6f6f3"
  link-grey: "#8d8d87"
  role-self: "#b03a2e"
  role-mule: "#e67e22"
  role-facilitator: "#7d3c98"
  role-accomplice: "#c9a227"
  role-p2p: "#5dade2"
  role-victim: "#45b39d"
  role-service: "#85929e"
  role-dust: "#d5d8dc"
  role-framed: "#2e86c1"
  role-bait: "#aab7b8"
  role-landlord: "#82c09a"
typography:
  display:
    fontFamily: "Libre Franklin, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "clamp(2rem, 1.4rem + 2vw, 2.9rem)"
    fontWeight: 800
    lineHeight: 1.15
    letterSpacing: "-0.015em"
  headline:
    fontFamily: "Libre Franklin, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "clamp(1.7rem, 1.3rem + 1.4vw, 2.3rem)"
    fontWeight: 800
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Libre Franklin, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "1.3rem"
    fontWeight: 800
    lineHeight: 1.15
  subtitle:
    fontFamily: "Libre Franklin, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "1rem"
    fontWeight: 500
    lineHeight: 1.5
  key-claim:
    fontFamily: "Source Serif 4, Georgia, Times New Roman, serif"
    fontSize: "clamp(1.3rem, 1.05rem + 0.9vw, 1.7rem)"
    fontWeight: 600
    lineHeight: 1.38
  body:
    fontFamily: "Source Serif 4, Georgia, Times New Roman, serif"
    fontSize: "1.125rem"
    fontWeight: 400
    lineHeight: 1.6
  data:
    fontFamily: "Libre Franklin, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "0.95rem"
    fontWeight: 400
    lineHeight: 1.4
    fontFeature: "tnum"
  label:
    fontFamily: "Libre Franklin, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "0.95rem"
    fontWeight: 700
    lineHeight: 1.2
  running-head:
    fontFamily: "Libre Franklin, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "0.8rem"
    fontWeight: 500
    lineHeight: 1.3
    letterSpacing: "0.04em"
  paragraph-number:
    fontFamily: "Libre Franklin, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "0.9rem"
    fontWeight: 600
rounded:
  none: "0px"
  tab: "8px"
spacing:
  hair: "4px"
  xs: "8px"
  sm: "12px"
  md: "18px"
  lg: "22px"
  xl: "28px"
  2xl: "40px"
  3xl: "56px"
  sheet-pad: "64px"
  gutter: "88px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.bond}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "10px 18px"
    height: "44px"
  button-primary-hover:
    backgroundColor: "#2b2b2b"
  button-primary-disabled:
    backgroundColor: "{colors.grade-g0}"
    textColor: "{colors.muted}"
  button-ghost:
    backgroundColor: "{colors.bond}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "10px 18px"
    height: "44px"
  button-ghost-hover:
    backgroundColor: "{colors.rule-2}"
  segment:
    backgroundColor: "{colors.bond}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "9px 14px"
    height: "42px"
  segment-selected:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.bond}"
  exhibit-tab-report:
    backgroundColor: "{colors.bond}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.tab}"
    padding: "14px 14px 14px 26px"
  exhibit-tab-a:
    backgroundColor: "{colors.exhibit-blue}"
    textColor: "{colors.bond}"
  exhibit-tab-b:
    backgroundColor: "{colors.exhibit-yellow}"
    textColor: "{colors.ink}"
  exhibit-tab-c:
    backgroundColor: "{colors.exhibit-green}"
    textColor: "{colors.bond}"
  exhibit-tab-d:
    backgroundColor: "{colors.exhibit-grey-light}"
    textColor: "{colors.ink}"
  exhibit-tab-e:
    backgroundColor: "{colors.exhibit-grey-dark}"
    textColor: "{colors.bond}"
  sheet:
    backgroundColor: "{colors.bond}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "48px 64px 72px 112px"
  grade-chip-g0:
    backgroundColor: "{colors.grade-g0}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "1px 6px 2px"
  grade-chip-g1:
    backgroundColor: "{colors.grade-g1}"
    textColor: "{colors.ink}"
  grade-chip-g2:
    backgroundColor: "{colors.grade-g2}"
    textColor: "{colors.ink}"
  grade-chip-g3:
    backgroundColor: "{colors.grade-g3}"
    textColor: "{colors.bond}"
  exhibit-sticker:
    backgroundColor: "{colors.bond}"
    textColor: "{colors.exhibit-blue-ink}"
    rounded: "{rounded.none}"
    width: "168px"
  ask-dialog:
    backgroundColor: "{colors.bond}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "16px 18px"
    width: "440px"
---

# Design System: Fraudster +1

## Overview

**Creative North Star: "The Expert Exhibit Binder"**

The site is a forensic-accounting expert report. One bond-white sheet lies on a grey desk; numbered paragraphs carry the argument in a reading serif, and every claim is cited to an exhibit the reader can pull from a coloured tab on the sheet's right edge. Evidence (simulator, results, real data, data notes, sources) lives behind those tabs, each exhibit opening with its own running head and reference code (FP1-R, FP1-A, FP1-B and on).

Density is that of a filed report, not a dashboard: ink rules separate things, tables are ruled not boxed, and colour is reserved for the binder's own stationery (exhibit tabs, the margin rule, the paragraph numbers, the highlighter) and for the grade and role encodings in the data. The academic-project template (hero, KPI tiles, card grid, pill navigation) is refused outright.

The system is built for a projector first: a large serif body (18px), black ink on white, heavy ink rules, and every grade readable in greyscale through drawn line forms.

**Key Characteristics:**
- A single bond sheet on a grey desk; exhibit tabs pinned to its right edge.
- Libre Franklin for headings, labels, tabs, tables and controls; Source Serif 4 for reading.
- Margin paragraph numbers (¶ 1, ¶ 2…) in exhibit blue, hung in a ruled left margin.
- Yellow highlighter only on the key figures of a claim.
- Square corners everywhere except the free edge of a tab.
- Grades always carry a line form (underline bars, rings) as well as colour.

## Colors

Stationery colours on a neutral desk: ink, bond and grey do the work; exhibit colours identify where you are; the grade ramp and role palette encode data and nothing else.

### Primary
- **Ink Black** (ink): text, heavy rules, primary buttons, selected segments, the language switch and the Ask button frames. The binder's one structural colour.
- **Exhibit Blue** (exhibit-blue): Exhibit A's tab, the exhibit sticker frame and band, focus outlines, the text caret, the "same person" dashed link in the network, and the leading Revision 3 series in charts. **Exhibit Blue Ink** (exhibit-blue-ink) is its text-weight darker form for links, citations and margin paragraph numbers.

### Secondary
- **Exhibit Yellow** (exhibit-yellow): Exhibit B's tab. Shares its value with the G1 grade.
- **Highlighter Yellow** (highlighter): marker strokes behind key figures (10 %, 62 %), the "try this" instruction, and text selection.
- **Ledger Green** (exhibit-green): Exhibit C's tab; also the **ok** state (passed-rule ticks, engine ready).

### Tertiary (data encodings)
- **Grade ramp** (grade-g0 Pale Stone, grade-g1 Watch Yellow, grade-g2 Review Orange, grade-g3 Case Red): G0 to G3 on chips, network node fills, and their legends. Case Red is also the **bad** state and the "innocent flagged" dashed ring.
- **Chart series**: Exhibit Blue for Revision 3, **Pale Blue** (chart-blue-light) for Revision 2 and secondary counts, **Rule Grey** (chart-grey) for the €10k rule, Case Red for negatives. Chart.js defaults: Libre Franklin 13px, label colour ink-2, gridlines rule-2.
- **Role palette** (role-self through role-landlord): the network's "colour by truth" view only, where every colour is named in the legend beside it.

### Neutral
- **Grey Desk** (desk): the page background the sheet rests on; also the phone tab strip's ground.
- **Bond** (bond): the sheet, tabs for the report, controls at rest, the dialog.
- **Ink Two** (ink-2): running heads, figure captions, chart labels, secondary diagram labels.
- **Muted** (muted): sub lines, notes, confidence intervals, disabled text, the reference code in a running head.
- **Rule** (rule) and **Rule Two** (rule-2): hairline table rules and borders; hover fills, user messages, bar-track and gridline grey.
- **Margin Red** (margin-red): the single 1px vertical margin rule on the sheet, desktop only.
- **Diagram Box** (diagram-box) and **Link Grey** (link-grey): exchange boxes and money-flow strokes in the network.
- **Exhibit greys** (exhibit-grey-light, exhibit-grey-dark): tabs D and E.

### Named Rules
**The Stationery Rule.** Exhibit colours mark exhibits (tabs, the sticker, citations) and never decorate content. If a colour is not stationery, it must be encoding data.

**The Highlighter Rule.** The highlighter goes only on the figures a claim rests on (one or two per paragraph, the bolded best row of a results table). It is a marker stroke, never a background for blocks.

**The Line-Form Rule.** A grade is never colour alone. Chips carry stacked ink underbars (G1 one bar, G2 two, G3 two heavier bars) and network nodes carry rings (G1 single, G2 double, G3 heavy double); "G0"–"G3" text always accompanies the colour.

## Typography

**Display Font:** Libre Franklin (with system-ui, Segoe UI, sans-serif), weights 500–800
**Body Font:** Source Serif 4 (with Georgia, Times New Roman), optical sizes 8–60, weights 400 and 600

**Character:** A plain, heavy grotesque for the report's apparatus (titles, tabs, tables, controls, captions) against a calm text serif for the argument itself. The sans speaks as the document; the serif speaks as the expert.

### Hierarchy
- **Display** (800, clamp 2rem–2.9rem, 1.15, −0.015em): the report's H1 on the first sheet only; max 22ch.
- **Headline** (800, clamp 1.7rem–2.3rem, −0.01em): each exhibit's H1.
- **Title** (800, 1.3rem): section heads inside a sheet, 56px above and 18px below. Smaller heads (h3) are 700 at 1.05rem.
- **Subtitle** (500 sans, 1rem/1.5, muted): the sub line under a title; max 60ch.
- **Key claim** (Source Serif 600, clamp 1.3rem–1.7rem, 1.38): the boxed ¶ 1 only; max 40ch.
- **Body** (Source Serif 400, 1.125rem/1.6): all reading paragraphs, max 68ch.
- **Data** (Libre Franklin 400, 0.95rem/1.4, tabular numerals on numbers): tables, figure captions, notes (0.92rem, muted).
- **Label** (Libre Franklin 700, 0.95rem): tab names, buttons, table captions, table heads, legends. Tab letters set at 1.5rem 800.
- **Running head** (Libre Franklin 500, 0.8rem, +0.04em): the caption line at the top of every sheet page.
- **Paragraph number** (Libre Franklin 600, 0.9rem, exhibit-blue-ink): ¶ numbers in the margin.

### Named Rules
**The Two Voices Rule.** Argument in the serif; everything the reader operates or scans (tabs, tables, controls, captions, charts) in the sans. Never set a table or control in the serif.

**The Small Caps Restraint Rule.** Uppercase tracked labels appear only as heads of their own block (the "Limits" boxes, account-card subheads, the rule-selector label before its control). Nothing uppercase sits above a heading as a lead-in.

## Layout

A two-column binder: the sheet (max 920px, or 1240px on wide exhibits) plus a 164px tab column, centred on the desk with 24px side padding. The sheet pads 48px top, 64px right (sheet-pad), 72px bottom and 112px left: an 88px margin gutter (gutter) holds the ¶ numbers to the left of a 1px margin-red rule. Reading columns hold at 68ch; key-claim at 40ch; notices and grade lists at 72ch.

Rhythm: paragraphs 22px apart; section heads 56px above, 18px below; folds 28px above; figures in a two-column grid with 40px row and 48px column gaps; tables 28px below.

Responsive:
- **≤1180px:** the simulator's network/account-card split (1fr + 340px) and figure grids collapse to one column.
- **≤900px:** gutter shrinks to 40px and sheet-pad to 22px; the margin rule disappears; the tab column becomes a sticky horizontal **tab strip** above the sheet on the desk ground (tabs rounded on their top corners, current tab 5px taller, strip scrolls sideways with a right-edge fade and hidden scrollbar); the sticker drops into flow at −2°; segmented controls stretch to equal full-width columns; the network gains a "scroll sideways" hint and a right-edge fade (the graph keeps a 640px minimum); measurement grid goes to two columns; the Ask dialog spans the viewport with 16px insets.
- **≤480px:** measurement grid goes to one column; segments tighten to 9px 10px at 0.88rem.

Print drops the desk, tabs, sticker, language switch and Ask button, and flattens the sheet.

## Elevation & Depth

Depth is physical paper, not interface layering. Three things lift: the sheet off the desk, the tabs behind the sheet, and the Ask dialog over everything. All shadows are soft and ambient; nothing uses a hard offset. Everything inside the sheet is flat and separated by ink rules.

### Shadow Vocabulary
- **Sheet** (`box-shadow: 0 1px 2px rgba(0,0,0,.08), 0 10px 30px rgba(0,0,0,.08)`): the bond sheet on the desk. Removed in print.
- **Tab** (`box-shadow: 0 2px 6px rgba(0,0,0,.08)`): resting exhibit tabs. The current tab deepens to `0 2px 10px rgba(0,0,0,.16)`. Tabs lose shadows in the phone strip.
- **Dialog** (`box-shadow: 0 12px 36px rgba(0,0,0,.22)`): the Ask Claude panel only.

### Named Rules
**The Paper Only Rule.** Only paper objects cast shadows: the sheet, the tabs, the floating dialog. Content inside the sheet never does.

## Shapes

Square. Every box, button, control, chip, table, figure, notice, sticker and dialog has 0 radius. The only curve is the free edge of an exhibit tab (8px on the outer corners: right corners on desktop, top corners in the phone strip) and round legend dots and network nodes.

Borders come in a fixed ink vocabulary: 1px hairlines (rule) for table rows and fieldsets; 2px ink for table heads, figure tops, fold tops, account-card tops, control frames; 2px ink above and below for the key claim and the Limits block; 3px ink for the full-frame Real-data notice; 3px exhibit blue for the sticker. The one vertical accent is the 1px margin rule.

## Components

### Sheet and Running Head
The bond sheet is the page; only one sheet page shows at a time. Each page opens with a running head: the exhibit name left, the reference code (FP1-R, FP1-A…) right in muted, on a 1px ink underline, 36px above the title. The left side truncates with an ellipsis rather than wrapping.

### Exhibit Tabs
Paper tabs pinned to the sheet's right edge, sticky 24px from the top, starting 72px down. Each shows its letter (1.5rem 800) over its name (0.95rem 700): R bond, A blue, B yellow, C green, D light grey, E dark grey. At rest a tab tucks 12px under the sheet; on hover it pulls out to −4px; the current tab sits flush (0) with a deeper shadow. Tab pull eases `margin-left .18s cubic-bezier(.2,.8,.2,1)`. On phones they become the horizontal tab strip described in Layout, letter and name inline.

### Numbered Paragraphs and Key Claim
Each argument paragraph is numbered "¶ n" in the left margin, right-aligned against the margin rule in exhibit-blue-ink. The key claim (¶ 1) sits between two 2px ink rules with 22px vertical padding, set in the key-claim style, its decisive figures highlighted. Citations ("see Exhibit A") are sans 500 links that never wrap.

### Highlighter
A highlighter-yellow mark with 0.18em side padding and cloned box decoration, so a broken line keeps both ends. Ink text on top.

### Exhibit Sticker
The primary call to open an exhibit: a 168px square-cornered label with a 3px exhibit-blue frame, a solid blue band reading "EXHIBIT" (0.85rem 800, +0.2em, white), the exhibit letter at 2.4rem 800 over a 2px blue rule, and a short action line. Placed top right of the first sheet, rotated −4°; hover straightens to −2° and scales 1.03. In flow at −2° on phones.

### Ruled Tables
Full-width, collapsed, sans 0.95rem. Caption top-left in 700 with the exhibit table number ("Table B-1"). Head row on a 2px ink rule, body rows on 1px rule hairlines, first column flush left. Numbers right-aligned, tabular, unwrapped; confidence intervals muted at 0.85em. No zebra striping, no cell fills, no outer frame. Wide tables scroll horizontally inside their wrapper.

### Figures
A figure opens on a 2px ink rule, then a caption (bold title line, then a 0.95rem ink-2 explanation), then the chart. Every chart gets a screen-reader data table and a role="img" label from its caption. Chart animation is 500ms or none under reduced motion.

### Measurement Grid
Simulator results for one world: three ruled columns of label (0.85rem 600), value (1.5rem 800 tabular), and a muted sub line. Cells are divided by 1px rule hairlines only; no fills, frames or shadows.

### Buttons and Links
- **Shape:** square (0), 2px ink frame, min height 44px.
- **Primary:** ink fill, white 0.95rem 700 sans, 10px 18px; hover lifts to #2b2b2b.
- **Ghost:** bond fill, ink text; hover fills rule-2.
- **Disabled:** G0 grey fill and frame, muted text, not-allowed cursor.
- **Text link button:** blue-ink, underlined at 0.18em offset, 600 0.92rem.
- **Focus:** a 3px exhibit-blue outline at 2px offset on everything.

### Segmented Controls
A 2px ink frame around flat bond buttons divided by 2px ink rules; the pressed button inverts to ink with white text (aria-pressed); hover on others fills rule-2. Used for the rule selector (€10k, Revision 2, Revision 3), visibility, and colour-by modes. The language switch (EN/FR) and the Ask button use the same inversion.

### Fields
Sans 0.92rem labels with the live value floated right in tabular bold; range inputs and checkboxes take ink as their accent colour; selects and text inputs have a 2px ink frame on bond, no radius.

### Folds
Disclosures open on a 2px ink rule: a 1.02rem 700 summary with an optional muted sub line, and a "+" that becomes "–" when open, set in the sans at 1.3rem 800. The browser marker is hidden.

### Account Card
Opens on a 2px ink rule: account title 1.1rem 800, exchange sub line, a two-column fact table (values bold, right-aligned), then per-grade rule checklists headed by their grade chip. Each rule shows a drawn 14px SVG mark: a ledger-green tick when passed, a muted cross when failed, stroke 2.4 with square caps, and a screen-reader "yes/no" before the text. The role line names the role and says "involved" or "innocent" in words.

### Grade Chips
Inline 2.6em minimum blocks, 0.85rem 800, square, filled with the grade colour, with stacked ink underbars drawn by inset shadows: G0 none, G1 one 2px bar, G2 two bars, G3 two 3px bars with white text.

### Network Graph (Exhibit A)
An SVG on bond inside a 1px rule frame. The blacklisted seed is an ink disc with a drawn white cross; exchanges are diagram-box rectangles with rule strokes and 15px 700 labels; money flows are link-grey Bézier strokes at 50% opacity, weight scaled by amount. Account nodes fill with the grade colour (or the role colour in the truth view) with a white 1.5px stroke, plus grade rings in ink (G1 one ring, G2 two, G3 two at 2.5px). Misses are rings at r+8: Case Red dashed for an innocent flagged, solid ink for an involved account missed. The same person across exchanges is joined by a dashed exhibit-blue line. Hover or selection draws a 3px ink stroke; keyboard focus a 3px blue ring. Legends repeat the ring swatches beside every grade name.

**Money-flow play:** links draw on via stroke-dashoffset (0.7s, `cubic-bezier(.2,.8,.2,1)`), staggered by route order over about 2.6s after a 300ms lead; nodes fade in over 0.4s behind them. Under reduced motion the finished graph appears at once.

### Notices and Limits
The Real-data notice is a full 3px ink frame (18px 22px padding) above the content, stating that real accounts are indicators that only an exchange can confirm. Limits blocks sit between two 2px ink rules with an uppercase tracked 1rem head.

### Ask Claude Dialog
A fixed panel 440px wide, 24px from the right and 72px from the top: bond, 2px ink frame, dialog shadow, sans throughout. User messages sit on rule-2; assistant messages open on a 2px ink rule; tool notes are muted 0.85rem. Key field and textarea use 2px ink frames.

### Motion
- **Page turn:** the incoming sheet page slides 14px from the right and fades up from 0.25 opacity in 0.32s `cubic-bezier(.16,1,.3,1)`.
- **Tab pull** and **sticker straighten:** 0.18s `cubic-bezier(.2,.8,.2,1)`.
- **Smooth scroll** only when motion is allowed.
- **Reduced motion:** every transition and animation is cut globally; charts render without animation; the network play shows the end state; scroll-into-view jumps.

## Do's and Don'ts

### Do:
- **Do** put every argument paragraph on the sheet with a margin ¶ number in exhibit-blue-ink, and cite the exhibit that proves it.
- **Do** separate content with ink rules (1px hairline, 2px structural, 3px for a framed notice) rather than boxes, fills or shadows.
- **Do** give every grade a line form (chip underbars, network rings, legend ring swatches) plus its "G0"–"G3" name.
- **Do** keep the highlighter to the figures a claim rests on.
- **Do** frame real accounts as indicators that only an exchange can confirm, in a full ink notice ahead of the data.
- **Do** draw marks (ticks, crosses, seed cross) as SVG strokes, with screen-reader text alongside.
- **Do** keep every corner square except the free edge of a tab (8px).
- **Do** cut all motion under prefers-reduced-motion and show end states.

### Don't:
- **Don't** build KPI tiles, stat cards, a hero, a card grid or pill navigation; numbers live in ruled tables and the ruled measurement grid.
- **Don't** set an uppercase lead-in (eyebrow or kicker) above a heading.
- **Don't** use a side-accent border thicker than 1px; the margin rule is the only vertical accent.
- **Don't** use glyph or emoji icons; draw marks in SVG or name them in words.
- **Don't** let colour alone carry a grade, a pass/fail, or an involved/innocent status.
- **Don't** use exhibit colours to decorate content, or the role palette outside the network's truth view.
- **Don't** add hard offset shadows or shadows inside the sheet.
- **Don't** set tables, controls or captions in the serif.
