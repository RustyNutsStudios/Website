"""Import the translator's WEBSITE_STRINGS_<lang>.txt files into strings.json.

    python tools/i18n/import_strings.py

Reads every file in SRC, writes the values next to the English ones in strings.json, and prints what it
did. It never writes wording of its own.

Amendment 1 (kit_contents says the trailer is now inside the kit; new key fs_publisher): until a
language's file contains fs_publisher it has not been amended, its kit_contents still says the trailer
is a separate download (no longer true), so kit_contents is NOT imported for that language and the
page shows the English sentence instead.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i18n_lib as L

SRC = Path(r"C:\Users\tgall\Documents\EggregiousSteamUpload\22 LOCALISED PAGE\website_strings")
LINE = re.compile(r"^ {2}([a-z_]+)\s*(.*)$")


def parse(path):
    out = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        m = LINE.match(line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def main():
    p = L.I18N / "strings.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    known = [k for k in data if k != "_note"]
    for lang in L.LANGS[1:]:
        code = lang["code"]
        f = SRC / f"WEBSITE_STRINGS_{code}.txt"
        if not f.exists():
            print(f"{code:6} no file")
            continue
        got = parse(f)
        amended = "fs_publisher" in got
        done, held, unknown = [], [], [k for k in got if k not in known]
        for k in known:
            if k not in got:
                continue
            if k == "kit_contents" and not amended:
                data[k].pop(code, None)
                held.append(k)
                continue
            data[k][code] = got[k]
            done.append(k)
        missing = [k for k in known if k not in got and k != "fs_publisher"]
        print(f"{code:6} imported {len(done):2}  held {held or '-'}  missing {missing or '-'}  unknown {unknown or '-'}  amended {amended}")
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
