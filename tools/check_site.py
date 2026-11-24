"""Static checks for the Rusty Nuts site. Run from anywhere:

    python tools/check_site.py            (checks the repo this file lives in)
    python tools/check_site.py <path>     (checks another copy of the site)

The playtest switch (tools/playtest.json) decides what the pages must and must not say:
  closed  no Discord invite, no Request Access, no playtest wording, no dates. The only call to action is Wishlist.
  open    the Discord invite and the playtest steps are present.

Exit code 1 if anything FAILs. WARNs do not fail.
"""
import html as htmllib
import json
import os
import re
import sys
import zipfile
from html.parser import HTMLParser
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "i18n"))
import i18n_lib as L  # noqa: E402

OPEN = json.loads((ROOT / "tools" / "playtest.json").read_text(encoding="utf-8"))["open"]
fails, warns = [], []


def fail(m):
    fails.append(m)


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs, self.text, self.skip, self.imgs_no_dims = [], [], 0, []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style"):
            self.skip += 1
        if tag in ("a", "link") and a.get("href"):
            self.refs.append(a["href"])
        if tag in ("img", "source", "video", "script") and a.get("src"):
            self.refs.append(a["src"])
        if tag == "video" and a.get("poster"):
            self.refs.append(a["poster"])
        if tag in ("img", "source") and a.get("srcset"):
            self.refs.append(a["srcset"].split()[0])
        if tag == "meta" and a.get("content", "").startswith(("images/", "/images/")):
            self.refs.append(a["content"].lstrip("/"))
        if tag == "img" and a.get("src") and not (a.get("width") and a.get("height")):
            self.imgs_no_dims.append(a["src"])

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip -= 1

    def handle_data(self, d):
        if not self.skip:
            self.text.append(d)


pages, raw, vis = {}, {}, {}
for f in sorted(os.listdir(ROOT)):
    if not f.endswith(".html"):
        continue
    src = (ROOT / f).read_text(encoding="utf-8")
    p = P()
    p.feed(src)
    pages[f], raw[f] = p, src
    stripped = re.sub(r"<!--.*?-->", "", src, flags=re.S)
    stripped = re.sub(r"<(script|style).*?</\1>", "", stripped, flags=re.S)
    inline_gone = re.sub(r"</?(?:strong|b|em|i|span|a)\b[^>]*>", "", stripped)
    vis[f] = htmllib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", inline_gone)))
    for ref in p.refs:
        if ref.startswith(("http://", "https://", "mailto:", "#", "data:")):
            continue
        path = ref.split("#")[0].split("?")[0].lstrip("/")
        if path and not (ROOT / path).exists():
            fail(f"{f}: missing local file {ref}")
    if p.imgs_no_dims and f not in ("field.html",):
        warns.append(f"{f}: {len(p.imgs_no_dims)} img without width/height")


def need(f, needle, label):
    if f not in raw:
        fail(f"missing page {f}")
    elif needle not in raw[f] and needle not in htmllib.unescape(raw[f]):
        fail(f"{f}: missing {label}")


def src_no_utm(f):
    return raw[f].replace("utm_campaign=playtest", "utm_campaign=XX")


# ---- the old site: Hard Boiled gone, Nidgets and F.I.E.L.D. kept ----
for f in pages:
    if f != "hardboiled.html":
        for bad in ("Hard Boiled", "HardBoiled", "TODO"):
            if bad in vis[f]:
                fail(f"{f}: public text contains '{bad}'")
if re.search(r"#hardboiled", re.sub(r"<script.*?</script>|<!--.*?-->", "", raw.get("index.html", ""), flags=re.S)):
    fail("index.html: a visible link still points at #hardboiled")
need("index.html", "location.hash", "#hardboiled redirect script")
need("index.html", "store.steampowered.com/app/4376220", "Nidgets Steam link")
need("index.html", "store.steampowered.com/app/5362610", "Nidgets demo link")
need("hardboiled.html", 'http-equiv="refresh"', "meta refresh")
need("404.html", "eggregious.html", "404 link to EGGREGIOUS")
for keep in ("NidgetsLibrary_Capsule__1_.jpg", "Nidgets_Libary_HERO.jpg", "NidgetsLibrary_Logo.png",
             "Nidgets_Steamrustynuts__steam_art.jpg", "field-capsule.jpg", "field-keyart.jpg"):
    if not (ROOT / "images" / keep).exists():
        fail(f"Nidgets/F.I.E.L.D. file deleted: images/{keep}")
for f in os.listdir(ROOT / "images"):
    if re.search(r"hard", f, re.I) or f == "banner.jpg":
        fail(f"old image still present: images/{f}")
