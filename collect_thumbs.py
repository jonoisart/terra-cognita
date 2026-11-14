#!/usr/bin/env python3
"""
collect_thumbs.py - gather thumbnails for the "Sixty Maps That Changed the World" page.

What it does
  1. For each map, asks the Wikimedia Commons API for an image (exact file title
     first, then keyword search).
  2. Keeps only files whose Commons license is public domain or Creative Commons.
  3. Downloads a ~480 px wide thumbnail to thumbs/<id>.<ext>.
  4. Writes credits.json (who/what/license per image) and review.html (contact
     sheet with alternates) so a human or agent can check every pick.
  5. Zips thumbs/ + credits.json into thumbs.zip, ready to hand back.

Stdlib only. macOS `sips` is used to downsize manual downloads when present.

Usage
  python3 collect_thumbs.py                 # collect everything not yet collected
  python3 collect_thumbs.py --only cantino nolli
  python3 collect_thumbs.py --redo          # ignore existing files
  python3 collect_thumbs.py --list          # print ids and exit (no network)

Fixing a wrong pick (stored in overrides.json, then re-run):
  python3 collect_thumbs.py --pick cantino="File:Cantino planisphere (1502).jpg"

Using a non-Commons source (museum, library, journal). You must supply the rights:
  python3 collect_thumbs.py --url tharp-heezen="https://example.org/img.jpg" \
      --credit "Library of Congress" --license "Public domain" \
      --source "https://example.org/item-page"

Set a real contact in the User-Agent (Wikimedia asks for one):
  export THUMBS_CONTACT="you@example.com"
"""
import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

API = "https://commons.wikimedia.org/w/api.php"
WIDTH = 480                      # thumbnail width requested from Commons, in px
PAUSE = 1.0                      # seconds between API calls (be polite)
HERE = Path(__file__).resolve().parent
THUMBS = HERE / "thumbs"
OVERRIDES = HERE / "overrides.json"
UA = f"maps-thumbs/1.0 (contact: {os.environ.get('THUMBS_CONTACT', 'set THUMBS_CONTACT')})"

# Licenses we accept, matched against Commons' LicenseShortName (case-insensitive prefix).
OK_LICENSE = ("public domain", "pd", "cc0", "cc by", "cc-by", "no restrictions")

