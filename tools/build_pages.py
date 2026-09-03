#!/usr/bin/env python3
"""Generate the content pages that mirror the live shop's own pages.

Chrome (head links, ticker, header, footer) is copied from shop.html at build time so
every page in the site stays byte-identical there — the site importer treats identical
chrome as one shared object instead of eight near-copies.
"""
import json, pathlib, re, html

ROOT = pathlib.Path(__file__).resolve().parent.parent
shop = (ROOT / "shop.html").read_text()
feed = json.loads((ROOT / "data" / "catalog.json").read_text())
WORKS = feed["works"]
e = html.escape

def chunk(pat):
    m = re.search(pat, shop, re.S); assert m, pat; return m.group(0)
HEAD   = chunk(r'<link rel="preconnect".*?<link rel="stylesheet" href="css/site.css">')
TICKER = chunk(r'<div class="ticker[^"]*".*?</div>\s*</div>')
HEADER = chunk(r'<header.*?</header>')
FOOTER = chunk(r'<footer.*?</footer>')

def page(fn, title, desc, body, script=""):
    out = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{e(desc)}">
{HEAD}
</head>
<body class="cmstemplate_bnfb">

{TICKER}

{HEADER}

<main>
{body}
</main>

{FOOTER}

<script src="data/catalog.js"></script>
<script src="js/store.js"></script>
{script}</body>
</html>
"""
    (ROOT / fn).write_text(out)
    return fn

def pagehead(label, h1, lede, extra=""):
    return f"""  <div class="pagehead">
    <div class="wrap">
      <p class="sec-label">{label}</p>
      <h1>{h1}</h1>
      <p class="lede">{lede}</p>
{extra}    </div>
  </div>
"""

# ---------------------------------------------------------------- bottle cards
def bottle_card(w, full=False):
    """A shelf card. `full` keeps the whole tasting note (Reserve List)."""
    tagbits = "".join(
        f'<span{" class=\"rsv\"" if t == "reserve" else ""}>{e(TAGLABEL.get(t, t))}</span>'
        for t in w.get("tagKeys", []))
    stock = w.get("stock")
    if w.get("cellarOnly"):
        buy = '<span class="cellar-only">In store only</span>'
    elif stock == 0:
        buy = '<button class="addbtn" disabled>Sold out</button>'
    else:
        buy = ('<div class="wcard__buy">'
               f'<div class="qty qty--sm"><button type="button" data-qdec="{e(w["id"])}" aria-label="Fewer">&minus;</button>'
               '<output>1</output>'
               f'<button type="button" data-qinc="{e(w["id"])}" aria-label="More">+</button></div>'
               f'<button class="addbtn" data-add="{e(w["id"])}">Add to cart</button>'
               '</div>')
    low = f'<span class="low">Only {stock} left</span>' if isinstance(stock, int) and 0 < stock <= 6 else ""
    size = f' · {e(w["size"])}' if w.get("size") and w["size"] != "750ml" else ""
    price = f'${w["price"]:,.0f}' if float(w["price"]).is_integer() else f'${w["price"]:,.2f}'
    pair = f'<p class="wcard__pair"><b>Pairs with</b> {e(w["pairings"])}</p>' if w.get("pairings") else ""
    return f"""      <article class="wcard{' wcard--full' if full else ''}" style="--label-cat:{CATCOLOR.get(w['category'],'#950951')};--label-tint:color-mix(in srgb,{CATCOLOR.get(w['category'],'#950951')} 14%,transparent)">
        <div class="wcard__img"><img src="{e(w['image']['thumb'])}" alt="{e(w['title'])}" loading="lazy" width="420" height="559"></div>
        <div class="wcard__body">
          <span class="wcard__cat">{e(w['series'])}{size}</span>
          <h3>{e(w['title'])}</h3>
          <p class="wcard__origin">{e(w['place'])}</p>
          <p class="wcard__desc">{e(w['description'])}</p>
{pair and '          ' + pair + chr(10)}          <button class="readmore" type="button">Read more</button>
          <div class="wcard__tags">{tagbits}{f'<span>{e(w["score"])}</span>' if w.get('score') else ''}{low}</div>
          <div class="wcard__meta"><span class="wcard__price">{price}</span>{buy}</div>
        </div>
      </article>