if (ROOT / "press").exists():
    fail("the old press/ folder is still present (the kit lives in media-kit/)")

# ---- the playtest switch ----
UTM = "utm_source=website&utm_medium=web&utm_campaign=playtest"
EGG_PAGES = ("eggregious.html", "index.html", "press.html", "faq.html", "devlog.html")
LOCAL_PAGES = tuple(l["file"] for l in L.LANGS[1:])
for f in EGG_PAGES:
    need(f, "store.steampowered.com/app/4036510/EGGREGIOUS/?", "Steam wishlist link")
    need(f, UTM, "wishlist UTM")
    if "<!-- ps:" in raw.get(f, "") and raw[f].count("<!-- ps:") != raw[f].count("<!-- /ps:"):
        fail(f"{f}: unbalanced playtest-switch markers")
if OPEN:
    for f in EGG_PAGES + LOCAL_PAGES:
        if f == "eggregious-zh.html":
            continue
        need(f, L.DISCORD, "Discord invite (switch is open)")
    need("eggregious.html", "Request Access", "the Request Access line (switch is open)")
else:
    for f in EGG_PAGES + LOCAL_PAGES:
        s = src_no_utm(f)
        if "discord.gg/ShP2fYkxZq" in s:
            fail(f"{f}: Discord invite present while the playtest is closed")
        if re.search(r"Request Access", s):
            fail(f"{f}: Request Access present while the playtest is closed")
        if re.search(r"discord", s, re.I):
            fail(f"{f}: the word Discord present while the playtest is closed")
        if re.search(r"[Pp]laytest", s):
            fail(f"{f}: playtest wording present while the playtest is closed")
        if "PLAY THE TEST" in s:
            fail(f"{f}: PLAY THE TEST present while the playtest is closed")
    # the one call to action is Wishlist
    for f in ("eggregious.html", "press.html", "faq.html", "devlog.html") + LOCAL_PAGES:
        if "Wishlist on Steam" not in raw.get(f, "") and f not in LOCAL_PAGES:
            fail(f"{f}: no Wishlist on Steam button")
for f in pages:
    if "PLAY THE TEST" in raw[f]:
        fail(f"{f}: the old button wording PLAY THE TEST is still there")
if "eggregious-zh.html" in raw and re.search(r"discord", raw["eggregious-zh.html"], re.I):
    fail("eggregious-zh.html: Discord appears (the Chinese page never shows Discord, switch on or off)")
if "index.html" in raw and "dsc.gg" in raw["index.html"]:
    fail("index.html: the dead Discord vanity dsc.gg is linked (use the invite of record, and only while the switch is open)")
for f in EGG_PAGES + LOCAL_PAGES:
    if f in raw and re.search(r"\bkeys?\b", re.sub(r"<!--.*?-->", "", raw[f], flags=re.S), re.I):
        fail(f"{f}: the word key/keys appears")
    if f in vis and re.search(r"this week|opening soon|opens in", vis[f], re.I):
        fail(f"{f}: dated or timed wording")

# ---- the home About paragraph describes EGGREGIOUS in the words of the locked short ----
if "index.html" in raw:
    if "squad of six" in raw["index.html"] or "horde of thousands" in raw["index.html"]:
        fail("index.html: the old EGGREGIOUS description (squad of six / horde of thousands) is still in the About paragraph")
    if "an elite team of shock troops holds the line against thousands of bugs" not in raw["index.html"]:
        fail("index.html: the About paragraph does not carry the approved clause")

# ---- the game's TikTok is @playeggregious; the old handle is a dead account ----
for f in pages:
    if "tiktok.com/@eggregiousgame" in raw[f]:
        fail(f"{f}: links the dead TikTok handle @eggregiousgame (the game's TikTok is @playeggregious)")
for f in ("eggregious.html", "faq.html", "devlog.html"):
    need(f, "tiktok.com/@playeggregious", "the game's TikTok link (@playeggregious)")

# ---- X is closed for good: no link, icon, handle or share button on any page ----
X_PATTERN = re.compile(r"x\.com|twitter\.com|X / Twitter|\bon X\b|share on|tweet|RustyNutsStudio\b|M18\.244 2\.25")
for f in pages:
    m = X_PATTERN.search(raw[f])
    if m:
        fail(f"{f}: an X / Twitter trace is on the page ({m.group(0)})")

# ---- old EGGREGIOUS pictures must not creep back onto any page ----
for f in pages:
    if "capsule-vertical-748.jpg" in raw[f]:
        fail(f"{f}: the old vertical capsule is still used (use images/eggregious/i18n/press-vertical-capsule.jpg)")
    if "images/eggregious/wordmark.png" in raw[f]:
        fail(f"{f}: the old wordmark picture is still used (use the current capsule)")