# id, page title, optional exact Commons file titles to try first, then search queries.
# "skip" marks works still in copyright: no automatic pick. Supply a licensed image
# with --url, or leave it and the page will show a drawn placeholder.
MAPS = [
    dict(id="nebra", title="Nebra Sky Disc", files=["File:Nebra Scheibe.jpg"], q=["Nebra sky disc"]),
    dict(id="turin-papyrus", title="Turin Papyrus Map", q=["Turin Papyrus Map", "Turin papyrus gold mine map"]),
    dict(id="babylonian", title="Babylonian Map of the World", files=["File:Baylonianmaps.JPG"], q=["Babylonian map of the world tablet"]),
    dict(id="ptolemy", title="Ptolemy's Geography", files=["File:PtolemyWorldMap.jpg"], q=["Ptolemy world map 15th century"]),
    dict(id="forma-urbis", title="Forma Urbis Romae", q=["Forma Urbis Romae fragment", "Severan marble plan"]),
    dict(id="peutinger", title="Tabula Peutingeriana", files=["File:TabulaPeutingeriana.jpg"], q=["Tabula Peutingeriana"]),
    dict(id="dunhuang", title="Dunhuang Star Atlas", files=["File:Dunhuang star map.jpg"], q=["Dunhuang star map", "Dunhuang star atlas"]),
    dict(id="yu-ji-tu", title="Yu Ji Tu", q=["Yu Ji Tu 1137", "Yujitu map tracks of Yu"]),
    dict(id="idrisi", title="Tabula Rogeriana", files=["File:TabulaRogeriana.jpg"], q=["Tabula Rogeriana", "al-Idrisi world map"]),
    dict(id="carte-pisane", title="Carte Pisane", q=["Carte Pisane", "Carta Pisana portolan"]),
    dict(id="hereford", title="Hereford Mappa Mundi", files=["File:Hereford-Karte.jpg"], q=["Hereford Mappa Mundi"]),
    dict(id="catalan-atlas", title="Catalan Atlas", q=["Catalan Atlas 1375", "Atlas catalan Cresques Mansa Musa"]),
    dict(id="kangnido", title="Kangnido", files=["File:KangnidoMap.jpg"], q=["Kangnido map", "Gangnido 1402"]),
    dict(id="mao-kun", title="Mao Kun Map", files=["File:Zhenghe-sailing-chart.gif"], q=["Mao Kun map", "Wubei Zhi Zheng He chart"]),
    dict(id="fra-mauro", title="Fra Mauro World Map", files=["File:FraMauroDetailedMap.jpg"], q=["Fra Mauro world map"]),
    dict(id="cantino", title="Cantino Planisphere", files=["File:Cantino planisphere (1502).jpg"], q=["Cantino planisphere"]),
    dict(id="imola", title="Plan of Imola", q=["Leonardo da Vinci map of Imola", "Leonardo Imola plan 1502"]),
    dict(id="waldseemuller", title="Waldseemuller World Map", files=["File:Waldseemuller map 2.jpg"], q=["Waldseemüller map 1507 Universalis Cosmographia"]),
    dict(id="tenochtitlan", title="Nuremberg Map of Tenochtitlan", q=["Map of Tenochtitlan 1524 Nuremberg", "Tenochtitlan 1524 Cortes map"]),
    dict(id="mercator", title="Mercator's World Map", files=["File:Mercator 1569.png"], q=["Mercator 1569 world map"]),
    dict(id="ortelius", title="Theatrum Orbis Terrarum", files=["File:OrteliusWorldMap1570.jpg"], q=["Ortelius Typus Orbis Terrarum 1570"]),
    dict(id="ricci", title="Kunyu Wanguo Quantu", q=["Kunyu Wanguo Quantu", "Matteo Ricci world map 1602"]),
    dict(id="riccioli", title="Riccioli and Grimaldi's Moon Map", q=["Riccioli Grimaldi moon map 1651", "Almagestum Novum lunar map"]),
    dict(id="halley", title="Halley's Chart of Compass Variation", q=["Halley isogonic chart 1701", "Halley compass variation chart Atlantic"]),
    dict(id="cassini", title="Cassini Map of France", q=["Carte de Cassini Paris feuille", "Cassini map of France 18th century"]),
    dict(id="nolli", title="Nolli's Plan of Rome", q=["Nolli map Rome 1748", "Nuova Pianta di Roma Nolli"]),
    dict(id="mitchell", title="Mitchell Map", files=["File:Mitchell Map-06full2.jpg"], q=["Mitchell Map 1755 British and French Dominions"]),
    dict(id="franklin-folger", title="Franklin-Folger Chart of the Gulf Stream", q=["Franklin Folger Gulf Stream chart", "Franklin Gulf Stream map"]),
    dict(id="tupaia", title="Tupaia's Chart", files=["File:Tupaia's map, c. 1769.jpg"], q=["Tupaia map 1769"]),
    dict(id="seven-ranges", title="Plat of the Seven Ranges", q=["Seven Ranges plat Hutchins", "Seven Ranges Ohio survey map"]),
    dict(id="gts-india", title="Great Trigonometrical Survey of India", q=["Great Trigonometrical Survey of India index chart 1870", "Great Trigonometrical Survey India"]),
    dict(id="humboldt", title="Humboldt's Naturgemalde", q=["Humboldt Naturgemälde Chimborazo", "Humboldt geography of plants 1807 Chimborazo"]),
    dict(id="gerrymander", title="The Gerry-mander", files=["File:The Gerry-Mander Edit.png", "File:The Gerry-Mander.png"], q=["Gerry-Mander 1812"]),
    dict(id="smith-geology", title="Smith's Geological Map", q=["William Smith geological map 1815", "Delineation of the Strata of England and Wales"]),
    dict(id="dupin", title="Dupin's Map of Schooling", files=["File:Carte figurative de l'instruction populaire de la France.jpg"], q=["Dupin carte figurative instruction populaire"]),
    dict(id="darwin-tree", title="Darwin's Tree Sketch", files=["File:Darwin Tree 1837.png"], q=["Darwin tree of life sketch 1837"]),
    dict(id="snow-cholera", title="Snow's Cholera Map", files=["File:Snow-cholera-map-1.jpg"], q=["John Snow cholera map 1854"]),
    dict(id="slavery-1861", title="Coast Survey Map of Slavery", q=["distribution of the slave population of the southern states 1861", "Hergesheimer slave population map"]),
    dict(id="mendeleev", title="Mendeleev's Periodic Table", q=["Mendeleev 1869 periodic table", "Mendeleev periodic table manuscript"]),
    dict(id="minard", title="Minard's Map", files=["File:Minard.png"], q=["Minard Napoleon Russian campaign 1869"]),
    dict(id="times-weather", title="The Times Weather Map", q=["Galton weather map Times 1875", "first newspaper weather map 1875"]),
    dict(id="schiaparelli", title="Schiaparelli's Map of Mars", q=["Schiaparelli Mars map 1877", "Schiaparelli Mars canali map"]),
    dict(id="booth", title="Booth's Poverty Map", q=["Booth poverty map London 1889", "Descriptive map of London poverty"]),
    dict(id="stick-charts", title="Marshall Islands Stick Charts", q=["Marshall Islands stick chart", "Micronesian navigational chart rebbelib"]),
    dict(id="brodmann", title="Brodmann's Map of the Cortex", q=["Brodmann 1909 cortex areas", "Brodmann areas lateral 1909"]),
    dict(id="wegener", title="Wegener's Maps of Continental Drift", files=["File:De Wegener Kontinente 018.jpg"], q=["Wegener Kontinente Pangaea 1929", "Wegener continental drift map"]),
    dict(id="sykes-picot", title="Sykes-Picot Map", files=["File:MPK1-426 Sykes Picot Agreement Map signed 8 May 1916.jpg"], q=["Sykes Picot Agreement map 1916"]),
    dict(id="beck-tube", title="Beck's London Underground Map", skip="in copyright (Transport for London)"),
    dict(id="holc", title="HOLC Residential Security Maps", q=["Home Owners' Loan Corporation redlining map", "HOLC residential security map 1937"]),
    dict(id="radcliffe", title="The Radcliffe Line", q=["Radcliffe Line map 1947", "Partition of India 1947 map Punjab boundary"]),
    dict(id="tharp-heezen", title="Tharp and Heezen's Ocean Floor Maps", skip="in copyright (Marie Tharp Maps / Berann estate)"),
    dict(id="arpanet", title="ARPANET Four-Node Map", q=["ARPANET 1969 map", "ARPANET logical map December 1969"]),
    dict(id="pioneer-plaque", title="Pioneer Plaque Pulsar Map", files=["File:Pioneer plaque sun.svg", "File:Pioneer plaque.svg"], q=["Pioneer plaque"]),
    dict(id="ozone-hole", title="Satellite Map of the Ozone Hole", q=["Antarctic ozone hole TOMS NASA", "ozone hole 1985 NASA map"]),
    dict(id="cfa-slice", title="A Slice of the Universe", skip="in copyright (journal figure, Smithsonian Astrophysical Observatory)"),
    dict(id="genome", title="Human Genome Sequence", q=["human karyotype NHGRI", "human chromosomes ideogram"],
         note="illustrative: a chromosome chart, since the sequence itself has no single picture"),
    dict(id="wmap", title="WMAP Map of the Early Universe", q=["WMAP cosmic microwave background 2003", "WMAP all-sky map"]),
    dict(id="google-maps", title="Google Maps", skip="in copyright (Google screenshot)"),
    dict(id="gaia", title="Gaia's Map of the Milky Way", q=["Gaia DR2 all-sky map Milky Way", "Gaia sky in colour"]),
    dict(id="jhu-covid", title="Johns Hopkins COVID-19 Dashboard", skip="in copyright (dashboard screenshot)"),
]


