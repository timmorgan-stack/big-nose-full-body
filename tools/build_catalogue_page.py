#!/usr/bin/env python3
"""Generate catalogue.html — a static, no-JavaScript list of every bottle with its label image.
Search engines and site crawlers see the whole cellar here (the shop page renders its cards with JS).
Chrome (ticker/header/footer) is copied from shop.html at build time so every page stays identical."""
import json, pathlib, re, html

root = pathlib.Path(__file__).resolve().parent.parent
feed = json.loads((root / "data" / "catalog.json").read_text())
shop = (root / "shop.html").read_text()

def chunk(pat):
    m = re.search(pat, shop, re.S); assert m, pat; return m.group(0)
head_links = chunk(r'<link rel="preconnect".*?<link rel="stylesheet" href="css/site.css">')
ticker = chunk(r'<div class="ticker[^"]*".*?</div>\s*</div>')
header = chunk(r'<header.*?</header>')
footer = chunk(r'<footer.*?</footer>')

order = ["reserve","sparkling","white","rose","orange","red","fortified","sake",
         "half","alt","kosher","dealc","gift"]
by_cat = {}
for w in feed["works"]:
    by_cat.setdefault(w["category"], []).append(w)

e = html.escape
def stock_note(w):
    s = w.get("stock")
    if s is None or s < 0: return ""
    if s == 0: return '<span class="cat-stock">Sold out</span>'
    return f'<span class="cat-stock">Only {s} left</span>' if s <= 6 else ""
sections = []
for cat in order:
    works = by_cat.get(cat, [])
    if not works: continue
    label = works[0]["series"]
    items = "".join(
        f'''      <li class="cat-item">
        <a class="cat-item__img" href="shop.html#q={e(w["title"])}"><img src="{e(w["image"]["thumb"])}" alt="{e(w["title"])} label" loading="lazy" width="600" height="780"></a>
        <div class="cat-item__body">
          <h3><a href="shop.html#q={e(w["title"])}">{e(w["title"])}</a></h3>
          <p class="cat-item__origin">{e(w["place"])}</p>
          <p class="cat-item__desc">{e(w["description"])}</p>
        </div>
        <p class="cat-item__price">${w["price"]:,}{stock_note(w)}</p>
      </li>
''' for w in works)
    sections.append(f'''  <section class="cat-section" id="{cat}">
    <div class="wrap">
      <p class="sec-label">{e(label)}</p>
      <h2>{e(label)} <small class="cat-count">{len(works)} {"bottle" if len(works)==1 else "bottles"}</small></h2>
      <ul class="cat-list">
{items}      </ul>
    </div>
  </section>
''')

page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Full Cellar List — Big Nose Full Body</title>
<meta name="description" content="Every bottle currently listed at Big Nose Full Body, Park Slope — sparkling, white, rosé, orange, red, sake and cider, large format, dessert and fortified.">
{head_links}
</head>
<body class="cmstemplate_bnfb">

{ticker}

{header}

<main>
  <div class="pagehead">
    <div class="wrap">
      <p class="sec-label">Full Cellar List</p>
      <h1>Every bottle, one page</h1>
      <p class="lede">The whole shelf in plain text — {len(feed["works"])} bottles across {len([c for c in order if by_cat.get(c)])} sections. For filters, search and ordering, head to <a href="shop.html">the cellar</a>.</p>
      <div class="cat-jump" role="group" aria-label="Jump to a section">
{"".join(f'        <a href="#{c}">{e(by_cat[c][0]["series"])}</a>' + chr(10) for c in order if by_cat.get(c))}      </div>
    </div>
  </div>

{"".join(sections)}</main>

{footer}

<script src="data/catalog.js"></script>
<script src="js/store.js"></script>
</body>
</html>
'''
(root / "catalogue.html").write_text(page)
print(f"catalogue.html: {len(feed['works'])} bottles in {len(sections)} sections")
