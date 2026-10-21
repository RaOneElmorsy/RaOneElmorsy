"""Draws pyramid.svg: the contribution graph flies, square by square, into a pyramid that is never finished."""
import json
import os
import random
import sys
import urllib.request

USER = os.environ.get("GH_USER", "RaOneElmorsy")
TOKEN = os.environ["GITHUB_TOKEN"]
OUT = sys.argv[1] if len(sys.argv) > 1 else "dist/pyramid.svg"

LEVEL_COLOR = {"FIRST_QUARTILE": "#0e4429", "SECOND_QUARTILE": "#006d32",
               "THIRD_QUARTILE": "#26a641", "FOURTH_QUARTILE": "#39d353"}
SAND = ["#d9b26f", "#cfa560", "#c39853", "#e0bd7c", "#b98a47"]


def graphql(query):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)["data"]


weeks = graphql(
    f'{{user(login:"{USER}"){{contributionsCollection{{contributionCalendar{{'
    f'weeks{{firstDay contributionDays{{weekday contributionLevel}}}}}}}}}}}}'
)["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]


def busy(week):
    return any(d["contributionLevel"] in LEVEL_COLOR for d in week["contributionDays"])


# Only show the stretch of weeks that actually has contributions.
first = next((i for i, w in enumerate(weeks) if busy(w)), len(weeks) - 1)
last = max((i for i, w in enumerate(weeks) if busy(w)), default=len(weeks) - 1)
weeks = weeks[first:last + 1]
stones = sum(d["contributionLevel"] in LEVEL_COLOR for w in weeks for d in w["contributionDays"])

W = 1000
SPLIT = W / 3                      # left third: the graph; right two thirds: the pyramid
PX = SPLIT + (W - SPLIT) / 2       # pyramid centre

# Size the pyramid so it is at most ~80% full: the top is always missing.
rows = 6
while rows * (rows + 1) / 2 * 0.8 < stones:
    rows += 1

bw = min(46, 560 / rows)
bh = bw * 0.58
top = 40
ground = top + rows * bh
H = int(ground + 90)

pitch = min(13, (SPLIT - 60) / len(weeks))
CELL = pitch * 0.78
grid_w = len(weeks) * pitch - (pitch - CELL)
gx0 = (SPLIT - grid_w) / 2
gy0 = top + (ground - top) / 2 - 7 * pitch / 2     # vertically centred beside the pyramid

grid, active, months = [], [], []  # active: grid squares that become stones, oldest first
prev_month, last_label = None, -9
for wi, week in enumerate(weeks):
    x = gx0 + wi * pitch
    month = week["firstDay"][5:7]
    if month != prev_month and wi - last_label >= 4:
        name = "JanFebMarAprMayJunJulAugSepOctNovDec"[(int(month) - 1) * 3:][:3]
        months.append(f'<text x="{x:.1f}" y="{gy0 - 7:.1f}">{name}</text>')
        last_label = wi
    prev_month = month
    for day in week["contributionDays"]:
        y = gy0 + day["weekday"] * pitch
        grid.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL:.1f}" height="{CELL:.1f}" rx="1.5"/>')
        if day["contributionLevel"] in LEVEL_COLOR:
            active.append((x, y, LEVEL_COLOR[day["contributionLevel"]]))

# One stone in the air at a time: each lands before the next one leaves the graph.
step = min(0.18, 10 / max(stones, 1))
fly = step
start = 0.8

random.seed(USER)
slots, placed = [], []
i = 0
for r in range(rows):              # r = 0 is the bottom row
    n = rows - r
    y = ground - (r + 1) * bh
    x0 = PX - n * bw / 2
    for c in range(n):
        x = x0 + c * bw
        sx, sy, sw, sh = x + 1, y + 1, bw - 2, bh - 2
        cls = ' class="next"' if i == stones else ""
        slots.append(f'<rect{cls} x="{sx:.1f}" y="{sy:.1f}" width="{sw:.1f}" height="{sh:.1f}" rx="2"/>')
        if i < stones:
            gx, gy, green = active[i]
            # The stone is drawn at its pyramid slot and animates from its grid square.
            placed.append(
                f'<rect x="{sx:.1f}" y="{sy:.1f}" width="{sw:.1f}" height="{sh:.1f}" rx="2" '
                f'fill="{random.choice(SAND)}" style="--dx:{gx - sx:.1f}px;--dy:{gy - sy:.1f}px;'
                f'--sx:{CELL / sw:.3f};--sy:{CELL / sh:.3f};--g:{green};animation-delay:{start + i * step:.3f}s"/>'
            )
        i += 1

stars = "\n".join(
    f'<circle cx="{random.randint(int(SPLIT), W - 10)}" cy="{random.randint(int(top), int(top + (ground - top) * 0.7))}" '
    f'r="{random.choice([1, 1.2, 1.5])}" style="animation-delay:{random.random() * 3:.1f}s"/>'
    for _ in range(30)
)
done = start + stones * step + fly

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#0b0f1a"/>
      <stop offset="1" stop-color="#241a36"/>
    </linearGradient>
    <clipPath id="card"><rect width="{W}" height="{H}" rx="18"/></clipPath>
    <style>
      .stars circle {{ fill: #fff; animation: tw 3s ease-in-out infinite; }}
      @keyframes tw {{ 50% {{ opacity: .15; }} }}
      .grid rect {{ fill: #1c1830; }}
      .months text {{ fill: #7d8590; font-size: 10px; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
      .slots rect {{ fill: #16112a; stroke: #3d3352; stroke-width: 1; }}
      .slots .next {{ animation: next 1.2s {done:.1f}s ease-in-out infinite; }}
      @keyframes next {{ 0%, 100% {{ stroke: #f2cc6b; }} 50% {{ stroke: #f2cc6b; opacity: .2; }} }}
      .placed rect {{ transform-box: fill-box; transform-origin: 0 0;
                     animation: fly {fly:.3f}s cubic-bezier(.5,0,.3,1) backwards; }}
      @keyframes fly {{
        from {{ transform: translate(var(--dx), var(--dy)) scale(var(--sx), var(--sy)); fill: var(--g); }}
        60% {{ fill: var(--g); }}
      }}
      .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    </style>
  </defs>
  <g clip-path="url(#card)">
    <rect width="{W}" height="{H}" fill="url(#sky)"/>
    <g class="stars">
{stars}
    </g>
    <g class="months">
{chr(10).join(months)}
    </g>
    <g class="grid">
{chr(10).join(grid)}
    </g>
    <rect y="{ground:.1f}" width="{W}" height="{H - ground:.1f}" fill="#2e2216"/>
    <g class="slots">
{chr(10).join(slots)}
    </g>
    <g class="placed">
{chr(10).join(placed)}
    </g>
    <text x="{PX:.0f}" y="{ground + 38:.0f}" text-anchor="middle" class="mono" font-size="20" font-weight="700" fill="#f2cc6b">every commit is a stone.</text>
    <text x="{PX:.0f}" y="{ground + 64:.0f}" text-anchor="middle" class="mono" font-size="14" fill="#a9a9c8">the great pyramid took decades. mine is still going.</text>
  </g>
</svg>
'''

os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
with open(OUT, "w") as f:
    f.write(svg)
print(f"{stones} active days -> {rows} rows")