def api(params):
    """GET the Commons API and return parsed JSON. Retries on throttling."""
    params = dict(params, format="json", formatversion="2")
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < 3:
                time.sleep(5 * (attempt + 1))   # back off, then try again
                continue
            raise
    return {}


def plain(s):
    """Commons metadata values are HTML; reduce to short plain text."""
    s = html.unescape(re.sub(r"<[^>]+>", "", s or ""))
    return re.sub(r"\s+", " ", s).strip()[:160]


def to_candidate(page):
    """Turn one API page record into a flat dict, or None if unusable."""
    info = (page.get("imageinfo") or [None])[0]
    if not info or "thumburl" not in info:
        return None
    meta = info.get("extmetadata") or {}
    lic = plain(meta.get("LicenseShortName", {}).get("value", ""))
    return dict(
        file_title=page["title"],
        thumb=info["thumburl"],
        page=info.get("descriptionurl", ""),
        mime=info.get("mime", ""),
        license=lic,
        artist=plain(meta.get("Artist", {}).get("value", "")) or "Unknown",
        ok=lic.lower().startswith(OK_LICENSE),
    )


IMAGEINFO = dict(prop="imageinfo", iiprop="url|mime|extmetadata", iiurlwidth=WIDTH)


def by_title(title):
    """Look up one exact file title. Returns [] when the file does not exist."""
    data = api(dict(action="query", titles=title, **IMAGEINFO))
    pages = data.get("query", {}).get("pages", [])
    return [c for c in map(to_candidate, pages) if c]