# ---- FAQ and press: locked English short in, old Steam line out, current capsule in ----
EN_SHORT = L.read_store(L.BY_CODE["en"])[0]
for f in ("faq.html", "press.html"):
    if "Recruit an elite team of specialists" in raw.get(f, ""):
        fail(f"{f}: the old Steam line is still there")
    if EN_SHORT not in htmllib.unescape(raw.get(f, "")):
        fail(f"{f}: the locked English short description is missing")
    need(f, "images/eggregious/i18n/capsule-en.jpg", "the current capsule")
    if "wordmark.png" in raw.get(f, ""):
        fail(f"{f}: the old wordmark picture is still used")
if "index.html" in raw:
    if "Six Soviet-style figures" in raw["index.html"] or "Recruit an elite team of specialists" in raw["index.html"]:
        fail("index.html: the old card text is still there")
    if EN_SHORT not in htmllib.unescape(raw["index.html"]):
        fail("index.html: the home card does not carry the locked English short description")
for f in ("faq.html",):
    if '<img src="images/eggregious/capsule-1232.jpg' in raw.get(f, "") or "capsule-1232.jpg" in raw.get(f, ""):
        fail(f"{f}: the old capsule is still referenced")

# ---- FAQ structured data parses ----
m = re.search(r'<script type="application/ld\+json">(.*?)</script>', raw.get("faq.html", ""), re.S)
try:
    json.loads(m.group(1))
except Exception as e:  # noqa: BLE001
    fail(f"faq.html: FAQ JSON-LD does not parse: {e}")

# ---- sitemap, robots ----
sm = (ROOT / "sitemap.xml").read_text(encoding="utf-8") if (ROOT / "sitemap.xml").exists() else ""
for f in ("eggregious.html", "devlog.html", "faq.html", "press.html", "field.html") + LOCAL_PAGES:
    if f"{L.BASE}/{f}" not in sm:
        fail(f"sitemap.xml: missing {f}")
for f in ("hardboiled.html", "404.html"):
    if f in sm:
        fail(f"sitemap.xml: should not list {f}")
rb = (ROOT / "robots.txt").read_text(encoding="utf-8") if (ROOT / "robots.txt").exists() else ""
if f"Sitemap: {L.BASE}/sitemap.xml" not in rb:
    fail("robots.txt: no sitemap line")

# ---- the seven-language EGGREGIOUS pages ----
# Rules in the fiction: no other games, no boss count, no e-mail, no AI. The developer and publisher MUST appear.
FORBIDDEN_CASE = [r"\bTbilisi\b", r"\bGeorgia\b"]
FORBIDDEN_ANY = [r"\bNidgets\b", r"F\.I\.E\.L\.D", r"Hard Boiled", r"\bBrotato\b", r"Vampire Survivors",
                 r"\bMegabonk\b", r"Halls of Torment"]
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
BOSS_COUNT = re.compile(r"\b(\d+|one|two|three|four|five|six)\s+bosses\b|\bbosses\s*[:x]\s*\d", re.I)
EGG_PUN = re.compile(r"eggcellent|eggs-|egg-cellent|eggstra|eggsplo|cracking|scrambl|yolk|omelet|sunny side", re.I)

