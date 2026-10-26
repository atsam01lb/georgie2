#!/usr/bin/env python3
"""Magic House static site builder.

Edit the files in /data, then run:   python3 build.py
It regenerates every HTML page, sitemap.xml, robots.txt and search.json
in the repository root, ready for GitHub Pages. No dependencies.
"""
import json, html, re, shutil, datetime
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
VERSION = datetime.datetime.now().strftime("%Y%m%d%H%M")
TODAY = datetime.date.today().isoformat()

site = json.loads((DATA / "site.json").read_text(encoding="utf-8"))
collections = json.loads((DATA / "collections.json").read_text(encoding="utf-8"))
products = json.loads((DATA / "products.json").read_text(encoding="utf-8"))
gallery = json.loads((DATA / "gallery.json").read_text(encoding="utf-8"))

BASE = site["baseUrl"].rstrip("/")
WA = re.sub(r"\D", "", site.get("whatsappNumber", ""))
COLL = {c["slug"]: c for c in collections}

# ---------- validation ----------
seen = set()
for p in products:
    for k in ("slug", "name", "collection"):
        if not p.get(k):
            raise SystemExit(f"Product is missing '{k}': {p}")
    if p["collection"] not in COLL:
        raise SystemExit(f"Product '{p['slug']}' uses unknown collection '{p['collection']}'. Use one of: {', '.join(COLL)}")
    if p["slug"] in seen:
        raise SystemExit(f"Duplicate product slug: {p['slug']}")
    seen.add(p["slug"])
    p.setdefault("images", []); p.setdefault("available", True); p.setdefault("featured", False)
    p.setdefault("colors", []); p.setdefault("sizes", [])


def esc(s):
    return html.escape(str(s or ""), quote=True)


def price_text(p):
    v = p.get("price")
    if v in (None, ""):
        return ""
    try:
        v = float(v)
        return f"${v:,.2f}".replace(".00", "")
    except (TypeError, ValueError):
        return str(v)


def wa(text=""):
    if WA:
        return f"https://wa.me/{WA}" + (f"?text={quote(text)}" if text else "")
    return site.get("whatsappFallbackLink", "#")


def wa_product(p):
    url = f"{BASE}/products/{p['slug']}/"
    return wa(f"Hello Magic House! I would like to inquire about {p['name']}.\n\n"
              f"Product: {p['name']}\nProduct Link: {url}\n\n"
              "Please provide more information about availability and ordering.")


WA_ORDER = wa("Hello Magic House! I would like to place an order.")
WA_CUSTOM = wa("Hello Magic House! I have a custom order in mind for a special occasion. Here are the details:")
WA_HELLO = wa("Hello Magic House!")

# ---------- icons (Lucide-style line icons, 24px grid) ----------
def icon(name):
    paths = {
        "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
        "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
        "x": '<path d="M18 6 6 18M6 6l12 12"/>',
        "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
        "left": '<path d="m15 18-6-6 6-6"/>',
        "right": '<path d="m9 18 6-6-6-6"/>',
        "plus": '<path d="M12 5v14M5 12h14"/>',
        "heart": '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10Z"/>',
        "sparkle": '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6.3 6.3l2.5 2.5M15.2 15.2l2.5 2.5M6.3 17.7l2.5-2.5M15.2 8.8l2.5-2.5"/>',
        "gift": '<rect x="3" y="8" width="18" height="4" rx="1"/><path d="M5 12v8h14v-8M12 8v12M12 8S10.5 4 8 4a2 2 0 0 0 0 4M12 8s1.5-4 4-4a2 2 0 0 1 0 4"/>',
        "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
        "hand": '<path d="M7 11V6a1.5 1.5 0 0 1 3 0v4M10 10V4.5a1.5 1.5 0 0 1 3 0V10M13 10V5.5a1.5 1.5 0 0 1 3 0V12M16 9.5a1.5 1.5 0 0 1 3 0V14a7 7 0 0 1-7 7h-.5a6 6 0 0 1-5-2.7L4 14.5a1.6 1.6 0 0 1 2.6-1.9L7 13"/>',
        "gem": '<path d="M6 3h12l4 6-10 12L2 9Z"/><path d="M2 9h20M12 21 8 9l4-6 4 6-4 12"/>',
        "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
        "pin": '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21Z"/><circle cx="12" cy="9.5" r="2.5"/>',
        "instagram": '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r=".8" fill="currentColor"/>',
        "tiktok": '<path d="M14 3v11.5a3.5 3.5 0 1 1-3.5-3.5M14 3c.4 2.6 2.2 4.4 5 4.7"/>',
        "whatsapp": '<path d="M4 20l1.3-3.9A8 8 0 1 1 8.2 19z"/><path d="M9 8.5c0 3.4 3 6.5 6.5 6.5l1-1.6-2-1-1 .8a4.5 4.5 0 0 1-2.2-2.2l.8-1-1-2Z"/>',
    }
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{paths[name]}</svg>')


FLOURISH = ('<svg class="flourish" viewBox="0 0 120 18" fill="none" stroke="currentColor" stroke-width="1" aria-hidden="true">'
            '<path d="M0 9h46M74 9h46"/><path d="M60 2c-4 3.5-4 10.5 0 14 4-3.5 4-10.5 0-14Z"/><path d="M60 9c-4-3-9-3-12 0 3 3 8 3 12 0Zm0 0c4-3 9-3 12 0-3 3-8 3-12 0Z"/></svg>')

