"""Build the portrait: my face drawn with the letters of my intro.

Everything is visible from the first frame. A few scattered letters brighten
now and then and the cursor after the intro blinks. Writes ascii-light.svg and ascii-dark.svg at the repo root.
Stdlib only. The density grid lives in tools/portrait-levels.txt (0 to 5).
"""

import random
import textwrap
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

INTRO = (
    "hey, i'm rajat :) i design and build products, and design engineering is my favourite part of it. "
    "lately i've been experimenting with hardware, creative tech, projection mapping and mixed media, "
    "and i'm learning to dj too."
)

MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace"

THEMES = {
    "light": dict(ink="#24292f", band="#2f6fed", text="#57606a", caret="#2f6fed", line="#d0d7de"),
    "dark": dict(ink="#e6edf3", band="#7aa7ff", text="#9da7b3", caret="#7aa7ff", line="#30363d"),
}

LINKS = [("x", "x", "@sethiHQ"), ("linkedin", "linkedin", "sethihq")]

BOLD = ' font-weight="700"'
OPACITY = {1: 0.12, 2: 0.26, 3: 0.46, 4: 0.72, 5: 1.0}


def build(theme):
    t = THEMES[theme]
    grid = (ROOT / "tools" / "portrait-levels.txt").read_text().rstrip("\n").split("\n")
    rows, cols = len(grid), max(len(r) for r in grid)

    afs, alh = 8, 9  # portrait font size and line height
    acw = afs * 0.62
    tfs, tlh = 13, 21  # intro text
    tcw = tfs * 0.62
    wrap = 58

    lines = textwrap.wrap(INTRO, wrap)
    w = int(max(cols * acw, wrap * tcw)) + 48
    art_x = (w - cols * acw) / 2
    art_y = 24
    text_top = art_y + rows * alh + 30
    text_x = (w - wrap * tcw) / 2
    h = int(text_top + len(lines) * tlh + 20)

    letters = [c for c in INTRO if c != " "]
    rng = random.Random(7)  # fixed seed so the file only changes when the inputs do

    body = [f'<g font-family="{MONO}" font-size="{afs}px" fill="{t["ink"]}">']
    k = 0
    for y, row in enumerate(grid):
        cells = [(x, lv) for x, lv in enumerate(row) if lv != "0"]
        if not cells:
            continue
        spans = []
        for x, lv in cells:
            ch = letters[k % len(letters)]
            k += 1
            base = OPACITY[int(lv)]
            glint = ""
            # a few scattered letters brighten now and then, never in a sweep
            if lv in "234" and rng.random() < 0.035:
                begin = rng.uniform(0.5, 14)
                glint = (
                    f'<animate attributeName="fill-opacity" values="{base};1;{base};{base}" keyTimes="0;0.06;0.16;1" '
                    f'dur="{rng.uniform(9, 15):.1f}s" begin="{begin:.1f}s" repeatCount="indefinite"/>'
                )
            spans.append(
                f'<tspan x="{art_x + x * acw:.1f}" fill-opacity="{base}"{BOLD if lv == "5" else ""}>{escape(ch)}{glint}</tspan>'
            )
        body.append(f'<text y="{art_y + y * alh + afs}">' + "".join(spans) + "</text>")
    body.append("</g>")

    body.append(f'<g font-family="{MONO}" font-size="{tfs}px" fill="{t["text"]}">')
    for i, line in enumerate(lines):
        body.append(f'<text x="{text_x:.1f}" y="{text_top + i * tlh}">{escape(line)}</text>')
    body.append("</g>")

    last = lines[-1]
    cx = text_x + len(last) * tcw + 3
    cy = text_top + (len(lines) - 1) * tlh - tfs + 2
    body.append(
        f'<rect x="{cx:.1f}" y="{cy}" width="{tcw:.1f}" height="{tfs + 2}" fill="{t["caret"]}">'
        '<animate attributeName="opacity" values="1;0" calcMode="discrete" dur="1s" repeatCount="indefinite"/>'
        "</rect>"
    )

    head = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
        f'aria-label="{escape(INTRO)}">',
        "<style>text,tspan{white-space:pre}</style>",
    ]
    return "\n".join(head + body + ["</svg>"]) + "\n"


def button(theme, label, handle):
    """A link drawn in characters, "[ x @sethiHQ ]"."""
    t = THEMES[theme]
    fs = 13
    cw = fs * 0.62
    parts = [("[ ", t["text"]), (label, t["ink"]), (" ", t["text"]), (handle, t["caret"]), (" ]", t["text"])]
    text = "".join(p for p, _ in parts)
    pad = 4
    w = int(len(text) * cw + pad * 2)
    h = 28
    spans = "".join(f'<tspan fill="{c}">{escape(p)}</tspan>' for p, c in parts)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{label} {handle}">'
        "<style>text,tspan{white-space:pre}</style>"
        f'<text x="{pad}" y="{h / 2 + fs * 0.36:.1f}" font-family="{MONO}" font-size="{fs}px">{spans}</text></svg>\n'
    )


def main():
    for theme in THEMES:
        (ROOT / f"ascii-{theme}.svg").write_text(build(theme))
        for slug, label, handle in LINKS:
            (ROOT / f"btn-{slug}-{theme}.svg").write_text(button(theme, label, handle))


if __name__ == "__main__":
    main()