"""

CATCOLOR = {"sparkling":"#b8891c","white":"#c2a12a","rose":"#d4607f","orange":"#c96a1f",
  "red":"#950951","sake":"#3f5b8c","fortified":"#6b3fa0","half":"#7a6a55","alt":"#2f7d6b",
  "kosher":"#1f5f8b","dealc":"#4a7c3f","gift":"#17120e","reserve":"#6d0339"}
TAGLABEL = {"reserve":"Reserve List","organic":"Organic","biodynamic":"Biodynamic",
  "sustainable":"Sustainable","vegan":"Vegan","natural":"Natural","minimal-sulfur":"Minimal Sulfur",
  "no-added-sulfur":"No Added Sulfur","unoaked":"Unoaked","kosher":"Kosher",
  "orange":"Orange / Skin Contact","skin-contact":"Skin Contact","pet-nat":"Pét-Nat",
  "off-dry":"Off Dry","new":"New Arrival"}

ADD_SCRIPT = ""   # store.js wires add-to-cart for every page

# ================================================================= RESERVE LIST
res = [w for w in WORKS if "reserve" in w.get("tagKeys", [])]
ORDER = ["sparkling","white","red","fortified","reserve"]
res.sort(key=lambda w: (ORDER.index(w["category"]) if w["category"] in ORDER else 9, -w["price"]))
groups = {}
for w in res: groups.setdefault(w["series"], []).append(w)

sections = ""
for label, ws in groups.items():
    sections += f"""  <section class="cat-section">
    <div class="wrap">
      <p class="sec-label">{e(label)}</p>
      <h2>{e(label)} <small class="cat-count">{len(ws)} {'bottle' if len(ws)==1 else 'bottles'}</small></h2>
      <div class="wgrid">
{''.join(bottle_card(w, full=True) for w in ws)}      </div>
    </div>
  </section>

"""
lo, hi = min(w["price"] for w in res), max(w["price"] for w in res)
counts = {}
for w in res: counts[w["category"]] = counts.get(w["category"], 0) + 1
countries = sorted({w["place"].split(",")[-1].strip() for w in res if w.get("place")})

page("reserve.html", "The Reserve List — Big Nose Full Body",
     "The cellar selection at Big Nose Full Body, Park Slope: rare, age-worthy and collectible bottles, hand-picked and honestly described.",
     f"""  <div class="rhero">
    <div class="rhero__img">
      <img src="img/interior.jpg" alt="Inside Big Nose Full Body — wooden shelves and a rosé display in the afternoon sun">
    </div>
    <div class="rhero__inner">
      <div class="rhero__note">
        <b>Ask at the counter</b>
        <span>The reserve bottles live behind the till, and we like talking about them.</span>
      </div>
      <p class="rhero__kicker">The Reserve List</p>
      <h1>Bottles worth <span class="outline">the wait</span></h1>
      <p class="rhero__lede">The cellar selection — {len(res)} rare and age-worthy finds, hand-picked and honestly
        described. Vintage Champagne, mountain Cabernet, Burgundy, Barolo and a few sweet things worth saving.
        From ${lo:,.0f} to ${hi:,.0f}.</p>
      <div class="rhero__facts">
        <div class="rhero__fact"><b>{len(res)}</b><span>Bottles on the list</span></div>
        <div class="rhero__fact"><b>{len(countries)}</b><span>Countries</span></div>
        <div class="rhero__fact"><b>${lo:,.0f}–${hi:,.0f}</b><span>Price range</span></div>
        <div class="rhero__fact"><b>{sum(1 for w in res if w.get("score"))}</b><span>Critically rated</span></div>
      </div>
    </div>
  </div>

