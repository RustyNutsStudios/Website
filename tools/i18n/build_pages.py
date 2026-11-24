"""Build the seven EGGREGIOUS pages (English included, same template), the press page, and the sitemap.

Writes no translated wording. Store text comes from tools/i18n/store/ (approved Steam
files); interface strings come from strings.json and fall back to English. Every string
that has no approved translation is printed at the end for the translator.

Run:  python tools/i18n/build_pages.py
"""
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i18n_lib as L

ROOT = L.ROOT
CSS_V = "20261116"
FONTS = ("https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow:wght@400;500;600;700"
         "&family=Barlow+Condensed:wght@400;600;700&display=swap")
FONT_RU = "https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;700&display=swap"
KIT_ALL = "media-kit/eggregious-media-kit-all.zip"
TRAILER = "media/trailer/eggregious-trailer-30s-v1.mp4"
POSTER = "media/trailer/eggregious-trailer-30s-v1-poster.jpg"


def esc(x):
    return html.escape(x, quote=True)


def hreflang_block():
    rows = [f'<link rel="alternate" hreflang="{l["htmllang"]}" href="{L.BASE}/{l["file"]}">' for l in L.LANGS]
    rows.append(f'<link rel="alternate" hreflang="x-default" href="{L.BASE}/eggregious.html">')
    return "\n".join(rows)


def switcher(current):
    items = []
    for l in L.LANGS:
        cur = ' aria-current="page"' if l["code"] == current else ""
        items.append(f'<li><a lang="{l["htmllang"]}" hreflang="{l["htmllang"]}" href="{l["file"]}"{cur}>{esc(l["name"])}</a></li>')
    return '<ul class="lang-switch">' + "".join(items) + "</ul>"


def credit_line(code):
    """Developer and publisher exactly as the Steam page shows them (labels are interface strings)."""
    return (f'<p class="credits">{esc(L.s("fs_developer", code))}: {L.DEVELOPER} &nbsp;&middot;&nbsp; '
            f'{esc(L.s("fs_publisher", code))}: {L.PUBLISHER}</p>')


def uses_discord(code):
    """Discord appears only while the playtest switch (tools/playtest.json) is open, and never on the
    Chinese page (Discord is blocked in mainland China: that page is Steam only, switch on or off)."""
    return L.playtest_open() and code != "zh"


def discord_link(code):
    if not uses_discord(code):
        return ""
    return f' &nbsp;&middot;&nbsp; <a href="{L.DISCORD}" target="_blank" rel="noopener">Discord</a>'


def discord_button(code):
    if not uses_discord(code):
        return ""
    return f'<a href="{L.DISCORD}" target="_blank" rel="noopener" class="btn btn-egg">{esc(L.s("discord_join", code))}</a>\n            '


TEMPLATES = L.I18N / "templates"
FULL_NAV = """<nav id="navbar">
    <a href="index.html" class="nav-logo">
        <img src="images/RustyNutsLogoSmall.png" width="80" height="80" alt="Rusty Nuts Studios">
        <span>Rusty Nuts Studios</span>
    </a>
    <ul class="nav-links" id="navLinks">
        <li><a href="index.html#about">About</a></li>
        <li><a href="eggregious.html" aria-current="page">EGGREGIOUS</a></li>
        <li><a href="index.html#nidgets">Nidgets</a></li>
        <li><a href="field.html">F.I.E.L.D.</a></li>
        <li><a href="index.html#tools">Tools</a></li>
        <li><a href="index.html#community">Community</a></li>
    </ul>
    <button class="nav-hamburger" id="navToggle" aria-label="Toggle menu">
        <span></span><span></span><span></span>
    </button>
</nav>"""
LOGO_NAV = """<nav id="navbar">
    <a href="index.html" class="nav-logo">
        <img src="images/RustyNutsLogoSmall.png" width="80" height="80" alt="Rusty Nuts Studios">
        <span>Rusty Nuts Studios</span>
    </a>
</nav>"""
NAV_SCRIPT = """<script>
    // Same nav behaviour as the home page.
    var navbar = document.getElementById('navbar');
    window.addEventListener('scroll', function () {
        navbar.classList.toggle('scrolled', window.scrollY > 60);
    });
    var navToggle = document.getElementById('navToggle');
    var navLinks = document.getElementById('navLinks');
    navToggle.addEventListener('click', function () { navLinks.classList.toggle('open'); });
    navLinks.querySelectorAll('a').forEach(function (a) {
        a.addEventListener('click', function () { navLinks.classList.remove('open'); });
    });
</script>"""


