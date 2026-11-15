"""Build the neofetch-style profile card (light and dark SVGs).

Reads the ASCII portrait from tools/portrait.txt, pulls live stats from the
GitHub GraphQL API (token from GITHUB_TOKEN or GH_TOKEN) and writes
card-light.svg and card-dark.svg at the repo root. Stdlib only.
"""

import json
import os
import urllib.request
from html import escape
from pathlib import Path

USER = "sethihq"
ROOT = Path(__file__).resolve().parent.parent
WIDTH = 58  # characters in the info column

INFO = [
    ("title", f"rajat@{USER}"),
    ("kv", "Role", "product designer, design engineer"),
    ("kv", "OS", "macOS, iOS"),
    ("kv", "Kernel", "design first, then code"),
    ("kv", "IDE", "Figma, Claude Code"),
    ("blank",),
    ("kv", "Languages.Code", "TypeScript, GLSL, Python"),
    ("kv", "Languages.Design", "Figma, Framer, Blender, Cavalry"),
    ("kv", "Languages.Real", "English, Hindi"),
    ("blank",),
    ("kv", "Hobbies.Software", "WebGL, motion, creative tech"),
    ("kv", "Hobbies.Hardware", "ESP32s, tiny OLEDs"),
    ("kv", "Hobbies.Other", "mixed media"),
    ("blank",),
    ("title", "Contact"),
    ("kv", "X", "@sethiHQ"),
    ("kv", "LinkedIn", "sethihq"),
    ("blank",),
    ("title", "GitHub Stats"),
    ("stats1",),
    ("stats2",),
    ("stats3",),
]

THEMES = {
    "light": dict(bg="#ffffff", line="#d0d7de", text="#24292f", key="#bf3989", value="#0550ae", dots="#afb8c1", art="#57606a"),
    "dark": dict(bg="#0d1117", line="#30363d", text="#c9d1d9", key="#f3a6d8", value="#79c0ff", dots="#484f58", art="#8b949e"),
}


def gql(query, variables, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-card"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if body.get("errors"):
        raise RuntimeError(body["errors"])
    return body["data"]


def stats():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("set GITHUB_TOKEN or GH_TOKEN")
    base = gql(
        """query($u:String!){user(login:$u){
            followers{totalCount}
            repositories(ownerAffiliations:OWNER,isFork:false,privacy:PUBLIC){totalCount}
            repositoriesContributedTo(contributionTypes:[COMMIT,PULL_REQUEST,REPOSITORY]){totalCount}
            contributionsCollection{contributionYears contributionCalendar{totalContributions}}
        }}""",
        {"u": USER},
        token,
    )["user"]

    stars, cursor = 0, None
    while True:
        page = gql(
            """query($u:String!,$c:String){user(login:$u){repositories(first:100,after:$c,ownerAffiliations:OWNER,privacy:PUBLIC){
                pageInfo{hasNextPage endCursor} nodes{stargazerCount}}}}""",
            {"u": USER, "c": cursor},
            token,
        )["user"]["repositories"]
        stars += sum(n["stargazerCount"] for n in page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]

    commits = 0
    for year in base["contributionsCollection"]["contributionYears"]:
        c = gql(
            """query($u:String!,$f:DateTime!,$t:DateTime!){user(login:$u){
                contributionsCollection(from:$f,to:$t){contributionCalendar{totalContributions}}}}""",
            {"u": USER, "f": f"{year}-01-01T00:00:00Z", "t": f"{year}-12-31T23:59:59Z"},
            token,
        )
        commits += c["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]

    return dict(
        repos=base["repositories"]["totalCount"],
        contributed=base["repositoriesContributedTo"]["totalCount"],
        stars=stars,
        followers=base["followers"]["totalCount"],
        commits=commits,
        year=base["contributionsCollection"]["contributionCalendar"]["totalContributions"],
    )


def kv(key, value, width):
    """'. Key: ...... value' padded with dot leaders to exactly `width` chars."""
    head = f". {key}:"
    fill = width - len(head) - len(value) - 2
    return [("dots", ". "), ("key", key), ("text", ":"), ("dots", " " + "." * max(fill, 1) + " "), ("value", value)]


def pair(k1, v1, k2, v2):
    left = kv(k1, v1, 31)
    right = kv(k2, v2, WIDTH - 31 - 3 + 2)[1:]
    return left + [("dots", " | ")] + right


def lines(s):
    out = []
    for row in INFO:
        kind = row[0]
        if kind == "blank":
            out.append([])
        elif kind == "title":
            name = row[1]
            if name.startswith("rajat@"):
                label = [("key", "rajat"), ("text", "@"), ("key", USER)]
            else:
                label = [("dots", "- "), ("text", name)]
            used = sum(len(t) for _, t in label)
            out.append(label + [("dots", " " + "─" * (WIDTH - used - 3) + " -")])
        elif kind == "kv":
            out.append(kv(row[1], row[2], WIDTH))
        elif kind == "stats1":
            out.append(pair("Repos", f"{s['repos']} {{Contributed: {s['contributed']}}}", "Stars", str(s["stars"])))
        elif kind == "stats2":
            out.append(pair("Contributions", f"{s['commits']:,}", "Followers", str(s["followers"])))
        elif kind == "stats3":
            out.append(kv("Last 12 months", f"{s['year']:,}", WIDTH))
    return out


def svg(theme, info, art):
    t = THEMES[theme]
    fs, lh, pad = 15, 21, 28
    afs, alh = 10, 11  # the portrait is set smaller so it holds more detail
    art_cols = max(len(l) for l in art)
    char_w = fs * 0.6
    info_x = pad + art_cols * afs * 0.6 + 4 * char_w
    w = int(info_x + WIDTH * char_w + pad)
    h = pad * 2 + max(len(info) * lh, len(art) * alh) - 6
    art_top = pad + 8
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'font-family="ui-monospace, SFMono-Regular, \'SF Mono\', Menlo, Consolas, monospace" font-size="{fs}px">',
        "<style>text,tspan{white-space:pre}"
        f".text{{fill:{t['text']}}}.key{{fill:{t['key']}}}.value{{fill:{t['value']}}}.dots{{fill:{t['dots']}}}"
        "</style>",
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="14" fill="{t["bg"]}" stroke="{t["line"]}"/>',
        f'<text fill="{t["art"]}" font-size="{afs}px">',
    ]
    for i, l in enumerate(art):
        parts.append(f'<tspan x="{pad}" y="{art_top + i * alh}">{escape(l)}</tspan>')
    parts.append("</text>")
    parts.append('<text class="text">')
    for i, segs in enumerate(info):
        if not segs:
            continue
        y = pad + 14 + i * lh
        spans = "".join(f'<tspan class="{c}">{escape(txt)}</tspan>' for c, txt in segs)
        parts.append(f'<tspan x="{info_x:.1f}" y="{y}">{spans}</tspan>')
    parts.append("</text></svg>")
    return "\n".join(parts) + "\n"


def main():
    art = (ROOT / "tools" / "portrait.txt").read_text().rstrip("\n").split("\n")
    info = lines(stats())
    for theme in THEMES:
        (ROOT / f"card-{theme}.svg").write_text(svg(theme, info, art))


if __name__ == "__main__":
    main()
