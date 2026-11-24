"""Build the web-sized images and the media kits for the localised EGGREGIOUS pages.

Reads Tommy's art folders (read only) and writes into this repo:
  images/eggregious/i18n/   web images (capsule per language, 12 screenshots)
  media/gifs/               the three GIFs
  media-kit/                fact sheets, one zip per language, one zip of everything
The trailer (media/trailer/) is encoded separately with ffmpeg; see README.md here.

Run:  python tools/i18n/build_kits.py
"""
import shutil
import sys
import zipfile
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i18n_lib as L

ART = Path(r"C:\Users\tgall\Documents\EggregiousSteamUpload")
CAP = ART / "16 CAPSULE FINAL" / "217"
SHOTS = Path(r"C:\Users\tgall\Documents\EggregiousCaptures\MEDIA-2026-11-10\STEAM_SHOTS")
GIFDIR = ART / "22 LOCALISED PAGE" / "gifs" / "r7"
GIF_SRC = {"eggregious-drop.gif": "slot1_b.gif", "eggregious-lead.gif": "slot2_a.gif", "eggregious-horde.gif": "slot3_b.gif"}
CAPSET = {"en": CAP / "steam", "ru": CAP / "steam_ru", "zh": CAP / "steam_zh", "ja": CAP / "steam_ja"}
CAPSULES = [  # (source file in a capsule set, name inside the kit)
    ("header_920x430.png", "eggregious-header-capsule-920x430.png"),
    ("small_462x174_composed.png", "eggregious-small-capsule-462x174.png"),
    ("main_1232x706_composed.png", "eggregious-main-capsule-1232x706.png"),
    ("vertical_748x896.png", "eggregious-vertical-capsule-748x896.png"),
    ("library_600x900.png", "eggregious-library-capsule-600x900.png"),
]
WORK = Path(__file__).resolve().parent / "_work"
OUT_IMG = L.ROOT / "images" / "eggregious" / "i18n"
OUT_GIF = L.ROOT / "media" / "gifs"
OUT_KIT = L.ROOT / "media-kit"
TRAILER = L.ROOT / "media" / "trailer" / "eggregious-trailer-30s-v1.mp4"
POSTER = L.ROOT / "media" / "trailer" / "eggregious-trailer-30s-v1-poster.jpg"
# The trailer is the copy that already exists (same cut, 9.2 MB), used once by the page and the kits. No re-encode.
TRAILER_SRC = ART / "19 TRAILERS" / "EGGREGIOUS_main_trailer_30s_v1_UNDER10MB.mp4"
POSTER_SRC = ART / "19 TRAILERS" / "EGGREGIOUS_main_trailer_30s_v1_THUMB.jpg"
LOOSE = L.ROOT / "media-kit" / "en"   # the English kit unzipped, for the press page's direct links
PREVIEW = {  # web previews of the English capsule set, for the press page
    "header_920x430.jpg": "press-header-capsule.jpg",
    "small_462x174_composed.jpg": "press-small-capsule.jpg",
    "main_1232x706_composed.jpg": "press-main-capsule.jpg",
    "vertical_748x896.jpg": "press-vertical-capsule.jpg",
    "library_600x900.jpg": "press-library-capsule.jpg",
}


def rgb(im):
    if im.mode in ("RGBA", "LA"):
        bg = Image.new("RGB", im.size, (0, 0, 0))
        bg.paste(im, mask=im.getchannel("A"))
        return bg
    return im.convert("RGB")