FLORAL = ('<svg class="floral" viewBox="0 0 200 320" fill="none" stroke="currentColor" stroke-width="1" aria-hidden="true">'
          '<path d="M100 320C100 230 96 150 120 70"/><path d="M104 250c-26-6-44-24-48-50 26 4 44 22 48 50Z"/>'
          '<path d="M108 190c24-10 46-8 62 8-22 12-44 10-62-8Z"/><path d="M112 130c-20-12-28-32-24-54 20 12 28 32 24 54Z"/>'
          '<path d="M120 70c-6-18 0-40 18-52 6 20 0 40-18 52Z"/><circle cx="138" cy="18" r="5"/><circle cx="56" cy="200" r="3"/></svg>')


def img_tag(src, alt, cls="", w=800, h=800, lazy=True, priority=False):
    if not src:
        return ""
    attrs = f'src="{esc(src)}" alt="{esc(alt)}" width="{w}" height="{h}" decoding="async"'
    if priority:
        attrs += ' fetchpriority="high"'
    elif lazy:
        attrs += ' loading="lazy"'
    if cls:
        attrs += f' class="{cls}"'
    return f"<img {attrs}>"


def tile_fallback():
    return '<span class="tile-fallback"><img src="/assets/img/mark-burgundy.svg" alt="" width="102" height="87"></span>'


# ---------- layout ----------
NAV = [("/", "Home"), ("/collections/", "Collections"), ("/about/", "About Us"), ("/gallery/", "Gallery"), ("/contact/", "Contact")]


def head(title, desc, path, og_image=None, schema=None, noindex=False):
    url = BASE + path
    og = og_image or "/assets/img/og-default.jpg"
    og_abs = og if og.startswith("http") else BASE + og
    ld = ""
    for s in (schema or []):
        ld += f'<script type="application/ld+json">{json.dumps(s, ensure_ascii=False)}</script>\n'
    robots = '<meta name="robots" content="noindex">' if noindex else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(url)}">
{robots}
<meta name="theme-color" content="#47070D">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Magic House">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(url)}">
<meta property="og:image" content="{esc(og_abs)}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/svg+xml" href="/assets/img/mark-burgundy.svg">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/img/favicon-32.png">
<link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=DM+Sans:opsz,wght@9..40,400;9..40,500&display=swap">
<link rel="stylesheet" href="/assets/css/style.css?v={VERSION}">
<script>window.MH={json.dumps({"wa": WA, "waFallback": site.get("whatsappFallbackLink", ""), "formEndpoint": site.get("formEndpoint", "")})};</script>
{ld}</head>
"""


def header(active):
    links = "".join(
        '<li><a href="%s"%s>%s</a></li>' % (h, ' aria-current="page"' if h == active else "", t) for h, t in NAV)
    social = (f'<a class="icon-btn" href="{esc(site["instagram"])}" target="_blank" rel="noopener" aria-label="Magic House on Instagram">{icon("instagram")}</a>'
              f'<a class="icon-btn" href="{esc(site["tiktok"])}" target="_blank" rel="noopener" aria-label="Magic House on TikTok">{icon("tiktok")}</a>')
    return f"""<body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="/" aria-label="Magic House home"><img src="/assets/img/logo-burgundy.svg" alt="Magic House" width="110" height="52"></a>
    <nav class="main-nav" aria-label="Main"><ul>{links}</ul></nav>
    <div class="header-actions">
      <button class="icon-btn" type="button" data-open-search aria-label="Search products">{icon("search")}</button>
      <a class="icon-btn wa-icon" href="{esc(WA_HELLO)}" target="_blank" rel="noopener" aria-label="Chat on WhatsApp">{icon("whatsapp")}</a>
      <a class="btn btn--sm" href="{esc(WA_ORDER)}" target="_blank" rel="noopener">Order Now</a>
      <button class="icon-btn menu-toggle" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="drawer">{icon("menu")}</button>
    </div>
  </div>
</header>
<div class="drawer" id="drawer" aria-hidden="true">
  <div class="drawer__scrim" data-close-drawer></div>
  <div class="drawer__panel" role="dialog" aria-modal="true" aria-label="Menu">
    <div class="drawer__top"><img src="/assets/img/logo-burgundy.svg" alt="Magic House" width="94" height="44">
      <button class="icon-btn drawer-close" type="button" data-close-drawer aria-label="Close menu">{icon("x")}</button></div>
    <nav aria-label="Mobile"><ul>{links}</ul></nav>
    <a class="btn" href="{esc(WA_ORDER)}" target="_blank" rel="noopener">{icon("whatsapp")} Order on WhatsApp</a>
    <div class="drawer__social">{social}</div>
  </div>
</div>
<div class="search" id="search" aria-hidden="true" role="dialog" aria-modal="true" aria-label="Search products">
  <button class="icon-btn close" type="button" data-close-search aria-label="Close search">{icon("x")}</button>
  <div class="search-box">
    <label for="search-input">Search the collection</label>
    <input id="search-input" type="search" placeholder="Try candle, tray, Mary, gift…" autocomplete="off">
    <p class="search-empty" aria-live="polite"></p>
    <ul class="search-results"></ul>
  </div>