def steps_section(code):
    """The English playtest steps. Exists only while the playtest switch is open."""
    steam = L.steam_url(L.BY_CODE[code])
    return f"""<section id="playtest">
    <div class="egg-wrap">
        <p class="section-label">The playtest</p>
        <h2 class="section-title">Play the test.</h2>
        <p class="game-desc">Access comes through Steam, in waves. The Discord is where you tell us what broke.</p>
        <div class="egg-steps">
            <div class="egg-step"><b>1</b><p>Join the Discord.</p></div>
            <div class="egg-step"><b>2</b><p>Wishlist EGGREGIOUS on Steam and hit Request Access when the button appears. Builds go out in waves; Steam tells you when yours is in.</p></div>
            <div class="egg-step"><b>3</b><p>Play it, then tell us what broke.</p></div>
        </div>
        <div class="egg-actions">
            {discord_button(code)}<a href="{esc(steam)}" target="_blank" rel="noopener" class="btn btn-egg">{esc(L.s('wishlist', code))}</a>
        </div>
    </div>
</section>

<div class="divider"></div>

"""


def kit_section(code):
    lang = L.BY_CODE[code]
    zip_lang = f"media-kit/eggregious-media-kit-{code}.zip"
    sheet = f"media-kit/fact-sheet-{code}.txt"
    return f"""<section id="kit">
    <div class="egg-wrap kit-wrap">
        <h2 class="section-title">{esc(L.s('kit_heading', code))}</h2>
        <p class="game-desc">{esc(L.s('kit_usage', code))}</p>
        <div class="egg-actions kit-actions">
            <a href="{zip_lang}" class="btn btn-egg" download>{esc(L.s('kit_download', code))}<span class="meta">ZIP &middot; {L.size_label(ROOT / zip_lang)}</span></a>
            <a href="{KIT_ALL}" class="btn btn-egg" download>{esc(L.s('kit_all', code))}<span class="meta">ZIP &middot; {L.size_label(ROOT / KIT_ALL)}</span></a>
            <a href="{TRAILER}" class="btn btn-egg" download>{esc(L.s('kit_trailer', code))}<span class="meta">MP4 &middot; {L.size_label(ROOT / TRAILER)}</span></a>
            <a href="{sheet}" class="btn btn-wait" style="cursor: pointer;" download>{esc(L.s('kit_factsheet', code))}<span class="meta">TXT</span></a>
        </div>
        <p class="game-desc kit-note">{esc(L.s('kit_contents', code))}</p>
    </div>
</section>"""


