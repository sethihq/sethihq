"""Build the animated portrait: my face drawn with the letters of my intro.

The face types itself in, letter by letter in reading order, then the intro
types out underneath, then a band of light keeps sweeping over the face like a
projector. Writes ascii-light.svg and ascii-dark.svg at the repo root.
Stdlib only. The density grid lives in tools/portrait-levels.txt (0 to 5).
"""

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
    "light": dict(ink="#24292f", band="#2f6fed", text="#57606a", caret="#2f6fed"),
    "dark": dict(ink="#e6edf3", band="#7aa7ff", text="#9da7b3", caret="#7aa7ff"),
}

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
    face_chars = sum(1 for r in grid for c in r if c != "0")
    face_time = 3.2
    step = face_time / face_chars

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
        f'aria-label="{escape(INTRO)}">',
        "<style>",
        "text,tspan{white-space:pre}",
        ".c{opacity:0;animation:on .01s linear forwards}",
        "@keyframes on{to{opacity:1}}",
        ".caret{opacity:0;animation:on .01s linear forwards,blink 1s steps(1) infinite}",
        "@keyframes blink{50%{fill-opacity:0}}",
        "@media (prefers-reduced-motion:reduce){.c,.caret{animation:none;opacity:1}}",
        "</style>",
        # the projector band: a gradient that slides down the face every few seconds
        f'<defs><linearGradient id="band" gradientUnits="userSpaceOnUse" x1="0" y1="{art_y}" x2="0" y2="{art_y + rows * alh}">',
        f'<stop offset="0" stop-color="{t["ink"]}"/>',
        f'<stop offset="0.42" stop-color="{t["ink"]}"/>',
        f'<stop offset="0.5" stop-color="{t["band"]}"/>',
        f'<stop offset="0.58" stop-color="{t["ink"]}"/>',
        f'<stop offset="1" stop-color="{t["ink"]}"/>',
        f'<animateTransform attributeName="gradientTransform" type="translate" values="0 {-rows * alh};0 {-rows * alh};0 {rows * alh}" '
        f'keyTimes="0;0.55;1" dur="6s" begin="{face_time + 1.5:.1f}s" repeatCount="indefinite"/>',
        "</linearGradient></defs>",
        f'<text font-family="{MONO}" font-size="{afs}px" fill="url(#band)">',
    ]

    k = 0
    for y, row in enumerate(grid):
        spans = []
        for x, lv in enumerate(row):
            if lv == "0":
                continue
            ch = letters[k % len(letters)]
            delay = k * step
            k += 1
            spans.append(
                f'<tspan class="c" x="{art_x + x * acw:.1f}" fill-opacity="{OPACITY[int(lv)]}"{BOLD if lv == "5" else ""} '
                f'style="animation-delay:{delay:.3f}s">{escape(ch)}</tspan>'
            )
        if spans:
            out.append(f'<tspan y="{art_y + y * alh + afs}">' + "".join(spans) + "</tspan>")
    out.append("</text>")

    # the readable intro, typed out after the face
    out.append(f'<text font-family="{MONO}" font-size="{tfs}px" fill="{t["text"]}">')
    start = face_time + 0.4
    per = 0.022
    n = 0
    for i, line in enumerate(lines):
        y = text_top + i * tlh
        spans = []
        for j, ch in enumerate(line):
            spans.append(
                f'<tspan class="c" x="{text_x + j * tcw:.1f}" style="animation-delay:{start + n * per:.3f}s">{escape(ch)}</tspan>'
            )
            n += 1
        n += 1
        out.append(f'<tspan y="{y}">' + "".join(spans) + "</tspan>")
    out.append("</text>")
    last = lines[-1]
    cx = text_x + len(last) * tcw + 3
    cy = text_top + (len(lines) - 1) * tlh - tfs + 2
    out.append(
        f'<rect class="caret" x="{cx:.1f}" y="{cy}" width="{tcw:.1f}" height="{tfs + 2}" fill="{t["caret"]}" '
        f'style="animation-delay:{start + n * per:.3f}s"/>'
    )
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main():
    for theme in THEMES:
        (ROOT / f"ascii-{theme}.svg").write_text(build(theme))


if __name__ == "__main__":
    main()
