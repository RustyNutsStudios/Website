"""Shared pieces for the localised EGGREGIOUS pages and media kits.

Nothing here writes translated wording. The store text is read from tools/i18n/store/
(copies of the approved Steam files) and only converted from Steam markup to HTML or
plain text. Interface strings come from strings.json and fall back to English.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
I18N = ROOT / "tools" / "i18n"
BASE = "https://rustynutsstudios.com"
STEAM_BASE = "https://store.steampowered.com/app/4036510/EGGREGIOUS/"
DISCORD = "https://discord.gg/ShP2fYkxZq"
UTM = "utm_source=website&utm_medium=web&utm_campaign=playtest"

# cap = which capsule set carries this language's title (de, es and pt-br use the English set)
LANGS = [
    dict(code="en",    file="eggregious.html",       htmllang="en",      steam="english",   name="English",            og="en_US", cap="en"),
    dict(code="ru",    file="eggregious-ru.html",    htmllang="ru",      steam="russian",   name="Русский",            og="ru_RU", cap="ru"),
    dict(code="zh",    file="eggregious-zh.html",    htmllang="zh-Hans", steam="schinese",  name="简体中文",            og="zh_CN", cap="zh"),
    dict(code="ja",    file="eggregious-ja.html",    htmllang="ja",      steam="japanese",  name="日本語",              og="ja_JP", cap="ja"),
    dict(code="de",    file="eggregious-de.html",    htmllang="de",      steam="german",    name="Deutsch",            og="de_DE", cap="en"),
    dict(code="es",    file="eggregious-es.html",    htmllang="es",      steam="spanish",   name="Español",            og="es_ES", cap="en"),
    dict(code="pt-br", file="eggregious-pt-br.html", htmllang="pt-BR",   steam="brazilian", name="Português (Brasil)", og="pt_BR", cap="en"),
]
BY_CODE = {l["code"]: l for l in LANGS}

# Steam's About text names three picture slots; these are the three GIFs.
GIFS = {
    "eggregious_about_1_drop":  "media/gifs/eggregious-drop.gif",
    "eggregious_about_2_lead":  "media/gifs/eggregious-lead.gif",
    "eggregious_about_3_horde": "media/gifs/eggregious-horde.gif",
}
GIF_SIZE = (616, 347)

SHOTS = [  # (source stem in STEAM_SHOTS, short name used in file names)
    ("11_late_night_a", "late-night"),
    ("04_night_lit_up_bugs_a", "night-lit-up-bugs"),
    ("25_chain_lightning_horde_a", "chain-lightning-horde"),
    ("15_snow_drop_a", "snow-drop"),
    ("18_centipede_incoming_a", "centipede-incoming"),
    ("26_hive_mother_fight_a", "hive-mother-fight"),
    ("06_gold_chest_epic_b", "gold-chest-epic"),
    ("13_choose_your_egg_a", "choose-your-egg"),
    ("09_poster_hold_the_line_b", "poster-hold-the-line"),
    ("02_request_troops_b", "request-troops"),
    ("14_choose_a_weapon_a", "choose-a-weapon"),
    ("01_hold_the_line_b", "hold-the-line"),
]


def shot_web(i):
    return f"images/eggregious/i18n/shot-{i + 1:02d}-{SHOTS[i][1]}.jpg"


def steam_url(lang):
    if lang["code"] == "en":
        return f"{STEAM_BASE}?{UTM}"
    return f"{STEAM_BASE}?l={lang['steam']}&{UTM}&utm_content={lang['code']}"


def read_store(lang):
    short = (I18N / "store" / f"{lang['steam']}_short.txt").read_text(encoding="utf-8")
    about = (I18N / "store" / f"{lang['steam']}_about.txt").read_text(encoding="utf-8")
    return short.strip(), about.strip()


_STRINGS = json.loads((I18N / "strings.json").read_text(encoding="utf-8"))
_STRINGS.pop("_note", None)

# Developer and publisher, exactly as the Steam page shows them. They appear on every language page.
DEVELOPER = "Tommy Allen"
PUBLISHER = "Rusty Nuts Studios LLC"
TRAILER_REL = "media/trailer/eggregious-trailer-30s-1080p.mp4"


def playtest_open():
    """The one switch: tools/playtest.json. False means no Discord link, no Request Access, no playtest wording."""
    return bool(json.loads((ROOT / "tools" / "playtest.json").read_text(encoding="utf-8"))["open"])


def s(key, code="en"):
    """Interface string for a language, falling back to English."""
    v = _STRINGS[key]
    return v.get(code) or v["en"]


def missing_strings():
    """{code: [keys with no value]} for every non-English language."""
    return {l["code"]: [k for k, v in _STRINGS.items() if not v.get(l["code"])] for l in LANGS if l["code"] != "en"}


def all_string_keys():
    return {k: v["en"] for k, v in _STRINGS.items()}


_TOK = re.compile(r"\[(/?)(p|b|list|\*|img)((?:\s[^\]]*)?)\]")


def _walk(src):
    pos = 0
    for m in _TOK.finditer(src):
        if m.start() > pos:
            yield ("text", src[pos:m.start()])
        yield ("tag", m.group(1) == "/", m.group(2), m.group(3))
        pos = m.end()
    if pos < len(src):
        yield ("text", src[pos:])


def about_to_html(src):
    out = []
    for t in _walk(src):
        if t[0] == "text":
            out.append(html.escape(t[1], quote=False))
            continue
        _, closing, name, attrs = t
        if name == "img":
            if closing:
                continue
            key = re.search(r'/extras/([A-Za-z0-9_]+)', attrs).group(1)
            out.append(f"\x00IMG:{key}\x00")
        elif name == "p":
            out.append("</p>" if closing else "<p>")
        elif name == "b":
            out.append("</strong>" if closing else "<strong>")
        elif name == "list":
            out.append("</ul>" if closing else "<ul>")
        elif name == "*":
            out.append("</li>" if closing else "<li>")
    res = "".join(out)

    def fig(m):
        key = m.group(1)
        return (f'<figure class="i18n-gif"><img src="{GIFS[key]}" width="{GIF_SIZE[0]}" height="{GIF_SIZE[1]}" '
                f'alt="EGGREGIOUS" loading="lazy"></figure>')

    res = re.sub(r"<p>\x00IMG:([A-Za-z0-9_]+)\x00</p>", fig, res)
    res = re.sub(r"(</ul>)<p>(.*?)</p>$", r'\1<p class="i18n-victory">\2</p>', res, flags=re.S)
    assert "[" not in res and "]" not in res and "\x00" not in res, "unconverted store markup"
    return res


def about_to_text(src):
    out = []
    for t in _walk(src):
        if t[0] == "text":
            out.append(t[1])
            continue
        _, closing, name, attrs = t
        if name == "*" and not closing:
            out.append("\n- ")
        elif name == "p" and closing:
            out.append("\n")
        elif name == "list" and closing:
            out.append("\n")
    res = "".join(out)
    res = re.sub(r"\n\n- ", "\n- ", res)
    res = re.sub(r"\n{3,}", "\n\n", res).strip()
    assert "[" not in res and "]" not in res, "unconverted store markup"
    return res


def about_plain_segments(src):
    """The visible words of the About text, one string per paragraph (for the exact-text check)."""
    segs = []
    for line in about_to_text(src).split("\n"):
        line = line.strip().lstrip("- ").strip()
        if line:
            segs.append(line)
    return segs


def size_label(path):
    mb = Path(path).stat().st_size / (1024 * 1024)
    return f"{mb:.1f} MB"


def fact_sheet(lang):
    code = lang["code"]
    short, about = read_store(lang)
    lines = [
        "EGGREGIOUS",
        "",
        f"{s('fs_name', code)}: EGGREGIOUS",
        f"{s('fs_developer', code)}: {DEVELOPER}",
        f"{s('fs_publisher', code)}: {PUBLISHER}",
        f"{s('fs_platform', code)}: Windows PC",
        f"{s('fs_steam', code)}: {STEAM_BASE}?l={lang['steam']}",
        f"{s('fs_release', code)}: {s('fs_tba', code)}",
        "",
        f"{s('fs_short', code)}",
        short,
        "",
        f"{s('fs_about', code)}",
        about_to_text(about),
        "",
        s("fs_figures", code),
        "",
        s("kit_usage", code),
        "",
    ]
    return "\n".join(lines)