</div>
<main id="main">
"""


def footer():
    coll_links = "".join(f'<li><a href="/collections/{c["slug"]}/">{esc(c["title"])}</a></li>' for c in collections)
    quick = "".join(f'<li><a href="{h}">{t}</a></li>' for h, t in NAV)
    year = datetime.date.today().year
    return f"""</main>
<footer class="site-footer on-dark">
  <div class="wrap">
    <div class="footer-grid">
      <div>
        <img class="flogo" src="/assets/img/logo-cream.svg" alt="Magic House" width="180" height="84">
        <p>Handmade gypsum decor, candles, incense burners, and gifts, crafted in Lebanon for your home and your special occasions.</p>
        <div class="footer-social">
          <a href="{esc(site["instagram"])}" target="_blank" rel="noopener" aria-label="Instagram">{icon("instagram")}</a>
          <a href="{esc(site["tiktok"])}" target="_blank" rel="noopener" aria-label="TikTok">{icon("tiktok")}</a>
          <a href="{esc(WA_HELLO)}" target="_blank" rel="noopener" aria-label="WhatsApp">{icon("whatsapp")}</a>
        </div>
      </div>
      <div><h3>Explore</h3><ul>{quick}</ul></div>
      <div><h3>Collections</h3><ul>{coll_links}</ul></div>
      <div><h3>Order</h3><ul>
        <li><a href="{esc(WA_ORDER)}" target="_blank" rel="noopener">Order on WhatsApp</a></li>
        <li><a href="{esc(WA_CUSTOM)}" target="_blank" rel="noopener">Request a custom order</a></li>
        <li><a href="{esc(site["instagram"])}" target="_blank" rel="noopener">{esc(site["instagramHandle"])}</a></li>
      </ul></div>
    </div>
    <div class="footer-bottom"><span>&copy; {year} Magic House. All Rights Reserved.</span><a href="/privacy-policy/">Privacy Policy</a></div>
  </div>
</footer>
<a class="wa-float" href="{esc(WA_HELLO)}" target="_blank" rel="noopener" aria-label="Chat with Magic House on WhatsApp">{icon("whatsapp")}</a>
<script src="/assets/js/main.js?v={VERSION}" defer></script>
</body>
</html>
"""


def page(path, title, desc, body, active=None, og=None, schema=None, noindex=False):
    out = ROOT / path.strip("/") / "index.html" if path != "/" else ROOT / "index.html"
    if path.endswith(".html"):
        out = ROOT / path.strip("/")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(head(title, desc, path, og, schema, noindex) + header(active) + body + footer(), encoding="utf-8")


def breadcrumbs(items, left=False):
    lis = []
    for i, (name, href) in enumerate(items):
        last = i == len(items) - 1
        inner = '<span aria-current="page">%s</span>' % esc(name) if last else '<a href="%s">%s</a>' % (href, esc(name))
        lis.append("<li>" + inner + "</li>")
    schema = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": BASE + h} for i, (n, h) in enumerate(items)]}
    return f'<nav class="breadcrumbs{" breadcrumbs--left" if left else ""}" aria-label="Breadcrumb"><ol>{"".join(lis)}</ol></nav>', schema


# ---------- components ----------
def product_card(p):
    url = f"/products/{p['slug']}/"
    img = p["images"][0] if p["images"] else ""
    media = img_tag(img, p.get("imageAlt") or p["name"], w=600, h=600) if img else tile_fallback()
    pr = price_text(p)
    badge = '' if p["available"] else '<span class="badge">Currently unavailable</span>'
    return f"""<article class="product-card">
  <a class="media" href="{url}" tabindex="-1" aria-hidden="true">{media}{badge}</a>
  <div class="body">
    <h3><a href="{url}">{esc(p["name"])}</a></h3>
    {f'<p class="desc">{esc(p.get("description"))}</p>' if p.get("description") else ""}
    {f'<p class="price">{pr}</p>' if pr else ""}
    <div class="actions">
      <a class="btn btn--ghost" href="{url}">View Details</a>
      <a class="btn" href="{esc(wa_product(p))}" target="_blank" rel="noopener">{icon("whatsapp")} Order via WhatsApp</a>
    </div>
  </div>
</article>"""


def coll_count(slug):
    return sum(1 for p in products if p["collection"] == slug)


def collection_card(c):
    n = coll_count(c["slug"])
    media = img_tag(c["cover"], c.get("coverAlt") or c["title"], w=600, h=800) if c.get("cover") else tile_fallback()
    return f"""<a class="collection-card" href="/collections/{c["slug"]}/">
  <span class="media">{media}</span>
  <span class="label"><span><h3>{esc(c["title"])}</h3>{f'<span class="count">{n} piece{"s" if n != 1 else ""}</span>' if n else ""}</span>
  <span class="go">{icon("arrow")}</span></span>
