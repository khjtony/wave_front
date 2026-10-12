# WW2 testbed data

Inputs to the WW2 v0 hindsight snapshots (`snapshots/ww2/hindsight/`) and to the replay
harness of [docs/ww2_testbed.md](../../docs/ww2_testbed.md) sections 6 and 8.

## Files

| File | What | Committed | Derived from |
|---|---|---|---|
| `raw/` | downloaded datasets, with `raw/MANIFEST.json` (URL, date, size, SHA-256 of each) | no (git-ignored) | `scripts/fetch_ww2_data.py` |
| `nmc_1936_1940.csv` | NMC rows for Germany, France, the United Kingdom, the USSR, Japan, Italy, the United States and Poland, 1933 to 1941 (70 rows: Poland has none after 1939) | yes | `raw/cow_nmc.rda` or an official NMC CSV |
| `events_ww2.csv` | dated structural events, 1935 to 1940, one row per event and variable | yes | written by hand from the sources in its `source` column |
| `realized_moves.csv` | the realized joint moves per quarter | yes | maintained with the historical documents, not by this pipeline |

## Sources and citations

- **Correlates of War, National Material Capabilities (NMC), version 7.0 (1816 to 2022).**
  Singer, J. D., Bremer, S. and Stuckey, J. (1972), "Capability Distribution, Uncertainty,
  and Major Power War, 1820-1965", in B. Russett (ed.), *Peace, War, and Numbers*; Singer,
  J. D. (1988), "Reconstructing the Correlates of War Dataset on Material Capabilities of
  States, 1816-1985", *International Interactions* 14(2). Data set page:
  https://correlatesofwar.org/data-sets/national-material-capabilities/
- **Correlates of War, Militarized Interstate Disputes (MID), version 5.0.** Palmer, G. et
  al. (2022), "The MID5 Dataset, 2011-2014: Procedures, coding rules, and description",
  *Conflict Management and Peace Science* 39(4). Data set page:
  https://correlatesofwar.org/data-sets/mids/
- **International Crisis Behavior (ICB), version 16.** Brecher, M. and Wilkenfeld, J.,
  *A Study of Crisis* (1997). https://sites.duke.edu/icbdata/ . No copy is reachable from the
  development environment: the ICB crisis names quoted in `events_ww2.csv` are given from the
  literature and must be checked against the data set when it is available.

**How the files were obtained here.** The official hosts are blocked from the development
environment, so the NMC and MID files were obtained through the R data mirrors in the
`peacesciencer` package (S. V. Miller), https://github.com/svmiller/peacesciencer :
`data/cow_nmc.rda` and `data/cow_mid_disps.rda`. The package documents `cow_nmc` as NMC
version 7.0 without the `stateabb` and `version` columns (the loader fills `stateabb` from the
COW codes and infers the version from the 2022 end of coverage), and `cow_mid_disps` as an
abbreviated MID 5.0 dispute-level table without participants. The mirror is a development
convenience: every citation above is to the data set itself, and every row and snapshot
indicator records `obtained_via`. The checksum of the raw file used for the committed extract
is in the extract's header.

**Licences.** The Correlates of War data are distributed free of charge by the project, which
asks users to cite the data set and its documentation; see the data set pages for the terms.
The raw files are not redistributed here. The committed extract and the test fixtures under
`tests/evidence/fixtures/` are small excerpts carrying the full citation. The `peacesciencer`
package's own licence (its `DESCRIPTION` file) governs the mirror files.

## How to fetch

```
pip install -e '.[data]'                     # pyreadr, needed only for the .rda mirrors
python3 scripts/fetch_ww2_data.py --mirror   # peacesciencer mirrors into data/ww2/raw/
```

On a machine that reaches the official host, download from the data set pages and either
pass the link or register the file:

```
python3 scripts/fetch_ww2_data.py --official --nmc-url <link to the NMC CSV or zip>
python3 scripts/fetch_ww2_data.py --from-file nmc=/path/to/NMC-60-abridged.csv
```

(`--official` without a URL prints the data set pages; the download links change with each
release, so none is built in.) An official CSV in `raw/` takes precedence over the mirror.
Each run rewrites `nmc_1936_1940.csv` from the raw file unless `--no-extract` is given; the
test `test_raw_mirror_reproduces_the_extract` checks that the committed extract equals a
fresh extraction whenever the raw file is present.

## What is derived

- `nmc_1936_1940.csv` is a row subset of NMC with no transformation. Units: `milex` thousands
  of current US dollars, `milper` thousands, `irst` thousands of tons, `pec` thousands of
  coal-ton equivalents, `tpop` and `upop` thousands; `-9` is missing (Italy 1941 `milper`).
- The snapshots read it through provisional thresholds and carry the annual value to each
  quarter of the year; see `snapshots/ww2/hindsight/README.md`.

## `events_ww2.csv`

Columns: `date, quarter, variable, level, event, source, note`. One row per event and
ontology variable it sets; an event that sets several variables (the declarations of war of
3 September 1939) has several rows. A row whose level equals the level already in force is a
dated confirming observation (the Pact of Steel for `axis`, the War Cabinet of May 1940 for
`britain`), kept so that the snapshot can cite it. The rows dated 1935 (German conscription,
the Anglo-German Naval Agreement, the Neutrality Act of 1935, Ethiopia) defend the
ontology's 1936Q1 initial levels.

Sources name the document (with its date), the data set (ICB crisis name) or a standard
reference with a chapter where the chapter is known (Weinberg 1994 ch. 1 for 1933 to 1939;
Kershaw 2007 ch. 1, 2 and 6); "(chapter not verified)" marks a reference whose chapter is not
yet checked. No page numbers are given. A `?` in the source cell marks a date or reference
recalled but not verified, and the note says which. Notes beginning "Threshold judgment" or
ending "For the historian" mark readings that the historian's review of the ontology should
confirm.
