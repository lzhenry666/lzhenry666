import json
import os
import urllib.error
import urllib.request
from collections import Counter
from html import escape
from pathlib import Path


OWNER = os.getenv("GITHUB_OWNER", "lzhenry666")
ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "profile-assets"
TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "profile-readme-panels"}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def get_json(url):
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def text(value):
    return escape(str(value), quote=True)


def base(title, width, height, content):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{text(title)}">
<defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#08131d"/><stop offset="1" stop-color="#101c34"/></linearGradient><linearGradient id="line"><stop stop-color="#2dd4bf"/><stop offset="1" stop-color="#6d8dff"/></linearGradient></defs>
<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="18" fill="url(#bg)" stroke="url(#line)" stroke-width="2"/>{content}</svg>'''


def update():
    profile = get_json(f"https://api.github.com/users/{OWNER}")
    repos = []
    page = 1
    while True:
        batch = get_json(f"https://api.github.com/users/{OWNER}/repos?type=owner&per_page=100&page={page}")
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    owned = [repo for repo in repos if not repo["fork"]]
    if not owned:
        raise RuntimeError(f"No public owned repositories found for {OWNER}")

    languages = Counter(repo["language"] for repo in owned if repo.get("language"))
    by_name = {repo["name"].lower(): repo for repo in owned}
    featured = [by_name[name.lower()] for name in ("GameRpgB7", "devsfood", "Dogs", "PokeTeamBuilder") if name.lower() in by_name]
    projects = featured + [repo for repo in sorted(owned, key=lambda repo: (repo["stargazers_count"], repo["updated_at"]), reverse=True) if repo not in featured and repo["name"].lower() != OWNER.lower()][:4-len(featured)]
    stars = sum(repo["stargazers_count"] for repo in repos)

    stats = ''.join(
        f'<g text-anchor="middle" font-family="Segoe UI,Arial,sans-serif"><text x="{x}" y="74" fill="#77e6d4" font-size="32" font-weight="700">{text(value)}</text><text x="{x}" y="105" fill="#a9bac9" font-size="15">{label}</text></g>'
        for x, value, label in [(190, len(repos), "PUBLIC REPOSITORIES"), (480, stars, "TOTAL STARS"), (770, profile["followers"], "FOLLOWERS")]
    )
    ASSETS.joinpath("profile.svg").write_text(base("GitHub profile snapshot", 960, 145, stats), encoding="utf-8")

    rows = []
    top_languages = languages.most_common(6)
    total = sum(languages.values()) or 1
    for index, (name, count) in enumerate(top_languages):
        y = 83 + index * 23
        pct = round(count / total * 100)
        rows.append(f'<text x="34" y="{y}" fill="#e8f6ff" font-family="Segoe UI,Arial,sans-serif" font-size="15">{text(name)}</text><rect x="190" y="{y-12}" width="650" height="9" rx="4" fill="#13283a"/><rect x="190" y="{y-12}" width="{max(5, round(650*count/total))}" height="9" rx="4" fill="#2dd4bf"/><text x="910" y="{y}" fill="#90a9bd" font-family="Segoe UI,Arial,sans-serif" font-size="13" text-anchor="end">{pct}%</text>')
    stack = '<text x="30" y="43" fill="#2dd4bf" font-family="Consolas,monospace" font-size="15" font-weight="700" letter-spacing="2">LANGUAGES / PUBLIC REPOSITORIES</text>' + ''.join(rows)
    ASSETS.joinpath("stack.svg").write_text(base("Programming languages used across public repositories", 960, 235, stack), encoding="utf-8")

    cards = []
    for index, repo in enumerate(projects):
        x, y = (30, 82) if index % 2 == 0 else (498, 82)
        y += (index // 2) * 108
        language = repo.get("language") or "No primary language"
        cards.append(f'<a href="{text(repo["html_url"])}"><rect x="{x}" y="{y}" width="432" height="86" rx="12" fill="#0d2232" stroke="#20556b"/><text x="{x+24}" y="{y+37}" fill="#e8f6ff" font-family="Segoe UI,Arial,sans-serif" font-size="22" font-weight="700">{text(repo["name"][:28])}</text><text x="{x+24}" y="{y+63}" fill="#90a9bd" font-family="Segoe UI,Arial,sans-serif" font-size="15">{text(language)} · ★ {repo["stargazers_count"]}</text></a>')
    heading = '<text x="30" y="44" fill="#2dd4bf" font-family="Consolas,monospace" font-size="15" font-weight="700" letter-spacing="2">PROJECTS / SELECTED WORK</text><path d="M30 60H930" stroke="#23465d"/>'
    ASSETS.joinpath("projects.svg").write_text(base("Featured public projects", 960, 300, heading + ''.join(cards)), encoding="utf-8")

    assert len(repos) >= len(owned) > 0 and len(top_languages) <= 6 and len(projects) <= 4
    print(f"Updated profile panels for {OWNER}: {len(repos)} repositories, {stars} stars, {len(projects)} projects")


if __name__ == "__main__":
    update()