</a>"""


def arch(src, alt, priority=False):
    inner = img_tag(src, alt, w=800, h=1000, priority=priority, lazy=not priority) if src else \
        '<span class="arch-fallback"><img src="/assets/img/mark-cream.svg" alt="" width="102" height="87"></span>'
    return f'<div class="arch arch--outline">{inner}</div>'


def faq_html(items):
    items = [f for f in items if f.get("a")]
    if not items:
        return "", None
    body = "".join(f'<details><summary>{esc(f["q"])}{icon("plus")}</summary><p>{esc(f["a"])}</p></details>' for f in items)
    schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in items]}
    return f"""<section class="section" aria-labelledby="faq-title"><div class="wrap">
  <div class="section-head reveal">{FLOURISH}<h2 id="faq-title">Questions, Answered</h2><p>What people usually ask before ordering.</p></div>
  <div class="faq reveal">{body}</div></div></section>""", schema


def cta_band():
    return f"""<section class="section cta-band on-dark" aria-labelledby="custom-title">
  <span class="ring ring--l" aria-hidden="true"></span><span class="ring ring--r" aria-hidden="true"></span>
  <div class="wrap reveal">
    <h2 id="custom-title">Have Something Special in Mind?</h2>
    <p>Let Magic House help you create something beautiful for your special occasion.</p>
    <a class="btn btn--light" href="{esc(WA_CUSTOM)}" target="_blank" rel="noopener">{icon("whatsapp")} Request a Custom Order</a>
  </div>
</section>"""


def masonry(items, filters=False):
    if not items:
        return ""
    cats = sorted({g.get("category") for g in items if g.get("category")})
    fbar = ""
    if filters and len(cats) > 1:
        fbar = '<div class="filters" role="group" aria-label="Filter gallery"><button type="button" data-filter="all" aria-pressed="true">All</button>' + \
               "".join(f'<button type="button" data-filter="{esc(c)}" aria-pressed="false">{esc(c)}</button>' for c in cats) + "</div>"
    figs = ""
    for g in items:
        w, h = g.get("width", 800), g.get("height", 1000)
        figs += (f'<figure data-cat="{esc(g.get("category", ""))}"><button type="button" data-full="{esc(g["src"])}" aria-label="Open image: {esc(g.get("alt", ""))}">'
                 f'{img_tag(g.get("thumb") or g["src"], g.get("alt", ""), w=w, h=h)}</button>'
                 + ("<figcaption>%s</figcaption>" % esc(g.get("caption")) if g.get("caption") else "") + "</figure>")
    return f'<div>{fbar}<div class="masonry" data-gallery>{figs}</div></div>'


LIGHTBOX = f"""<div class="lightbox" id="lightbox" aria-hidden="true" role="dialog" aria-modal="true" aria-label="Image viewer">
  <button class="icon-btn lb-close" type="button" aria-label="Close">{icon("x")}</button>
  <button class="icon-btn lb-prev" type="button" aria-label="Previous image">{icon("left")}</button>
  <img src="" alt="">
  <button class="icon-btn lb-next" type="button" aria-label="Next image">{icon("right")}</button>
  <p class="lb-caption"></p>
</div>"""

ORG = {"@context": "https://schema.org", "@type": "Organization", "name": "Magic House", "alternateName": site["legalName"],
       "url": BASE + "/", "logo": BASE + "/assets/img/icon-512.png", "sameAs": [site["instagram"], site["tiktok"]],
       "description": "Handmade gypsum decor, candles, incense burners, souvenirs, and gifts from Lebanon."}
if site.get("email"):
    ORG["email"] = site["email"]
if WA:
    ORG["contactPoint"] = {"@type": "ContactPoint", "telephone": "+" + WA, "contactType": "sales", "availableLanguage": ["en", "ar"]}

# ---------- clean previous output ----------
for d in ("collections", "products", "about", "gallery", "contact", "privacy-policy"):
    shutil.rmtree(ROOT / d, ignore_errors=True)

featured = [p for p in products if p["featured"]][:8] or products[:8]

# ---------- HOME ----------
coll_cards = "".join(collection_card(c) for c in collections)
featured_html = ""
if featured:
    featured_html = f"""<section class="section" aria-labelledby="featured-title"><div class="wrap">
  <div class="section-head reveal">{FLOURISH}<h2 id="featured-title">Made to Be Loved</h2><p>Discover some of our favorite handmade creations.</p></div>
  <div class="product-grid">{"".join(product_card(p) for p in featured)}</div></div></section>"""

gallery_preview = ""
if gallery:
    gallery_preview = f"""<section class="section section--beige" aria-labelledby="glimpse-title"><div class="wrap">
  <div class="section-head reveal">{FLOURISH}<h2 id="glimpse-title">A Glimpse of Magic</h2><p>Arrangements, gift packaging, custom pieces, and the small details.</p></div>
  {masonry(gallery[:8])}
  <p class="center-link"><a class="btn btn--ghost" href="/gallery/">View Gallery</a></p></div></section>{LIGHTBOX}"""

faq_block, faq_schema = faq_html(site["faq"])

contact_items = f"""<li><a href="{esc(WA_HELLO)}" target="_blank" rel="noopener"><span class="ci">{icon("whatsapp")}</span><span><small>WhatsApp</small>Chat with us to order</span></a></li>
<li><a href="{esc(site["instagram"])}" target="_blank" rel="noopener"><span class="ci">{icon("instagram")}</span><span><small>Instagram</small>{esc(site["instagramHandle"])}</span></a></li>
<li><a href="{esc(site["tiktok"])}" target="_blank" rel="noopener"><span class="ci">{icon("tiktok")}</span><span><small>TikTok</small>{esc(site["instagramHandle"])}</span></a></li>"""
if site.get("email"):
    contact_items += f'<li><a href="mailto:{esc(site["email"])}"><span class="ci">{icon("mail")}</span><span><small>Email</small>{esc(site["email"])}</span></a></li>'
if site.get("location"):
    contact_items += f'<li><span><span class="ci">{icon("pin")}</span><span><small>Location</small>{esc(site["location"])}</span></span></li>'

CONTACT_FORM = f"""<form class="form" id="contact-form" novalidate>
  <div class="form-row">
    <div class="field"><label for="f-name">Full Name</label><input id="f-name" name="name" autocomplete="name" required aria-describedby="e-name"><p class="err" id="e-name" aria-live="polite"></p></div>
    <div class="field"><label for="f-phone">Phone Number</label><input id="f-phone" name="phone" type="tel" inputmode="tel" autocomplete="tel" required aria-describedby="e-phone"><p class="err" id="e-phone" aria-live="polite"></p></div>
  </div>
  <div class="field"><label for="f-email">Email <span style="font-weight:400;color:var(--muted)">(optional)</span></label><input id="f-email" name="email" type="email" autocomplete="email" aria-describedby="e-email"><p class="err" id="e-email" aria-live="polite"></p></div>
  <div class="field"><label for="f-msg">Message</label><textarea id="f-msg" name="message" required aria-describedby="e-msg" placeholder="Tell us the piece, occasion, colors, and quantity you have in mind."></textarea><p class="err" id="e-msg" aria-live="polite"></p></div>
  <div class="hp" aria-hidden="true"><label for="f-co">Company</label><input id="f-co" name="company" tabindex="-1" autocomplete="off"></div>
  <button class="btn" type="submit">Send message</button>
  <p class="form-status" role="status" aria-live="polite"></p>
  <p class="form-note">{"Your message is sent to our team by email." if site.get("formEndpoint") else "Sending opens WhatsApp with your message ready, so we can reply right away."}</p>