""" + sections + """  <section class="how">
    <div class="wrap">
      <p class="sec-label">How the list works</p>
      <h2>Ask us anything about it</h2>
      <div class="njw">
        <a href="shop.html#tag=reserve">Reserve bottles in the shop <small>Order online</small></a>
        <a href="visit.html">Talk to the crew <small>389 7th Ave</small></a>
        <a href="tastings.html">Taste before you commit <small>Daily pours</small></a>
      </div>
      <p class="tags-note how__note">The list rotates as bottles sell and new allocations land. Two of them are cellar-only — we keep them in the shop rather than the online store, so ask at the counter.</p>
    </div>
  </section>
""", ADD_SCRIPT)

# ================================================================= NEW ARRIVALS
new = [w for w in WORKS if "new" in w.get("tagKeys", [])]
new.sort(key=lambda w: (ORDER.index(w["category"]) if w["category"] in ORDER else 9, w["title"]))
page("new-arrivals.html", "New Arrivals — Big Nose Full Body",
     "The bottles that just landed at Big Nose Full Body, Park Slope — fresh allocations, new vintages and first-time producers.",
     pagehead("New Arrivals", "Just landed",
       f"{len(new)} bottles that came through the door most recently — new vintages, first-time producers and "
       f"the small allocations we only get a few cases of. They move quickly.")
     + """  <div class="wrap">
    <figure class="reserve-hero">
      <img src="img/interior.jpg" alt="Inside Big Nose Full Body — the rosé table and wall of bottles" loading="lazy">
      <figcaption>New arrivals go out on the front table first. If you want the pick of them, come early in the week.</figcaption>
    </figure>
  </div>

  <section class="cat-section">
    <div class="wrap">
      <p class="sec-label">On the front table</p>
      <h2>This week's arrivals</h2>
      <div class="wgrid">
""" + "".join(bottle_card(w) for w in new) + """      </div>
      <p style="margin-top:2rem"><a class="btn btn--solid" href="shop.html#tag=new">See them in the shop</a></p>
    </div>
  </section>
""", ADD_SCRIPT)

# ======================================================================= GUIDES
page("guides.html", "Guides — Big Nose Full Body",
     "Food and wine pairings, pre-built six packs, holiday essentials and how to search the shelf at Big Nose Full Body.",
     pagehead("Guides", "Ways in",
       "Four ways we help people choose, written down. Start with what you're cooking, let us build the case for you, "
       "get the holiday table sorted, or learn the words we tag every bottle with.")
     + """  <section class="cat-section">
    <div class="wrap">
      <div class="njw guides-grid">
        <a href="pairings.html">Food &amp; Wine Pairings <small>Light to heavy, whites and reds</small></a>
        <a href="six-packs.html">Pre-Built Six Packs <small>Six bottles, one decision</small></a>
        <a href="holiday.html">Holiday Essentials <small>Cooking to dozing off</small></a>
        <a href="searchable-terms.html">Searchable Terms <small>How we tag the shelf</small></a>
        <a href="reserve.html">The Reserve List <small>Cellar selections</small></a>
        <a href="new-arrivals.html">New Arrivals <small>Just landed</small></a>
      </div>
    </div>
  </section>
