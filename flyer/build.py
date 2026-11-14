#!/usr/bin/env python3
"""Build the one-page printable flyer as flyer/flyer.html (US Letter, no margins).

Print flyer.html to PDF at 8.5 x 11 in with background graphics on, or use Playwright:
  page.pdf(width="8.5in", height="11in", print_background=True)
Run flyer/make_qr.py first so qr.svg exists.
"""
from pathlib import Path

here = Path(__file__).resolve().parent
URL_TEXT = "research.jonoisart.com/terra-cognita"
qr = (here / "qr.svg").read_text()

# Entries named on the flyer, to show the range of what counts as a map.
INSIDE = ["Stick charts of ocean swells", "The star atlas from Dunhuang", "Mercator's projection",
          "John Snow's cholera map", "Mendeleev's periodic table", "The first sketch of the internet",
          "The human genome", "A map sent to the stars"]
inside = "".join(f"<li>{t}</li>" for t in INSIDE)

html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Terra Cognita flyer</title>
<style>
@page {{ size: 8.5in 11in; margin: 0 }}
/* Site fonts, bundled in flyer/fonts (SIL OFL 1.1) so the build does not depend on installed fonts */
@font-face {{ font-family:'Bodoni Moda'; src:url(fonts/BodoniModa-Variable.ttf); font-weight:400 900 }}
@font-face {{ font-family:'IBM Plex Sans'; src:url(fonts/IBMPlexSans-Regular.ttf); font-weight:400 }}
@font-face {{ font-family:'IBM Plex Sans'; src:url(fonts/IBMPlexSans-SemiBold.ttf); font-weight:600 }}
@font-face {{ font-family:'IBM Plex Mono'; src:url(fonts/IBMPlexMono-Regular.ttf); font-weight:400 }}
:root {{ --ink:#13232b; --muted:#536770; --sea:#1b5b6c; --gilt:#9a6f0c; --rule:#cbd5d5; --grid:rgba(27,91,108,.13);
  --display:'Bodoni Moda',Didot,Georgia,serif;
  --body:'IBM Plex Sans',Helvetica,Arial,sans-serif;
  --mono:'IBM Plex Mono',Menlo,monospace; }}
* {{ box-sizing:border-box; margin:0; padding:0 }}
html,body {{ width:8.5in; height:11in; background:#fff; color:var(--ink); font-family:var(--body);
  -webkit-print-color-adjust:exact; print-color-adjust:exact }}
.page {{ width:8.5in; height:11in; display:flex; flex-direction:column; overflow:hidden }}
/* Header sits on a graticule, like the site */
header {{ padding:.5in .7in .32in; border-bottom:1.5pt solid var(--ink);
  background-image:linear-gradient(var(--grid) 1px,transparent 1px),linear-gradient(90deg,var(--grid) 1px,transparent 1px);
  background-size:.3in .3in }}
.eyebrow {{ font-family:var(--mono); font-size:9.5pt; letter-spacing:.12em; text-transform:uppercase; color:var(--gilt) }}
h1 {{ font-family:var(--display); font-weight:700; font-size:74pt; line-height:.95; letter-spacing:-.015em; margin-top:.1in }}
.sub {{ font-family:var(--display); font-weight:400; font-size:25pt; line-height:1.1; margin-top:.08in; color:var(--sea) }}
.lede {{ font-size:12.5pt; line-height:1.45; margin-top:.2in; max-width:6.3in }}
main {{ flex:1; padding:.3in .7in 0; display:flex; flex-direction:column; gap:.24in }}
.plates {{ display:grid; grid-template-columns:1fr 1fr; gap:.3in }}
figure img {{ display:block; width:100%; height:2.05in; object-fit:cover; border:.75pt solid var(--ink) }}
figcaption {{ margin-top:.09in; font-size:9.6pt; line-height:1.4 }}
figcaption .yr {{ display:block; font-family:var(--mono); font-size:8.5pt; letter-spacing:.08em; text-transform:uppercase; color:var(--gilt) }}
figcaption b {{ display:block; font-family:var(--display); font-size:14pt; font-weight:700; line-height:1.15; margin:.02in 0 .03in }}
.lower {{ display:grid; grid-template-columns:2in 1fr; gap:.4in; align-items:center;
  border-top:.75pt solid var(--rule); padding-top:.24in }}
.qr svg {{ display:block; width:2in; height:2in }}
.scan .lab {{ font-family:var(--mono); font-size:9.5pt; letter-spacing:.12em; text-transform:uppercase; color:var(--gilt) }}
.scan h2 {{ font-family:var(--display); font-size:27pt; font-weight:700; line-height:1.05; margin:.04in 0 .07in }}
.scan .url {{ font-family:var(--mono); font-size:13pt; color:var(--sea) }}
.scan h3 {{ font-family:var(--mono); font-size:8.5pt; font-weight:400; letter-spacing:.12em; text-transform:uppercase;
  color:var(--muted); margin:.2in 0 .06in }}
.scan ul {{ list-style:none; columns:2; column-gap:.3in; font-size:10pt; line-height:1.5 }}
.scan li {{ break-inside:avoid; padding-left:.14in; text-indent:-.14in }}
.scan li::before {{ content:"+ "; font-family:var(--mono); color:var(--gilt) }}
footer {{ padding:.16in .7in .34in; font-size:7.2pt; line-height:1.4; color:var(--muted) }}
</style></head><body><div class="page">
<header>
  <div class="eyebrow">A sourced timeline &middot; c. 1600 BCE to 2020</div>
  <h1>Terra Cognita</h1>
  <p class="sub">Sixty Maps That Changed the World</p>
  <p class="lede">Each of these maps did more than record a place. It moved a border, launched a science, fixed a name, or changed how people find their way.</p>
</header>
<main>
  <div class="plates">
    <figure><img src="img/babylonian.jpg" alt="Babylonian clay tablet map">
      <figcaption><span class="yr">c. 600 BCE</span><b>Babylonian Map of the World</b>A clay tablet the size of a palm. The oldest surviving attempt to draw the whole world on one surface.</figcaption></figure>
    <figure><img src="img/tenochtitlan.jpg" alt="1524 woodcut map of Tenochtitlan">
      <figcaption><span class="yr">1524</span><b>Nuremberg Map of Tenochtitlan</b>Europe's first picture of the Aztec island capital, printed three years after the Spanish razed it.</figcaption></figure>
  </div>
  <div class="lower">
    <div class="qr">{qr}</div>
    <div class="scan">
      <div class="lab">Scan to explore</div>
      <h2>Read all sixty</h2>
      <div class="url">{URL_TEXT}</div>
      <h3>Also on the map</h3>
      <ul>{inside}</ul>
    </div>
  </div>
</main>
<footer>Every entry says what the map is, what it changed, where it is now, and links a source.
Images: Babylonian tablet photographed by Osama Shukir Muhammed Amin, CC BY-SA 4.0. Map of Tenochtitlan, woodcut, Nuremberg 1524, public domain. Both via Wikimedia Commons.</footer>
</div></body></html>
"""
(here / "flyer.html").write_text(html, encoding="utf-8")
print("flyer.html written")