</form>"""

home = f"""
<section class="hero"><div class="wrap hero-grid">
  <div class="hero-copy">
    <span class="eyebrow">Handmade gypsum collections</span>
    <h1>More Than Decor</h1>
    <p class="subtitle">It&rsquo;s a Feeling</p>
    <p class="lede">Handcrafted gypsum creations, candles, and decorative pieces designed to add a special touch to your home, celebrations, and every beautiful occasion.</p>
    <div><a class="btn" href="/collections/">Explore Collections {icon("arrow")}</a></div>
    <ul class="hero-points">
      <li>{icon("hand")}Handmade with Love</li>
      <li>{icon("gem")}Unique Designs</li>
      <li>{icon("calendar")}Perfect for Every Occasion</li>
    </ul>
  </div>
  <div class="hero-visual">{arch(site.get("heroImage"), site.get("heroImageAlt") or "Magic House handmade gypsum pieces", priority=True)}</div>
</div></section>

<section class="section section--tight" aria-labelledby="collections-title"><div class="wrap">
  <div class="section-head reveal">{FLOURISH}<h2 id="collections-title">Our Collections</h2><p>Explore our handcrafted collections, thoughtfully designed to make every moment special.</p></div>
  <div class="collection-grid reveal">{coll_cards}</div>
  <p class="center-link"><a class="link-arrow" href="/collections/">View All Collections {icon("arrow")}</a></p>
</div></section>

<section class="section section--beige about-band" aria-labelledby="about-title">{FLORAL}<div class="wrap split">
  <div class="reveal">{arch(site.get("aboutImage"), site.get("aboutImageAlt") or "Handmade gypsum decor by Magic House")}</div>
  <div class="reveal">
    <span class="eyebrow">About Magic House</span>
    <h2 id="about-title">Handmade Creations for a More Beautiful World</h2>
    <p>At Magic House, we believe in the beauty of details. Our handcrafted gypsum collections are designed to bring elegance, warmth, and a unique touch to your spaces and special occasions.</p>
    <a class="link-arrow" href="/about/">Learn More {icon("arrow")}</a>
  </div>
</div></section>

{featured_html}

<section class="section{" section--beige" if not featured else ""}" aria-labelledby="why-title"><div class="wrap">
  <div class="section-head reveal">{FLOURISH}<h2 id="why-title">The Magic Is in the Details</h2></div>
  <ul class="advantages reveal">
    <li><span class="advantage-icon">{icon("hand")}</span><h3>Handcrafted with Care</h3><p>Every creation is made with attention to detail.</p></li>
    <li><span class="advantage-icon">{icon("gem")}</span><h3>Unique &amp; Elegant</h3><p>Thoughtful designs for beautiful spaces.</p></li>
    <li><span class="advantage-icon">{icon("gift")}</span><h3>Perfect for Gifting</h3><p>Special creations for meaningful occasions.</p></li>
    <li><span class="advantage-icon">{icon("sparkle")}</span><h3>Made for Every Moment</h3><p>Decorative pieces for everyday beauty and celebrations.</p></li>
  </ul>
</div></section>

{gallery_preview}
{cta_band()}
{faq_block}

<section class="section section--beige" id="contact" aria-labelledby="contact-title"><div class="wrap contact-grid">
  <div class="reveal"><h2 id="contact-title" style="font-size:var(--step-3)">Let&rsquo;s Create Something Magical</h2>
    <p style="color:var(--muted)">Message us to order a piece, ask about colors and sizes, or plan a custom set for your occasion.</p>
    <ul class="contact-list">{contact_items}</ul></div>
  <div class="reveal">{CONTACT_FORM}</div>
