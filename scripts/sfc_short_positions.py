#!/usr/bin/env python3
"""Fetch SFC aggregated reportable short positions for selected HK stocks."""

from __future__ import annotations

import argparse
import csv
import html
import io
import re
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urljoin

import requests


INDEX_URL = (
    "https://www.sfc.hk/en/Regulatory-functions/Market/Short-position-reporting/"
    "Aggregated-reportable-short-positions-of-specified-shares"
)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; hk-flow-tape/1.0; public market data research)",
    "Accept": "text/html,text/csv,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass(frozen=True)
class ReportLink:
    date_key: str
    url: str


def normalize_code(code: str) -> str:
    cleaned = code.strip().upper().removesuffix(".HK").removeprefix("HK")
    return cleaned.zfill(5)


def parse_total_shares(items: list[str]) -> dict[str, float]:
    result: dict[str, float] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"bad shares item: {item}; use CODE=TOTAL_SHARES")
        code, value = item.split("=", 1)
        result[normalize_code(code)] = float(value.replace(",", ""))
    return result


def report_links() -> list[ReportLink]:
    response = requests.get(INDEX_URL, headers=HEADERS, timeout=20)
    response.raise_for_status()
    page = html.unescape(response.text)
    urls = re.findall(r'href="([^"]*Short_Position_Reporting_Aggregated_Data_(\d{8})\.csv[^"]*)"', page)
    links = [ReportLink(date_key=date_key, url=urljoin(INDEX_URL, url)) for url, date_key in urls]
    unique = {link.date_key: link for link in links}
    return [unique[key] for key in sorted(unique, reverse=True)]


def read_report(url: str) -> list[dict[str, str]]:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    text = response.content.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def find_links(date_key: str | None, history: int) -> list[ReportLink]:
    links = report_links()
    if date_key:
        normalized = date_key.replace("-", "")
        selected = [link for link in links if link.date_key == normalized]
        if not selected:
            available = ", ".join(link.date_key for link in links[:10])
            raise RuntimeError(f"report {date_key} not found; latest available: {available}")
        start = links.index(selected[0])
        return links[start : start + history]
    return links[:history]


def hkd_yi(value: float) -> str:
    return f"{value / 100_000_000:,.2f}"


def pct(value: float | None) -> str:
    return "" if value is None else f"{value * 100:.2f}%"


def rows_for_codes(links: Iterable[ReportLink], codes: list[str], total_shares: dict[str, float]) -> list[dict[str, object]]:
    wanted = {normalize_code(code) for code in codes}
    output: list[dict[str, object]] = []
    for link in links:
        for row in read_report(link.url):
            code = normalize_code(row["Stock Code"])
            if wanted and code not in wanted:
                continue
            shares = float(row["Aggregated Reportable Short Positions (Shares)"] or 0)
            hkd = float(row["Aggregated Reportable Short Positions (HK$)"] or 0)
            ratio = shares / total_shares[code] if code in total_shares and total_shares[code] else None
            output.append(
                {
                    "date": link.date_key,
                    "code": code,
                    "name": row["Stock Name"],
                    "shares": shares,
                    "hkd": hkd,
                    "ratio": ratio,
                }
            )
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None, help="report date YYYYMMDD or YYYY-MM-DD; default latest")
    parser.add_argument("--history", type=int, default=8, help="number of weekly reports to fetch")
    parser.add_argument("--codes", nargs="*", default=[], help="HK codes, e.g. 00700 09988")
    parser.add_argument("--shares", nargs="*", default=[], help="optional total shares, e.g. 00700=9108033432")
    args = parser.parse_args()

    links = find_links(args.date, args.history)
    totals = parse_total_shares(args.shares)
    rows = rows_for_codes(links, args.codes, totals)

    print("date      code   name                    short_shares      short_hkd_yi  short/total")
    for row in rows:
        print(
            f"{row['date']:<9} "
            f"{row['code']:<5} "
            f"{str(row['name'])[:22]:<22} "
            f"{int(row['shares']):>16,} "
            f"{hkd_yi(float(row['hkd'])):>13} "
            f"{pct(row['ratio'] if isinstance(row['ratio'], float) else None):>11}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
