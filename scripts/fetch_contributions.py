"""Fetch the public contribution calendar and summarize it to JSON.

No auth token needed — scrapes the same HTML fragment GitHub serves for
the profile contributions graph. Writes data/contributions.json with
per-day counts, current/longest streak, best day, and monthly totals.

Usage: python scripts/fetch_contributions.py [username]
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DEFAULT_USERNAME = "vkinsane"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_PATH = DATA_DIR / "contributions.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; profile-readme-bot/1.0)"
}


def fetch_calendar_html(username: str) -> str:
    url = f"https://github.com/users/{username}/contributions"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_tooltip_counts(soup: BeautifulSoup) -> dict:
    """Map a td's id -> contribution count, read from its tool-tip text."""
    counts_by_id = {}
    for tip in soup.select("tool-tip"):
        target_id = tip.get("for")
        if not target_id:
            continue
        text = tip.get_text(strip=True)
        match = re.match(r"([\d,]+)\s+contribution", text)
        count = int(match.group(1).replace(",", "")) if match else 0
        counts_by_id[target_id] = count
    return counts_by_id


def parse_days(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    tooltip_counts = parse_tooltip_counts(soup)

    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        date = td.get("data-date")
        if not date:
            continue

        td_id = td.get("id")
        if td_id and td_id in tooltip_counts:
            count = tooltip_counts[td_id]
        elif td.get("data-count") is not None:
            count = int(td["data-count"])
        else:
            # Fall back to the coarse 0-4 intensity level GitHub exposes
            # when exact counts aren't present in the markup.
            count = int(td.get("data-level", 0))

        days.append({"date": date, "count": count})

    days.sort(key=lambda d: d["date"])
    return days


def compute_streaks(days: list) -> tuple:
    longest = 0
    current_run = 0
    for day in days:
        if day["count"] > 0:
            current_run += 1
            longest = max(longest, current_run)
        else:
            current_run = 0

    current = 0
    for day in reversed(days):
        if day["count"] > 0:
            current += 1
        elif current == 0:
            # Today may legitimately have 0 contributions yet; skip only
            # the trailing zero(s) before the streak has started.
            continue
        else:
            break

    return current, longest


def compute_monthly_totals(days: list) -> dict:
    totals = defaultdict(int)
    for day in days:
        month = day["date"][:7]
        totals[month] += day["count"]
    return dict(sorted(totals.items()))


def main() -> None:
    username = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USERNAME

    html = fetch_calendar_html(username)
    days = parse_days(html)

    if not days:
        print("No contribution data parsed — GitHub's markup may have changed.")
        sys.exit(1)

    current_streak, longest_streak = compute_streaks(days)
    best_day = max(days, key=lambda d: d["count"])
    total_contributions = sum(d["count"] for d in days)

    summary = {
        "username": username,
        "total_contributions": total_contributions,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "monthly_totals": compute_monthly_totals(days),
        "days": days,
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(summary, indent=2))
    print(f"Saved {len(days)} days to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
