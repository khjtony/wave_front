# Visualizer design

A single static HTML file, generated from engine output, that lets a reader see where a model starts, what each actor could do at each tick, what was chosen, where trajectories fork, and when the balance was lost. It is the reading surface for every trace the project produces, from the toy model to the WW2 and Cold War episodes and the AGI reports.

Status: implemented (phase 0.14) and verified on the toy model; section 9 records the verified numbers and section 10 the choices settled during implementation.

---

## 0. What the reader needs to see

| Question | View |
|---|---|
| Where does the world start, and how safe is that start? | Initial state card with kernel membership and distances |
| What could each actor do at each tick, what did it do, and was that choice safe? | Trajectory board: decision lanes with alternatives classified as safe, risky or losing |
| How did the state change along the way? | Trajectory board: variable heatmap |
| When was the balance lost, and when did it become visible? | Trajectory board: status band with the point of no return, the loss point and the visible failure |
| Where do trajectories fork, and what did the other branch lead to? | Decision tree from any tick; compare view for two traces |
| What does the whole reachable space look like, and where is the boundary? | Landscape: every reachable state by tick and one variable, colored by status, with the two wavefronts |
| Which assumptions, actors and variables carry the result? | Tables: minimal relaxation sets, pivotal coalitions, sensitivity, speculative actions |

Everything is computed by the Python side (`wavefront.viz.bundle`) from the engine and analysis layer; the page only draws. Every chart has a table-view twin. Every value a tooltip shows is also reachable without hovering.

## 1. Encodings (fixed across all views)

Chosen by the job of the data, after the project's data-visualization guidance; colors from the reference palette there, declared once as CSS custom properties and validated with its script.

| Data | Job | Encoding |
|---|---|---|
| State status relative to a coalition's kernel for the selected *property* (`not E` for the selected ending, or a declared invariant; a filter-row select, defaulting to `not E`) | status | four reserved status colors with an icon and a label: **kept** (inside the kernel; good `#0ca30c`, icon ●), **contested** (neither side can force; warning `#fab219`, ◐), **lost** (the rest can force the invariant false; serious `#ec835a`, ◔), **failed** (the invariant is false; critical `#d03b3b`, ✕). Endings are a fifth, categorical mark (a small labeled flag), never a fifth status color. |
| Actors | identity | categorical slots in declaration order (slot 1 blue `#2a78d6`, slot 2 orange `#eb6834`, slot 3 aqua `#1baf7a`, then 4 to 8); Nature is the de-emphasis gray. Color follows the actor everywhere; filtering never repaints. Actors are always also named in text. |
| A variable's level over time | ordinal magnitude | one-hue ordinal ramp (blue, light to dark by level index, starting no lighter than step 250 on light); level names as selective direct labels where the level changes; one hue for every row because rows are not compared with each other |
| Two traces compared | identity | trace A slot 1, trace B slot 2; differing cells carry a muted ◆ marker and the second value in the tooltip; never a diverging ramp |
| Forward depth, backward rank | magnitude | sequential blue ramp with a scale legend; one at a time |
| Decision class of an alternative action | status | the same four status colors as state status, because a decision class is the status of the worst successor: **safe** (every completion stays kept), **risky** (some completion leaves), **losing** (every completion leaves), **ends** (every completion is terminal) |

Text never wears a data color. Marks are thin, gridlines are hairlines, every chart has a legend when it has two or more series, and dark mode is its own selected set of steps.

## 2. Page layout

```
┌ header: model name, fingerprint, horizon, profile, caveat ─────────────────────────┐
│ filter row: hypothesis (one select per swept variable) · coalition · ending · trace │
├ stat tiles: reachable states · kernel membership of s₀ · shortest distance ·        │
│             point of no return (reference trace) · minimum relaxation (ending)      │
├ 1. Initial state ──────────────────────────────────────────────────────────────────┤
├ 2. Trajectory board ───────────────────────────────────────────────────────────────┤
├ 3. Decision tree (from the selected tick) ─────────────────────────────────────────┤
├ 4. Compare (reference trace vs. a second trace) ───────────────────────────────────┤
├ 5. Landscape ──────────────────────────────────────────────────────────────────────┤
├ 6. Tables ─────────────────────────────────────────────────────────────────────────┤
└ footer: how to read this page; theme toggle; table-view toggles ───────────────────┘
```

The filter row scopes everything below it. Changing the hypothesis changes the initial state, the reference traces, the kernels shown and the landscape. Changing the coalition changes every status color on the page. Changing the ending changes the reference trace and the backward wavefront.

## 3. Views

### 3.1 Initial state card

- A table of variables: name, level (as a position on a small horizontal level scale, so two states can be compared by eye), provenance when a snapshot was loaded (indicator id, source, observed date, rule), and confidence.
- Status chips per analysed coalition: kept / contested / lost / failed, with the shortest distance to leaving the kernel and the margin.
- The endings reachable from this state with the minimum depth to each.
- When the hypothesis variable is swept, a note that the initial states of the other hypotheses look identical to the actors that cannot observe it (the list of such actors is computed from `observe`).

