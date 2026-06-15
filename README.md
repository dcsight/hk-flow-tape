# HK Flow Tape

港股资金盘面判读 Codex Skill，用来把南向资金、ADR、ETF、沽空和 SFC 可申报空头仓位拆开看，避免把“净额、成交额、全市场成交额、沽空比例”混成一个信号。

## What It Does

This skill helps Codex answer questions such as:

- 今天港股通净买入/净卖出哪些个股？
- 股价上涨但南向净卖，是谁在买？
- 南向资金是否从左侧转为右侧？
- 沽空金额、沽空比率、偏离值说明什么？
- SFC 每周净空头仓位是否构成股价压力或逼空条件？
- ADR 折价是否代表外资/离岸资金不认可？

It is designed as a **flow and tape diagnosis layer**, not a full stock valuation framework.

## Core Rules

- Do not use `southbound net amount / total market turnover` as participation.
- Use `southbound deal amount / total market turnover` for participation.
- Use `southbound net amount / southbound deal amount` for direction strength.
- Treat daily short-sale turnover as trading pressure, not net short position.
- Treat SFC reportable short positions as delayed weekly crowding data.
- Do not treat missing top-10 southbound data as zero flow.

## Installation

Clone or download this repository, then copy it into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -R hk-flow-tape ~/.codex/skills/hk-flow-tape
```

Then invoke it in Codex:

```text
$hk-flow-tape 看一下腾讯、阿里、美团、小米、港交所这几天资金是否右侧
```

For portfolio or asset-class decisions, pair it with a broader Hong Kong stock framework:

```text
$yunlei-hk $hk-flow-tape 看一下持仓港股是否可以买入/加仓
```

## Scripts

### Southbound Top-10 Active Stocks

```bash
python3 scripts/southbound_top10.py \
  --date 2026-06-12 \
  --codes 00700 09988 \
  --turnover 00700=129.74 09988=182.29
```

The script fetches Eastmoney `RPT_MUTUAL_TOP10DEAL` and aggregates 港股通(沪) + 港股通(深).

Coverage note: this source only covers daily top-10 active stocks per channel. If a stock is missing, it is not covered by this source; that is not the same as zero flow.

### SFC Reportable Short Positions

```bash
python3 scripts/sfc_short_positions.py \
  --history 8 \
  --codes 00700 09988 \
  --shares 00700=9108033432 09988=19193071958
```

The script fetches SFC aggregated reportable short-position CSV data and optionally calculates short shares / total shares when total share counts are supplied.

## Data Sources

- Eastmoney Data Center: `RPT_MUTUAL_TOP10DEAL`
- SFC Aggregated Reportable Short Positions
- HKEX short selling data or reputable redistributors
- Current quote and turnover sources such as exchange pages, broker terminals, or quote APIs
- ADR parity and US trading data where relevant

## Disclaimer

This skill is for research and workflow assistance only. It is not investment advice. Market data can be delayed, incomplete, or source-dependent. Always verify live facts before making trading decisions.

## License

MIT