def page(lang):
    code = lang["code"]
    en = code == "en"
    short, about = L.read_store(lang)
    steam = L.steam_url(lang)
    cap = f"images/eggregious/i18n/capsule-{lang['cap']}.jpg"
    noto = f'\n<link href="{FONT_RU}" rel="stylesheet">' if code == "ru" else ""
    tagline = short.split(". ")[0] + "."          # the approved English tag line is the first sentence
    title = f"EGGREGIOUS &mdash; {esc(tagline[:-1])}" if en else "EGGREGIOUS &mdash; Rusty Nuts Studios"
    og_desc = esc(tagline) if en else esc(short)
    nav = FULL_NAV if en else LOGO_NAV
    steps = steps_section(code) if (en and L.playtest_open()) else ""
    follow = (TEMPLATES / "follow-en.html").read_text(encoding="utf-8").strip("\n") + "\n\n" if en else ""
    nav_script = NAV_SCRIPT + "\n\n" if en else ""
    follow_divider = '<div class="divider"></div>\n\n' if en else ""
    if en:   # the English footer is unchanged: the city stays until Tommy rules
        footer = f"""<footer>
    {credit_line(code)}
    <p>&copy; 2026 Rusty Nuts Studios LLC. All rights reserved.</p>
    <p class="footer-location">Tbilisi, Georgia</p>
</footer>"""
    else:
        footer = f"""<footer class="i18n-foot">
    {credit_line(code)}
    <p>&copy; 2026 Rusty Nuts Studios LLC</p>
    <p class="footer-location"><a href="{esc(steam)}" target="_blank" rel="noopener">Steam</a>{discord_link(code)}</p>
</footer>"""
    shots = "\n".join(
        f'            <img src="{L.shot_web(i)}" width="1280" height="720" loading="lazy" alt="EGGREGIOUS">'
        for i in range(len(L.SHOTS)))
    return f"""<!DOCTYPE html>
<html lang="{lang['htmllang']}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{esc(short)}">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="theme-color" content="#141210">
<link rel="canonical" href="{L.BASE}/{lang['file']}">
{hreflang_block()}
<meta property="og:type" content="website">
<meta property="og:site_name" content="Rusty Nuts Studios">
<meta property="og:locale" content="{lang['og']}">
<meta property="og:title" content="EGGREGIOUS">
<meta property="og:description" content="{og_desc}">
<meta property="og:url" content="{L.BASE}/{lang['file']}">
<meta property="og:image" content="{L.BASE}/{cap}">
<meta property="og:image:width" content="1232">
<meta property="og:image:height" content="706">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS}" rel="stylesheet">{noto}
<link rel="stylesheet" href="css/site.css?v={CSS_V}">
</head>
<body class="egg-page i18n-page">

{nav}

<section class="i18n-hero">
    <img src="{cap}" width="1232" height="706" class="i18n-hero-img" alt="EGGREGIOUS" fetchpriority="high">
    <div class="i18n-hero-body">
        {switcher(code)}
        <p class="i18n-short">{esc(short)}</p>
        <div class="egg-actions">
            {discord_button(code)}<a href="{esc(steam)}" target="_blank" rel="noopener" class="btn btn-egg">{esc(L.s('wishlist', code))}</a>
        </div>
    </div>
</section>

<div class="divider"></div>

<section id="about">
    <div class="i18n-wrap i18n-about">
{L.about_to_html(about)}
    </div>
</section>

<div class="divider"></div>

<section id="screenshots">
    <div class="egg-wrap">
        <div class="i18n-shots">
{shots}
        </div>
    </div>
</section>

<div class="divider"></div>

<section id="trailer">
    <div class="egg-wrap">
        <video class="i18n-video" controls preload="none" playsinline width="1920" height="1080" poster="{POSTER}">
            <source src="{TRAILER}" type="video/mp4">
        </video>
    </div>
</section>

<div class="divider"></div>

{steps}{kit_section(code)}

{follow_divider}{follow}{footer}

{nav_script}</body>
</html>
"""


def wr(path, text):
    Path(path).write_text(text, encoding="utf-8", newline="\n")


def fmt_size(path):
    n = Path(path).stat().st_size
    return f"{n / 1024:.0f} KB" if n < 1024 * 1024 else f"{n / 1048576:.1f} MB"


def item(img, w, h, title, meta, links, alt="EGGREGIOUS"):
    anchors = "".join(f'<a href="{href}" download>{esc(label)}</a>' for label, href in links)
    return (f'            <div class="press-item">\n'
            f'                <img src="{img}" width="{w}" height="{h}" loading="lazy" alt="{esc(alt)}">\n'
            f'                <div class="meta"><b>{esc(title)}</b><span>{meta}</span>\n                    {anchors}</div>\n'
            f'            </div>')


def img_dims(rel):
    from PIL import Image
    with Image.open(ROOT / rel) as im:
        return im.size