</div></section>
"""
website_schema = {"@context": "https://schema.org", "@type": "WebSite", "name": "Magic House", "url": BASE + "/"}
page("/", "Magic House Lebanon | Handmade Gypsum Decor, Candles & Gifts",
     "Discover handmade gypsum decorations, elegant candles, incense burners, and unique gifts at Magic House Lebanon. Explore our collections and order online.",
     home, "/", schema=[s for s in (ORG, website_schema, faq_schema) if s])

# ---------- COLLECTIONS INDEX ----------
rows = ""
for c in collections:
    n = coll_count(c["slug"])
    media = img_tag(c["cover"], c.get("coverAlt") or c["title"], w=800, h=600) if c.get("cover") else tile_fallback()
    rows += f"""<article class="collection-row reveal">
  <a class="media" href="/collections/{c["slug"]}/" tabindex="-1" aria-hidden="true">{media}</a>
  <div class="text"><h2><a href="/collections/{c["slug"]}/" style="text-decoration:none">{esc(c["title"])}</a></h2>
    {f'<p class="meta">{n} piece{"s" if n != 1 else ""}</p>' if n else ""}
    <p>{esc(c["description"])}</p>
    <a class="btn btn--ghost" href="/collections/{c["slug"]}/">Explore {esc(c["title"])} {icon("arrow")}</a></div>
</article>"""
bc, bc_schema = breadcrumbs([("Home", "/"), ("Collections", "/collections/")])
itemlist = {"@context": "https://schema.org", "@type": "ItemList", "name": "Magic House collections", "itemListElement": [
    {"@type": "ListItem", "position": i + 1, "name": c["title"], "url": f"{BASE}/collections/{c['slug']}/"} for i, c in enumerate(collections)]}
page("/collections/", "Collections | Magic House Lebanon",
     "Browse Magic House collections: handmade gypsum incense burners, candles, souvenirs and gifts, and decorative items, made in Lebanon.",
     f"""<section class="page-hero"><div class="wrap">{bc}<h1>Our Collections</h1>
<p>Every collection is cast and finished by hand. Choose a collection to see its pieces, then order the ones you love on WhatsApp.</p></div></section>
<section class="section" style="padding-top:0"><div class="wrap collection-rows">{rows}</div></section>{cta_band()}""",
     "/collections/", schema=[bc_schema, itemlist])

# ---------- INDIVIDUAL COLLECTIONS ----------
for c in collections:
    items = [p for p in products if p["collection"] == c["slug"]]
    path = f"/collections/{c['slug']}/"
    bc, bc_schema = breadcrumbs([("Home", "/"), ("Collections", "/collections/"), (c["title"], path)])
    if items:
        grid = f'<div class="product-grid" data-paginate="12">{"".join(product_card(p) for p in items)}</div>'
    else:
        grid = f"""<div class="empty-note"><h3>New pieces coming soon</h3>
<p>We are photographing this collection now. Message us on WhatsApp to ask about what is available today.</p>
<a class="btn" href="{esc(wa(f"Hello Magic House! What do you have available in {c['title']}?"))}" target="_blank" rel="noopener">{icon("whatsapp")} Ask on WhatsApp</a></div>"""
    il = {"@context": "https://schema.org", "@type": "ItemList", "name": c["title"], "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "url": f"{BASE}/products/{p['slug']}/", "name": p["name"]} for i, p in enumerate(items)]}
    page(path, f"{c['title']} | Handmade by Magic House Lebanon", c["description"],
         f"""<section class="page-hero"><div class="wrap">{bc}<h1>{esc(c["title"])}</h1><p>{esc(c["description"])}</p></div></section>
<section class="section" style="padding-top:0"><div class="wrap">{grid}</div></section>{cta_band()}""",
         "/collections/", og=c.get("cover") or None, schema=[bc_schema, il])

# ---------- PRODUCT PAGES ----------
for p in products:
    c = COLL[p["collection"]]
    path = f"/products/{p['slug']}/"
    bc, bc_schema = breadcrumbs([("Home", "/"), (c["title"], f"/collections/{c['slug']}/"), (p["name"], path)], left=True)
    alt = p.get("imageAlt") or p["name"]
    if p["images"]:
        main = img_tag(p["images"][0], alt, w=1000, h=1000, priority=True)
        thumbs = ""
        if len(p["images"]) > 1:
            thumbs = '<div class="thumbs">' + "".join(
                f'<button type="button" data-src="{esc(src)}" aria-current="{"true" if i == 0 else "false"}" aria-label="Show image {i + 1}">{img_tag(src, "", w=78, h=78)}</button>'
                for i, src in enumerate(p["images"])) + "</div>"
    else:
        main, thumbs = tile_fallback(), ""
    specs = f'<li><span>Collection</span><span><a href="/collections/{c["slug"]}/">{esc(c["title"])}</a></span></li>'
    if p["colors"]:
        specs += f'<li><span>Colors</span><span>{esc(", ".join(p["colors"]))}</span></li>'
    if p["sizes"]:
        specs += f'<li><span>Sizes</span><span>{"<br>".join(esc(s) for s in p["sizes"])}</span></li>'
    if p.get("customization"):
        specs += f'<li><span>Customization</span><span>{esc(p["customization"])}</span></li>'
    pr = price_text(p)
    related = [x for x in products if x["collection"] == p["collection"] and x["slug"] != p["slug"]][:4]
    if len(related) < 4:
        related += [x for x in products if x["slug"] != p["slug"] and x not in related][:4 - len(related)]
    rel_html = ""
    if related:
        rel_html = f"""<section class="section section--beige" aria-labelledby="rel-title"><div class="wrap">
