# 港股资金数据源

## Southbound Stock Connect

Preferred same-day source:

- Eastmoney data center report `RPT_MUTUAL_TOP10DEAL`.
- `MUTUAL_TYPE="002"` means 港股通(沪).
- `MUTUAL_TYPE="004"` means 港股通(深).

Important limitation:

- This source covers only daily top-10 active stocks per channel.
- If a stock is missing, say "not covered by the same-day top-10 source"; do not treat missing as zero flow.
- For full Stock Connect holding/shareholding history, use exchange/broker terminal or CCASS-style holdings sources when available.

## Total Turnover And Quote

Use a current quote source to get:

- close/latest price,
- change percent,
- total market turnover,
- total shares if calculating reportable short-position ratio.

Tencent quote API, exchange pages, and broker terminals are acceptable when they match visible market data.

## Daily Short Selling

Preferred primary source:

- HKEX daily short selling turnover data.

Broker or media redistributors are acceptable for quick interpretation if:

- date is explicit,
- stock code and counter are clear,
- short amount, short ratio, and deviation definition are shown.

Be careful with RMB counters and low-liquidity counters. A high ratio on a tiny counter is not the same as heavy short pressure on the main HKD counter.

## Weekly Reportable Short Positions

Primary source:

- SFC "Aggregated reportable short positions of specified shares" page:
  `https://www.sfc.hk/en/Regulatory-functions/Market/Short-position-reporting/Aggregated-reportable-short-positions-of-specified-shares`

Use it for:

- weekly short-position trend,
- crowded short identification,
- potential short-covering/squeeze setups.

Limitations:

- Data is delayed and normally based on the last trading day of the week.
- It only includes reportable positions above the threshold.
- It is aggregated, not participant-level.
- It does not capture all derivative or economic short exposure.

## ADR / Offshore Sentiment

Use ADR parity as an offshore sentiment clue, not as a mechanical forecast:

- ADR discount vs HK close can signal offshore caution.
- ADR premium can signal offshore risk appetite.
- Low ADR turnover weakens the signal.
- Strong ADR divergence matters more when it aligns with sector/US market moves and HK southbound flow.

## Data Confidence Labels

Use these labels in analysis:

- **High confidence**: primary source, exact date, direct field.
- **Medium confidence**: reputable redistributor, visible table/screenshot, exact date.
- **Low confidence**: inferred from price behavior or partial source.

Never hide uncertainty. A flow conclusion with missing source coverage should be labeled as incomplete.
