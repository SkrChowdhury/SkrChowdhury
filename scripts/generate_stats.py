#!/usr/bin/env python3
"""
Generate a custom GitHub stats card (riso palette) as a static SVG.
Runs inside a GitHub Action with the built-in GITHUB_TOKEN -> assets/stats.svg
No Vercel, no personal token, no shared rate-limited instance.
"""
import os, json, math, urllib.request, urllib.error

USER  = os.environ.get("GH_USER", "skrchowdhury")
TOKEN = os.environ.get("GH_TOKEN", "")
OUT   = os.environ.get("OUT", "assets/stats.svg")

PINK, BLUE, INK, PAPER = "#FF5D73", "#5468FF", "#0E0E16", "#EDE6D8"
LANG_COLORS = {
    "JavaScript":"#F1E05A","TypeScript":"#3178C6","HTML":"#E34C26","CSS":"#563D7C",
    "Dart":"#00B4AB","Java":"#B07219","Kotlin":"#A97BFF","Python":"#3572A5",
    "Swift":"#F05138","C++":"#F34B7D","C":"#555555","Shell":"#89E051","Ruby":"#701516",
    "Go":"#00ADD8","PHP":"#4F5D95","Vue":"#41B883","SCSS":"#C6538C","Jupyter Notebook":"#DA5B0B",
}
FALLBACK = [PINK, BLUE, "#06B6D4", "#F59E0B", "#22C55E", "#A855F7"]

def api(path):
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={"User-Agent": "stats-card", "Accept": "application/vnd.github+json",
                 **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def collect():
    """Return real stats, or None if no token / API unavailable (-> placeholder)."""
    if not TOKEN:
        return None
    try:
        u = api(f"/users/{USER}")
        repos = []
        for pg in range(1, 6):
            page = api(f"/users/{USER}/repos?per_page=100&page={pg}&type=owner&sort=pushed")
            repos += page
            if len(page) < 100:
                break
        own = [r for r in repos if not r["fork"]]
        stars = sum(r["stargazers_count"] for r in repos)
        forks = sum(r["forks_count"] for r in repos)
        bytes_by_lang = {}
        for r in own[:60]:
            try:
                for lang, b in api(f"/repos/{USER}/{r['name']}/languages").items():
                    bytes_by_lang[lang] = bytes_by_lang.get(lang, 0) + b
            except Exception:
                if r["language"]:
                    bytes_by_lang[r["language"]] = bytes_by_lang.get(r["language"], 0) + 1
        total = sum(bytes_by_lang.values()) or 1
        langs = sorted(bytes_by_lang.items(), key=lambda x: -x[1])[:6]
        langs = [(n, round(b / total * 100, 1)) for n, b in langs]
        return {"followers": u["followers"], "repos": u["public_repos"],
                "stars": stars, "forks": forks, "langs": langs}
    except Exception as e:
        print("stats fetch failed, using placeholder:", e)
        return None

def esc(s): return str(s).replace("&", "&amp;").replace("<", "&lt;")

def color_for(name, i): return LANG_COLORS.get(name, FALLBACK[i % len(FALLBACK)])

def render(d):
    placeholder = d is None
    if placeholder:
        d = {"followers":"—","repos":"—","stars":"—","forks":"—",
             "langs":[("JavaScript",34),("TypeScript",26),("HTML",16),
                      ("CSS",12),("Dart",8),("Other",4)]}
    stats = [("stars earned",d["stars"]),("public repos",d["repos"]),
             ("followers",d["followers"]),("total forks",d["forks"])]

    # left stat grid (2x2)
    cells=[]
    gx, gy, cw, ch = 44, 96, 152, 66
    for i,(label,val) in enumerate(stats):
        x = gx + (i%2)*cw; y = gy + (i//2)*ch
        dot = PINK if i%2==0 else BLUE
        cells.append(f'''
    <g transform="translate({x},{y})">
      <text x="0" y="0" font-size="30" font-weight="900" fill="{BLUE}">{esc(val)}</text>
      <rect x="1" y="10" width="7" height="7" rx="1.5" fill="{dot}"/>
      <text x="14" y="20" font-size="12" font-family="'Courier New',monospace" fill="{PAPER}" opacity=".78">{label}</text>
    </g>''')

    # right language bar
    bx, by, bw, bh = 400, 118, 316, 18
    segs, legend, acc = [], [], 0.0
    for i,(name,pct) in enumerate(d["langs"]):
        w = bw * (pct/100.0)
        col = color_for(name, i)
        segs.append(f'<rect x="{bx+acc:.1f}" y="{by}" width="{max(w-2,1):.1f}" height="{bh}" rx="3" fill="{col}"/>')
        col_x = bx + (i%2)*160; col_y = 168 + (i//2)*24
        legend.append(f'''<g transform="translate({col_x},{col_y})">
        <rect x="0" y="-9" width="10" height="10" rx="2" fill="{col}"/>
        <text x="16" y="0" font-size="12.5" fill="{PAPER}" opacity=".85">{esc(name)} <tspan opacity=".55">{pct}%</tspan></text></g>''')
        acc += w

    note = f'<text x="400" y="250" font-size="10.5" font-family="\'Courier New\',monospace" fill="{PAPER}" opacity=".4">run the stats action to populate live numbers</text>' if placeholder else ""

    return f'''<svg viewBox="0 0 760 270" xmlns="http://www.w3.org/2000/svg" font-family="'Segoe UI',Arial,sans-serif">
  <defs>
    <pattern id="d" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.2" fill="{PAPER}" opacity=".06"/></pattern>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#14141F"/><stop offset="1" stop-color="{INK}"/></linearGradient>
  </defs>
  <rect width="760" height="270" rx="18" fill="url(#bg)"/>
  <rect width="760" height="270" rx="18" fill="url(#d)"/>
  <rect x="1.5" y="1.5" width="757" height="267" rx="16.5" fill="none" stroke="{PINK}" stroke-opacity=".35"/>
  <g stroke="{BLUE}" stroke-width="1.3" opacity=".5">
    <path d="M24 30 h14 M31 23 v14"/><path d="M736 30 h-14 M729 23 v14"/>
    <path d="M24 240 h14 M31 233 v14"/><path d="M736 240 h-14 M729 233 v14"/>
  </g>
  <text x="44" y="52" font-size="12" letter-spacing="5" font-weight="700" fill="{PAPER}" opacity=".55" font-family="'Courier New',monospace">// BY THE NUMBERS</text>
  <text x="44" y="80" font-size="22" font-weight="900" fill="{PINK}">{esc(USER)}</text>
  <line x1="380" y1="60" x2="380" y2="230" stroke="{PAPER}" stroke-opacity=".12"/>
  {''.join(cells)}
  <text x="400" y="96" font-size="12" letter-spacing="4" font-weight="700" fill="{PAPER}" opacity=".55" font-family="'Courier New',monospace">TOP LANGUAGES</text>
  <rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="4" fill="{PAPER}" opacity=".08"/>
  {''.join(segs)}
  {''.join(legend)}
  {note}
</svg>'''

if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    svg = render(collect())
    open(OUT, "w").write(svg)
    print("wrote", OUT)
