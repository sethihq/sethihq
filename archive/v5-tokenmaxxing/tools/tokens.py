"""Build the tokenmaxxing score card with a 2026 activity heatmap.

Pulls public data from api.tokenmaxxing.sh (no auth) and writes
tokens-light.svg and tokens-dark.svg at the repo root. Stdlib only.
"""

import datetime as dt
import json
import urllib.request
from collections import defaultdict
from pathlib import Path

LOGIN = "sethihq"
API = "https://api.tokenmaxxing.sh"
ROOT = Path(__file__).resolve().parent.parent

SANS = "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Inter', 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace"

THEMES = {
    "light": dict(
        bg="#ffffff", line="#e4e4e7", ink="#27272a", mute="#71717a", faint="#a1a1aa",
        empty="#f1f1f3", future="#f7f7f8", ramp=["#d6e4fd", "#a8c6fb", "#6fa0f6", "#3b78ee", "#1d4fd1"],
        peak="#e2559f",
    ),
    "dark": dict(
        bg="#0d1117", line="#262a31", ink="#ededf0", mute="#9b9ba5", faint="#6b6b75",
        empty="#191c22", future="#13161b", ramp=["#17305e", "#1f4691", "#2c64c9", "#4f86f2", "#8fb5ff"],
        peak="#f08cc3",
    ),
}