""")

# ===================================================================== PAIRINGS
PAIRINGS = [
 ("Shellfish &amp; Light Fish", "Oysters, crudo, sole, a plate of shrimp.",
  ["Domaine des Cassagnoles Blanc ($13)","Inama Soave Classico ($16)","Bohigas Xarel-Lo ($13)",
   "Tenuta Rapitala Grillo ($14)","Chateau du Coing de St. Fiacre Muscadet ($15)",
   "Forstreiter Gruner Veltliner ($15)","Casa d'Ambra Bianco ($17)","HMR Mont Rubi White ($20)",
   "Barbaglia Lucino Bianco ($32)"], []),
 ("Rich Fish &amp; Bold Seafood", "Salmon, tuna, swordfish, anything off the grill.",
  ["Zestos Malvar ($13)","Hugel Gentil ($17)","La Cana Albarino ($19)","Feudo Montoni Catarratto ($22)",
   "Val de Mer Chablis ($28)","Lundeen “Articulate” Chardonnay ($34)"],
  ["Robert Perroud Brouilly ($18)","Pasaeli “6N” Karasakiz ($18)",
   "Marchesi Alfieri “Sansoero” Grignolino ($19)","Lundeen Pinot Noir ($25)","Millton Pinot Noir ($38)"]),
 ("Chicken &amp; Poultry", "Roast bird, schnitzel, anything with a pan sauce.",
  ["Dos Minas Torrontes ($12)","Yalumba Unwooded Chardonnay ($14)",
   "Saint Elena “Klodic” Orange Pinot Grigio ($17)","Pinon Vouvray ($19)",
   "Hearst Ranch White Blend ($20)","La Spinona Langhe Chardonnay ($25)","Faiveley Bourgogne Blanc ($27)"],
  ["Salcheto Chianti ($15)","Chateau de Brague Bordeaux ($15)","Oracle “Labyrinth” Red Blend ($15)",
   "Alvaro Castro DAC Tinto ($17)","Agostino Bosco Dolcetto ($17)","J. Bouchon Pais Viejo ($17)",
   "Troupis “Fteri” Agiorgitiko ($18)","Alto Limay Pinot Noir ($20)",
   "Domaine Eric Herault Chinon ($21)","Domaine de Fa Fleurie ($32)"]),
 ("Pork Dishes", "Chops, belly, sausage, a shoulder in the oven all afternoon.",
  ["Arnaldo Caprai Grechetto ($18)","Fuchs Sylvaner ($19)","JJ Vincent Bourgogne Blanc ($24)",
   "I Pentri Flora Falanghina ($25)","Fitapreta Branco ($26)","Miner Chardonnay ($34)"],
  ["Root 1 Carmenere ($12)","Chateau Gabelot Bordeaux ($15)","Occam's Razor Red Blend ($16)",
   "Nobis “Love and Grapes” Syrah ($17)","Barone di Villagrande Etna Rosso ($22)",
   "Dashe Grenache ($25)","Domaine Glinavos Vlahiko ($25)","Domaine Montirius Vacqueyras ($27)",
   "Anima Negra “AN/2” ($32)"]),
 ("Red Meat", "Steak, lamb, short ribs, the Sunday roast.", [],
  ["Stone Forest Red Blend ($13)","Pinuaga “Nature” Tempranillo ($16)","Mocali I Piaggioni ($17)",
   "Vina Robles “The Arborist” Red ($17)","Chateau La Canorgue ($19)","Buglioni Valpolicella ($20)",
   "Lapostolle Rouge ($23)","Alvaro Palacios Priorat ($28)","Dupuy de Lome Bandol ($32)"]),
]
def wine_col(kind, wines):
    if not wines: return ""
    items = "".join(f"          <li>{w}</li>\n" for w in wines)
    return f"""        <div class="pair-col pair-col--{kind}">
          <h4>{kind.title()}s</h4>
          <ul>
{items}          </ul>
        </div>
"""
body = ""
for i, (course, blurb, whites, reds) in enumerate(PAIRINGS, 1):
    body += f"""  <section class="cat-section">
    <div class="wrap">
      <p class="sec-label">Course {i:02d}</p>
      <h2>{course}</h2>
      <p class="lede">{blurb}</p>
      <div class="pair-grid">
{wine_col('white', whites)}{wine_col('red', reds)}      </div>
    </div>
  </section>