<div class="section-head">{FLOURISH}<h2 id="rel-title">You May Also Love</h2></div>
<div class="product-grid">{"".join(product_card(x) for x in related)}</div></div></section>"""
    prod_schema = {"@context": "https://schema.org", "@type": "Product", "name": p["name"], "category": c["title"],
                   "brand": {"@type": "Brand", "name": "Magic House"}, "url": BASE + path}
    if p.get("description"):
        prod_schema["description"] = p["description"]
    if p["images"]:
        prod_schema["image"] = [i if i.startswith("http") else BASE + i for i in p["images"]]
    if p.get("price") not in (None, ""):
        try:
            prod_schema["offers"] = {"@type": "Offer", "price": f'{float(p["price"]):.2f}', "priceCurrency": site.get("currency", "USD"),
                                     "availability": "https://schema.org/InStock" if p["available"] else "https://schema.org/OutOfStock",
                                     "url": BASE + path}
        except (TypeError, ValueError):
            pass
    desc = p.get("description") or f"{p['name']}, handmade gypsum piece from the Magic House {c['title']} collection. Order via WhatsApp."
    body = f"""<div class="wrap" style="padding-top:1.5rem">{bc}</div>
<div class="wrap pdp">
  <div class="pdp-gallery"><div class="main">{main}</div>{thumbs}</div>
  <div class="pdp-info">
    <a class="cat" href="/collections/{c["slug"]}/">{esc(c["title"])}</a>
    <h1>{esc(p["name"])}</h1>
    {f'<p class="price">{pr}</p>' if pr else ""}
    {'' if p["available"] else '<p class="availability">Currently unavailable. Message us to ask when it will be back, or to order a similar piece.</p>'}
    {f'<p class="desc">{esc(p["description"])}</p>' if p.get("description") else ""}
    <ul class="spec">{specs}</ul>
    <a class="btn" href="{esc(wa_product(p))}" target="_blank" rel="noopener">{icon("whatsapp")} Order via WhatsApp</a>
    <a class="btn btn--ghost" href="{esc(WA_CUSTOM)}" target="_blank" rel="noopener">Ask about a custom version</a>
  </div>
</div>
{rel_html}"""
    page(path, f"{p['name']} | Magic House Lebanon", desc[:158], body, "/collections/",
         og=p["images"][0] if p["images"] else None, schema=[bc_schema, prod_schema])

# ---------- ABOUT ----------
bc, bc_schema = breadcrumbs([("Home", "/"), ("About Us", "/about/")])
faq_block, faq_schema = faq_html(site["faq"])
page("/about/", "About Magic House | Handmade Gypsum Decor from Lebanon",
     "Magic House is a Lebanese brand of handmade gypsum decor, candles, incense burners, souvenirs, and gifts, crafted by hand for homes and special occasions.",
     f"""<section class="page-hero"><div class="wrap">{bc}<h1>About Magic House</h1>
<p>Handmade creations for a more beautiful world.</p></div></section>
<section class="section" style="padding-top:0"><div class="wrap split">
  <div class="reveal">{arch(site.get("aboutImage"), site.get("aboutImageAlt") or "Handmade gypsum decor by Magic House")}</div>
  <div class="reveal">
    <h2>The beauty is in the details</h2>
    <p>Magic House is a Lebanese brand of handmade decorative pieces. We cast and finish gypsum by hand to make incense burners and boxes, candles and candle holders, decorative trays, coasters, souvenirs, and gift sets.</p>
    <p>Because every piece is made by hand, no two are exactly alike. Many designs can be made in the colors you choose, and we put together sets for weddings, baptisms, baby showers, Mother&rsquo;s Day, holidays, and corporate gifts.</p>
    <p>Ordering is simple: pick a piece, tap Order via WhatsApp, and we confirm availability and delivery with you directly.</p>
    <a class="btn" href="/collections/">Explore Collections {icon("arrow")}</a>
  </div>
</div></section>
<section class="section section--beige"><div class="wrap">
  <div class="section-head reveal">{FLOURISH}<h2>The Magic Is in the Details</h2></div>
  <ul class="advantages reveal">
    <li><span class="advantage-icon">{icon("hand")}</span><h3>Handcrafted with Care</h3><p>Every creation is made with attention to detail.</p></li>
    <li><span class="advantage-icon">{icon("gem")}</span><h3>Unique &amp; Elegant</h3><p>Thoughtful designs for beautiful spaces.</p></li>
    <li><span class="advantage-icon">{icon("gift")}</span><h3>Perfect for Gifting</h3><p>Special creations for meaningful occasions.</p></li>
    <li><span class="advantage-icon">{icon("sparkle")}</span><h3>Made for Every Moment</h3><p>Decorative pieces for everyday beauty and celebrations.</p></li>
  </ul></div></section>
{faq_block}{cta_band()}""", "/about/", schema=[s for s in (bc_schema, faq_schema) if s])

# ---------- GALLERY ----------
bc, bc_schema = breadcrumbs([("Home", "/"), ("Gallery", "/gallery/")])
gal_body = masonry(gallery, filters=True) + LIGHTBOX if gallery else f"""<div class="empty-note"><h3>The gallery is on its way</h3>
<p>New photos of our pieces are being added. Follow us on Instagram to see the latest creations.</p>
<a class="btn" href="{esc(site["instagram"])}" target="_blank" rel="noopener">{icon("instagram")} {esc(site["instagramHandle"])}</a></div>"""
page("/gallery/", "Gallery | Magic House Lebanon",
     "See Magic House handmade gypsum pieces, decorative arrangements, gift packaging, and custom creations.",
     f"""<section class="page-hero"><div class="wrap">{bc}<h1>A Glimpse of Magic</h1>