### 3.2 Trajectory board

One shared x axis of ticks, three stacked lanes, a crosshair that snaps to the nearest tick, and one tooltip listing the whole state and every actor's choice at that tick.

- **Status band**, one row per analysed coalition: a cell per tick in the status color with its icon; vertical markers at t_K (point of no return, "the coalition can no longer guarantee the invariant"), t_L ("the rest can now force failure"), t_φ ("the invariant is visibly false") and the ending; the silent phase [t_K, t_φ) is shaded with a hairline bracket and labeled.
- **Decision lanes**, one row per actor in actor color: the chosen action as a chip (text in ink, the actor color as a 2px left bar); hovering or focusing a tick expands the alternatives as ghost chips, each with its decision-class icon for the selected coalition; `idle` and `none` are shown but de-emphasized. The chip tooltip shows the guard expression, the `source`, and whether the action is speculative. A delayed action shows a pending marker on the ticks until its effect lands.
- **Variable heatmap**, one row per declared variable (built-ins collapsed behind a toggle): cells in the ordinal ramp by level index, a level-name label on the first cell and on every cell where the level changes, and a hairline tick mark where a latch fires.

### 3.3 Decision tree

Selecting a tick on the board (click or keyboard) opens the fan of alternatives from that state:

- Rows grouped by actor (actor color). Each row is one available action; to its right a thin stacked bar (status colors, 2px surface gaps) of the successor statuses over all completions by the other actors and Nature, with counts in the tooltip and the table twin; then the best and worst outcome labels; then the endings reachable from the best and worst successor with minimum depth.
- Choosing an action for every actor (or "as in the trace" for the rest) steps the tree one tick and appends to a **counterfactual trace** drawn on the board as a second line, so the reader builds the branch by hand. Where the counterfactual's status first differs from the reference, both the board and the tree show a **fork** marker with the tick number.
- Expansion is available while successor data is in the bundle (section 5); beyond that the page says so instead of guessing.

### 3.4 Compare

Two traces side by side on one tick axis: the reference and either the counterfactual built in 3.3, a trace to a different ending, or the same actions replayed under a different hypothesis (the page includes, for each reference trace, its replay under every other hypothesis when the moves stay available; where they stop being available the replay ends with a marker). Rows: both status bands, both decision lanes (chips side by side), the variable heatmap with ◆ on differing cells. A single line above states the first differing tick and what differed (an action, a Nature event, or the hidden variable).

### 3.5 Landscape

All reachable states for the selected hypothesis as points: x = tick, y = the level of a chosen variable (select), jittered inside the level band; color = status for the selected coalition; terminal states drawn as small flags labeled with their ending. The reference trace is a 2px line with 8px markers and surface rings. Modes: **status** (default), **forward** (sequential by BFS depth: the forward wavefront from s₀), **backward** (sequential by attractor rank to the selected ending: the backward wavefront). Canvas above 5,000 points with a nearest-point hover (24px minimum hit area) and the same tooltip as the board. A legend with icons; a table twin listing counts per tick and status.

### 3.6 Tables

Minimal relaxation sets per ending (with the quantifier stated: from some initial state of the selected hypothesis), pivotal coalitions per ending, the sensitivity rows, the speculative actions used by any shown trace, the uniformity notes, and the parameter budget. These are the same numbers the Markdown report prints; the page is not a second source of truth.

## 4. Interactions

- Crosshair snaps to ticks on the board and the compare view; one tooltip, every row.
- Marks are hit targets larger than themselves; keyboard focus shows what hover shows.
- Legend entries toggle-to-isolate; the actor legend never repaints survivors.
- Theme toggle (light, dark, system); the dark values are the palette's dark steps.
- Every figure has a "table" toggle that swaps the chart for its table twin.
- Labels and names from the model are inserted with `textContent`, never `innerHTML`.

## 5. Data bundle

`wavefront.viz.bundle(model, *, coalitions=None, endings=None, profile=None, initial=None, snapshot=None, max_states=..., max_moves=1_500_000) -> dict`, JSON-serializable:

```
meta        name, description, fingerprint, horizon, timed, profile, caveat, budget
variables   [{name, kind, levels, builtin, hidden_from, origin}]
actors      [{name, is_nature, color_slot, actions: [{name, guard_text, source, speculative, delay, is_idle}]}]
hypotheses  the swept variables and their values; the initial state id per combination
coalitions  [{name, members}]
endings     [names]
states      compact arrays over state ids: tick (or depth), terminal, ending, per-variable level index,
            per-coalition status code (0 kept, 1 contested, 2 lost, 3 failed), per-ending backward rank
moves       for states inside the neighborhood (section 5.1): per actor available action indices and,
            per joint move, the successor id (flat arrays)
traces      per hypothesis and ending: the reference trace (state ids, joint moves), its silent-phase
            indices per coalition, its decision classes per tick, actor and action for each coalition,
            and the replays under the other hypotheses
tables      relaxations, pivotal, sensitivity, uniformity, speculative actions (as in the Markdown report)
snapshot    the loaded snapshot's provenance per variable, when one was given
```

