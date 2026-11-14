#!/usr/bin/env python3
"""Write flyer/qr.svg for a URL and check that it scans.

Usage: python3 flyer/make_qr.py https://research.jonoisart.com/terra-cognita/
Needs: reportlab (QR encoder), opencv-python + numpy (scan check).
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from reportlab.graphics.barcode.qr import QrCodeWidget

url = sys.argv[1]
here = Path(__file__).resolve().parent

# Error correction level Q: survives a smudged or creased printout.
w = QrCodeWidget(url, barLevel="Q")
w.qr.make()
n = w.qr.getModuleCount()
dark = [[bool(w.qr.isDark(r, c)) for c in range(n)] for r in range(n)]

# One <rect> per dark module on an n x n grid, with the 4-module quiet zone the spec asks for.
quiet = 4
rects = "".join(f'<rect x="{c + quiet}" y="{r + quiet}" width="1" height="1"/>'
                for r in range(n) for c in range(n) if dark[r][c])
size = n + 2 * quiet
(here / "qr.svg").write_text(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" shape-rendering="crispEdges">'
    f'<rect width="{size}" height="{size}" fill="#fff"/><g fill="#000">{rects}</g></svg>\n')

# Scan check: rasterise the same matrix and decode it.
img = np.full((size, size), 255, np.uint8)
for r in range(n):
    for c in range(n):
        if dark[r][c]:
            img[r + quiet, c + quiet] = 0
img = cv2.resize(img, (size * 10, size * 10), interpolation=cv2.INTER_NEAREST)
decoded, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
if decoded != url:
    sys.exit(f"QR check FAILED: decoded {decoded!r}")
print(f"qr.svg written ({n}x{n} modules); scans as {decoded}")