hl_expected = {f'hreflang="{l["htmllang"]}"' for l in L.LANGS} | {'hreflang="x-default"'}
for lang in L.LANGS:
    f, code = lang["file"], lang["code"]
    if f not in raw:
        fail(f"missing page {f}")
        continue
    src, text = raw[f], vis[f]
    if f'<html lang="{lang["htmllang"]}"' not in src:
        fail(f"{f}: wrong or missing html lang")
    need(f, f'<link rel="canonical" href="{L.BASE}/{f}">', "canonical")
    for h in hl_expected:
        if h not in src:
            fail(f"{f}: missing {h}")
    for og in ('property="og:title"', 'property="og:description"', 'property="og:image"', 'property="og:url"'):
        need(f, og, og)
    if src.count('class="lang-switch"') != 1 or src.count("<li><a lang=") != len(L.LANGS):
        fail(f"{f}: language switcher is not the seven-link list")
    if f'aria-current="page">{lang["name"]}<' not in src:
        fail(f"{f}: current language not marked in the switcher")
    for rel in (f"media-kit/eggregious-media-kit-{code}.zip", "media-kit/eggregious-media-kit-all.zip",
                f"media-kit/fact-sheet-{code}.txt", L.TRAILER_REL):
        need(f, rel, rel)
    # developer and publisher, exactly as the Steam page shows them
    if L.DEVELOPER not in text or L.PUBLISHER not in text:
        fail(f"{f}: developer/publisher credit missing ({L.DEVELOPER}, {L.PUBLISHER})")
    if code != "en":
        need(f, f"?l={lang['steam']}&{UTM}", "language Steam link with UTM")
        for key in ("wishlist", "kit_heading", "kit_usage", "kit_download", "kit_all", "kit_trailer", "kit_factsheet", "kit_contents", "fs_developer", "fs_publisher"):
            tr = L.s(key, code)
            if key in L.missing_strings()[code]:
                warns.append(f"{f}: no translation for {key} (English shows)")
            elif htmllib.escape(tr, quote=True) not in src and tr not in text:
                fail(f"{f}: translated string {key} is not on the page")
        short, about = L.read_store(lang)
        if short not in text:
            fail(f"{f}: approved short description not found verbatim")
        if htmllib.unescape(re.search(r'<meta name="description" content="([^"]*)"', src).group(1)) != short:
            fail(f"{f}: meta description is not the approved short description")
        for seg in L.about_plain_segments(about):
            seg = re.sub(r"\s+", " ", seg)
            if seg not in text:
                fail(f"{f}: approved About text missing: {seg[:50]}")
        if src.count('<figure class="i18n-gif">') != 3:
            fail(f"{f}: expected 3 GIFs in the About text")
        if src.count('class="i18n-shots"') != 1 or src.count('src="images/eggregious/i18n/shot-') != 12:
            fail(f"{f}: expected 12 screenshots")
        for pat in FORBIDDEN_CASE:
            if re.search(pat, text + " " + src):
                fail(f"{f}: forbidden place name {pat}")
        for pat in FORBIDDEN_ANY:
            if re.search(pat, text + " " + src, re.I):
                fail(f"{f}: forbidden game name {pat}")
        if EMAIL.search(src):
            fail(f"{f}: contains an e-mail address")
        if re.search(r"\bAI\b", text):
            fail(f"{f}: the word AI appears")
    else:
        short, about = L.read_store(lang)
        if "Post-Soviet survivors-like" not in src:
            fail(f"{f}: English title/description is not the approved store text")
        if short not in text:
            fail(f"{f}: approved English short description not found verbatim")
        if htmllib.unescape(re.search(r'<meta name="description" content="([^"]*)"', src).group(1)) != short:
            fail(f"{f}: meta description is not the approved short description")
        for seg in L.about_plain_segments(about):
            seg = re.sub(r"\s+", " ", seg)
            if seg not in text:
                fail(f"{f}: approved About text missing: {seg[:50]}")
        if src.count('<figure class="i18n-gif">') != 3:
            fail(f"{f}: expected 3 GIFs in the About text")
        if src.count('src="images/eggregious/i18n/shot-') != 12:
            fail(f"{f}: expected 12 screenshots")
        for old in ("squad of six", "Six specialists", "Trailer coming", "Hundreds of bugs", "still-horde", "still-boss",
                    "still-storm", "squad-1600", "hero-1920", "wordmark.png"):
            if old.lower() in src.lower():
                fail(f"{f}: old content still present ({old})")
        if 'id="navLinks"' not in src or src.count('class="social-link"') != 3:
            fail(f"{f}: site nav or the Follow row is missing")
        for rel in ("devlog.html", "faq.html", "press.html"):
            need(f, rel, f"link to {rel}")
        if "Tbilisi, Georgia" not in src:
            fail(f"{f}: the footer city was changed (it stays until Tommy rules)")
    if EGG_PUN.search(text):
        warns.append(f"{f}: possible egg pun")
    if BOSS_COUNT.search(text):
        fail(f"{f}: a boss count appears")

# ---- the press kit page: the current set only, every kit file linked ----
loose = ROOT / "media-kit" / "en"
if "press.html" in raw:
    for p in sorted(loose.rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(ROOT)).replace("\\", "/")
            if rel not in raw["press.html"]:
                fail(f"press.html: kit file not linked: {rel}")
    pl = raw["press.html"]
    if pl.count('src="images/eggregious/i18n/shot-') != 12:
        fail("press.html: expected 12 screenshots")
    for l in L.LANGS:
        if f"media-kit/eggregious-media-kit-{l['code']}.zip" not in pl:
            fail(f"press.html: no download for {l['code']}")
    for old in ("posters/", "recruitment", "A WEDGE", 'href="press/', 'src="press/'):
        if old in pl:
            fail(f"press.html: still mentions the old kit ({old})")

