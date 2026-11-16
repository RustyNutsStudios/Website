"""The playtest switch.

tools/playtest.json says whether the playtest is open. This script rewrites every marked
region in the hand-written English pages to match, then rebuilds the generated pages
(the six localised pages and press.html), which read the same file.

    closed (open: false)  no Discord link, no Request Access line, no playtest wording.
                          The only call to action is Wishlist on Steam.
    open   (open: true)   the Play button (Discord invite), the three playtest steps with the
                          Steam Request Access line, and the playtest FAQ answers come back.

A region is a pair of comment lines in the page:
    <!-- ps:NAME -->
      ...generated, do not edit by hand...
    <!-- /ps:NAME -->

Run:  python tools/playtest_switch.py
"""
import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE / "i18n"))
import i18n_lib as L  # noqa: E402

STEAM = f"{L.STEAM_BASE}?{L.UTM}"


def is_open():
    return bool(json.loads((HERE / "playtest.json").read_text(encoding="utf-8"))["open"])


def play(cls):
    return f'<a href="{L.DISCORD}" target="_blank" rel="noopener" class="btn {cls}">{L.s("discord_join")}</a>'


# ---- the FAQ questions that change with the switch -------------------------------------------------
Q_WHEN_OPEN = "Release date to be announced. A playtest comes first, with access through Steam in waves."
Q_WHEN_CLOSED = "Release date to be announced."


def faq_jsonld(open_):
    qs = [
        ("What is EGGREGIOUS?", L.read_store(L.BY_CODE["en"])[0] + " Made in Unreal Engine 5 by Rusty Nuts Studios."),
        ("When is it out?", Q_WHEN_OPEN if open_ else Q_WHEN_CLOSED),
        ("How much will it cost?", "To be announced. The Steam page will carry the price when it is set."),
        ("What platforms?", "Windows PC, on Steam. Other platforms to be announced. Language: English."),
        ("Does it support a controller?", "To be announced. The Steam page does not list controller support yet."),
    ]
    if open_:
        qs += [
            ("What is the playtest?", "A build of the game in players' hands before release, with access through Steam Playtest in waves. It is not the finished game."),
            ("How do I join the playtest?", "Press the JOIN THE DISCORD button. Wishlist EGGREGIOUS on Steam and hit Request Access when the button appears. Builds go out in waves; Steam tells you when yours is in. Then play and say what broke."),
        ]
    qs += [
        ("What are the system specs?", "Minimum: Windows 10 64-bit, Intel Core i5-4590 or AMD FX-8350, 8 GB RAM, NVIDIA GTX 960 4 GB or AMD RX 570 4 GB, DirectX 12, 4 GB storage. Recommended: Windows 10 or 11 64-bit, Intel Core i5-8400 or AMD Ryzen 5 2600, 16 GB RAM, NVIDIA GTX 1060 6 GB or AMD RX 580 8 GB, DirectX 12, 4 GB storage, SSD recommended."),
    ]
    if open_:
        qs.append(("Is the playtest the demo?", "No. The playtest is a limited test with access in waves through Steam. A public demo is to be announced."))
    else:
        qs.append(("Is there a demo?", "To be announced."))
    qs += [
        ("Can I stream it or make videos?", "To be announced."),
        ("Who makes it?", "Tommy Allen at Rusty Nuts Studios, a solo studio in Tbilisi, Georgia, in Unreal Engine 5. Publisher: Rusty Nuts Studios LLC."),
        ("Where do I follow it?", "EGGREGIOUS on TikTok, Instagram and YouTube (@eggregiousgame), the studio on X (@RustyNutsStudio), the wishlist on Steam, and the devlog on this site."),
    ]
    rows = ",\n".join(
        '{"@type":"Question","name":' + json.dumps(n, ensure_ascii=False) + ',"acceptedAnswer":{"@type":"Answer","text":' + json.dumps(t, ensure_ascii=False) + "}}"
        for n, t in qs)
    return ('<script type="application/ld+json">\n{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[\n'
            + rows + "\n]}\n</script>")


FAQ_WHAT = """<details class="faq" id="what" open>
    <summary>What is EGGREGIOUS?</summary>
    <div class="faq-a">
        <p>{short}</p>
        <p>It is made in Unreal Engine 5 by <a href="index.html#about">Rusty Nuts Studios</a>. The <a href="eggregious.html">EGGREGIOUS page</a> has the art.</p>
    </div>
</details>"""

