#!/usr/bin/env python3
"""Fetch and aggregate Hong Kong southbound Stock Connect top-10 active stocks.

Source: Eastmoney RPT_MUTUAL_TOP10DEAL.
Coverage: daily top-10 active stocks for 港股通(沪) and 港股通(深) only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from collections import defaultdict
from typing import Any

import requests


API_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"
CHANNELS = {"002": "港股通(沪)", "004": "港股通(深)"}


def normalize_code(code: str) -> str:
    cleaned = code.strip().upper().removesuffix(".HK").removeprefix("HK")
    return cleaned.zfill(5)


def parse_turnover(items: list[str]) -> dict[str, float]:
    result: dict[str, float] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"bad turnover item: {item}; use CODE=HKD_YI")
        code, value = item.split("=", 1)
        result[normalize_code(code)] = float(value) * 100_000_000
    return result


def fetch_top10(trade_date: str, mutual_type: str) -> list[dict[str, Any]]:
    params = {
        "sortColumns": "TRADE_DATE,RANK",
        "sortTypes": "-1,1",
        "pageSize": "10",
        "pageNumber": "1",
        "reportName": "RPT_MUTUAL_TOP10DEAL",
        "columns": "ALL",
        "source": "WEB",
        "client": "WEB",
        "filter": f"""(MUTUAL_TYPE="{mutual_type}")(TRADE_DATE='{trade_date}')""",
    }
    response = requests.get(API_URL, params=params, timeout=15)
    response.raise_for_status()
    payload = response.json()
    result = payload.get("result")
    if not result:
        message = payload.get("message", "no result")
        raise RuntimeError(f"Eastmoney returned no data for {trade_date} {mutual_type}: {message}")
    return result.get("data", [])


def hkd_yi(value: float) -> str:
    return f"{value / 100_000_000:,.2f}"


def pct(value: float | None) -> str:
    return "" if value is None else f"{value * 100:.1f}%"


def build_rows(trade_date: str) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    raw_rows: list[dict[str, Any]] = []
    by_code: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "code": "",
            "name": "",
            "net": 0.0,
            "buy": 0.0,
            "sell": 0.0,
            "deal": 0.0,
            "channels": [],
        }
    )

    for mutual_type, channel_name in CHANNELS.items():
        for item in fetch_top10(trade_date, mutual_type):
            code = normalize_code(str(item["SECURITY_CODE"]))
            row = {
                "channel": channel_name,
                "rank": item.get("RANK"),
                "code": code,
                "name": item.get("SECURITY_NAME", ""),
                "net": float(item.get("NET_BUY_AMT") or 0),
                "buy": float(item.get("BUY_AMT") or 0),
                "sell": float(item.get("SELL_AMT") or 0),
                "deal": float(item.get("DEAL_AMT") or 0),
                "close": item.get("CLOSE_PRICE"),
                "change_rate": item.get("CHANGE_RATE"),
            }
            raw_rows.append(row)
            agg = by_code[code]
            agg["code"] = code
            agg["name"] = row["name"]
            agg["net"] += row["net"]
            agg["buy"] += row["buy"]
            agg["sell"] += row["sell"]
            agg["deal"] += row["deal"]
            agg["channels"].append(channel_name)
    return raw_rows, by_code


def print_rows(rows: list[dict[str, Any]], title: str, turnover: dict[str, float]) -> None:
    print(f"\n## {title}")
    print("channels        code   name           net_yi   buy_yi  sell_yi  deal_yi  participation direction")
    for row in rows:
        code = row["code"]
        deal = row["deal"]
        net = row["net"]
        channel_value = row.get("channels", row.get("channel", ""))
        channels = "+".join(channel_value) if isinstance(channel_value, list) else str(channel_value)
        participation = deal / turnover[code] if code in turnover and turnover[code] else None
        direction = net / deal if deal else None
        print(
            f"{channels:<15} "
            f"{code:<5} "
            f"{row['name'][:12]:<12} "
            f"{hkd_yi(net):>8} "
            f"{hkd_yi(row['buy']):>8} "
            f"{hkd_yi(row['sell']):>8} "
            f"{hkd_yi(deal):>8} "
            f"{pct(participation):>13} "
            f"{pct(direction):>9}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="trade date, e.g. 2026-06-02")
    parser.add_argument("--codes", nargs="*", default=[], help="HK codes, e.g. 00700 03690 09988")
    parser.add_argument("--all", action="store_true", help="print all aggregated top-10 covered stocks")
    parser.add_argument(
        "--turnover",
        nargs="*",
        default=[],
        help="optional total market turnover in HKD yi, e.g. 00700=477.89 03690=114.89",
    )
    args = parser.parse_args()

    turnover = parse_turnover(args.turnover)
    raw_rows, by_code = build_rows(args.date)
    print_rows(raw_rows, f"{args.date} raw channel rows", turnover)

    codes = [normalize_code(code) for code in args.codes]
    if args.all or not codes:
        aggregated = sorted(by_code.values(), key=lambda item: item["net"], reverse=True)
    else:
        aggregated = [by_code[code] for code in codes if code in by_code]

    print_rows(aggregated, f"{args.date} aggregated 港股通(沪+深)", turnover)

    missing = [code for code in codes if code not in by_code]
    if missing:
        print("\nNot covered by same-day top-10 source:", ", ".join(missing), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
