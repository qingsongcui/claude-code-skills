# Known failure boundaries — Autonomous Slide Deck Engine (buyer-facing)

Eight places where the engine either **silently passes bad input**, **fails
loudly you can rely on**, or **needs a step the README does not mention**.
Verified on 2026-09-11 against two decks on this machine: the shipped Beaconloop
QBR (10 pages, `demo/qbr-project/`) and a fresh one-page Kestrel board update
(`demo/d3-single/`). Every row is a real command output, not a hypothetical.

| # | Situation | What the engine does | Gate verdict | What a buyer has to do |
|---|---|---|---|---|
| 1 | Body copy at 10px, text crammed top-to-bottom | Renders fine, no warning | Density gate `PASS failures=0` — it measures **vertical coverage (24 bands × 30px)**, not font size | Keep body ≥ 16px. A density PASS is not a readability guarantee. |
| 2 | Declared brand font is not installed on the machine that opens the `.pptx` | Chromium and python-pptx both fall back to a system face silently | No gate asserts font availability | Install the font on both the build machine and the reader's machine, and eyeball one render PNG before delivery. The demos pin `Arial` for this reason. |
| 3 | Page has no `[id$="-chart"]` element | `shoot-charts.mjs` prints `No [id$="-chart"] chart elements detected, skipping.` and exits 0 without writing anything | Not a failure — silent skip | Downstream `build-pptx.py` refuses to build without the PNG (exit 3, see row 5), so nothing ships silently. Check the capture log line exists before building. |
| 4 | Empty `pages/` directory | `render-deck.mjs` exits 1 with `no .html files found in <dir>` | Loud | Nothing to fix. |
| 5 | Chart PNG missing when `build-pptx.py` runs | Exits 3 with `FATAL: chart capture missing … Run shoot-charts.mjs first` | Loud, with recovery command | Run `shoot-charts.mjs` on the exact page file, then rebuild. |
| 6 | Bottom half of a slide is contiguous whitespace ≥ 1/3 viewport height | `check-density.mjs` FAILs with per-file pixel counts | Loud | Add a takeaway strip or enlarge metric blocks. The Beaconloop demo failed 5/10 pages on the first run this way and passed after the fix (see `demo/DEMO-RUN.md` step 4). |
| 7 | Expecting `brief → deck` with zero authoring | The engine ships a 1-slide `build-pptx.template.py` skeleton; the per-deck content layer (`build-pptx.py`) **and** the HTML pages are hand-authored by you or your agent from a master. The engine renders, gates, and assembles — it does not invent pages from a brief. | Not a gate — expectation | Budget for page authoring. See `demo/d3-single/` for one worked single-page example (brief → HTML → build-pptx.py → passing deck, 30 native text runs). |
| 8 | First run on a fresh machine, or offline | Playwright downloads ~82 MB Chromium (rev 1187 for npm 1.55.0). Offline machines cannot render at all. | Not a gate — environment | `npx playwright install chromium` on a networked machine before the run. Cache lives at `~/Library/Caches/ms-playwright/` (macOS) / `%LOCALAPPDATA%\ms-playwright\` (Windows). |

## What "half-editable" actually means in the `.pptx`

Native `python-pptx` text boxes and vector shapes for every piece of copy,
metric card, timeline node, and takeaway strip. Only complex ECharts/SVG
visuals are rasterised to 3× PNG. Verified on the D3-B single-page deck:
30 native text runs / 937 characters on one slide, all selectable in
PowerPoint and Keynote.

## What is not yet recorded

- No 30–60 s screen-capture video exists yet. `demo/qbr-project/screenshots/`
  and `demo/d3-single/screenshots/` PNGs are the current visual evidence.
- Windows rendering path has not been re-tested on this machine. macOS arm64
  is the only verified environment as of 2026-09-11.