Guard text comes from a small expression formatter over the visitor protocol (`V.cap >= "agi" and ...`), kept in `wavefront.viz`, not in the core.

### 5.1 Size policy

The whole graph's move table is included when its joint-move count is at most `max_moves` (about 6 MB of JSON for 1.5 million moves). Above that, the bundle includes moves only for the neighborhood of the shown traces: every trace state, its successors, and their successors, and the page disables deeper expansion with a notice. The landscape always has the per-state arrays (a few integers per state). The page must stay under 16 MB including the embedded JSON.

## 6. Architecture

- `wavefront/viz/bundle.py`: computes the bundle from the engine and analysis layer (re-using `run_all` where it fits).
- `wavefront/viz/format.py`: the expression formatter.
- `wavefront/viz/template/`: `index.html`, `viz.css`, `viz.js`, inlined into one file at render time; no external resources, no build step, vanilla JS and SVG, canvas for the landscape above 5,000 points.
- `wavefront/viz/render.py`: `render_html(bundle, out_path)`; `wavefront.viz.render(model, out_path, **bundle_kwargs)`.
- `wf viz MODEL --out FILE [--profile P] [--snapshot S] [--coalition A,B] [--ending E] [--max-moves N]`.

## 7. Contract for implementation

Implement sections 1 to 6. Keep the Python side pure (bundle in, HTML out). Use the palette's CSS custom-property pattern with the dark values declared under both scopes. Validate the colors used with the guidance's validator script and record its output in the tests directory. Keep the JS in plain functions with the bundle as the single state; render every view from the filter state; no framework.

## 8. Tests

- Bundle: status codes per coalition agree with `contested` and `safe` on hand-built games; decision classes agree with their definition computed directly from successors; backward ranks agree with `attractor`; replays under other hypotheses stop where an action becomes unavailable; the size policy switches at `max_moves`; the bundle is JSON-serializable and round-trips.
- Formatter: every expression node kind renders and re-reads sensibly.
- Render: the file is self-contained (no `http` references), under the size limit for the toy, contains the caveat, and includes the JSON.
- Page: with Playwright (skipped when unavailable; Chromium is at the path in `PLAYWRIGHT_BROWSERS_PATH`), the toy page loads without console errors, every view renders at least one mark, the filter row changes the status band, and a screenshot is written to the test's temporary directory.

## 9. Acceptance on the toy model (verified)

Rendered from `models/toy/two_power.py`, hypothesis `aims = hegemonic`, coalition `{INC}`, ending `TAKEOVER`, property `not TAKEOVER`:

- the status band shows the point of no return t_K at tick 1, the loss point t_L also at tick 1 (from tick 1 the challenger and Nature can force the takeover whatever INC does: if INC resists, CH defects next tick), the declared invariant `balance` first false at tick 2 (marked separately), and the visible failure t_φ with the TAKEOVER flag at tick 3; the silent phase is [1, 3);
- the decision tree at tick 0 shows `resist` as the only safe INC action; `idle` and `concede` are risky (their worst successor is lost, but a CH that also idles keeps the play inside the kernel), which is the precise reading of the decision-class definition;
- the compare view against the `aims = limited` replay reports the first difference at tick 1, where `expand` stops being available to a limited challenger and the replay stops, and notes that the hidden variable differs throughout;
- the landscape shows the kept share falling with control (85 percent at control 0, 73 at 1, 40 at 2, all failed at 3) with the kept/lost boundary between control 1 and 2;
- no label collides, nothing overflows at 1280 or 390 pixels, both themes read, and the table twins carry every number. The toy page is 2.1 MB.

## 10. Settled during implementation

- Statuses are computed against a selectable property (section 1); the board also marks the first tick at which each other declared invariant is false.
- Status and decision icons are drawn as shapes (dot, half ring, quarter ring, cross) because the Unicode glyphs render unreliably.
- The bundle adds `schema`, `properties`, `all_endings`, `meta.default`, `meta.counts`, per-hypothesis `card` and `tables` (computed from that hypothesis's initial state) and per-hypothesis BFS `depth`; statuses are stored as one digit string per property and coalition to keep the page small.
- The landscape's backward mode has a "forced by" select defaulting to any play; the filter state is mirrored in the URL fragment and the theme choice is kept in browser storage, both as per-viewer conveniences.
- Narrow screens put row labels above rows and stack compare chips.
- Variables with more than five levels use adjacent ordinal-ramp steps below the validator's gap and rely on direct labels, tooltips and the table twin.
- `wf viz` also takes `--max-relax` and `--max-states`.
