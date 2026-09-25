"""
Apply the hairline top bar to FoldScape's pages.

The landing view read as floaty because the nav sat on the page with no ground
under it. This adds a sticky bar: a soft vertical wash, one hairline underneath,
and a white catch-light along the top edge. No new object, no chrome — which is
what the in-file design note asks for.

Idempotent: a page that already has `.topbar` is skipped.

    python scripts/apply_topbar.py            # apply
    python scripts/apply_topbar.py --check    # report only
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = [
    ROOT / "site" / "index.html",
    ROOT / "site" / "tools.html",
    ROOT / "site-sandbox" / "index.html",
    ROOT / "site-sandbox" / "tools.html",
]

CSS = """
        /* ─────────────────────────────────────────────────────────────
           Top bar — hairline with a hint of tone
           The landing view read as floaty because the nav had no ground
           under it. A soft wash and a single hairline supply that ground
           without adding an object to the page, which is what the rest
           of this system asks for.
           ───────────────────────────────────────────────────────────── */
        .topbar {
            position: sticky;
            top: 0;
            z-index: 100;
            background: linear-gradient(180deg,
                #ffffff  0%,
                #fcfcfb 62%,
                #f7f6f4 100%);
            border-bottom: 1px solid rgba(0,0,0,0.09);
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.9),
                0 6px 16px -14px rgba(0,0,0,0.30);
        }

        .topbar nav { padding-block: 0.15rem; }

        .topbar nav ul:first-child strong {
            color: var(--ink);
            letter-spacing: 0.005em;
        }

        .topbar nav a {
            color: var(--ink-soft);
            padding: 0.35rem 0.6rem;
            border-radius: 6px;
            transition: background 140ms ease, color 140ms ease;
        }
        .topbar nav a:hover {
            color: var(--ink);
            background: rgba(0,0,0,0.04);
        }
"""

NAV_RE = re.compile(r'([ \t]*)(<nav class="container">.*?</nav>)', re.S)


def apply(path, check=False):
    if not path.exists():
        return f"{path.name:22s} MISSING"
    text = path.read_text(encoding="utf-8")

    if ".topbar" in text:
        return f"{path.relative_to(ROOT)!s:34s} already has topbar, skipped"
    if "</style>" not in text:
        return f"{path.relative_to(ROOT)!s:34s} NO </style>, skipped"
    m = NAV_RE.search(text)
    if not m:
        return f"{path.relative_to(ROOT)!s:34s} nav block not matched, skipped"

    if check:
        return f"{path.relative_to(ROOT)!s:34s} would apply"

    # 1. CSS before the first </style>
    text = text.replace("    </style>", CSS + "    </style>", 1)

    # 2. wrap the nav (re-find: indices moved after the CSS insert)
    m = NAV_RE.search(text)
    indent, nav = m.group(1), m.group(2)
    # keep the block's own relative indentation; push it in one level
    lines = nav.splitlines()
    nav_indented = "\n".join(
        [indent + "    " + lines[0]]
        + [("    " + ln) if ln.strip() else ln for ln in lines[1:]]
    )
    wrapped = (f'{indent}<div class="topbar">\n'
               f'{nav_indented}\n'
               f'{indent}</div>')
    text = text[:m.start()] + wrapped + text[m.end():]

    path.write_text(text, encoding="utf-8")

    # verify what we just wrote
    back = path.read_text(encoding="utf-8")
    ok = (back.count('<div class="topbar">') == 1
          and ".topbar {" in back
          and back.count("<div") == back.count("</div>"))
    return (f"{path.relative_to(ROOT)!s:34s} "
            + ("applied" if ok else "APPLIED BUT VERIFY FAILED"))


def main():
    check = "--check" in sys.argv
    for p in PAGES:
        print("  " + apply(p, check))


if __name__ == "__main__":
    main()
