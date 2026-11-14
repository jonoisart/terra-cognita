# terra-cognita

The maps that redrew the world, from Bronze Age sky discs to the live map in your pocket.

**Live site: https://research.jonoisart.com/terra-cognita/**

A sourced timeline of how people have charted land, sea, stars, bodies and networks, and what changed because they did. Each entry says what the map is, what it changed, where it is now, and links a source.

## What counts as a map

Anything that puts a territory on a surface so someone can find their way through it. That includes the obvious (Ptolemy, Mercator, the Cassini survey) and the less obvious: Marshall Islands stick charts of ocean swells, Darwin's tree sketch, Mendeleev's table, Brodmann's cortex, the first ARPANET sketch, the human genome.

The test for inclusion is consequence. A map is here because a border moved, a science started, a name stuck, or people began finding their way differently once it existed. Entries run in date order. The numbers are sequence, not rank.

## View it

Online at https://research.jonoisart.com/terra-cognita/. The [research hub](https://github.com/jonoisart/research) pulls this repo's `main` and deploys it to Cloudflare.

To run it locally, open `index.html` in a browser. It is one self-contained page that loads its thumbnails from `thumbs/` and its fonts from Google Fonts. No build step.

Clicking a thumbnail opens a full-window viewer. It shows the local thumbnail at once, then swaps in a 1280 px copy fetched from Wikimedia Commons at view time; if that fetch fails, the thumbnail stays. Close it with the X at top left, Esc, or Back.

## What's in here

| Path | What it is |
| --- | --- |
| `index.html` | The page: entries, filters, styles and script in one file |
| `thumbs/` | Thumbnails, 360 px wide JPEGs |
| `credits.json` | Artist, license and source for every thumbnail |
| `collect_thumbs.py` | Collects openly licensed thumbnails from Wikimedia Commons |
| `LICENSE` | MIT, for the code and text |

## Collecting thumbnails

`collect_thumbs.py` uses only the Python standard library.

```bash
export THUMBS_CONTACT="you@example.com"   # Wikimedia asks for a contact in the User-Agent
python3 collect_thumbs.py                 # writes thumbs/, credits.json, review.html, thumbs.zip
python3 collect_thumbs.py --list          # print every map id, no network
```

For each map it tries a known Commons file title, then falls back to keyword search, and keeps only files that Commons marks as public domain or Creative Commons. Open `review.html` afterwards and check every pick by eye. Search gets some of them wrong.

Fix a wrong pick, or bring in an image from a museum, library or journal:

```bash
python3 collect_thumbs.py --pick cantino="File:Cantino planisphere (1502).jpg"
python3 collect_thumbs.py --url ID=https://example.org/img.jpg \
    --credit "Holding institution" --license "Public domain" --source "https://example.org/item"
```

`--url` refuses to run without a credit and a license. Only use images you have the rights to.

Two things the script does not do:

- It downloads thumbnails as Commons serves them (480 px, mixed formats). The ones in this repo were flattened onto white and resized to 360 px JPEG afterwards.
- It does not edit the page. Thumbnail paths and credits live in the `THUMBS` table inside `index.html`, so a new or changed image needs that table updated by hand.

## Images and licenses

The MIT license covers the code and the written text. It does not cover the thumbnails.

Most thumbnails are public domain. A few are Creative Commons (CC BY, CC BY-SA, CC0), and those terms travel with the image. `credits.json` records the artist, license and source page for each file, and the page prints the same credit under each entry. Keep both if you reuse the images.

Five maps are still in copyright and have no thumbnail: Harry Beck's Underground map, Google Maps, the Johns Hopkins COVID-19 dashboard, the Tharp and Heezen ocean floor maps, and the CfA "Slice of the Universe".

Some thumbnails stand in for the thing described, and the credit line says so. Examples: the ozone image is from September 2000, not 1985; the WMAP image is from the 2006 data release; the Brodmann plate is a marmoset cortex from the same 1909 monograph; the genome entry shows a chromosome chart.

## Accuracy

Dates marked "c." are approximate. Where historians dispute a date or an effect, the entry says so. Every entry links one source, and corrections with a better source are welcome as issues or pull requests.

Selection is a judgement call. Near misses are listed at the bottom of the page.