<p>Collections, arrangements, gift packaging, and custom pieces, up close.</p></div></section>
<section class="section" style="padding-top:0"><div class="wrap">{gal_body}</div></section>{cta_band()}""",
     "/gallery/", schema=[bc_schema])

# ---------- CONTACT ----------
bc, bc_schema = breadcrumbs([("Home", "/"), ("Contact", "/contact/")])
page("/contact/", "Contact Magic House | Order on WhatsApp",
     "Contact Magic House Lebanon to order handmade gypsum decor, candles, and gifts, or to request a custom piece for your occasion.",
     f"""<section class="page-hero"><div class="wrap">{bc}<h1>Let&rsquo;s Create Something Magical</h1>
<p>Order a piece, ask about colors and sizes, or plan a custom set. WhatsApp is the fastest way to reach us.</p></div></section>
<section class="section" style="padding-top:0"><div class="wrap contact-grid">
  <div><h2 style="font-size:var(--step-2)">Reach us</h2><ul class="contact-list">{contact_items}</ul></div>
  <div>{CONTACT_FORM}</div>
</div></section>""", "/contact/", schema=[bc_schema, ORG])

# ---------- PRIVACY ----------
bc, bc_schema = breadcrumbs([("Home", "/"), ("Privacy Policy", "/privacy-policy/")])
page("/privacy-policy/", "Privacy Policy | Magic House Lebanon", "How Magic House handles the information you share when you contact us or place an order.",
     f"""<section class="page-hero"><div class="wrap">{bc}<h1>Privacy Policy</h1><p>Last updated {datetime.date.today().strftime("%B %d, %Y")}</p></div></section>
<section class="section" style="padding-top:0"><div class="wrap prose">
<p>This website is a catalog. You cannot pay on it, and it does not create accounts.</p>
<h2>Information you share with us</h2>
<p>When you order through WhatsApp or send the contact form, you share your name, phone number, optional email address, and message. We use this only to answer you, prepare your order, and arrange delivery.</p>
<h2>WhatsApp</h2>
<p>Order buttons open WhatsApp, which is run by Meta. Messages you send there are covered by WhatsApp&rsquo;s own privacy policy.</p>
<h2>Cookies and analytics</h2>
<p>This website does not set advertising cookies. Fonts are loaded from Google Fonts, which may receive your IP address when the page loads.</p>
<h2>Sharing</h2>
<p>We do not sell your information. We share it only with a delivery partner when needed to deliver your order.</p>
<h2>Your choices</h2>
<p>You can ask us at any time to see, correct, or delete the information you have sent us. Message us on WhatsApp or Instagram ({esc(site["instagramHandle"])}).</p>
</div></section>""", schema=[bc_schema])

# ---------- 404 ----------
page("/404.html", "Page not found | Magic House", "This page does not exist.",
     f"""<section class="notfound"><div class="wrap"><p class="num" aria-hidden="true">404</p>
<h1>This page is not here</h1><p style="color:var(--muted)">The link may be old, or the piece may have moved to another collection.</p>
<p style="display:flex;gap:.6rem;justify-content:center;flex-wrap:wrap;margin-top:1.6rem">
<a class="btn" href="/collections/">Browse collections</a><a class="btn btn--ghost" href="/">Go to the home page</a></p></div></section>""",
     noindex=True)

# ---------- search index, sitemap, robots ----------
(ROOT / "search.json").write_text(json.dumps([
    {"n": p["name"], "u": f"/products/{p['slug']}/", "c": COLL[p["collection"]]["title"], "d": p.get("description", ""),
     "i": p["images"][0] if p["images"] else "", "p": price_text(p)} for p in products], ensure_ascii=False), encoding="utf-8")

urls = ["/", "/collections/", "/about/", "/gallery/", "/contact/", "/privacy-policy/"] + \
       [f"/collections/{c['slug']}/" for c in collections] + [f"/products/{p['slug']}/" for p in products]
(ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    "".join(f"  <url><loc>{BASE}{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
(ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n", encoding="utf-8")
cname = re.sub(r"^https?://", "", BASE)
if not (ROOT / "CNAME").exists():
    (ROOT / "CNAME").write_text(cname + "\n", encoding="utf-8")
(ROOT / ".nojekyll").write_text("", encoding="utf-8")

print(f"Built {len(urls) + 1} pages: {len(collections)} collections, {len(products)} products, {len(gallery)} gallery images.")
if not WA:
    print("Note: whatsappNumber is empty in data/site.json, so order buttons use the fallback link without the prefilled message.")
