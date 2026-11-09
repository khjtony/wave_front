# Cold War v1: V6 (a) under the ambiguous projection window (exploratory)

**Exploratory.** This is not a rerun of V6 and changes no verdict. cw_v1's first sight is recorded (reports/cw_v1.md section 6), and V6 (a) failed in 1961. This note asks one question of its inputs. V6 (a) compares the replayed band of `belief_force_USA` with the hindsight `count_USSR` band at the date the estimate projects for. Does that comparison stay the same for every member of the estimates' own low-to-high spread? It compares inputs only: no model, engine or kernel is run. Each year is **robust** (the same answer from every member) or **fragile** (the answer depends on the member). Members are not weighted (docs/ambiguous_levels.md section 2).

## The window as built (owner's decision 7j, candidate 4)

The window is built by `scripts/build_ambiguous_layer.py` from `data/ambiguous_windows.csv` and `data/ambiguous_members.csv` into `snapshots/cw_v1/replay_ambiguous/`. The canonical `snapshots/cw_v1/replay/` is unchanged, and `tests/evidence/test_ambiguous_layer.py` checks it against its builder. A member's band is the estimate's projection for the date it projects for, read on decision 7g's count (ICBM launchers, heavy bombers and tankers, and SLBM launchers where the estimate counts missile submarines; docs/cw_v1_decisions.md D9). The low and high ends put every range at its low or high end. The canonical member is the canonical row, read at the midpoints. The estimates were read in the crest corpus with `wavefront.evidence.corpora.crest`.

| 1 Jan | Estimate (projected for) | Low end | Canonical (midpoints) | High end | Set |
|---|---|---|---|---|---|
| 1958 | SNIE 11-10-57 (10 Dec 1957), Concl. 3 and 4, with NIE 11-4-57 (12 Nov 1957), para. 23a and the table at para. 139 (mid-1960) | 500: 100 ICBMs (first capability mid-1959, 100 a year later) + 400 heavy bombers and tankers | about 580 | 1,100: 500 ICBMs (first capability mid-1958, 500 two years later) + 600 | {under_1000, over_1000} (**built**) |
| 1959 | NIE 11-4-58 (23 Dec 1958), para. 150 and the Long Range Aviation table (mid-1961) | 250: 100 ICBMs + 150 | about 430 | 750: 500 ICBMs (two-year build-up) + 250 | {under_1000}: one band, not built |
| 1960 | NIE 11-4-58 carried (NIE 11-5-59 projects no force) (mid-1961) | 250 | about 430 | 750 | {under_1000}: one band, not built |
| 1961 | NIE 11-8-60 (1 Aug 1960), Concl. 5 and 12, paras. 33 to 40 (mid-1963) | 482: program C 200 launchers + 130 bombers and tankers + 152 SLBM (330 without the submarines) | about 700 (program A) | 1,018: program B 700 + 130 + 188 SLBM | {under_1000, over_1000} (**built**) |

Two notes on the inputs:

- **1961's high member sits on the band edge.** The 4 Z-class, 18 G-class and 6 nuclear submarines carry 2, about 6, and 6 to 12 missiles each. At 12 per nuclear boat the high case is 1,018; at the midpoint of 6 to 12 it is 1,000, still `over_1000`; at 6 it is 982, `under_1000`. Program B is the USAF's program. The estimate presents its three programs as "the range of judgments" (Conclusion 5), and the DCI regarded program A as the nearest.
- **1958's canonical row reads the wrong column of NIE 11-4-57's table.** The row in `data/cw/v1/events.csv` gives 250 to 450 heavy bombers and tankers for mid-1960. That is the table's mid-1959 column. The mid-1960 column and para. 23a give 400 to 600. With those figures the midpoints give about 730 instead of 580, which is still `under_1000`, so the band and V6 are unaffected. The finding is recorded here and in the window's text; the canonical row is not changed (that is the owner's call).

## V6 (a) across the spread, per year

The count is the hindsight `count_USSR` at the projected date, read from the latest 1 January not after it (decision 7i). The blind series' rule dates (the estimate plus 30 months: 1960-05, 1961-06, 1961-06, 1963-02) read the same count years as the recorded dates, so the reading below holds for the blind series and the hand-coded one alike.

| 1 Jan | Count at the projected date | Exceeds, per member | Reading |
|---|---|---|---|
| 1958 | 1960: 108, `under_200` | under_1000: yes; over_1000: yes | **robust** (exceeds) |
| 1959 | 1961: 138, `under_200` | under_1000: yes (single member) | **robust** (exceeds) |
| 1960 | 1961: 138, `under_200` | under_1000: yes (single member) | **robust** (exceeds) |
| 1961 | 1963: 235, `under_1000` | under_1000: no; over_1000: yes | **fragile** |

**Reading.** The 1958 to 1960 rows of (a) are robust: every member exceeds the count. The 1961 failure is fragile. On the estimate's midpoints (program A) the projection and the count fall in the same band. On its high case (program B) the projection exceeds the count by a band. That high case is itself at the band's edge, decided by how many missiles each nuclear submarine carries. So "(a) in every year 1958 to 1961" is fragile, and the fragility is all in 1961. This agrees with section 6.2 of reports/cw_v1.md: the bands of decision 7g cannot express the 1961 error (a projection about three times the force) once the comparison moves to 1963. The recorded verdict stays a fail; this note does not reread it.