# ---- the kits ----
need_names = {"logo": 2, "capsules": 6, "screenshots": 12, "gifs": 3, "trailer": 1}
kit_dir = ROOT / "media-kit"
trailer = ROOT / L.TRAILER_REL
total_kit = 0
for lang in L.LANGS:
    code = lang["code"]
    zp = kit_dir / f"eggregious-media-kit-{code}.zip"
    fs = kit_dir / f"fact-sheet-{code}.txt"
    if not zp.exists() or not fs.exists():
        fail(f"media-kit: missing {zp.name} or {fs.name}")
        continue
    total_kit += zp.stat().st_size
    if zp.stat().st_size > 95 * 1024 * 1024:
        fail(f"{zp.name}: over 95 MB")
    z = zipfile.ZipFile(zp)
    if z.testzip() is not None:
        fail(f"{zp.name}: corrupt")
    names = z.namelist()
    for folder, n in need_names.items():
        c = sum(1 for x in names if f"/{folder}/" in x)
        if c != n:
            fail(f"{zp.name}: {folder}/ has {c} files, expected {n}")
    tz = [x for x in names if x.endswith(".mp4")]
    if tz and trailer.exists() and z.getinfo(tz[0]).file_size != trailer.stat().st_size:
        fail(f"{zp.name}: the trailer inside is not the site's trailer")
    sheet_names = [x for x in names if x.endswith("00-fact-sheet.txt")]
    if not sheet_names:
        fail(f"{zp.name}: no fact sheet")
        continue
    sheet = z.read(sheet_names[0]).decode("utf-8")
    if sheet.replace("\r\n", "\n") != fs.read_bytes().decode("utf-8").replace("\r\n", "\n"):
        fail(f"{zp.name}: fact sheet differs from media-kit/{fs.name}")
    short, about = L.read_store(lang)
    if short not in sheet:
        fail(f"{fs.name}: approved short description not verbatim")
    for seg in L.about_plain_segments(about):
        if seg not in sheet:
            fail(f"{fs.name}: approved About text missing: {seg[:40]}")
    if L.s("fs_figures", code) not in sheet or L.s("fs_tba", code) not in sheet:
        fail(f"{fs.name}: figures line or release line missing")
    if L.DEVELOPER not in sheet or L.PUBLISHER not in sheet:
        fail(f"{fs.name}: developer/publisher missing")
    for pat in FORBIDDEN_CASE:
        if re.search(pat, sheet):
            fail(f"{fs.name}: forbidden place name {pat}")
    for pat in FORBIDDEN_ANY:
        if re.search(pat, sheet, re.I):
            fail(f"{fs.name}: forbidden game name {pat}")
    if EMAIL.search(sheet):
        fail(f"{fs.name}: contains an e-mail address")
za = kit_dir / "eggregious-media-kit-all.zip"
if not za.exists():
    fail("media-kit: missing the all zip")
else:
    z = zipfile.ZipFile(za)
    if z.testzip() is not None:
        fail("all zip: corrupt")
    names = z.namelist()
    if sum(1 for x in names if x.endswith("00-fact-sheet.txt")) != len(L.LANGS):
        fail("all zip: not one fact sheet per language")
    if sum(1 for x in names if x.endswith(".mp4")) != 1:
        fail("all zip: expected exactly one trailer")
    if sum(1 for x in names if "/screenshots/" in x) != 12 or sum(1 for x in names if "/gifs/" in x) != 3:
        fail("all zip: shared screenshots or GIFs wrong")
    if za.stat().st_size > 95 * 1024 * 1024:
        fail("all zip: over 95 MB")
    total_kit += za.stat().st_size
if not trailer.exists() or trailer.stat().st_size > 95 * 1024 * 1024:
    fail("trailer missing or over 95 MB")
for p in ROOT.rglob("*"):
    if p.is_file() and ".git" not in p.parts and p.stat().st_size > 95 * 1024 * 1024:
        fail(f"file over 95 MB (GitHub refuses 100 MB): {p.relative_to(ROOT)}")

# ---- store text copies are intact (14 files) ----
for lang in L.LANGS:
    for k in ("short", "about"):
        if not (ROOT / "tools" / "i18n" / "store" / f"{lang['steam']}_{k}.txt").exists():
            fail(f"store text copy missing: {lang['steam']}_{k}.txt")

for w in warns:
    print("WARN", w)
for x in fails:
    print("FAIL", x)
print(f"{len(fails)} failures, {len(warns)} warnings; playtest switch: {'OPEN' if OPEN else 'closed'}; "
      f"pages checked: {len(pages)}; kit zips total {total_kit / 1048576:.0f} MB")
sys.exit(1 if fails else 0)
