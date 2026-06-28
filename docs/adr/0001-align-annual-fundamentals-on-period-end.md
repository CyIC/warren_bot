---
status: accepted
---

# Align all annual fundamentals on income-statement period-end keys via a single builder

## Context

The stock report drew revenue and EPS from two independent yfinance paths with two different
notions of "year": revenue from `stock.financials` (real fiscal period-end dates) and Reported
EPS from `get_earnings_dates()` (announcement dates shifted back two months and force-stamped to
`YYYY-12-31`). Each report section sliced these frames independently (`[-1]`, `iloc[-years:]`),
so "most recent year" for sales could be FY2025 while EPS showed FY2026, and the tables printed
no year labels, hiding the drift.

## Decision

The **income-statement fiscal period-end date is the single source of truth** for which Fiscal
Year a data point belongs to. A new builder (`get_aligned_annual_fundamentals`) re-keys quarterly
Reported EPS onto period-end dates (by matching each announcement to the immediately preceding
quarter-end) and joins it to annual revenue, producing one structure consumed by every
year-comparison section:

- `complete` — one row per Complete Fiscal Year (all four quarters present, both revenue and EPS),
  keyed by period-end. Revenue is the authoritative annual figure when present, else the sum of
  four quarters; Reported EPS is always the sum of the four aligned quarters.
- `current` — the in-progress Fiscal Year (fewer than four quarters), kept separate.
- `sufficient_history` / `complete_year_count` — a non-blocking flag raised when fewer than
  `YRS_LOOKBACK + 1` complete years exist.

Period-end keying means non-December fiscal years work without special-casing; no calendar-year or
Dec-31 assumption remains.

## Considered options

- **Reduce both sides to an integer year and intersect** — keeps the −2-month heuristic and
  mis-buckets non-December filers; rejected.
- **Derive EPS from Net Income ÷ shares** — guarantees one source but changes EPS from *reported*
  to *derived*; rejected to preserve reported figures.
- **Patch each section to intersect years locally** — smaller diff, but the alignment invariant
  would live in five places and regress on the next new section; rejected in favor of one builder.

## Consequences

- Fundamentals now have two access paths: the new builder (year-aligned comparisons) and the raw
  per-statement getters (balance sheet, cash flow, quarterly charts/forecasts), which are
  intentionally left on raw frames.
- Semiannual filers (2 periods/year) never satisfy the hard 4-quarter completeness rule and are
  explicitly out of scope until needed.