def get(path):
    req = urllib.request.Request(f"{API}{path}", headers={"accept": "application/json", "User-Agent": "profile-readme"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def short(n):
    for div, unit in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if n >= div:
            return f"{n / div:.1f}{unit}"
    return str(int(n))


def build(theme, profile, daily, today):
    t = THEMES[theme]
    s = profile["stats"]
    year = today.year
    start = dt.date(year, 1, 1)
    grid_start = start - dt.timedelta(days=(start.weekday() + 1) % 7)  # weeks start on Sunday
    end = dt.date(year, 12, 31)
    weeks = ((end - grid_start).days // 7) + 1

    cell, gap = 11, 3.7
    pad = 32
    w = 880
    grid_x = pad + 34
    grid_y = 196
    h = grid_y + 7 * (cell + gap) + 64

    active = sorted(v for v in daily.values() if v > 0)

    def level(v):
        if v <= 0 or not active:
            return -1
        rank = sum(1 for a in active if a <= v) / len(active)
        return min(4, int(rank * 5 - 1e-9))

    peak = s.get("peakDay") or {}
    peak_date = dt.date.fromisoformat(peak["date"]) if peak.get("date") else None

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
        f'aria-label="{LOGIN} on tokenmaxxing: {short(s["totalTokens"])} tokens, ${s["spendUsd"]:,.0f} spent over {s["activeDays"]} active days">',
        "<style>",
        f".sans{{font-family:{SANS}}} .mono{{font-family:{MONO}}}",
        ".c{opacity:0;animation:in .5s ease-out forwards}",
        "@keyframes in{from{opacity:0;transform:scale(.4)}to{opacity:1;transform:none}}",
        ".c{transform-box:fill-box;transform-origin:center}",
        "@media (prefers-reduced-motion:reduce){.c{animation:none;opacity:1}}",
        "</style>",
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="18" fill="{t["bg"]}" stroke="{t["line"]}"/>',
        # top row: label and rank
        f'<text class="mono" x="{pad}" y="{pad + 12}" font-size="11" letter-spacing="1.2" fill="{t["faint"]}">TOKENMAXXING.SH/{LOGIN.upper()}</text>',
    ]
    if s.get("leaderboardRank"):
        out.append(
            f'<text class="mono" x="{w - pad}" y="{pad + 12}" text-anchor="end" font-size="11" letter-spacing="1.2" fill="{t["faint"]}">'
            f'RANK <tspan fill="{t["ink"]}">#{s["leaderboardRank"]}</tspan> OVER 30 DAYS</text>'
        )
    # the score
    out.append(
        f'<text class="sans" x="{pad - 3}" y="{pad + 86}" font-size="64" font-weight="650" letter-spacing="-2.5" fill="{t["ink"]}">'
        f'{short(s["totalTokens"])}<tspan font-size="22" font-weight="500" letter-spacing="-0.3" fill="{t["mute"]}" dx="10">tokens</tspan></text>'
    )
    out.append(
        f'<text class="sans" x="{pad}" y="{pad + 118}" font-size="16" fill="{t["mute"]}">'
        f'<tspan fill="{t["ink"]}" font-weight="600">${s["spendUsd"]:,.0f}</tspan> of api-equivalent spend since '
        f'{dt.date.fromisoformat(s["firstDate"]).strftime("%b %-d").lower()}, mostly on {s["topModel"]["model"]}</text>'
    )
    # stat column on the right
    stats = [
        (f'{s["activeDays"]}', "active days"),
        (f'{s["currentStreakDays"]}', "day streak"),
        (f'{s["longestStreakDays"]}', "longest streak"),
        (f'{s["sessionCount"]}', "sessions"),
    ]
    sx = w - pad
    for i, (num, label) in enumerate(stats):
        y = pad + 46 + i * 24
        out.append(
            f'<text class="sans" x="{sx}" y="{y}" text-anchor="end" font-size="14" fill="{t["mute"]}">'
            f'<tspan fill="{t["ink"]}" font-weight="600" style="font-variant-numeric:tabular-nums">{num}</tspan> {label}</text>'
        )

    # month labels
    for m in range(1, 13):
        first = dt.date(year, m, 1)
        col = (first - grid_start).days // 7
        out.append(
            f'<text class="sans" x="{grid_x + col * (cell + gap)}" y="{grid_y - 10}" font-size="11" fill="{t["faint"]}">'
            f'{first.strftime("%b").lower()}</text>'
        )
    for row, name in ((1, "mon"), (3, "wed"), (5, "fri")):
        out.append(
            f'<text class="sans" x="{pad}" y="{grid_y + row * (cell + gap) + 9}" font-size="11" fill="{t["faint"]}">{name}</text>'
        )

    # cells
    for wk in range(weeks):
        for dow in range(7):
            d = grid_start + dt.timedelta(days=wk * 7 + dow)
            if d.year != year:
                continue
            x = grid_x + wk * (cell + gap)
            y = grid_y + dow * (cell + gap)
            if d > today:
                out.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{t["future"]}"/>')
                continue
            lv = level(daily.get(d.isoformat(), 0))
            fill = t["empty"] if lv < 0 else t["ramp"][lv]
            delay = wk * 0.025 + dow * 0.01
            tip = f'{d.strftime("%b %-d")}: {short(daily.get(d.isoformat(), 0))} tokens'
            out.append(
                f'<rect class="c" style="animation-delay:{delay:.3f}s" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{fill}">'
                f"<title>{tip}</title></rect>"
            )
            if d == peak_date:
                out.append(
                    f'<rect x="{x - 2.5}" y="{y - 2.5}" width="{cell + 5}" height="{cell + 5}" rx="5" fill="none" stroke="{t["peak"]}" stroke-width="1.5"/>'
                )

    # footer: legend and peak note
    fy = grid_y + 7 * (cell + gap) + 30
    if peak_date:
        out.append(
            f'<circle cx="{grid_x + 5}" cy="{fy - 4}" r="5" fill="none" stroke="{t["peak"]}" stroke-width="1.5"/>'
            f'<text class="sans" x="{grid_x + 18}" y="{fy}" font-size="12" fill="{t["mute"]}">biggest day, '
            f'{peak_date.strftime("%b %-d").lower()}, <tspan fill="{t["ink"]}">${peak["spendUsd"]:,.0f}</tspan></text>'
        )
    lx = w - pad - 5 * (cell + gap) - 34
    out.append(f'<text class="sans" x="{lx - 8}" y="{fy}" text-anchor="end" font-size="11" fill="{t["faint"]}">less</text>')
    for i, c in enumerate([t["empty"]] + t["ramp"][1:]):
        out.append(f'<rect x="{lx + i * (cell + gap)}" y="{fy - 10}" width="{cell}" height="{cell}" rx="3" fill="{c}"/>')
    out.append(
        f'<text class="sans" x="{lx + 5 * (cell + gap) + 4}" y="{fy}" font-size="11" fill="{t["faint"]}">more</text>'
    )
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main():
    today = dt.date.today()
    profile = get(f"/profiles/{LOGIN}")
    rows = get(f"/profiles/{LOGIN}/daily?since={today.year}-01-01")["days"]
    daily = defaultdict(float)
    for r in rows:
        daily[r["date"]] += r["totalTokens"]
    for theme in THEMES:
        (ROOT / f"tokens-{theme}.svg").write_text(build(theme, profile, daily, today))


if __name__ == "__main__":
    main()
