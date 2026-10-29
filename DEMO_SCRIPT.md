# Demo script

Two parts, each ≤5 minutes. Part 1 is the business pitch — screen directions only, no
code. Part 2 is the technical walkthrough, built around the data-coverage
investigation rather than a file-by-file tour, because that investigation is the best
available demonstration of how this codebase is verified, not just written.

---

## Part 1 — Business pitch (≤5 min)

**Audience**: the purchasing desk and whoever signs off on using this tool's numbers.
**Goal**: show what the tool tells them each morning, and be straight about the one
thing in the error numbers they need to know before they trust them.

### Beat 1 — the decision (0:00–1:30)

Screen: **Decision view**, a mid-month date selected (e.g. 15 Jan 2026).

- Point at the chart: "This is the forecast the desk actually had in hand at gate
  closure — 11:00 the morning before delivery. Not a forecast published later with
  the benefit of hindsight — the one that existed at the moment the desk had to
  decide."
- Point at the three headline tiles: forecast volume, safe volume, risk buffer.
- "Safe volume isn't the forecast — it's the forecast minus a margin, sized from a
  month of real forecast error. At 90% confidence, this is the volume actual
  generation has met or beaten 90% of the time historically."
- Change the confidence selector (80% → 95%) live: "Tighten the confidence and the
  buffer grows — that's the desk trading off cost of over-buying against risk of
  coming up short."

### Beat 2 — the honest caveat, before trusting any error number (1:30–3:15)

Screen: **Accuracy view**. The "Known data caveat" banner is visible immediately —
don't scroll past it.

- "Before I show you forecast accuracy, there's something you need to know about
  these two numbers, because it changes how to read every chart on this page."
- "The actuals we compare against — FUELHH — only capture wind farms with
  transmission-level metering. Smaller, embedded wind farms aren't in that number.
  The forecast, WINDFOR, is trying to predict *all* GB wind, embedded included. So
  forecast and actual aren't quite measuring the same thing, and the error numbers on
  this page read more negative than the forecast's real skill, because of that gap —
  not because the forecast is that far off."
- "We didn't take that on faith — we checked it against National Grid ESO's own
  published embedded-wind numbers, and it holds up almost exactly. I'll show the
  numbers in Part 2."
- Scroll to the metrics table: "What doesn't change: the safe-volume number from
  Part 1. That's built directly from the real error distribution, not from an
  assumption that forecast and actual should match on average — so it's already
  accounting for this, and it's the number to act on."

### Beat 3 — the takeaway (3:15–5:00)

Back to **Decision view**.

- "So: trust the safe-volume and risk-buffer numbers on this screen to size
  purchases. Read the raw bias number on the Accuracy screen as 'mostly a reporting
  gap between two datasets, not a forecaster that's off by two gigawatts' — and we can
  show exactly how much of each, because we checked."
- Close on the forecast chart with the confidence band: "That shaded band is what the
  desk should actually plan around."

---

## Part 2 — Technical walkthrough (≤5 min)

**Audience**: engineers/reviewers.
**Goal**: demonstrate method, using the coverage-gap investigation as the worked
example, because it's the clearest evidence of how claims in this codebase get
verified rather than asserted. A codebase tour follows the same structure (api →
services → cache) described in `ARCHITECTURE.md`; this script doesn't re-walk it
file by file.

### Beat 1 — state the hypothesis and why it's dangerous to skip (0:00–0:45)

Screen: Accuracy view, metrics table.

- "Every slice of this table — every settlement period, every day, every
  actual-generation decile — shows the same thing: actual reads below forecast, by
  about 1,840 MW on average. The easy, wrong move is to write 'forecaster overshoots
  wind by ~1.8 GW' into the README and move on. That would be stating a conclusion
  with no evidence behind it, and if it's wrong, it's wrong in a way the client would
  repeat to their own stakeholders."

### Beat 2 — rule out a bug (0:45–1:45)

- "First question: is this even real, or is it a join/timezone bug — are we lining up
  the wrong forecast against the wrong actual?"
- "Test: shift the forecast ±1, ±2, ±4 settlement periods and recompute MAE. A real
  alignment bug would show *some* shift reducing error — the bug would have a
  'correct' offset that fixes it."
- Show/describe the result: "MAE across every shift tested: 2,048 to 2,295 MW. MAE at
  zero shift: 2,126 MW. No shift reduces it, and bias stays -1,800 to -1,856 MW
  throughout. There's no hidden offset. This rules out a bug."

### Beat 3 — check whether it's a simple scaling artifact (1:45–2:30)

- "Second question: does the error just scale with output — e.g. is it always ~15% of
  whatever the actual generation is? That would point at something more mundane, like
  a unit or calibration issue."
- Show the decile table: "Bias by actual-generation decile ranges from -677 MW up to
  -2,827 MW — -8.2% to -52.6% of that decile's mean. It's not flat in MW, and it's not
  a clean percentage either. That's consistent with a coverage gap — embedded wind
  capacity isn't a fixed share of total output across all wind conditions — but it
  doesn't prove it by itself."

### Beat 4 — the independent cross-check that actually confirms it (2:30–4:00)

This is the centrepiece — slow down here.

- "Third question: can we find outside evidence for *why*, not just rule things out?"
- "FUELHH's wind figure is built from Operational Metering of Balancing Mechanism
  units — transmission-connected wind farms. WINDFOR is NESO's national forecast,
  which is meant to approximate total GB wind, embedded included."
- "NESO happens to publish its own estimate of embedded wind generation, separately,
  as part of its demand-data series — because embedded wind is 'invisible' to them
  for metering purposes but still suppresses demand, so they model it. We pulled
  that series for January 2026, over the same 1,488 half-hourly periods as our data."
- State the numbers on screen or in a terminal:
  - FUELHH actual total: **8,616 GWh**
  - NESO's independent embedded-wind-generation total: **1,921 GWh**
  - Sum: **10,537 GWh**
  - Independently reported January 2026 GB wind record (trade press): **10,600 GWh**
  - **Difference: 0.6%.**
- "FUELHH alone is 81% of the independently reported total. FUELHH plus NESO's own
  embedded-wind number is within half a percent of it. That's not a coincidence we're
  reading into — it's a direct quantitative match against a source we don't control."
- "And WINDFOR itself sits at 9,985 GWh — 5.5% below that combined total, versus 16%
  *above* FUELHH alone. That's the signature of a forecast that's already targeting
  the combined total and running an ordinary, small underforecast — not a forecast on
  FUELHH's narrower scope."

### Beat 5 — say plainly what's still not proven (4:00–4:45)

- "Two honest limits, stated rather than glossed over. One: the bias we observe
  (-1,840 MW) is smaller than NESO's mean embedded-wind estimate for the month
  (2,582 MW) — so roughly 700–900 MW of the gap looks like ordinary forecast error on
  top of the coverage gap, not the coverage gap alone. Two: we went looking for a
  single primary-source sentence that explicitly defines WINDFOR's scope as
  'transmission plus embedded,' and didn't find one we could point at directly — this
  conclusion rests on the quantitative match against NESO's and trade press's
  independent numbers, not a documentation citation."
- "So the caveat in the product says 'dominant driver, confirmed quantitatively' —
  not 'fully explained' and not 'unverified guess.' That's the distinction that
  matters when this goes in front of a client."

### Beat 6 — close (4:45–5:00)

- "That's the standard applied throughout: decision rule, metrics, and this
  investigation are each backed by a test or an independent check, not just a
  plausible-sounding comment. `ARCHITECTURE.md` has the rest of the design decisions
  if you want the longer version."
