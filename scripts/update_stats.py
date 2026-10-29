#!/usr/bin/env python3
"""Generate self-contained profile cards from public GitHub REST data (stdlib only)."""
import json
import os
import time
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    from .pixel_art import pixel_text
except ImportError:
    from pixel_art import pixel_text

ROOT = Path(__file__).resolve().parents[1]
USERNAME = "AntonioMelgarMendez"
COMMITS_YEAR = 2026
COLORS = ["#dea85e", "#86b5a6", "#8ba1b8", "#bd8979", "#c3bd89", "#637c83"]


def github(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-stats-generator",
               "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    for attempt in range(3):
        try:
            with urlopen(Request("https://api.github.com" + path, headers=headers), timeout=30) as response:
                return json.load(response)
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise
        except URLError:
            if attempt == 2:
                raise
        time.sleep(2 ** (attempt + 1))


def fetch_repositories():
    repositories = []
    page = 1
    while True:
        batch = github(f"/users/{USERNAME}/repos?type=owner&sort=full_name&per_page=100&page={page}")
        if not isinstance(batch, list):
            raise ValueError("Unexpected GitHub repositories response")
        repositories.extend(batch)
        if len(batch) < 100:
            return repositories
        page += 1


def fetch_commits(through):
    """Indexed public authored commits in the requested year, not contribution events."""
    start = f"{COMMITS_YEAR}-01-01"
    end = min(through, f"{COMMITS_YEAR}-12-31")
    if end < start:
        raise ValueError("Commit cutoff precedes the requested year")
    query = f"author:{USERNAME} is:public author-date:{start}..{end}"
    result = github("/search/commits?" + urlencode({"q": query, "per_page": 1}))
    if result.get("incomplete_results") is not False:
        raise ValueError("GitHub returned incomplete commit search results; keeping previous cards")
    count = result.get("total_count")
    if type(count) is not int or count < 0:
        raise ValueError("GitHub returned an invalid commit count")
    return {"year": COMMITS_YEAR, "count": count, "from": start, "through": end,
            "metric": "public authored commits indexed on default branches", "query": query}


def summarize(user, repositories, date, commits=None):
    # Deduplicate pages and explicitly exclude private, forked, and organization-owned work.
    originals = {r["id"]: r for r in repositories
                 if not r["fork"] and not r["private"]
                 and r["owner"]["login"].lower() == USERNAME.lower()}.values()
    languages = Counter(r["language"] for r in originals if r["language"])
    return {
        "username": USERNAME,
        "updated": date,
        "repositories": len(originals),
        "stars": sum(r["stargazers_count"] for r in originals),
        "forks": sum(r["forks_count"] for r in originals),
        "followers": user["followers"],
        "commits": commits,
        "languages": dict(sorted(languages.items(), key=lambda pair: (-pair[1], pair[0]))),
        "language_metric": "primary language by original public repository count",
    }


def text(x, y, value, size=13, color="#a6b6b6", extra=""):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" {extra}>{escape(str(value))}</text>'


def card(title, description, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="440" height="280" '
            f'viewBox="0 0 440 280" role="img" aria-labelledby="title desc">'
            f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>'
            '<path d="M8 0H432V8H440V272H432V280H8V272H0V8H8Z" fill="#725f47"/>'
            '<path d="M10 2H430V10H438V270H430V278H10V270H2V10H10Z" fill="#101a20"/>'
            '<path d="M14 48H426 M14 240H426" stroke="#475552" stroke-width="2"/>'
            '<g font-family="ui-monospace,Consolas,monospace">'
            + body + '</g></svg>\n')


def stats_card(data):
    body = pixel_text(22, 20, "PUBLIC STATS", 2, "#dea85e")
    commits = data.get("commits")
    count = f'{commits["count"]:,}' if commits is not None else "--"
    year = commits["year"] if commits is not None else COMMITS_YEAR
    scale = min(5, 138 / max(1, len(count) * 6 - 1))
    body += pixel_text(24, 72, count, scale, "#f2d5a0")
    body += pixel_text(184, 76, f"COMMITS / {year}", 2, "#dea85e")
    body += text(184, 112, "Public / since Jan 1", 11)
    body += '<path d="M22 140H418" stroke="#354641" stroke-dasharray="4 4"/>'
    metrics = [("Original repos", "repositories", 24, 179), ("Stars earned", "stars", 126, 179),
               ("Followers", "followers", 228, 179), ("Forks received", "forks", 330, 179)]
    for label, key, x, y in metrics:
        body += pixel_text(x, y - 21, f'{data[key]:,}', 3, "#f2d5a0")
        for line, word in enumerate(label.split()):
            body += text(x, y + 22 + 14 * line, word, 11)
    body += text(24, 260, f'{data["updated"]} / PUBLIC ACTIVITY', 10)
    description = f"{count} public authored commits in {year}; " + ", ".join(
        f"{data[key]} {label.lower()}" for label, key, _, _ in metrics)
    return card("GitHub public statistics", description, body)


def language_rows(languages):
    rows = sorted(languages.items(), key=lambda pair: (-pair[1], pair[0]))
    if len(rows) > 6:
        rows = rows[:5] + [("Other", sum(n for _, n in rows[5:]))]
    return rows


def language_card(data):
    body = pixel_text(22, 20, "LANGUAGE MIX", 2, "#86b5a6")
    total = sum(data["languages"].values())
    rows = language_rows(data["languages"])
    x = 24
    if total:
        for i, (_, count) in enumerate(rows):
            width = 392 * count / total
            body += f'<rect x="{x:.2f}" y="66" width="{width:.2f}" height="10" fill="{COLORS[i]}"/>'
            x += width
        for i, (name, count) in enumerate(rows):
            y = 108 + i * 23
            body += f'<rect x="25" y="{y - 8}" width="7" height="7" fill="{COLORS[i]}"/>'
            body += text(42, y, name, 12, "#e1d6bf")
            body += text(416, y, f'{count / total:.1%}  /  {count} repos', 11,
                         extra='text-anchor="end"')
    else:
        body += text(24, 132, "No public language data yet.", 15)
    body += text(24, 260, f'{data["updated"]} / BY REPO COUNT ({total})', 10)
    description = "; ".join(f"{name}: {count} repositories" for name, count in rows)
    return card("Primary languages in public repositories", description, body)


def write_assets(data, destination):
    # Render everything first; API/render failures leave the last good snapshot intact.
    rendered = {"github-stats.svg": stats_card(data), "top-languages.svg": language_card(data),
                "stats.json": json.dumps(data, indent=2, ensure_ascii=False) + "\n"}
    destination.mkdir(parents=True, exist_ok=True)
    for name, content in rendered.items():
        temporary = destination / (name + ".tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(destination / name)


def main():
    user = github(f"/users/{USERNAME}")
    repositories = fetch_repositories()
    date = datetime.now(timezone.utc).date().isoformat()
    commits = fetch_commits(date)
    data = summarize(user, repositories, date, commits)
    write_assets(data, ROOT / "assets")
    print(f'Updated cards: {data["repositories"]} original public repos, '
          f'{len(data["languages"])} primary languages. Snapshot: {data["updated"]}')


if __name__ == "__main__":
    main()