def by_search(query, limit=6):
    """Keyword search in the File: namespace, images and drawings only."""
    data = api(dict(action="query", generator="search", gsrnamespace=6, gsrlimit=limit,
                    gsrsearch=f"{query} filetype:bitmap|drawing", **IMAGEINFO))
    pages = data.get("query", {}).get("pages", [])
    pages.sort(key=lambda p: p.get("index", 99))        # keep search-rank order
    return [c for c in map(to_candidate, pages) if c]


def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)


def ext_of(url):
    e = Path(urllib.parse.urlparse(url).path).suffix.lower()
    return e if e in (".jpg", ".jpeg", ".png", ".gif", ".webp") else ".jpg"


def shrink(path):
    """Downsize a manual download with macOS sips, if available. No-op elsewhere."""
    if shutil.which("sips") and path.stat().st_size > 150_000:
        subprocess.run(["sips", "-Z", str(WIDTH), str(path)], capture_output=True)


def existing(mid):
    return next(iter(THUMBS.glob(mid + ".*")), None)


def collect(m, overrides, redo):
    """Return (credit dict or None, candidates list, status string) for one map."""
    mid, ov = m["id"], overrides.get(m["id"])
    have = existing(mid)
    if have and not redo:
        return None, [], "kept"                      # already collected on an earlier run
    if have:
        have.unlink()

    # 1) Manual non-Commons source: rights are whatever the operator declared.
    if ov and "url" in ov:
        dest = THUMBS / (mid + ext_of(ov["url"]))
        download(ov["url"], dest)
        shrink(dest)
        return dict(id=mid, title=m["title"], file=dest.name, artist=ov.get("credit", ""),
                    license=ov.get("license", ""), source_url=ov.get("source", ov["url"]),
                    note=m.get("note", "")), [], "manual"

    if m.get("skip") and not ov:
        return None, [], "skipped: " + m["skip"]

    # 2) Commons: forced pick, then known titles, then searches.
    cands = []
    for t in ([ov["file"]] if ov and "file" in ov else []) + m.get("files", []):
        cands += by_title(t)
        time.sleep(PAUSE)
    if not any(c["ok"] for c in cands):
        for q in m.get("q", []):
            cands += by_search(q)
            time.sleep(PAUSE)
            if any(c["ok"] for c in cands):
                break
    pick = next((c for c in cands if c["ok"]), None)
    if not pick:
        return None, cands, "NOT FOUND"
    dest = THUMBS / (mid + ext_of(pick["thumb"]))
    download(pick["thumb"], dest)
    return dict(id=mid, title=m["title"], file=dest.name, artist=pick["artist"],
                license=pick["license"], source_url=pick["page"], commons_title=pick["file_title"],
                note=m.get("note", "")), cands, "ok"