def press_page():
    """The English press kit page: the current set only (twelve screenshots, capsules, three GIFs, the trailer)."""
    en = L.BY_CODE["en"]
    short, _ = L.read_store(en)
    zip_en, zip_all = "media-kit/eggregious-media-kit-en.zip", KIT_ALL
    loose = "media-kit/en"
    play = (f'\n        <a href="{L.DISCORD}" target="_blank" rel="noopener" class="btn btn-egg">{esc(L.s("discord_join"))}</a>'
            if L.playtest_open() else "")
    langs = " &nbsp;&middot;&nbsp; ".join(
        f'<a lang="{l["htmllang"]}" href="media-kit/eggregious-media-kit-{l["code"]}.zip" download style="color: var(--egg-gold);">{esc(l["name"])}</a>'
        for l in L.LANGS[1:])

    def grid(items):
        return '        <div class="press-grid">\n' + "\n".join(items) + "\n        </div>"

    logos = grid([
        item(f"{loose}/logo/eggregious-logo-en-1280x720.png", 1280, 720, "EGGREGIOUS logo",
             f"PNG, 1280 &times; 720, transparent, {fmt_size(ROOT / loose / 'logo/eggregious-logo-en-1280x720.png')}",
             [("Download", f"{loose}/logo/eggregious-logo-en-1280x720.png")], alt="EGGREGIOUS logo"),
        item(f"{loose}/logo/eggregious-icon-512x512.png", 512, 512, "Icon",
             f"PNG, 512 &times; 512, {fmt_size(ROOT / loose / 'logo/eggregious-icon-512x512.png')}",
             [("Download", f"{loose}/logo/eggregious-icon-512x512.png")], alt="EGGREGIOUS icon"),
    ])
    caps = []
    for title, prev, src, dims in [
        ("Library hero", "press-library-hero.jpg", "eggregious-library-hero-3840x1240.jpg", "JPG, 3840 &times; 1240, art only, no title"),
        ("Main capsule", "press-main-capsule.jpg", "eggregious-main-capsule-1232x706.png", "PNG, 1232 &times; 706"),
        ("Header capsule", "press-header-capsule.jpg", "eggregious-header-capsule-920x430.png", "PNG, 920 &times; 430"),
        ("Vertical capsule", "press-vertical-capsule.jpg", "eggregious-vertical-capsule-748x896.png", "PNG, 748 &times; 896"),
        ("Library capsule", "press-library-capsule.jpg", "eggregious-library-capsule-600x900.png", "PNG, 600 &times; 900"),
        ("Small capsule", "press-small-capsule.jpg", "eggregious-small-capsule-462x174.png", "PNG, 462 &times; 174"),
    ]:
        w, h = img_dims(f"images/eggregious/i18n/{prev}")
        caps.append(item(f"images/eggregious/i18n/{prev}", w, h, title,
                         f"{dims}, {fmt_size(ROOT / loose / 'capsules' / src)}",
                         [("Download", f"{loose}/capsules/{src}")], alt=f"EGGREGIOUS {title.lower()}"))
    capsules = grid(caps)
    shots = []
    for i, (stem, name) in enumerate(L.SHOTS):
        full = f"{loose}/screenshots/eggregious-{i + 1:02d}-{name}-1920x1080.jpg"
        shots.append(item(L.shot_web(i), 1280, 720, f"{i + 1:02d}",
                          f"JPG, 1920 &times; 1080, {fmt_size(ROOT / full)}", [("Download", full)]))
    screenshots = grid(shots)
    gifs = grid([
        item(g, 616, 347, f"GIF {i + 1}", f"GIF, 616 &times; 347, {fmt_size(ROOT / g)}", [("Download", g)])
        for i, g in enumerate(sorted(set(L.GIFS.values()), key=lambda x: ["drop", "lead", "horde"].index(x.split("-")[-1][:-4])))])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>EGGREGIOUS press kit &mdash; Rusty Nuts Studios</title>
<meta name="description" content="Press kit for EGGREGIOUS: fact sheet, logo, capsules, twelve screenshots, three GIFs and the trailer, in seven languages, plus one zip of everything.">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="theme-color" content="#141210">
<link rel="canonical" href="{L.BASE}/press.html">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Rusty Nuts Studios">
<meta property="og:title" content="EGGREGIOUS press kit">
<meta property="og:description" content="Fact sheet, logo, capsules, screenshots, GIFs and the trailer for EGGREGIOUS, in seven languages.">
<meta property="og:url" content="{L.BASE}/press.html">
<meta property="og:image" content="{L.BASE}/images/eggregious/i18n/capsule-en.jpg">
<meta property="og:image:width" content="1232">
<meta property="og:image:height" content="706">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS}" rel="stylesheet">
<link rel="stylesheet" href="css/site.css?v={CSS_V}">
</head>
<body class="egg-page">

