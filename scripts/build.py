"""Builds the animated profile images into dist/.

    py scripts/build.py                 all four, sample commit data
    py scripts/build.py --flight-only   only the commit flight (used by the GitHub Action)

With GH_TOKEN and GH_USER set, the flight uses the real contribution calendar.
"""
import base64, json, math, os, random, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
DIST = os.path.join(ROOT, "dist")
os.makedirs(DIST, exist_ok=True)


def data_uri(name):
    ext = name.rsplit(".", 1)[1]
    mime = {"gif": "image/gif", "webp": "image/webp", "png": "image/png"}[ext]
    with open(os.path.join(ASSETS, name), "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()


# ---------- shared look: pastel day sky, starry night under dark mode ----------
CSS = '''
:root{--sky1:#cfe8ff;--sky2:#fff0f7;--cloud:#fff;--cloudline:#d6e8fb;--star:#ffd36e;--spark:#ff9ec7;--heart:#ff8fb8;--ink:#4a6fa5;--sub:#7f9cc4;--pill:#fff;--pillink:#4a6fa5;--card:#ffffffcc;
--base:#e3eefb;--l1:#bfe0ff;--l2:#8fc7ff;--l3:#ffb3d1;--l4:#ff8fb8;--sun:1;--moon:0;--night:0}
@media (prefers-color-scheme:dark){:root{--sky1:#171e4a;--sky2:#3a2a62;--cloud:#8696d6;--cloudline:#6f7fc4;--star:#ffe49a;--spark:#ffb3d9;--ink:#e6eeff;--sub:#b4c1f2;--pill:#232d62;--pillink:#e6eeff;--card:#232d62cc;
--base:#1b2340;--l1:#35508f;--l2:#4f7fd1;--l3:#a24d78;--l4:#d96a9b;--sun:0;--moon:1;--night:1}}
.sun{opacity:var(--sun)}.moon{opacity:var(--moon)}.nightstar{opacity:var(--night)}
.cloud{fill:var(--cloud);stroke:var(--cloudline);stroke-width:2}
.cloudfill{fill:var(--cloud)}
.tw{transform-box:fill-box;transform-origin:center;animation:tw 2.6s ease-in-out infinite}
@keyframes tw{0%,100%{opacity:.25;transform:scale(.6) rotate(0)}50%{opacity:1;transform:scale(1.15) rotate(25deg)}}
.dr{animation:dr ease-in-out infinite alternate}
@keyframes dr{from{transform:translateX(-45px)}to{transform:translateX(45px)}}
.bob{animation:bob 3.4s ease-in-out infinite}
@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-12px)}}
.rise{animation:ri 4.5s ease-in infinite;opacity:0}
@keyframes ri{0%{transform:translateY(0) scale(.5);opacity:0}15%{opacity:.95}100%{transform:translateY(-70px) scale(1.1);opacity:0}}
.heart{fill:var(--heart)}
.ink{fill:var(--ink);font-family:'Trebuchet MS',Verdana,sans-serif}
.sub{fill:var(--sub);font-family:'Trebuchet MS',Verdana,sans-serif}
'''


def defs(w, h, rx=28):
    return (f'<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="var(--sky1)"/>'
            f'<stop offset="1" stop-color="var(--sky2)"/></linearGradient></defs>'
            f'<rect width="{w}" height="{h}" rx="{rx}" fill="url(#sky)"/>')


def star(x, y, s, cls, delay, night=False):
    q = s * .18
    d = f"M0 {-s} Q{q:.1f} {-q:.1f} {s} 0 Q{q:.1f} {q:.1f} 0 {s} Q{-q:.1f} {q:.1f} {-s} 0 Q{-q:.1f} {-q:.1f} 0 {-s}Z"
    fill = "var(--spark)" if cls == "p" else "var(--star)"
    g = f'<g transform="translate({x} {y})"><path class="tw" style="animation-delay:{delay}s" fill="{fill}" d="{d}"/></g>'
    return f'<g class="nightstar">{g}</g>' if night else g


def cloud(x, y, k, dur, delay):
    return (f'<g transform="translate({x} {y}) scale({k})"><g class="dr" style="animation-duration:{dur}s;animation-delay:{delay}s">'
            f'<g class="cloudfill"><ellipse rx="46" ry="16"/><circle cx="-16" cy="-12" r="18"/><circle cx="14" cy="-18" r="22"/>'
            f'<circle cx="34" cy="-6" r="14"/></g></g></g>')


def heart(x, y, delay):
    return (f'<g transform="translate({x} {y})"><g class="rise" style="animation-delay:{delay}s">'
            f'<path class="heart" d="M0 6 C-12 -4 -8 -14 0 -8 C8 -14 12 -4 0 6Z"/></g></g>')


def sky_dressing(w, h, seed, n_stars=18):
    rnd = random.Random(seed)
    day = ''.join(star(rnd.randint(30, w - 30), rnd.randint(20, h - 20), rnd.choice([5, 7, 9]), rnd.choice(['', 'p']),
                       round(rnd.random() * 2.6, 1)) for _ in range(n_stars))
    night = ''.join(star(rnd.randint(30, w - 30), rnd.randint(14, h - 40), rnd.choice([3, 4, 5]), '',
                         round(rnd.random() * 2.6, 1), night=True) for _ in range(26))
    sunmoon = (f'<g transform="translate({w-90} 62)"><circle class="sun" r="30" fill="#ffd36e"/>'
               f'<path class="moon" d="M-8 -30 A30 30 0 1 0 28 12 A24 24 0 1 1 -8 -30Z" fill="#fff3b8"/></g>')
    return day + night + sunmoon


def svg(w, h, body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{label}">'
            f'<style>{CSS}</style>{defs(w, h)}{body}</svg>')


def write(name, text):
    with open(os.path.join(DIST, name), "w", encoding="utf-8") as f:
        f.write(text)


# ---------- 1. hero ----------
def hero():
    w, h = 900, 340
    body = sky_dressing(w, h, 7)
    body += cloud(120, 280, 1.2, 8, 0) + cloud(760, 285, 1.0, 10, -4) + cloud(430, 60, .8, 9, -2) + cloud(40, 70, .8, 11, -6)
    body += (f'<g transform="translate(70 70)"><g class="bob"><image href="{data_uri("float.gif")}" width="300" height="199"/></g></g>'
             + heart(190, 95, 0) + heart(300, 120, 1.8) + heart(120, 130, 3.2))
    body += ('<clipPath id="type"><rect x="400" y="100" width="0" height="120">'
             '<animate attributeName="width" from="0" to="480" dur="2.8s" begin="0.4s" fill="freeze" calcMode="discrete" '
             'values="0;40;80;120;160;200;240;280;320;360;400;440;480" keyTimes="0;.08;.17;.25;.33;.42;.5;.58;.67;.75;.83;.92;1"/></rect></clipPath>'
             '<g clip-path="url(#type)"><text class="ink" x="400" y="160" font-size="40" font-weight="700">hello, i\'m Salsabil</text></g>'
             '<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="1s" begin="3.2s" fill="freeze"/>'
             '<text class="sub" x="402" y="200" font-size="19" font-weight="600">AI and data science engineer</text>'
             '<text class="sub" x="402" y="228" font-size="15">molecular medicine researcher &#183; Japan-experienced AI intern</text>'
             '<text class="sub" x="402" y="254" font-size="15">genomics &#183; bioinformatics </text></g>')
    write("hero.svg", svg(w, h, body, "Cinnamoroll floating in a sky with a typed greeting"))


# ---------- 2. flight over the contribution calendar ----------
def fetch_calendar(user, token):
    q = ('query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{weeks{contributionDays{contributionLevel}}}}}}')
    req = urllib.request.Request("https://api.github.com/graphql", data=json.dumps({"query": q, "variables": {"u": user}}).encode(),
                                 headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"})
    weeks = json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    lv = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
    return [[lv[d["contributionLevel"]] for d in wk["contributionDays"]] for wk in weeks]


def sample_calendar():
    rnd = random.Random(3)
    return [[rnd.choice([0, 0, 1, 1, 2, 3, 4]) if rnd.random() < .7 else 0 for _ in range(7)] for _ in range(53)]


def flight(calendar):
    cell, gap = 13, 3
    pitch = cell + gap
    cols = len(calendar)
    gw = cols * pitch
    w, h = gw + 60, 300
    gx, gy = 30, 150
    dur = 12
    cells = []
    for c, week in enumerate(calendar):
        x = gx + c * pitch
        delay = round((x - 20) / (w - 20) * dur * .8, 2)
        for r, lvl in enumerate(week):
            y = gy + r * pitch
            if lvl:
                cells.append(f'<rect class="act" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3.5" style="--c:var(--l{lvl});animation-delay:{delay}s"/>')
            else:
                cells.append(f'<rect fill="var(--base)" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3.5"/>')
    pts = []
    n = 60
    for i in range(n + 1):
        x = -60 + (w + 120) * i / n
        y = 80 + math.sin(i / n * math.pi * 3.5) * 34
        pts.append(f"{x:.0f},{y:.0f}")
    path = "M" + " L".join(pts)
    extra = f'''<style>.act{{fill:var(--base);animation:lit {dur}s linear infinite}}
@keyframes lit{{0%{{fill:var(--base)}}3%{{fill:var(--c)}}88%{{fill:var(--c)}}95%{{fill:var(--base)}}100%{{fill:var(--base)}}}}</style>'''
    body = (extra + sky_dressing(w, 150, 11, 8) + cloud(110, 130, .7, 9, 0) + cloud(w - 160, 126, .7, 11, -5)
            + ''.join(cells)
            + f'<g><image href="{data_uri("fly.webp")}" x="-40" y="-40" width="80" height="80"/>'
              f'<animateMotion dur="{dur}s" repeatCount="indefinite" path="{path}"/></g>')
    write("flight.svg", svg(w, h, body, "Cinnamoroll flying over my contribution calendar, lighting up each square"))


# ---------- 3. skills sky board ----------
BUBBLE_CSS = '''
:root{--bio1:#ffe0ee;--bio2:#ff9ec7;--ml1:#e0f0ff;--ml2:#8fc7ff;--sw1:#eee4ff;--sw2:#b9a0f5;--da1:#dcfaee;--da2:#7fdcb8;--btxt:#3d4f86;--rb:.55}
@media (prefers-color-scheme:dark){:root{--bio1:#7a3a66;--bio2:#d96a9b;--ml1:#35508f;--ml2:#5a8fe0;--sw1:#56449a;--sw2:#8a73e0;--da1:#2f7566;--da2:#47b895;--btxt:#f2f6ff;--rb:.38}}
.pop{transform-box:fill-box;transform-origin:center;opacity:0;animation:pop .8s cubic-bezier(.3,1.7,.5,1) forwards}
@keyframes pop{0%{opacity:0;transform:scale(0)}100%{opacity:1;transform:scale(1)}}
.fl{animation:fl 4.6s ease-in-out infinite}
@keyframes fl{0%,100%{transform:translate(0,0)}50%{transform:translate(3px,-9px)}}
.btxt{fill:var(--btxt);font-family:'Trebuchet MS',Verdana,sans-serif;font-weight:700;text-anchor:middle}
'''


SKILLS = {  # left to right across the rainbow; ML sits in the middle
    "sw": ["JavaScript", "TypeScript", "Java", "C", "C++", "React", "Vue.js", "Svelte", "AngularJS", "HTML5", "CSS3",
           "Bootstrap", "Django", "FastAPI", "Node.js", "REST APIs", "Android", "Unity"],
    "bio": ["genomics", "TP53 variants", "pQTL / MR", "single-cell", "Biopython", "AlphaFold", "FoldX", "PyMOL", "Modeller"],
    "ml": ["Python", "PyTorch", "TensorFlow", "scikit-learn", "NumPy", "pandas", "SciPy", "OpenCV", "Hugging Face",
           "Transformers", "LLMs", "RAG", "NLP", "Computer Vision", "CNNs", "GANs", "LoRA", "Generative AI", "spaCy",
           "MediaPipe", "Streamlit", "MLflow"],
    "da": ["SQL", "PostgreSQL", "MySQL", "Oracle", "MongoDB", "Firebase", "Spark", "Kafka", "Docker", "Kubernetes",
           "CI/CD", "Git", "GitHub", "GitHub Actions", "GitLab CI", "AWS", "Azure", "Google Cloud", "Nginx", "Linux", "R",
           "Bash"],
}
CATS = {"sw": "software and web", "bio": "bioinformatics", "ml": "ML and AI", "da": "data, cloud and tools"}

with open(os.path.join(ASSETS, "icons.json"), encoding="utf-8") as _f:
    ICONS = json.load(_f)  # brand logo paths (24x24), from Simple Icons

LABELS = {"TP53 variants": "TP53", "pQTL / MR": "pQTL MR", "Google Cloud": "GCloud", "GitHub Actions": "Actions",
          "GitLab CI": "GitLab", "Hugging Face": "HuggingFace"}

# no brand logo exists for acronyms, so they are shown as lettering in the bubble
BADGES = {"LLMs": (["LLMs"], 11), "RAG": (["RAG"], 11), "NLP": (["NLP"], 11), "GANs": (["GANs"], 11), "CNNs": (["CNNs"], 11),
          "LoRA": (["LoRA"], 11), "SQL": (["SQL"], 11), "CI/CD": (["CI/CD"], 10), "REST APIs": (["REST", "APIs"], 10.5),
          "Computer Vision": (["Computer", "Vision"], 8.6), "Generative AI": (["Gen", "AI"], 10.5)}

WORDMARKS = {"MySQL", "spaCy", "scikit-learn"}
INK = "var(--btxt)"
# no brand logo exists for the research tools either, so they get small hand-drawn icons (24x24)
CUSTOM_ICONS = {
    "genomics": (f'<g fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round"><path d="M7 2 C7 8 17 8 17 12 C17 16 7 16 7 22"/>'
                 '<path d="M17 2 C17 8 7 8 7 12 C7 16 17 16 17 22"/><path d="M8.5 5.2 H15.5 M8.5 18.8 H15.5" stroke-width="1.6"/></g>'),
    "TP53 variants": f'<text x="12" y="17" text-anchor="middle" font-size="14" font-weight="800" font-style="italic" fill="{INK}" '
                     'style="font-family:Trebuchet MS,Verdana,sans-serif">p53</text>',
    "pQTL / MR": (f'<g fill="{INK}"><circle cx="5" cy="17" r="1.8"/><circle cx="9.5" cy="12.5" r="1.8"/><circle cx="12.5" cy="16" r="1.8"/>'
                  f'<circle cx="16.5" cy="9" r="1.8"/><circle cx="20" cy="6" r="1.8"/></g>'
                  f'<path d="M3 19.5 L21 4.5" stroke="{INK}" stroke-width="1.6" stroke-linecap="round"/>'),
    "single-cell": (f'<circle cx="12" cy="12" r="9" fill="none" stroke="{INK}" stroke-width="2"/><circle cx="11" cy="12" r="3.4" fill="{INK}"/>'
                    f'<circle cx="16.5" cy="8.5" r="1.3" fill="{INK}"/><circle cx="16" cy="16.5" r="1.1" fill="{INK}"/>'),
    "Biopython": f'<text x="12" y="16.5" text-anchor="middle" font-size="12.5" font-weight="800" font-style="italic" fill="{INK}" '
                 'style="font-family:Trebuchet MS,Verdana,sans-serif">bio</text>',
    "AlphaFold": (f'<path d="M2.5 15 C5.5 3 9 21 12 10.5 S18 5 21.5 13" fill="none" stroke="{INK}" stroke-width="2.4" stroke-linecap="round"/>'
                  f'<circle cx="2.5" cy="15" r="1.6" fill="{INK}"/><circle cx="21.5" cy="13" r="1.6" fill="{INK}"/>'),
    "FoldX": f'<text x="12" y="16" text-anchor="middle" font-size="10.5" font-weight="800" fill="{INK}" '
             'style="font-family:Trebuchet MS,Verdana,sans-serif">ΔΔG</text>',
    "PyMOL": (f'<path d="M12 7 L7 16 M12 7 L17 16 M7 16 H17" stroke="{INK}" stroke-width="1.8" fill="none"/>'
              f'<circle cx="12" cy="6.5" r="3.6" fill="{INK}"/><circle cx="6.5" cy="16.5" r="3.2" fill="{INK}"/><circle cx="17.5" cy="16.5" r="3.2" fill="{INK}"/>'),
    "Modeller": f'<path d="M12 2.5 L20.5 7.2 V16.8 L12 21.5 L3.5 16.8 V7.2 Z M12 12 V21.5 M12 12 L3.5 7.2 M12 12 L20.5 7.2" fill="none" stroke="{INK}" stroke-width="1.8" stroke-linejoin="round"/>',
    "Transformers": (f'<g stroke="{INK}" stroke-width="1" opacity=".55">' +
                     ''.join(f'<path d="M{a} 6 L{b} 18"/>' for a in (5, 12, 19) for b in (5, 12, 19)) + '</g>'
                     f'<g fill="{INK}">' + ''.join(f'<circle cx="{x}" cy="{y}" r="2.6"/>' for x in (5, 12, 19) for y in (6, 18)) + '</g>'),
}


def bubble_face(name):
    """Inside of a bubble: a logo with its name beneath, or lettering for acronyms."""
    if name in BADGES:
        lines, fs = BADGES[name]
        ys = [4] if len(lines) == 1 else [-2.5, 9]
        return ''.join(f'<text class="btxt" y="{y}" font-size="{fs}">{t}</text>' for t, y in zip(lines, ys))
    if name in WORDMARKS:  # these logos already spell their own name
        return f'<g transform="translate(-18 -18) scale(1.5)"><path d="{ICONS[name]}" fill="{INK}"/></g>'
    label = LABELS.get(name, name)
    fs = 8.4 if len(label) < 10 else 7.6 if len(label) < 12 else 7
    icon = CUSTOM_ICONS.get(name) or f'<path d="{ICONS[name]}" fill="{INK}"/>'
    return f'<g transform="translate(-9.6 -21.5) scale(.8)">{icon}</g><text class="btxt" y="14" font-size="{fs}">{label}</text>'


def skills():
    r = 25
    rings = [(388, 21), (330, 17), (272, 14), (214, 11), (156, 8)]
    cx0, cy0 = 450, 446
    w, h = 900, 500
    assert sum(n for _, n in rings) >= sum(len(v) for v in SKILLS.values())
    body = sky_dressing(w, h, 21, 12)
    for i, col in enumerate(["#ff9ec7", "#ffc9a3", "#fff0a3", "#b6f0c8", "#a8d8ff", "#cdb6ff"]):
        rr = 416 - i * 11
        body += (f'<path d="M{cx0 - rr} {cy0} A{rr} {rr} 0 0 1 {cx0 + rr} {cy0}" fill="none" stroke="{col}" stroke-width="11" '
                 f'style="opacity:var(--rb)"/>')
    for x, y, k in ((110, 17, 1.6), (290, 34, 1.4), (450, 22, 1.8), (610, 34, 1.4), (790, 17, 1.6)):
        body += (f'<g transform="translate({x} {cy0 + y}) scale({k})"><g class="cloudfill"><ellipse rx="60" ry="22"/>'
                 f'<circle cx="-20" cy="-14" r="24"/><circle cx="18" cy="-22" r="28"/><circle cx="44" cy="-8" r="17"/></g></g>')
    # fill the slots from left to right so each category forms a wedge of the rainbow
    slots = []
    for j, (rad, n) in enumerate(rings):
        for i in range(n):
            ang = math.pi * (1 + (i + .5) / n)
            slots.append((round(ang, 3), j, cx0 + rad * math.cos(ang), cy0 + rad * math.sin(ang)))
    slots.sort()
    order = [(name, cat) for cat, names in SKILLS.items() for name in names]
    # every item gets a slot; leftover slots are spread evenly by skipping every k-th one
    spare = len(slots) - len(order)
    skip = {round((k + .5) * len(slots) / spare) for k in range(spare)} if spare else set()
    free = [s for i, s in enumerate(slots) if i not in skip][:len(order)]
    bubbles = ''
    for idx, ((name, cat), (_, _, x, y)) in enumerate(zip(order, free)):
        bubbles += (f'<g transform="translate({x:.0f} {y:.0f})"><g class="pop" style="animation-delay:{round(.3 + idx * .05, 2)}s">'
                    f'<g class="fl" style="animation-duration:{4 + (idx % 4) * .7:.1f}s;animation-delay:{-idx * .6:.1f}s">'
                    f'<circle r="{r}" fill="url(#g-{cat})" stroke="#fff" stroke-opacity=".8" stroke-width="2"/>'
                    f'<ellipse cx="-9" cy="-15" rx="10" ry="5" fill="#fff" opacity=".55" transform="rotate(-30 -9 -15)"/>'
                    f'{bubble_face(name)}</g></g></g>')
    grads = ''.join(f'<radialGradient id="g-{c}" cx=".35" cy=".3" r=".9"><stop offset="0" stop-color="var(--{c}1)"/>'
                    f'<stop offset="1" stop-color="var(--{c}2)"/></radialGradient>' for c in CATS)
    lw = 700
    lx = 450 - lw // 2
    legend = f'<g transform="translate(0 {cy0 + 34})"><rect x="{lx}" y="-17" width="{lw}" height="28" rx="14" fill="var(--pill)" opacity=".92"/>'
    for (c, label), x in zip(CATS.items(), [lx + 30, lx + 215, lx + 365, lx + 500]):
        legend += (f'<circle cx="{x}" cy="-3" r="7" fill="url(#g-{c})" stroke="#fff" stroke-width="1.5"/>'
                   f'<text class="ink" x="{x + 14}" y="1" font-size="13" font-weight="600">{label}</text>')
    legend += '</g>'
    body += (f'<defs>{grads}</defs>' + bubbles
             + f'<g transform="translate(355 {cy0 - 116})"><g class="bob"><image href="{data_uri("skills.gif")}" width="190" height="116"/></g></g>'
             + legend)
    body = f'<style>{BUBBLE_CSS}</style>' + body
    write("skills.svg", svg(w, h, body, "Cinnamoroll floating under a rainbow, surrounded by bubbles of all my skills"))


# ---------- 4. cafe menu ----------
CAFE_CSS = '''
:root{--wall:#fdeef2;--dot:#ffd6e5;--wood:#efd0a8;--woodd:#d9b283;--board:#33466b;--chalk:#fff;--chalk2:#ffc2dc;--chalk3:#ffe49a;--aw1:#ff9ec7;--aw2:#fff;--bulb:#ffd36e;--bulb2:#ff9ec7}
@media (prefers-color-scheme:dark){:root{--wall:#2a2450;--dot:#383066;--wood:#8a6a58;--woodd:#6c5042;--board:#171f3d;--aw1:#d96a9b;--aw2:#e9e3ff;--bulb:#ffe49a;--bulb2:#ffb3d9}}
.swing{animation:sw 3.6s ease-in-out infinite;transform-origin:0 0}
@keyframes sw{0%,100%{transform:rotate(-7deg)}50%{transform:rotate(7deg)}}
.row{opacity:0;animation:rw .8s ease-out forwards}
@keyframes rw{from{opacity:0;transform:translateX(-24px)}to{opacity:1;transform:none}}
.steam{opacity:0;animation:st 3s ease-in-out infinite}
@keyframes st{0%{opacity:0;transform:translateY(8px)}40%{opacity:.8}100%{opacity:0;transform:translateY(-16px)}}
.glow{animation:gw 2.4s ease-in-out infinite}
@keyframes gw{0%,100%{opacity:.45}50%{opacity:1}}
.chalk{font-family:'Trebuchet MS',Verdana,sans-serif}
'''


def cafe():
    w, h = 900, 470
    items = [("TP53 structural patches", "master's thesis", "AUC 0.82"),
             ("Protein multimodal classifier", "ESM-2 + EfficientNet", "EC classes"),
             ("Endometriosis pQTL MR", "two-platform, subtype-resolved", "pQTL"),
             ("Fibro NLP pipeline", "Reddit + Claude API tagging", "NLP"),
             ("Endo-fibro literature mining", "BERTopic + RAG on PubMed", "RAG")]
    b = f'<style>{CAFE_CSS}</style>'
    # wall with polka dots
    b += ('<defs><pattern id="dots" width="34" height="34" patternUnits="userSpaceOnUse"><circle cx="9" cy="9" r="3.2" fill="var(--dot)"/>'
          '<circle cx="26" cy="26" r="3.2" fill="var(--dot)"/></pattern>'
          '<clipPath id="win"><path d="M50 352 V196 A115 115 0 0 1 280 196 V352 Z"/></clipPath></defs>'
          f'<rect width="{w}" height="{h}" rx="28" fill="var(--wall)"/><rect width="{w}" height="{h}" rx="28" fill="url(#dots)"/>')
    # window onto the sky
    b += ('<g clip-path="url(#win)"><rect x="40" y="70" width="250" height="290" fill="url(#sky)"/>'
          '<g transform="translate(230 150) scale(.45)"><circle class="sun" r="30" fill="#ffd36e"/>'
          '<path class="moon" d="M-8 -30 A30 30 0 1 0 28 12 A24 24 0 1 1 -8 -30Z" fill="#fff3b8"/></g>'
          + star(95, 190, 5, 'p', .4, True) + star(240, 260, 4, '', 1.1, True) + star(130, 250, 4, '', 1.8, True)
          + cloud(120, 240, .8, 8, 0) + cloud(230, 300, .6, 10, -4) + '</g>'
          '<path d="M50 352 V196 A115 115 0 0 1 280 196 V352" fill="none" stroke="var(--woodd)" stroke-width="9"/>'
          '<path d="M165 81 V352 M50 230 H280" stroke="var(--woodd)" stroke-width="6"/>'
          '<rect x="38" y="346" width="254" height="12" rx="6" fill="var(--woodd)"/>')
    # chalkboard menu
    # edit the menu text here: (section title, [(line, right-hand tag)])
    sections = [("mains", [("TP53 structural patches", "AUC 0.82"),
                           ("Protein multimodal classifier", "EC classes"),
                           ("Endometriosis pQTL MR", "two-platform"),
                           ("Fibromyalgia blood RNA-seq", "discriminative signal")]),
                ("specials", [("now cooking: pQTL MR + single-cell mapping", ""),
                              ("also cooking: endometriosis-fibromyalgia NLP", "")])]
    b += ('<rect x="470" y="112" width="400" height="232" rx="16" fill="var(--board)" stroke="var(--woodd)" stroke-width="9"/>'
          )
    y, n = 168, 0
    for title, lines in sections:
        b += (f'<g class="row" style="animation-delay:{round(.3 + n * .22, 2)}s"><text class="chalk" x="490" y="{y}" font-size="12.5" '
              f'font-weight="700" letter-spacing="1.5" fill="var(--chalk2)">{title.upper()}</text>'
              f'<line x1="{490 + len(title) * 10 + 14}" x2="850" y1="{y - 4}" y2="{y - 4}" stroke="var(--chalk2)" stroke-width="1.6" '
              f'stroke-dasharray="1 6" stroke-linecap="round"/></g>')
        n += 1
        y += 20
        for text, tag in lines:
            b += (f'<g class="row" style="animation-delay:{round(.3 + n * .22, 2)}s">'
                  f'<text class="chalk" x="490" y="{y}" font-size="13.5" font-weight="700" fill="var(--chalk)">{text}</text>'
                  f'<text class="chalk" x="850" y="{y}" text-anchor="end" font-size="12.5" font-weight="700" fill="var(--chalk3)">{tag}</text></g>')
            n += 1
            y += 20
        y += 12
    # counter, props and Cinnamoroll
    b += ('<rect x="0" y="352" width="900" height="118" fill="var(--wood)"/><rect x="0" y="344" width="900" height="16" fill="var(--woodd)"/>'
          + ''.join(f'<path d="M{x} 470 v-60 a22 22 0 0 1 44 0 v60" fill="none" stroke="var(--woodd)" stroke-width="3" opacity=".7"/>' for x in range(20, 900, 88)))
    b += (f'<g transform="translate(232 222)"><g class="bob"><image href="{data_uri("cafe.gif")}" width="215" height="112"/></g></g>')
    # cake under a glass dome
    b += ('<g transform="translate(118 344)"><ellipse cy="2" rx="46" ry="7" fill="var(--woodd)"/><rect x="-30" y="-28" width="60" height="28" rx="6" fill="#ffd6e5"/>'
          '<rect x="-30" y="-28" width="60" height="9" rx="4" fill="#fff"/><circle cy="-34" r="6" fill="#ff6f9c"/>'
          '<path d="M-40 0 A40 44 0 0 1 40 0 Z" fill="#fff" fill-opacity=".28" stroke="#fff" stroke-opacity=".8" stroke-width="2.5"/>'
          '<ellipse cx="-16" cy="-34" rx="5" ry="12" fill="#fff" opacity=".5" transform="rotate(25 -16 -34)"/></g>')
    # steaming cup
    b += ('<g transform="translate(430 344)"><path d="M-22 -34 h44 v18 a22 22 0 0 1 -22 22 a22 22 0 0 1 -22 -22 Z" fill="#fff" stroke="var(--l2)" stroke-width="3"/>'
          '<path d="M22 -28 q18 2 12 16 q-4 8 -14 8" fill="none" stroke="var(--l2)" stroke-width="3"/>'
          '<ellipse cy="-34" rx="22" ry="5" fill="#c98a5e"/><ellipse cx="0" cy="-12" rx="5" ry="4" fill="#ff9ec7" opacity=".8"/>'
          + ''.join(f'<path class="steam" style="animation-delay:{d}s" d="M{x} -42 q-6 -9 0 -18 q6 -9 0 -18" fill="none" stroke="var(--sub)" stroke-width="3" stroke-linecap="round"/>'
                    for x, d in ((-10, 0), (6, 1.0), (20, 1.9))) + '</g>')
    # awning with plaque
    stripes = ''.join(f'<rect x="{i * 50}" y="0" width="50" height="58" fill="{"var(--aw1)" if i % 2 == 0 else "var(--aw2)"}"/>'
                      f'<circle cx="{i * 50 + 25}" cy="58" r="25" fill="{"var(--aw1)" if i % 2 == 0 else "var(--aw2)"}"/>' for i in range(18))
    b += f'<clipPath id="top"><rect width="{w}" height="{h}" rx="28"/></clipPath><g clip-path="url(#top)">{stripes}</g>'
    b += ('<rect x="300" y="14" width="300" height="46" rx="23" fill="#fff" stroke="var(--aw1)" stroke-width="3"/>'
          '<text class="ink" x="450" y="45" text-anchor="middle" font-size="25" font-weight="700" style="fill:#d9608f">café cinnamoroll</text>')
    # fairy lights
    n = 19
    wire = "M10 92 Q450 160 890 92"
    b += f'<path d="{wire}" fill="none" stroke="var(--woodd)" stroke-width="2"/>'
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * 10 + 2 * (1 - t) * t * 450 + t ** 2 * 890
        y = (1 - t) ** 2 * 92 + 2 * (1 - t) * t * 160 + t ** 2 * 92
        col = "var(--bulb)" if i % 2 == 0 else "var(--bulb2)"
        b += (f'<g transform="translate({x:.0f} {y + 6:.0f})"><circle class="glow" style="animation-delay:{round(i * .17, 2)}s" r="9" fill="{col}" opacity=".35"/>'
              f'<circle r="4.5" fill="{col}"/></g>')
    # hanging OPEN sign
    b += ('<g transform="translate(385 98)"><g class="swing"><path d="M-22 0 L-26 36 M22 0 L26 36" stroke="var(--woodd)" stroke-width="2"/>'
          '<rect x="-34" y="34" width="68" height="26" rx="8" fill="#fff" stroke="var(--aw1)" stroke-width="2.5"/>'
          '<text class="ink" y="52" text-anchor="middle" font-size="14" font-weight="700" style="fill:#d9608f">OPEN</text></g></g>')
    write("cafe.svg", svg(w, h, b, "A cozy cafe scene where the chalkboard menu lists my projects"))


if __name__ == "__main__":
    flight_only = "--flight-only" in sys.argv
    user, token = os.environ.get("GH_USER"), os.environ.get("GH_TOKEN")
    cal = fetch_calendar(user, token) if user and token else sample_calendar()
    flight(cal)
    if not flight_only:
        hero(); skills(); cafe()
    print("built", os.listdir(DIST))