def main():
    for d in (OUT_IMG, OUT_GIF, OUT_KIT, WORK):
        d.mkdir(parents=True, exist_ok=True)

    # 1. capsule per language for the page hero (the "composed" main capsule carries the title)
    for code, folder in CAPSET.items():
        shutil.copyfile(folder / "main_1232x706_composed.jpg", OUT_IMG / f"capsule-{code}.jpg")

    # 2. screenshots: full-size JPEG for the kits, 1280 JPEG for the pages
    full = []
    for i, (stem, name) in enumerate(L.SHOTS):
        im = rgb(Image.open(SHOTS / f"{stem}.png"))
        assert im.size == (1920, 1080), (stem, im.size)
        f = WORK / f"eggregious-{i + 1:02d}-{name}-1920x1080.jpg"
        im.save(f, "JPEG", quality=92, optimize=True, progressive=True)
        full.append(f)
        im.resize((1280, 720), Image.LANCZOS).save(L.ROOT / L.shot_web(i), "JPEG", quality=82, optimize=True, progressive=True)

    # 3. GIFs, byte for byte
    for dst, src in GIF_SRC.items():
        shutil.copyfile(GIFDIR / src, OUT_GIF / dst)
    gifs = [OUT_GIF / n for n in GIF_SRC]

    # 3b. the trailer: the existing under-10-MB copy, byte for byte
    TRAILER.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TRAILER_SRC, TRAILER)
    shutil.copyfile(POSTER_SRC, POSTER)

    # 3c. the English kit unzipped (press page links) and web previews of the English capsule set
    if LOOSE.exists():
        shutil.rmtree(LOOSE)
    for sub in ("logo", "capsules", "screenshots"):
        (LOOSE / sub).mkdir(parents=True, exist_ok=True)
    en_set = CAPSET["en"]
    shutil.copyfile(en_set / "logo_1280x720.png", LOOSE / "logo" / "eggregious-logo-en-1280x720.png")
    shutil.copyfile(en_set / "client_icon_512.png", LOOSE / "logo" / "eggregious-icon-512x512.png")
    for src, arc in CAPSULES:
        shutil.copyfile(en_set / src, LOOSE / "capsules" / arc)
    shutil.copyfile(en_set / "hero_3840x1240.jpg", LOOSE / "capsules" / "eggregious-library-hero-3840x1240.jpg")
    for f in full:
        shutil.copyfile(f, LOOSE / "screenshots" / f.name)
    for src, dst in PREVIEW.items():
        shutil.copyfile(en_set / src, OUT_IMG / dst)
    Image.open(en_set / "hero_3840x1240.jpg").convert("RGB").resize((1280, 413), Image.LANCZOS).save(
        OUT_IMG / "press-library-hero.jpg", "JPEG", quality=85, optimize=True, progressive=True)

    # 4. fact sheets
    for lang in L.LANGS:
        text = L.fact_sheet(lang)
        (OUT_KIT / f"fact-sheet-{lang['code']}.txt").write_text(text, encoding="utf-8", newline="\n")

    # 5. per-language zips
    hero = CAPSET["en"] / "hero_3840x1240.jpg"   # art only, no title: the same for every language
    icon = CAPSET["en"] / "client_icon_512.png"

    def add(z, src, arc):
        stored = Path(src).suffix.lower() in (".jpg", ".gif", ".mp4")
        z.write(src, arc, compress_type=zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED)

    for lang in L.LANGS:
        code = lang["code"]
        root = f"EGGREGIOUS-media-kit-{code}"
        cs = CAPSET[lang["cap"]]
        zpath = OUT_KIT / f"eggregious-media-kit-{code}.zip"
        with zipfile.ZipFile(zpath, "w") as z:
            add(z, OUT_KIT / f"fact-sheet-{code}.txt", f"{root}/00-fact-sheet.txt")
            add(z, cs / "logo_1280x720.png", f"{root}/logo/eggregious-logo-{code}-1280x720.png")
            add(z, icon, f"{root}/logo/eggregious-icon-512x512.png")
            for src, arc in CAPSULES:
                add(z, cs / src, f"{root}/capsules/{arc}")
            add(z, hero, f"{root}/capsules/eggregious-library-hero-3840x1240.jpg")
            for f in full:
                add(z, f, f"{root}/screenshots/{f.name}")
            for g in gifs:
                add(z, g, f"{root}/gifs/{g.name}")
            add(z, TRAILER, f"{root}/trailer/{TRAILER.name}")
        print(f"{zpath.name:36} {zpath.stat().st_size:>11,}")

    # 6. the zip of everything: every language's logo, capsules and fact sheet, the shared files once, the trailer
    root = "EGGREGIOUS-media-kit-all"
    zpath = OUT_KIT / "eggregious-media-kit-all.zip"
    with zipfile.ZipFile(zpath, "w") as z:
        for lang in L.LANGS:
            code = lang["code"]
            cs = CAPSET[lang["cap"]]
            add(z, OUT_KIT / f"fact-sheet-{code}.txt", f"{root}/languages/{code}/00-fact-sheet.txt")
            add(z, cs / "logo_1280x720.png", f"{root}/languages/{code}/logo/eggregious-logo-{code}-1280x720.png")
            for src, arc in CAPSULES:
                add(z, cs / src, f"{root}/languages/{code}/capsules/{arc}")
        add(z, icon, f"{root}/shared/eggregious-icon-512x512.png")
        add(z, hero, f"{root}/shared/eggregious-library-hero-3840x1240.jpg")
        for f in full:
            add(z, f, f"{root}/shared/screenshots/{f.name}")
        for g in gifs:
            add(z, g, f"{root}/shared/gifs/{g.name}")
        add(z, TRAILER, f"{root}/shared/trailer/{TRAILER.name}")
    print(f"{zpath.name:36} {zpath.stat().st_size:>11,}")

    shutil.rmtree(WORK, ignore_errors=True)


if __name__ == "__main__":
    main()