<nav id="navbar">
    <a href="index.html" class="nav-logo">
        <img src="images/RustyNutsLogoSmall.png" width="80" height="80" alt="Rusty Nuts Studios">
        <span>Rusty Nuts Studios</span>
    </a>
    <ul class="nav-links" id="navLinks">
        <li><a href="index.html#about">About</a></li>
        <li><a href="eggregious.html">EGGREGIOUS</a></li>
        <li><a href="index.html#nidgets">Nidgets</a></li>
        <li><a href="field.html">F.I.E.L.D.</a></li>
        <li><a href="index.html#tools">Tools</a></li>
        <li><a href="index.html#community">Community</a></li>
    </ul>
    <button class="nav-hamburger" id="navToggle" aria-label="Toggle menu">
        <span></span><span></span><span></span>
    </button>
</nav>

<section class="press-head" id="top">
    <img src="images/eggregious/i18n/capsule-en.jpg" width="1232" height="706" alt="EGGREGIOUS" class="press-head-capsule">
    <h1>Press kit</h1>
    <p class="game-desc">{esc(L.s('kit_usage'))}</p>
    <div class="egg-actions">
        <a href="{zip_en}" class="btn btn-egg" download>{esc(L.s('kit_download'))}<span class="meta">ZIP &middot; {L.size_label(ROOT / zip_en)}</span></a>
        <a href="{zip_all}" class="btn btn-egg" download>{esc(L.s('kit_all'))}<span class="meta">ZIP &middot; {L.size_label(ROOT / zip_all)}</span></a>
        <a href="{L.STEAM_BASE}?{L.UTM}" target="_blank" rel="noopener" class="btn btn-egg">{esc(L.s('wishlist'))}</a>{play}
    </div>
    <p class="game-desc" style="margin-top: 22px;">Kits in other languages: {langs}</p>
</section>

<div class="divider"></div>

<section id="facts">
    <div class="egg-wrap">
        <p class="section-label">Fact sheet</p>
        <h2 class="section-title">EGGREGIOUS</h2>
        <p class="game-desc">As on the Steam page.</p>
        <table class="press-table">
            <tr><th>Title</th><td>EGGREGIOUS</td></tr>
            <tr><th>Developer</th><td>{L.DEVELOPER}</td></tr>
            <tr><th>Publisher</th><td>{L.PUBLISHER}</td></tr>
            <tr><th>Short description</th><td>{esc(short)}</td></tr>
            <tr><th>In the game</th><td>{esc(L.s('fs_figures'))}</td></tr>
            <tr><th>Platform</th><td>Windows PC, on Steam.</td></tr>
            <tr><th>Release</th><td>To be announced.</td></tr>
            <tr><th>Steam</th><td><a href="{L.STEAM_BASE}?{L.UTM}" target="_blank" rel="noopener">store.steampowered.com/app/4036510</a></td></tr>
        </table>
        <p class="game-desc" style="margin-top: 18px;"><a href="media-kit/fact-sheet-en.txt" download style="color: var(--egg-gold);">{esc(L.s('kit_factsheet'))} (TXT)</a></p>
    </div>
</section>

<div class="divider"></div>

<section id="logo">
    <div class="egg-wrap">
        <p class="section-label">Logo</p>
        <h2 class="section-title">The marks.</h2>
{logos}
    </div>
</section>

<div class="divider"></div>

<section id="capsules">
    <div class="egg-wrap">
        <p class="section-label">Steam art</p>
        <h2 class="section-title">Capsules and hero.</h2>
{capsules}
    </div>
</section>

<div class="divider"></div>

<section id="screenshots">
    <div class="egg-wrap">
        <p class="section-label">Screenshots</p>
        <h2 class="section-title">Twelve stills.</h2>
{screenshots}
    </div>
</section>

<div class="divider"></div>

<section id="gifs">
    <div class="egg-wrap">
        <p class="section-label">GIFs</p>
        <h2 class="section-title">Three loops.</h2>
{gifs}
    </div>
