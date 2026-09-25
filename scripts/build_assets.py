"""
Build FoldScape's production asset set from the traced emblem.

The files in assets/ are concept art — moodboards and colourway sheets.
Useful for deciding, useless for shipping: not square, no alpha, 1 MB
each, and inconsistent between versions.

This derives real assets from assets/emblem-traced.svg, which was traced
once off the original. Everything below is reproducible: delete the output
and run this again and the bytes come back identical.

    python scripts/build_assets.py

Outputs into assets/brand/:
    emblem.svg              master, gradient, transparent
    emblem-flat.svg         one colour, for stamps and single-ink use
    favicon.svg             square, padded, for modern browsers
    favicon-16/32/48.png    raster fallbacks
    favicon.ico             multi-resolution, for legacy
    apple-touch-icon.png    180x180 on the brushed ground (iOS ignores alpha)
    og-image.png            1200x630 social card
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "emblem-traced.svg"
OUT = ROOT / "assets" / "brand"
TMP = OUT / ".render"
CHROME = Path(r"C:/Program Files/Google/Chrome/Application/chrome.exe")

CYAN_FLAT = "#0E9AAD"


def svg_parts(text):
    vb = re.search(r'viewBox="([\d.\s]+)"', text).group(1).split()
    w, h = float(vb[2]), float(vb[3])
    body = re.search(r"(<defs>.*)</svg>", text, re.S).group(1).strip()
    return w, h, body


def square_svg(w, h, body, pad_frac=0.07, bg=None):
    """Centre the mark in a square canvas with padding."""
    side = max(w, h) * (1 + 2 * pad_frac)
    dx, dy = (side - w) / 2, (side - h) / 2
    ground = f'<rect width="{side:.1f}" height="{side:.1f}" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {side:.1f} {side:.1f}" role="img" '
            f'aria-labelledby="t"><title id="t">FoldScape</title>'
            f'{ground}<g transform="translate({dx:.1f} {dy:.1f})">{body}</g></svg>\n')


def render(svg_path, png_path, px, transparent=True):
    """Rasterize an SVG at an exact pixel size using headless Chrome."""
    html = TMP / (png_path.stem + ".html")
    html.write_text(
        f'<body style="margin:0;width:{px}px;height:{px}px;overflow:hidden">'
        f'<img src="{svg_path.name}" style="width:{px}px;height:{px}px;display:block">'
        f'</body>', encoding="utf-8")
    cmd = [str(CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars",
           "--virtual-time-budget=3000", f"--window-size={px},{px}",
           f"--screenshot={png_path}", html.as_uri()]
    if transparent:
        cmd.insert(3, "--default-background-color=00000000")
    subprocess.run(cmd, capture_output=True, check=False)
    return png_path.exists()


def main():
    if not SRC.exists():
        sys.exit(f"missing {SRC} — run scripts/vectorize_emblem.py first")
    if not CHROME.exists():
        sys.exit(f"Chrome not found at {CHROME}")

    OUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(exist_ok=True)
    text = SRC.read_text(encoding="utf-8")
    w, h, body = svg_parts(text)
    print(f"master {w:.0f}x{h:.0f} (aspect {w/h:.3f})")

    made = []

    # ── master, as traced ───────────────────────────────────────────
    (OUT / "emblem.svg").write_text(text, encoding="utf-8")
    made.append("emblem.svg")

    # ── one-colour version ──────────────────────────────────────────
    flat = re.sub(r'fill="url\(#fs\)"', f'fill="{CYAN_FLAT}"', text)
    flat = re.sub(r"<defs>.*?</defs>", "", flat, flags=re.S)
    (OUT / "emblem-flat.svg").write_text(flat, encoding="utf-8")
    made.append("emblem-flat.svg")

    # ── square icon ─────────────────────────────────────────────────
    fav = square_svg(w, h, body)
    (OUT / "favicon.svg").write_text(fav, encoding="utf-8")
    shutil.copy(OUT / "favicon.svg", TMP / "favicon.svg")
    made.append("favicon.svg")

    for px in (16, 32, 48, 180):
        name = f"favicon-{px}.png" if px != 180 else "apple-touch-icon.png"
        if px == 180:
            # iOS composites onto black if alpha is present, so give it a ground
            ios = square_svg(w, h, body, pad_frac=0.13, bg="#F2F1EE")
            (TMP / "ios.svg").write_text(ios, encoding="utf-8")
            ok = render(TMP / "ios.svg", OUT / name, px, transparent=False)
        else:
            ok = render(TMP / "favicon.svg", OUT / name, px)
        print(f"  {name:24s} {'ok' if ok else 'FAILED'}")
        if ok:
            made.append(name)

    # ── .ico from the rendered PNGs ─────────────────────────────────
    ico_src = [OUT / f"favicon-{p}.png" for p in (16, 32, 48)]
    if all(p.exists() for p in ico_src):
        base = Image.open(ico_src[-1]).convert("RGBA")
        base.save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
        made.append("favicon.ico")

    # ── social card ─────────────────────────────────────────────────
    og = TMP / "og.html"
    og.write_text(
        '<body style="margin:0;width:1200px;height:630px;display:flex;'
        'align-items:center;justify-content:center;gap:54px;'
        'background:linear-gradient(140deg,#fbfbfa,#eceae6 60%,#e2e0db);'
        'font-family:Inter,system-ui,sans-serif">'
        '<img src="favicon.svg" style="width:260px">'
        '<div><div style="font-size:82px;font-weight:600;letter-spacing:-.03em;'
        'color:#0a0a0a;line-height:1">FoldScape</div>'
        '<div style="font-size:30px;font-weight:300;color:#5c5c61;margin-top:14px">'
        'Daily-updated landscape of computational protein design &amp; ML tools</div>'
        '</div></body>', encoding="utf-8")
    subprocess.run([str(CHROME), "--headless=new", "--disable-gpu",
                    "--hide-scrollbars", "--virtual-time-budget=3000",
                    "--window-size=1200,630",
                    f"--screenshot={OUT/'og-image.png'}", og.as_uri()],
                   capture_output=True, check=False)
    if (OUT / "og-image.png").exists():
        made.append("og-image.png")
        print(f"  {'og-image.png':24s} ok")

    shutil.rmtree(TMP, ignore_errors=True)

    print(f"\n{len(made)} assets in {OUT.relative_to(ROOT)}/")
    for f in sorted(OUT.iterdir()):
        print(f"   {f.name:24s} {f.stat().st_size:>8,} bytes")


if __name__ == "__main__":
    main()