FAQ_WHEN_OPEN = f"""<details class="faq" id="when">
    <summary>When is it out?</summary>
    <div class="faq-a">
        <p><span class="tba">To be announced</span> No release date yet.</p>
        <p>Before that comes a playtest, with access through Steam in waves. <a href="{STEAM}" target="_blank" rel="noopener">Wishlist it on Steam</a> and you hear the moment the date is set.</p>
    </div>
</details>"""
FAQ_WHEN_CLOSED = f"""<details class="faq" id="when">
    <summary>When is it out?</summary>
    <div class="faq-a">
        <p><span class="tba">To be announced</span> No release date yet.</p>
        <p><a href="{STEAM}" target="_blank" rel="noopener">Wishlist it on Steam</a> and you hear the moment the date is set.</p>
    </div>
</details>"""
FAQ_PLAYTEST_OPEN = """<details class="faq" id="playtest">
    <summary>What is the playtest?</summary>
    <div class="faq-a">
        <p>A build of the game in players' hands before release. You play, we watch what breaks and what works, and the game changes because of it.</p>
        <p>Access comes through Steam Playtest, granted in waves. It is not the finished game, and it is not the demo.</p>
    </div>
</details>"""
FAQ_JOIN_OPEN = f"""<details class="faq" id="join">
    <summary>How do I join the playtest?</summary>
    <div class="faq-a">
        <p>Press JOIN THE DISCORD. It is one click, and the invite does not expire.</p>
        <p>Then <a href="{STEAM}" target="_blank" rel="noopener">wishlist EGGREGIOUS on Steam</a> and hit Request Access when the button appears. Builds go out in waves; Steam tells you when yours is in. Play it, and tell us what broke.</p>
    </div>
</details>"""
FAQ_DEMO_OPEN = """<details class="faq" id="demo">
    <summary>Is the playtest the demo?</summary>
    <div class="faq-a">
        <p>No. The playtest is a limited test, with access in waves through Steam, and it ends when we have what we need.</p>
        <p><span class="tba">To be announced</span> A public demo.</p>
    </div>
</details>"""
FAQ_DEMO_CLOSED = """<details class="faq" id="demo">
    <summary>Is there a demo?</summary>
    <div class="faq-a">
        <p><span class="tba">To be announced</span></p>
    </div>
</details>"""


def variants(open_):
    """{region name: text} for the current state. Empty string means the region is empty."""
    return {
        "play-egg": play("btn-egg") if open_ else "",
        "play-primary": play("btn-primary") if open_ else "",
        "index-label": '<p class="section-label">Playtest on Discord</p>' if open_ else '<p class="section-label">In Development</p>',
        "index-badge": '<div class="game-badge">Playtest</div>' if open_ else '<div class="game-badge">In Development</div>',
        "faq-head-a": ('<title>EGGREGIOUS FAQ — what it is, when, platforms, the playtest</title>\n'
                       '<meta name="description" content="Twelve questions about EGGREGIOUS: what it is, when it is out, price, platforms, controller support, the playtest and how to join it, system specs, the demo, streaming, who makes it, where to follow.">') if open_ else
                      ('<title>EGGREGIOUS FAQ — what it is, when, platforms, price</title>\n'
                       '<meta name="description" content="Questions about EGGREGIOUS: what it is, when it is out, price, platforms, controller support, system specs, the demo, streaming, who makes it, where to follow.">'),
        "faq-head-b": '<meta property="og:description" content="What it is, when, platforms, the playtest and how to join it. Where the answer is not settled yet, it says so.">' if open_
                      else '<meta property="og:description" content="What it is, when, platforms and price. Where the answer is not settled yet, it says so.">',
        "faq-jsonld": faq_jsonld(open_),
        "faq-sub": '<p class="game-desc">Twelve things people ask. Where the answer is not settled yet, it says so.</p>' if open_
                   else '<p class="game-desc">The things people ask. Where the answer is not settled yet, it says so.</p>',
        "faq-what": FAQ_WHAT.replace("{short}", html.escape(L.read_store(L.BY_CODE["en"])[0], quote=False)),
        "faq-when": FAQ_WHEN_OPEN if open_ else FAQ_WHEN_CLOSED,
        "faq-q-what": FAQ_PLAYTEST_OPEN if open_ else "",
        "faq-join": FAQ_JOIN_OPEN if open_ else "",
        "faq-demo": FAQ_DEMO_OPEN if open_ else FAQ_DEMO_CLOSED,
    }


REGION = re.compile(r"(?P<i>[ \t]*)<!-- ps:(?P<n>[\w-]+) -->\n(?P<body>.*?)(?P<j>[ \t]*)<!-- /ps:(?P=n) -->", re.S)
PAGES = ["index.html", "faq.html", "devlog.html"]


def apply_regions(open_):
    v = variants(open_)
    for name in PAGES:
        p = ROOT / name
        s = p.read_text(encoding="utf-8")
        nl = "\r\n" if "\r\n" in s else "\n"
        s = s.replace("\r\n", "\n")
        seen = []

        def sub(m):
            n = m.group("n")
            seen.append(n)
            if n not in v:
                raise SystemExit(f"{name}: unknown region {n}")
            text = v[n]
            body = "".join(m.group("i") + line + "\n" if line else "\n" for line in text.split("\n")) if text else ""
            return f"{m.group('i')}<!-- ps:{n} -->\n{body}{m.group('j')}<!-- /ps:{n} -->"

        s2 = REGION.sub(sub, s)
        p.write_text(s2.replace("\n", nl), encoding="utf-8", newline="")
        print(f"{name}: {len(seen)} regions set ({'open' if open_ else 'closed'})")


def main():
    open_ = is_open()
    apply_regions(open_)
    import build_pages  # noqa: E402  (generated pages read the same switch)
    build_pages.main()
    print("playtest is", "OPEN" if open_ else "CLOSED")


if __name__ == "__main__":
    main()
