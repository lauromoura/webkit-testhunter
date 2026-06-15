# Test-results trend charts

Long-term trend charts for the WPE and GTK layout-test bots, built from the
archived JSON results in `../jsonresults/`.

## Pipeline

```
fetch.sh (parent repo) -> jsonresults/  -> report.py  -> <Config>.csv
                                        -> plot_trends.py -> PNGs
                                        -> pandoc        -> HTML gallery
```

- **`report.py`** consolidates a bot's JSON result files into one CSV (one row
  per build): `report.py ../jsonresults/<bot-dir> -o <Config>.csv --full-parse -c configuration=<Config>`.
- **`plot_trends.py`** reads those CSVs and renders multi-bot overlay charts per
  metric. It's a thin CLI over the importable **`trends/`** package
  (`data`, `windows`, `smoothing`, `style`, `render`, `charts`).

## Requirements

Python 3, pandas, matplotlib. `pandoc` for the HTML gallery.

## Usage

Everything is driven by the `Makefile` (CSVs are rebuilt from `jsonresults/` as
needed):

```
make trends        # charts for the default window (last 12 months), all standard bots
make trends-html   # the above, into trend-report/, plus an HTML gallery
make trends-legacy # same charts with the legacy (winsorize+ffill) smoothing
```

Or call the CLI directly:

```
./plot_trends.py [CSV ...] [time range] [--smoothing rolling7d|legacy|raw]
                 [--charts k1,k2,...] [--include-interrupted] [-d DIR]
```

With no CSV arguments it loads the standard set (WPE/GTK Release+Debug and
WPE-ARM64-Release).

### Time range

`--since YYYY-MM-DD` / `--until YYYY-MM-DD`, `--year 2025`, `--last 12m` (also
`90d`, `2y`), and `--windows 2024,2025,2024-25,2022-25` (several windows in one
run). The window is encoded in each output filename.

### Smoothing

`--smoothing rolling7d` (default) is a time-based 7-day rolling mean — gaps stay
NaN and spikes are preserved. `legacy` reproduces the older winsorize+ffill
chain (for comparison); `raw` plots the values as-is.

## Charts

Each chart overlays all configurations on one axis: WPE red, GTK green,
WPE-ARM64 purple; Release solid, Debug dashed in the port color. Metrics include
passing/skipped/fixable tests, unexpected crashes+timeouts (with the 50
early-exit threshold), failures, regressions vs flakies, and the interrupted-run
ratio. See `trends/charts.py` for the full list.

## Output

PNGs and the generated HTML are build output (gitignored). `make trends-html`
produces `trend-report/` for publishing to a web server; only its
`chart_details.md` source is tracked.

## Helpers

`inspect_report.py <file>.csv` prints a CSV and flags any out-of-order dates.