def write_review(credits, alternates, statuses):
    """Contact sheet: every pick, its license, and the runners-up to choose from."""
    rows = []
    for m in MAPS:
        mid = m["id"]
        c = credits.get(mid)
        img = f'<img src="thumbs/{html.escape(c["file"])}" width="240">' if c else "<i>no image</i>"
        meta = (f'{html.escape(c.get("commons_title", c["source_url"]))}<br>{html.escape(c["license"])} '
                f'&middot; {html.escape(c["artist"])}') if c else html.escape(statuses.get(mid, ""))
        alts = "".join(
            f'<figure><img src="{html.escape(a["thumb"])}" width="120"><figcaption>{html.escape(a["file_title"])}'
            f'<br>{html.escape(a["license"] or "no license")}{"" if a["ok"] else " (rejected)"}</figcaption></figure>'
            for a in alternates.get(mid, [])[:5])
        rows.append(f"<tr><td><b>{html.escape(m['title'])}</b><br><code>{mid}</code></td>"
                    f"<td>{img}<br><small>{meta}</small></td><td class='alts'>{alts}</td></tr>")
    (HERE / "review.html").write_text(
        "<!doctype html><meta charset='utf-8'><title>Thumbnail review</title>"
        "<style>body{font:14px system-ui;margin:20px}td{vertical-align:top;padding:10px;border-top:1px solid #ccc}"
        ".alts{display:flex;gap:8px;flex-wrap:wrap}figure{margin:0;width:120px;font-size:11px;word-break:break-word}</style>"
        "<h1>Thumbnail review</h1><p>Check each pick shows the right map. To change one: "
        "<code>python3 collect_thumbs.py --pick ID=\"File:Exact title.jpg\"</code></p>"
        "<table>" + "".join(rows) + "</table>", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Collect map thumbnails from Wikimedia Commons.")
    ap.add_argument("--only", nargs="*", help="ids to process (default: all)")
    ap.add_argument("--redo", action="store_true", help="re-download even if a file exists")
    ap.add_argument("--list", action="store_true", help="print ids and exit")
    ap.add_argument("--pick", metavar='ID="File:Title"', help="force a Commons file for one id")
    ap.add_argument("--url", metavar="ID=URL", help="use an image from another source for one id")
    ap.add_argument("--credit", default="", help="with --url: who to credit")
    ap.add_argument("--license", default="", help="with --url: license or rights statement")
    ap.add_argument("--source", default="", help="with --url: page the image came from")
    a = ap.parse_args()

    ids = [m["id"] for m in MAPS]
    if a.list:
        for m in MAPS:
            print(f'{m["id"]:16} {m["title"]}{"   [" + m["skip"] + "]" if m.get("skip") else ""}')
        print(len(MAPS), "maps")
        return

    overrides = json.loads(OVERRIDES.read_text()) if OVERRIDES.exists() else {}
    forced = []
    for arg, key in ((a.pick, "file"), (a.url, "url")):
        if arg:
            mid, _, val = arg.partition("=")
            if mid not in ids:
                sys.exit(f"unknown id: {mid}")
            if key == "url" and not (a.credit and a.license):
                sys.exit("--url needs --credit and --license (only use images you have the rights to)")
            overrides[mid] = {key: val.strip('"'), "credit": a.credit, "license": a.license, "source": a.source}
            forced.append(mid)
    if forced:
        OVERRIDES.write_text(json.dumps(overrides, indent=2))

    THUMBS.mkdir(exist_ok=True)
    credits_path = HERE / "credits.json"
    credits = {c["id"]: c for c in json.loads(credits_path.read_text())} if credits_path.exists() else {}
    alternates, statuses = {}, {}
    todo = [m for m in MAPS if (not a.only or m["id"] in a.only) or m["id"] in forced]

    for m in todo:
        try:
            credit, cands, status = collect(m, overrides, a.redo or m["id"] in forced)
        except Exception as e:                       # one failure should not stop the run
            credit, cands, status = None, [], f"ERROR: {e}"
        if credit:
            credits[m["id"]] = credit
        alternates[m["id"]], statuses[m["id"]] = cands, status
        print(f'{m["id"]:16} {status}')

    # Drop credits whose file is gone, then write outputs in page order.
    ordered = [credits[i] for i in ids if i in credits and (THUMBS / credits[i]["file"]).exists()]
    credits_path.write_text(json.dumps(ordered, indent=2, ensure_ascii=False), encoding="utf-8")
    write_review({c["id"]: c for c in ordered}, alternates, statuses)

    with zipfile.ZipFile(HERE / "thumbs.zip", "w", zipfile.ZIP_DEFLATED) as z:
        z.write(credits_path, "credits.json")
        for c in ordered:
            z.write(THUMBS / c["file"], "thumbs/" + c["file"])

    missing = [i for i in ids if i not in {c["id"] for c in ordered}]
    print(f"\n{len(ordered)}/{len(ids)} collected. Open review.html to check them.")
    if missing:
        print("No image:", ", ".join(missing))
    print("Send back: thumbs.zip")


if __name__ == "__main__":
    main()
