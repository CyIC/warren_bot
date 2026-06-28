# Context & Glossary — Warren Bot

The ubiquitous language for the stock-analysis domain. Glossary only — no implementation
details. Terms are canonical; when code or conversation drifts from these, the term wins
until deliberately changed.

## Glossary

### Fiscal Year (FY)
A company's annual reporting period, identified by the **period-end date of its annual income
statement** (yfinance `stock.financials`). This is the *single source of truth* for "which year"
a data point belongs to. All other series (EPS, balance sheet, cash flow) are aligned to a
Fiscal Year by joining on it — they do not derive their own year independently.

Not every company's Fiscal Year ends in December; the period-end date carries the real boundary.

### Reported EPS
Earnings-per-share as announced by the company, retrieved from yfinance earnings announcements
(`get_earnings_dates`). Distinct from **Derived EPS** (Net Income ÷ shares outstanding). An annual
Reported EPS is the sum of its four quarterly Reported EPS values. Reported EPS is *aligned to* a
Fiscal Year, not the definer of one.

### Complete Fiscal Year
A Fiscal Year for which all four quarterly period-ends are present. Only Complete Fiscal Years that
have *both* a revenue and an aligned Reported EPS figure appear in the comparable full-year history.
(The 4-quarter rule is a deliberate simplification; semiannual filers are out of scope for now.)

### Current Year (in-progress)
The trailing Fiscal Year with fewer than four reported quarters. Its data is **incomplete** and must
be presented separately from the comparable full-year history (e.g. "Current FY 2026 — 2 of 4
quarters reported"), never placed in the "most recent year" slot as if it were a settled figure.

### Aligned Annual Fundamentals
The comparable full-year history of the company: Complete Fiscal Years carrying revenue and Reported
EPS that are guaranteed to refer to the *same* Fiscal Year, because every series is keyed on the
income-statement period-end date. This is the dataset every year-over-year comparison reads from;
sections must not re-derive year membership from any other source. See ADR-0001.