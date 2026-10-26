# Magic House website

Static site for Magic House Lebanon, built for GitHub Pages. Every page is generated from the JSON files in `/data` by `build.py` (Python 3.8+, no packages needed).

## Update content

1. Edit the files in `/data`.
2. Run `python3 build.py`.
3. Commit and push everything (including the regenerated HTML, `sitemap.xml`, `search.json`).

### data/site.json
| Key | What it does |
|---|---|
| `whatsappNumber` | WhatsApp number with country code, e.g. `+961 70 123 456`. **Fill this in**: until it is set, buttons fall back to `wa.link/q1vlt1` without the prefilled product message. |
| `baseUrl` | Final domain, used for canonical URLs, sitemap, and structured data. |
| `heroImage`, `aboutImage` | Paths to lifestyle photos, e.g. `/assets/img/site/hero.webp` (portrait, about 4:5). Empty shows the branded arch. |
| `email`, `location` | Shown on the contact section and in structured data only when filled. |
| `formEndpoint` | Optional form service URL (e.g. Formspree). Empty = the contact form opens WhatsApp with the message ready. |
| `faq` | Questions and answers. An FAQ with an empty `a` is hidden until you confirm the answer (location and delivery are hidden now). |

### data/collections.json
The four collections from the brief. Set `cover` to an image path (about 3:4) and `coverAlt` to a short description.

### data/products.json
One object per product. See `data/products.example.json`.

| Field | Required | Notes |
|---|---|---|
| `slug` | yes | URL name: `/products/<slug>/`. Lowercase, hyphens, unique. |
| `name` | yes | |
| `collection` | yes | `incense-burners`, `candles`, `souvenirs-gifts`, or `decorative-items` |
| `description` | | One or two sentences. |
| `images` | | List of paths; the first is the main image. Square images work best. |
| `imageAlt` | | Describes the photo for screen readers and Google. |
| `price` | | Number in USD, or `null` to hide the price. |
| `colors`, `sizes` | | Lists of text. |
| `customization` | | e.g. "Custom colors available." |
| `available` | | `false` shows "Currently unavailable". |
| `featured` | | `true` shows it on the home page (up to 8). |

### data/gallery.json
`[{"src": "/assets/img/gallery/x.webp", "alt": "...", "caption": "...", "category": "Weddings", "width": 800, "height": 1000}]`. Filters appear automatically when there are 2+ categories.

## Images
Put files in `/assets/img/products`, `/collections`, `/gallery`, `/site`. Export as WebP, about 1200 px on the long side, under 200 KB. Set `width`/`height` in gallery items to the real ratio to avoid layout shift.

## Deploy (GitHub Pages)
Settings → Pages → Deploy from branch → `main` / root. `CNAME` is set to `georgesmounzer.colartdigitalmarketingagency.com` (temporary host; switch `baseUrl` and `CNAME` to `www.magichouselb.com` at launch); at Namecheap add a CNAME record `www` → `<user>.github.io` and the four GitHub A records on `@`. For a different domain, change `baseUrl` and the `CNAME` file, then rebuild.

## Brand
Logo files: `assets/img/logo-burgundy.svg`, `logo-cream.svg`, `mark-*.svg` (from the supplied `magic_house.ai`). Colors and fonts are set at the top of `assets/css/style.css`.