"""
page("pairings.html", "Food &amp; Wine Pairings — Big Nose Full Body",
     "What to drink with what, from the crew at Big Nose Full Body: shellfish to red meat, whites and reds, with prices.",
     pagehead("Guides", "Food &amp; wine pairings",
       "Organised from light dishes to heavy ones. Whites on one side, reds on the other, prices as they stand on the shelf. "
       "Not rules — just what we reach for, and a good place to start an argument.")
     + body + """  <section class="how">
    <div class="wrap">
      <p class="sec-label">Still stuck?</p>
      <h2>Tell us what's for dinner</h2>
      <div class="njw">
        <a href="visit.html">Ask at the counter <small>389 7th Ave, every day 12–9</small></a>
        <a href="shop.html">Browse the shelf <small>Filter by colour and country</small></a>
        <a href="six-packs.html">Let us build the case <small>Pre-built six packs</small></a>
      </div>
    </div>
  </section>
""")

# =================================================================== SIX PACKS
PACKS = [
 ("American Standard", 107, "Everything the table needs, all from the States.",
  ["1 Saint Vincent NV Rosé Sparkler","1 Hedges CMS Sauvignon Blanc","1 Eola Cellars Chardonnay",
   "2 L'Umami Pinot Noir","1 Delta Zin"]),
 ("American Deluxe", 183, "The same idea with the good stuff in it.",
  ["1 Schramsberg Blanc de Blanc","1 Cuvaison Sauvignon Blanc","1 Miner Chardonnay",
   "2 Lundeen Pinot Noir","1 Frank Family Zinfandel"]),
 ("I Love New York", 139, "Six bottles that never left the state.",
  ["1 Buttonwood Pét-Nat","1 Ravines DRY Riesling","1 Channing Daughters Cabernet Sauvignon Rosato",
   "2 Pellegrini Vineyards Cabernet Franc","1 Macari Dos Aguas Bordeaux Style Blend"]),
 ("Off the Beaten Path", 99, "Six countries most people haven't drunk this week.",
  ["1 Orbis Moderandi Pét-Nat Sauvignon Blanc","1 Mayu Pedro Ximenez","1 Dos Minas Torrontes",
   "1 Weninger Kekfrankos","1 DAC Dao Tinto","1 Domaine Tatsis “Young Vines” Agiorgitiko"]),
 ("Vive La France", 186, "Champagne, Sancerre, Burgundy and Bandol walk into a box.",
  ["1 Chapuy Blanc de Blanc Champagne","1 Vieux Pruniers Sancerre",
   "1 Olivier Leflaive “Les Setilles” Bourgogne","2 Faiveley Bourgogne Pinot Noir",
   "1 Dupuy de Lome Bandol"]),
 ("Valores Españoles", 70, "Spain, top to bottom, for the price of one good bottle.",
  ["1 Casteller Cava","1 Torres Verdejo","1 Zestos Malvar","2 Manon Tempranillo",
   "1 Luzon Verde Monastrell"]),
]
cards = ""
for name, price, blurb, contents in PACKS:
    items = "".join(f"          <li>{c}</li>\n" for c in contents)
    cards += f"""      <article class="pack">
        <div class="pack__head">
          <h3>{name}</h3>
          <span class="pack__price">${price}</span>
        </div>
        <p class="pack__blurb">{blurb}</p>
        <ul class="pack__list">
{items}        </ul>
      </article>
"""
page("six-packs.html", "Pre-Built Six Packs — Big Nose Full Body",
     "Six bottles chosen by the crew at Big Nose Full Body, Park Slope — Thanksgiving packs from $70 to $186.",
     pagehead("Guides", "Pre-built six packs",
       "Six bottles, one decision. We built these for a full table at Thanksgiving, but they work for any long dinner "
       "where you'd rather pour than think. Order one at the counter or call the shop and we'll have it ready.")
     + f"""  <section class="cat-section">
    <div class="wrap">
      <div class="packs">
{cards}      </div>
      <p class="tags-note how__note">Packs qualify for the case discounts — six bottles takes 5% off with <b>HALF5</b>, twelve takes 15% off with <b>CASE15</b>. Want one built around a different budget or a fussy relative? Ask us.</p>
      <p style="margin-top:1.6rem"><a class="btn btn--solid" href="visit.html">Call the shop to order</a></p>
    </div>
  </section>
