"""
Turn the emblem concept art into editable vector geometry.

The emblem exists only as a 1 MB raster in assets/. Rasters drift: each
pass over one comes back subtly different. This converts it once into
vector geometry that can be edited, recoloured and scaled indefinitely.

An earlier attempt quantized colour and traced each tone. That fails here:
the facets carry gradients, so colour bands cut *across* facet edges rather
than along them, and the result is shards. What is actually stable is the
silhouette — the outline plus the two counters of the F. That is the design.
The interior shading is a gradient, which vector reproduces exactly without
tracing anything.

So: trace the outline and the holes, fill with the sampled ramp.

    python scripts/vectorize_emblem.py
    python scripts/vectorize_emblem.py --epsilon 0.8 --width 1400
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "concept-emblem.png"

def trace(mask):
    """
    Boundary contours of a binary mask, via marching squares.

    A hand-rolled Moore-neighbour walk was tried first and collapsed a
    125k-pixel silhouette to six points at the apex, where the shape comes
    to a single-pixel tip and the walk turns back on itself. Marching
    squares has no such failure mode and handles the notches of the F.

    Returns a list of contours, each a list of (row, col), largest first.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    padded = np.pad(mask.astype(float), 2)          # keep edges off the border
    fig = plt.figure()
    try:
        cs = fig.gca().contour(padded, levels=[0.5])
        segs = [s for s in cs.allsegs[0] if len(s) >= 4]
    finally:
        plt.close(fig)

    out = [[(y - 2, x - 2) for x, y in s] for s in segs]   # undo pad, to (row, col)
    out.sort(key=len, reverse=True)
    return out


def dp(points, eps):
    """Douglas-Peucker."""
    if len(points) < 3:
        return points
    pts = np.asarray(points, float)
    keep = np.zeros(len(pts), bool)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        a, b = pts[i], pts[j]
        ab = b - a
        n = float(np.hypot(*ab))
        seg = pts[i + 1:j]
        if n < 1e-9:
            d = np.hypot(*(seg - a).T)
        else:
            v = seg - a
            d = np.abs(ab[0] * v[:, 1] - ab[1] * v[:, 0]) / n
        m = int(np.argmax(d))
        if d[m] > eps:
            k = i + 1 + m
            keep[k] = True
            stack += [(i, k), (k, j)]
    return [tuple(p) for p in pts[keep]]


def sub(points, r0, c0, scale):
    return "M " + " L ".join(f"{(c-c0)*scale:.2f} {(r-r0)*scale:.2f}"
                             for r, c in points) + " Z"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=int, default=1400)
    ap.add_argument("--epsilon", type=float, default=0.9)
    ap.add_argument("--min-hole", type=int, default=250)
    a = ap.parse_args()

    if not SRC.exists():
        sys.exit(f"source not found: {SRC}")

    im = Image.open(SRC).convert("RGB")
    im = im.resize((a.width, round(a.width * im.height / im.width)), Image.LANCZOS)
    arr = np.asarray(im).astype(int)

    mx, mn = arr.max(2), arr.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    mask = (sat > 0.24) & (mx > 38)
    mask = ndimage.binary_closing(mask, np.ones((5, 5)))
    mask = ndimage.binary_opening(mask, np.ones((3, 3)))

    lab, n = ndimage.label(mask)
    if n == 0:
        sys.exit("no mark found")
    sizes = ndimage.sum(mask, lab, range(1, n + 1))
    mark = lab == (int(np.argmax(sizes)) + 1)

    rs, cs = np.nonzero(mark)
    r0, r1, c0, c1 = rs.min(), rs.max(), cs.min(), cs.max()
    W, H = int(c1 - c0 + 1), int(r1 - r0 + 1)
    scale = 1000.0 / W                       # emit in a 1000-wide space
    print(f"mark {W}x{H}px  aspect {W/H:.3f}  ({int(mark.sum()):,} px)")

    contours = trace(mark)
    if not contours:
        sys.exit("no contour found")
    paths = [dp(c, a.epsilon) for c in contours]
    paths = [p for p in paths if len(p) >= 3]
    print(f"contours: {len(paths)}  points: {[len(p) for p in paths]}")

    # The F's counters are notches open to the outside, not enclosed holes,
    # so they arrive as part of the outer contour. Any additional contour is
    # a genuine hole and gets reversed so evenodd knocks it out.
    d = sub(paths[0], r0, c0, scale)
    for extra in paths[1:]:
        d += " " + sub(extra[::-1], r0, c0, scale)

    vb_h = H * scale
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 {vb_h:.0f}"
     role="img" aria-labelledby="t"><title id="t">FoldScape</title>
  <defs>
    <linearGradient id="fs" x1="0.08" y1="0" x2="0.92" y2="1">
      <stop offset="0%"   stop-color="#80EBE5"/>
      <stop offset="28%"  stop-color="#22C9C4"/>
      <stop offset="58%"  stop-color="#00A0AE"/>
      <stop offset="82%"  stop-color="#00708F"/>
      <stop offset="100%" stop-color="#034A68"/>
    </linearGradient>
  </defs>
  <path fill-rule="evenodd" fill="url(#fs)" d="{d}"/>
</svg>
'''
    out = ROOT / "assets" / "emblem-traced.svg"
    out.write_text(svg, encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}  ({out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
