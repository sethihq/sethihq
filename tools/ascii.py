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
    "light": dict(ink="#24292f", band="#2f6fed", text="#57606a", caret="#2f6fed", line="#d0d7de"),
    "dark": dict(ink="#e6edf3", band="#7aa7ff", text="#9da7b3", caret="#7aa7ff", line="#30363d"),
}

LINKS = [("x", "x", "@sethiHQ"), ("linkedin", "linkedin", "sethihq")]

BOLD = ' font-weight="700"'
OPACITY = {1: 0.12, 2: 0.26, 3: 0.46, 4: 0.72, 5: 1.0}


def typing(clip_id, x0, y0, height, stops, begin, dur):
    """A clipPath whose width steps open one character at a time (SMIL, so it runs inside <img>)."""
    widths = ";".join(f"{w:.1f}" for w in [0] + stops)
    n = len(stops)
    times = ";".join(f"{i / (n + 1):.4f}" for i in range(n + 1))
    return (
        f'<clipPath id="{clip_id}"><rect x="{x0:.1f}" y="{y0:.1f}" width="0" height="{height}">'
        f'<animate attributeName="width" values="{widths}" keyTimes="{times}" calcMode="discrete" '
        f'begin="{begin:.3f}s" dur="{dur:.3f}s" fill="freeze"/></rect></clipPath>'
    )


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

    defs, body = [], []
    # the portrait, one line of text per row, each row typed open in reading order
    body.append(f'<g font-family="{MONO}" font-size="{afs}px" fill="url(#band)">')
    k = 0
    clock = 0.4
    for y, row in enumerate(grid):
        cells = [(x, lv) for x, lv in enumerate(row) if lv != "0"]
        if not cells:
            continue
        spans, stops = [], []
        for x, lv in cells:
            ch = letters[k % len(letters)]
            k += 1
            spans.append(
                f'<tspan x="{art_x + x * acw:.1f}" fill-opacity="{OPACITY[int(lv)]}"{BOLD if lv == "5" else ""}>{escape(ch)}</tspan>'
            )
            stops.append(x * acw + acw)
        dur = len(cells) * step
        top = art_y + y * alh
        defs.append(typing(f"r{y}", art_x, top - 1, alh + 1, stops, clock, dur))
        body.append(f'<text y="{top + afs}" clip-path="url(#r{y})">' + "".join(spans) + "</text>")
        clock += dur
    body.append("</g>")

    # the readable intro, typed out after the face
    clock += 0.4
    per = 0.022
    body.append(f'<g font-family="{MONO}" font-size="{tfs}px" fill="{t["text"]}">')
    for i, line in enumerate(lines):
        y = text_top + i * tlh
        stops = [(j + 1) * tcw for j in range(len(line))]
        dur = len(line) * per
        defs.append(typing(f"t{i}", text_x, y - tfs, tlh, stops, clock, dur))
        body.append(f'<text x="{text_x:.1f}" y="{y}" clip-path="url(#t{i})">{escape(line)}</text>')
        clock += dur + per
    body.append("</g>")

    last = lines[-1]
    cx = text_x + len(last) * tcw + 3
    cy = text_top + (len(lines) - 1) * tlh - tfs + 2
    body.append(
        f'<rect x="{cx:.1f}" y="{cy}" width="{tcw:.1f}" height="{tfs + 2}" fill="{t["caret"]}" opacity="0">'
        f'<animate attributeName="opacity" values="1;0" calcMode="discrete" dur="1s" begin="{clock:.3f}s" repeatCount="indefinite"/>'
        "</rect>"
    )

    head = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
        f'aria-label="{escape(INTRO)}">',
        "<style>text,tspan{white-space:pre}</style>",
        "<defs>",
        # the projector band: a gradient that slides down the face every few seconds
        f'<linearGradient id="band" gradientUnits="userSpaceOnUse" x1="0" y1="{art_y}" x2="0" y2="{art_y + rows * alh}" '
        f'gradientTransform="translate(0 {-rows * alh})">',
        f'<stop offset="0" stop-color="{t["ink"]}"/>',
        f'<stop offset="0.42" stop-color="{t["ink"]}"/>',
        f'<stop offset="0.5" stop-color="{t["band"]}"/>',
        f'<stop offset="0.58" stop-color="{t["ink"]}"/>',
        f'<stop offset="1" stop-color="{t["ink"]}"/>',
        f'<animateTransform attributeName="gradientTransform" type="translate" values="0 {-rows * alh};0 {-rows * alh};0 {rows * alh}" '
        f'keyTimes="0;0.55;1" dur="6s" begin="{face_time + 1.5:.1f}s" repeatCount="indefinite"/>',
        "</linearGradient>",
    ]
    return "\n".join(head + defs + ["</defs>"] + body + ["</svg>"]) + "\n", clock


def button(theme, label, handle, begin):
    """A link drawn in characters, "[ x @sethiHQ ]", typed in after the intro."""
    t = THEMES[theme]
    fs = 13
    cw = fs * 0.62
    parts = [("[ ", t["text"]), (label, t["ink"]), (" ", t["text"]), (handle, t["caret"]), (" ]", t["text"])]
    text = "".join(p for p, _ in parts)
    pad = 4
    w = int(len(text) * cw + pad * 2)
    h = 28
    n = len(text)
    stops = ";".join(f"{(i + 1) * cw:.1f}" for i in range(n))
    times = ";".join(f"{i / (n + 1):.4f}" for i in range(n + 1))
    spans = "".join(f'<tspan fill="{c}">{escape(p)}</tspan>' for p, c in parts)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{label} {handle}">'
        "<style>text,tspan{white-space:pre}</style>"
        f'<defs><clipPath id="c"><rect x="{pad}" y="0" width="0" height="{h}">'
        f'<animate attributeName="width" values="0;{stops}" keyTimes="{times}" calcMode="discrete" begin="{begin:.3f}s" dur="{n * 0.03:.3f}s" fill="freeze"/>'
        "</rect></clipPath></defs>"
        f'<text x="{pad}" y="{h / 2 + fs * 0.36:.1f}" font-family="{MONO}" font-size="{fs}px" clip-path="url(#c)">{spans}</text></svg>\n'
    )


def main():
    for theme in THEMES:
        svg, done = build(theme)
        (ROOT / f"ascii-{theme}.svg").write_text(svg)
        for i, (slug, label, handle) in enumerate(LINKS):
            (ROOT / f"btn-{slug}-{theme}.svg").write_text(button(theme, label, handle, done + 0.2 + i * 0.25))


if __name__ == "__main__":
    main()