</section>

<div class="divider"></div>

<section id="trailer">
    <div class="egg-wrap">
        <p class="section-label">Trailer</p>
        <h2 class="section-title">30 seconds.</h2>
        <video class="i18n-video" controls preload="none" playsinline width="1920" height="1080" poster="{POSTER}">
            <source src="{TRAILER}" type="video/mp4">
        </video>
        <p class="game-desc" style="margin: 20px auto 0; text-align: center;"><a href="{TRAILER}" download style="color: var(--egg-gold);">{esc(L.s('kit_trailer'))} (MP4, {fmt_size(ROOT / TRAILER)})</a></p>
    </div>
</section>

<div class="divider"></div>

<section id="all">
    <div class="egg-wrap kit-wrap">
        <p class="section-label">Everything</p>
        <h2 class="section-title">One zip.</h2>
        <p class="game-desc">{esc(L.s('kit_usage'))}</p>
        <div class="egg-actions kit-actions">
            <a href="{zip_en}" class="btn btn-egg" download>{esc(L.s('kit_download'))}<span class="meta">ZIP &middot; {L.size_label(ROOT / zip_en)}</span></a>
            <a href="{zip_all}" class="btn btn-egg" download>{esc(L.s('kit_all'))}<span class="meta">ZIP &middot; {L.size_label(ROOT / zip_all)}</span></a>
        </div>
        <p class="game-desc" style="margin: 30px auto 0;"><a href="eggregious.html" style="color: var(--egg-gold); text-decoration: none; font-weight: 600;">&larr; Back to EGGREGIOUS</a></p>
    </div>
</section>

<footer>
    {credit_line('en')}
    <p>&copy; 2026 Rusty Nuts Studios LLC. All rights reserved.</p>
    <p class="footer-location">Tbilisi, Georgia</p>
</footer>

<script>
    var navbar = document.getElementById('navbar');
    window.addEventListener('scroll', function () {{
        navbar.classList.toggle('scrolled', window.scrollY > 60);
    }});
    var navToggle = document.getElementById('navToggle');
    var navLinks = document.getElementById('navLinks');
    navToggle.addEventListener('click', function () {{ navLinks.classList.toggle('open'); }});
</script>

</body>
</html>
"""


def build_press():
    p = ROOT / "press.html"
    old = p.read_text(encoding="utf-8") if p.exists() else ""
    nl = "\r\n" if "\r\n" in old else "\n"
    p.write_text(press_page().replace("\n", nl), encoding="utf-8", newline="")


def patch_sitemap():
    p = ROOT / "sitemap.xml"
    s = p.read_text(encoding="utf-8")
    for l in L.LANGS[1:]:
        url = f"{L.BASE}/{l['file']}"
        if url not in s:
            s = s.replace("</urlset>", f"  <url><loc>{url}</loc><lastmod>2026-11-16</lastmod></url>\n</urlset>")
    p.write_text(s, encoding="utf-8", newline="")


def main():
    for lang in L.LANGS:
        wr(ROOT / lang["file"], page(lang))
        print("wrote", lang["file"])
    build_press()
    patch_sitemap()
    print("rebuilt press.html, updated sitemap.xml")

    missing = L.missing_strings()
    keys = L.all_string_keys()
    lines = ["Interface strings still without an approved translation (English shows until they are sent):", ""]
    todo = {c: [k for k in v if not (c == "zh" and k == "discord_join")] for c, v in missing.items()}
    if not any(todo.values()):
        lines.append("  none: every language has every string (zh discord_join is empty on purpose).")
    for c, ks in todo.items():
        for k in ks:
            lines.append(f"  {c:6} {k:14} {keys[k]}")
    lines += ["", "Language names are used as written (autonyms): " + ", ".join(l["name"] for l in L.LANGS),
              "Image alt text on the localised pages is the game name only: EGGREGIOUS."]
    wr(ROOT / "tools" / "i18n" / "TRANSLATOR_STRINGS.txt", "\n".join(lines) + "\n")
    print("wrote tools/i18n/TRANSLATOR_STRINGS.txt")


if __name__ == "__main__":
    main()
