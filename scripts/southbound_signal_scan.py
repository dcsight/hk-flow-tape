#!/usr/bin/env python3
"""Scan recent southbound top-10 active stocks for emerging right-side signals.

This is a guardrail script: it helps avoid missing stocks that repeatedly enter
港股通(沪/深) top-10 active lists with sustained positive net buying.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from typing import Any

from southbound_top10 import build_rows, hkd_yi


def pct(value: float | None) -> str:
    return "" if value is None else f"{value * 100:.1f}%"


def scan_dates(dates: list[str]) -> dict[str, dict[str, Any]]:
    signals: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "code": "",
            "name": "",
            "days": 0,
            "positive_days": 0,
            "both_channel_days": 0,
            "cum_net": 0.0,
            "cum_buy": 0.0,
            "cum_sell": 0.0,
            "cum_deal": 0.0,
            "first_close": None,
            "last_close": None,
            "last_change_rate": None,
            "dates": [],
        }
    )

    for trade_date in dates:
        _, by_code = build_rows(trade_date)
        for code, row in by_code.items():
            item = signals[code]
            item["code"] = code
            item["name"] = row["name"]
            item["days"] += 1
            item["positive_days"] += 1 if row["net"] > 0 else 0
            item["both_channel_days"] += 1 if len(set(row["channels"])) >= 2 else 0
            item["cum_net"] += row["net"]
            item["cum_buy"] += row["buy"]
            item["cum_sell"] += row["sell"]
            item["cum_deal"] += row["deal"]
            item["dates"].append(trade_date)
    return signals


def classify(item: dict[str, Any], min_net: float, min_direction: float) -> str:
    direction = item["cum_net"] / item["cum_deal"] if item["cum_deal"] else 0.0
    if item["days"] >= 3 and item["positive_days"] >= 3 and item["cum_net"] >= min_net and direction >= min_direction:
        if item["days"] >= 4 and item["cum_net"] >= min_net * 2:
            return "右侧确认"
        return "右侧早期"
    if item["days"] >= 2 and item["positive_days"] >= 2 and item["cum_net"] > 0 and direction >= min_direction:
        return "观察"
    return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dates", nargs="+", required=True, help="complete trading dates, e.g. 2026-06-09 2026-06-10")
    parser.add_argument("--min-net-y", type=float, default=10.0, help="minimum cumulative net buy in HKD yi")
    parser.add_argument("--min-direction", type=float, default=0.15, help="minimum net/deal direction strength")
    parser.add_argument("--show-all", action="store_true", help="show non-flagged rows too")
    args = parser.parse_args()

    min_net = args.min_net_y * 100_000_000
    signals = scan_dates(args.dates)
    rows = []
    for item in signals.values():
        direction = item["cum_net"] / item["cum_deal"] if item["cum_deal"] else 0.0
        stage = classify(item, min_net, args.min_direction)
        if not stage and not args.show_all:
            continue
        score = (item["positive_days"], item["cum_net"], direction, item["days"])
        rows.append((score, stage, direction, item))

    rows.sort(reverse=True, key=lambda row: row[0])
    print("stage      code   name           days pos both net_yi deal_yi direction dates")
    for _, stage, direction, item in rows:
        print(
            f"{stage or '-':<10} "
            f"{item['code']:<5} "
            f"{item['name'][:12]:<12} "
            f"{item['days']:>4} "
            f"{item['positive_days']:>3} "
            f"{item['both_channel_days']:>4} "
            f"{hkd_yi(item['cum_net']):>8} "
            f"{hkd_yi(item['cum_deal']):>8} "
            f"{pct(direction):>9} "
            f"{','.join(item['dates'])}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