""")

# ============================================================ HOLIDAY ESSENTIALS
HOLIDAY = [
 ("Cooking", "The bottles that go in the pan before they go in the glass.",
  [("Dry Red Cooking Wine","$7"),("Dry White Cooking Wine","$8"),("Ruby Port","$16"),
   ("Dry Sherry","$14"),("Madeira","$15"),("Dry Marsala","$10"),
   ("Sweet Marsala","$10"),("Dry Hard Cider","$12")]),
 ("Before the Meal", "Something to hand people at the door.",
  [("Traditional Craft Cider",""),("Sparkling Wine",""),("Orange Wine",""),("Fine Sherry","")]),
 ("After the Meal", "For the stretch between pudding and the armchair.",
  [("Dessert Wines",""),("Port",""),("Bulk Offerings",""),("Luxury Offerings","")]),
]
secs = ""
for i, (stage, blurb, items) in enumerate(HOLIDAY, 1):
    lis = "".join(
        f'          <li><span>{n}</span>{f"<b>{p}</b>" if p else ""}</li>\n' for n, p in items)
    secs += f"""  <section class="cat-section">
    <div class="wrap">
      <p class="sec-label">Stage {i:02d}</p>
      <h2>{stage}</h2>
      <p class="lede">{blurb}</p>
      <ul class="holiday-list">
{lis}      </ul>
    </div>
  </section>

"""
page("holiday.html", "Holiday Essentials — Big Nose Full Body",
     "Everything the holiday table needs from Big Nose Full Body, Park Slope — cooking wine, aperitifs, dessert bottles and port.",
     pagehead("Guides", "Holiday essentials",
       "A number of items to enhance your meal as well as your sense of goodwill, organised around the progress of the "
       "meal — from what goes in the pan to what you're still nursing in the good chair.")
     + secs + """  <section class="how">
    <div class="wrap">
      <p class="sec-label">Sorted in one trip</p>
      <h2>We'll put the box together</h2>
      <div class="njw">
        <a href="six-packs.html">Pre-built six packs <small>From $70</small></a>
        <a href="shop.html#cat=fortified">Fortified &amp; dessert <small>Port, sherry, madeira</small></a>
        <a href="tastings.html">Free delivery <small>Across Park Slope</small></a>
      </div>
    </div>
  </section>
""")

# =============================================================== SEARCHABLE TERMS
TERMS = [
 ("vegan","Vegan","Fined without animal products — no isinglass, casein or egg white."),
 ("organic","Organic","Grown without synthetic pesticides or herbicides, certified or practising."),
 ("biodynamic","Biodynamic","Organic, plus farming to the calendar and treating the vineyard as one organism."),
 ("unoaked","Unoaked","Aged in steel, concrete or old neutral barrels. Fruit and site, no vanilla."),
 ("minimal-sulfur","Minimal Sulfur","A small dose at bottling and nothing more."),
 ("no-added-sulfur","No Added Sulfur","Nothing added at all. Alive, occasionally wild, best drunk young."),
 ("natural","Natural","Native yeasts, little intervention, nothing stripped out on the way."),
 ("sustainable","Sustainable","Farmed with a long view — water, cover crops, soil left better than found."),
 ("pet-nat","Pét-Nat","Bottled before the first fermentation finishes. Cloudy, gulpable, no two the same."),
 ("kosher","Kosher","Produced under rabbinical supervision."),
]
chips = "".join(
  f"""        <a class="term" href="shop.html#tag={k}">
          <b>{label}</b>
          <span>{blurb}</span>
        </a>
