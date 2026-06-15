---
name: hk-flow-tape
description: 港股资金盘面判读系统。Use when the user asks who is buying or selling Hong Kong stocks, whether southbound funds/港股通 are flowing in or out, whether a Hong Kong stock or HSTECH has right-side flow confirmation, how to interpret 沽空金额/沽空比率/偏离值/净空头仓位, whether ADR weakness implies foreign selling, why price rises despite southbound selling, or how to combine 南向资金、ETF、ADR、沽空 and SFC short-position data into a tradable conclusion.
---

# HK Flow Tape

## Core Job

Judge Hong Kong stock tape from the flow side. Separate **who is trading** from **whether the asset is good**:

- Southbound Stock Connect flow: mainland money through 沪港通/深港通.
- Offshore/foreign flow: inferred from ADR, price-volume behavior, broker custody changes, CCASS if available, and Hong Kong local turnover.
- Short-sale pressure: daily short turnover, short-sale ratio, deviation from recent average.
- Reportable short positions: SFC weekly aggregated net short positions.
- ETF/passive flow: index ETF turnover and connect activity as beta/hedging/rebalance behavior.

Use this skill as the flow/tape layer. Pair it with `yunlei-hk` when the user asks whether a Hong Kong stock has reached the right-side zone for buying or adding.

## Required Workflow

### 1. Define The Question

Classify the task first:

| Question | Output |
|---|---|
| "南向今天买了谁/卖了谁？" | Current southbound top net buys/sells, with data coverage caveat |
| "股价涨但南向卖，是谁在买？" | Buyer inference: offshore/foreign/local/passive vs short covering |
| "是否右侧，可以加仓？" | Flow confirmation state plus action lane |
| "沽空/净空头说明什么？" | Short pressure, crowding, squeeze risk, and time lag |
| "ADR折价/没跟涨，能不能做T？" | Offshore sentiment check plus intraday execution conditions |

### 2. Gather Current Data

For live or recent market facts, verify before concluding. Prefer these sources:

- Southbound top-10 active stocks: Eastmoney `RPT_MUTUAL_TOP10DEAL` or exchange/broker terminal.
- Current quote and total turnover: exchange, Tencent quote API, broker terminal, or other reliable market feed.
- Daily short selling: HKEX short selling turnover data or reputable redistributors.
- Weekly reportable short positions: SFC aggregated reportable short positions CSV.
- ADR: latest US close and ADR-to-HKD parity.
- Portfolio context: when the user asks about holdings, check `/Users/dc/DCmacOB/stock/scheme.md` and `/Users/dc/invest/.workbuddy/memory/MEMORY.md` if available.

Use bundled scripts when helpful:

- `scripts/southbound_top10.py` fetches Eastmoney 港股通沪/深十大成交活跃股 and aggregates by code.
- `scripts/sfc_short_positions.py` fetches and summarizes SFC aggregated reportable short positions.

### 3. Keep Data Meanings Separate

Never mix these ratios:

- **Southbound participation** = southbound buy amount + sell amount / total market turnover.
- **Southbound direction strength** = southbound net amount / southbound buy amount + sell amount.
- **Southbound net amount** = buy amount - sell amount. It shows direction, not participation.
- **Daily short-sale ratio** = daily short-sale turnover / total turnover.
- **Short-sale deviation** = today's short-sale ratio minus the recent average ratio, usually 30-day average if the source defines it that way.
- **Reportable short-position ratio** = SFC aggregated reportable short shares / total issued shares or market cap proxy.

Do not use `southbound net amount / total market turnover` as a participation measure. It understates churn and confuses direction with presence.

### 4. Build The Flow Diagnosis

Use this order:

1. **Price and total turnover**: Is the move real or thin?
2. **Southbound**: Net buy/sell, buy amount, sell amount, deal amount, 沪 vs 深 split.
3. **Offshore/foreign clue**: ADR parity, US sector move, HK price behavior when southbound is opposite.
4. **Short-sale pressure**: short amount, ratio, deviation; judge pressure vs covering potential.
5. **Weekly net short**: SFC trend, crowding, and whether data is stale.
6. **ETF/passive**: index ETF connect flow and benchmark move.
7. **Conclusion**: right-side, left-side, divergent, squeeze-prone, or weak rebound only.

### 5. Interpret Common Patterns

| Pattern | Meaning | Trading Bias |
|---|---|---|
| Price up, southbound net buy, strong turnover | Clean right-side flow | Can add if valuation/position allows |
| Price up, southbound net sell | Offshore/local/passive/short-covering buying likely | Do not call southbound right-side; hold or T only |
| Price down, southbound net buy | Mainland dip-buying against offshore selling | Wait unless price stabilizes |
| Price down, southbound net sell | Flow resonance down | Avoid catching falling knife |
| High short-sale ratio with positive deviation | Fresh short pressure or hedging | Watch failed rebounds |
| High net short position but falling | Potential covering/squeeze setup | Needs price/flow confirmation |
| ETF heavy turnover without stock confirmation | Beta/hedging/rebalance flow | Weak evidence for individual stocks |

### 6. Output Shape

For trading questions, answer in this structure:

```markdown
结论：一句话给出买/等/减/T/不追。

资金结论：
- 南向：
- 外资/离岸：
- 沽空：
- ETF/被动：

关键比例：
- 南向参与度：
- 南向方向强度：
- 沽空比率/偏离：
- 净空头趋势：

右侧判断：
- 已右侧 / 右侧早期 / 分歧 / 仍左侧 / 反弹但未反转

操作：
- 可做：
- 等待：
- 失效：
```

If data coverage is incomplete, say exactly what is missing. Do not treat "not in top-10 active list" as zero flow.

## Detailed References

Read `references/flow-framework.md` when the user asks for methodology, ratio definitions, or ambiguous flow interpretation.

Read `references/data-sources.md` when choosing or validating data sources.