""" for k, label, blurb in TERMS)
cats = "".join(
  f'        <a class="tag" href="shop.html#cat={c}">{lbl}</a>\n' for c, lbl in
  [("sparkling","Sparkling"),("white","White"),("rose","Rosé"),("orange","Orange &amp; Beyond"),
   ("red","Red"),("fortified","Fortified &amp; Dessert"),("sake","Sake &amp; Cider"),
   ("half","Half Bottles"),("alt","Boxes, Cans &amp; Cartons"),("kosher","Kosher"),
   ("dealc","De-Alcoholized"),("gift","Gift Cards")])
page("searchable-terms.html", "Searchable Terms — Big Nose Full Body",
     "How Big Nose Full Body tags every bottle — vegan, organic, biodynamic, unoaked, minimal sulfur and no added sulfur.",
     pagehead("Guides", "Searchable terms",
       "We have meticulously tagged every bottle in the shop. Search the usual suspects — a varietal like Cabernet "
       "Sauvignon, or a region like Napa or Greece — or browse by the key terms below. Each one is a live filter.")
     + f"""  <section class="cat-section">
    <div class="wrap">
      <p class="sec-label">Key terms</p>
      <h2>What the words mean</h2>
      <div class="terms-grid">
{chips}      </div>
    </div>
  </section>

  <section class="tags-band">
    <div class="wrap">
      <p class="sec-label">Or by the shelf</p>
      <h2>Browse <span class="outline">by category</span></h2>
      <div class="tags">
{cats}      </div>
      <p class="tags-note">Not just wine, either — sake and cider, a comprehensive sparkling selection, half bottles, boxes and cans, and a special selection of kosher and de-alcoholized bottles.</p>
    </div>
  </section>
""")

# ========================================================================= TERMS
page("terms.html", "Terms of Service — Big Nose Full Body",
     "Delivery zone, delivery times, order requirements, age verification and inventory notes for Big Nose Full Body online orders.",
     pagehead("Big Nose Full Body Online", "Terms of service",
       "The plain version of how online orders work — where we deliver, when, what we need from you, and what happens "
       "when a wine sells out between your order and our shelf.")
     + """  <section class="cat-section">
    <div class="wrap terms-body">
      <h2>Local delivery zone</h2>
      <p>Because we are a small shop, we can only accommodate local deliveries in Park Slope south of Union St and north of Prospect Ave. Our east–west boundary begins at 4th Avenue and ends at Prospect Park West.</p>
      <p>If you are concerned about your location as it applies to our delivery area, please give us a call at <a href="tel:+17183694030">718 369 4030</a> and we will do our best to accommodate.</p>

      <h2>Delivery times</h2>
      <p>We offer a one hour window for local delivery. Please allow one hour from time of submission to process and fill the order — if you place your order at noon, the earliest delivery time would be 1–2pm. Keep in mind that we make most deliveries on foot using a rolling hand truck, so please be patient.</p>
      <p>If your plans change and there will not be anyone home to accept the delivery, please contact the store to reschedule. Orders placed after 7:00pm will be accommodated the following afternoon; we are unable to fulfill local delivery orders past 7:00pm.</p>

      <h2>Order requirements</h2>
      <p>Orders placed for local delivery must be at least $50 or 6 bottles. Orders must be to a physical residential address. We do not deliver to the park or to locations outside our delivery zone.</p>

      <h2>Age verification</h2>
      <p>All wine orders must be placed by a person 21 years of age or older. Verification of age is required at the time of delivery. Failure to produce age verification forfeits the right to receive the order until identification is produced.</p>

      <h2>Notes about inventory</h2>
      <p>Our website is monitored to reflect changes in our inventory, but note that there may be certain items which are no longer available and have not yet been updated on the Big Nose Full Body online store. Given the high-volume nature of our business and the finite availability of some wines, please be aware that without notice there may be a vintage change or a product out-of-stock with any of the wines that you order. Should that happen, we will notify you by email or phone before your order is processed.</p>

      <p class="fine">Questions about any of this? Call <a href="tel:+17183694030">718 369 4030</a> or email <a href="mailto:wine@bignosefullbody.com">wine@bignosefullbody.com</a>.</p>
    </div>
  </section>
""")

print("generated: reserve, new-arrivals, guides, pairings, six-packs, holiday, searchable-terms, terms")
print(f"  reserve list: {len(res)} bottles | new arrivals: {len(new)} bottles")
