#!/usr/bin/env python3
"""
Key2Nest — Digital Business Card generator.

Single source of truth for the team member "digital business card" pages that
are accessed via QR codes printed on physical cards. Running this script
regenerates, for every person in PEOPLE:

    <slug>/index.html   the premium mobile-first card page
    vcards/<slug>.vcf   a Save-to-Contacts file (vCard 3.0, photo embedded)
    qr/<slug>.svg       a crisp vector QR pointing at the card URL
    qr/<slug>.png       a print-ready raster QR (same payload)

Everything inherits the Key2Nest Rev 10 design system (navy / 22K gold / ivory,
Source Serif 4 + Source Sans 3) so the cards feel native to the brand.

Usage:
    python3 build.py                       # uses BASE_URL below
    python3 build.py --base-url https://cards.example.com
                                           # override the QR / canonical host

IMPORTANT — QR payload: the QR codes encode  BASE_URL + "/" + slug.  Set
BASE_URL (or pass --base-url) to the host the cards are actually deployed to
BEFORE printing any QR codes, then re-run this script.
"""

import argparse
import base64
import html
import json
import re
from pathlib import Path

import segno

ROOT = Path(__file__).resolve().parent

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
# The host the printed QR codes should point to. These cards are, for now,
# deployed INDEPENDENTLY of the main marketing site. The slugs are chosen so
# they migrate cleanly to the main domain later (e.g. /vivek -> /team/vivek).
BASE_URL = "https://key2nesthomeloans.com"

COMPANY = {
    "name": "Key2Nest Home Loans LLC",
    "nmls": "2819804",
    "nmls_url": "https://www.nmlsconsumeraccess.org/EntityDetails.aspx/COMPANY/2819804",
    "states": "Licensed in Alabama, Arkansas, Florida & Texas",
    "apply_url": "https://key2nesthomeloans.com/#contact",
    "site_url": "https://key2nesthomeloans.com",
}

# One entry per team member. Extend freely — the generator does the rest.
PEOPLE = [
    {
        "slug": "vivek",
        "name": "Sai Vivek Boddu",
        "first": "Sai Vivek", "last": "Boddu",
        "title": "Co-Founder / Sr. Mortgage Loan Originator",
        "nmls": "2331676",
        "photo": "Vivek.jpeg",
        "phone": "+18643597122", "phone_display": "+1 (864) 359-7122",
        "email": "vivek.boddu@key2nesthomeloans.com",
        "whatsapp": "18643597122",
        "bio": "A seasoned mortgage loan originator known for being exceptionally responsive — guiding first-time buyers, refinances, and investors through every step with clear, patient communication.",
    },
    {
        "slug": "naveen",
        "name": "Naveen Cheedhalla",
        "first": "Naveen", "last": "Cheedhalla",
        "title": "Co-Founder / Sr. Mortgage Loan Originator",
        "nmls": "2666486",
        "photo": "Naveen.jpeg",
        "phone": "+13095335169", "phone_display": "+1 (309) 533-5169",
        "email": "naveen.cheedhalla@key2nesthomeloans.com",
        "whatsapp": "13095335169",
        "bio": "Attentive guidance and competitive loan options for a seamless mortgage experience. A certified Top 1% Partner and Best of the Best Loan Officer with a nation-leading lender.",
    },
    {
        "slug": "sreedhar",
        "name": "Sreedhar Seelam",
        "first": "Sreedhar", "last": "Seelam",
        "title": "Co-Founder / Sr. Mortgage Loan Originator",
        "nmls": "2085620",
        "photo": "Sreedhar.jpeg",
        "phone": "+19016049299", "phone_display": "+1 (901) 604-9299",
        "email": "sreedhar@key2nesthomeloans.com",
        "whatsapp": "19016049299",
        "bio": "Seasoned across both residential and commercial financing, including builders navigating shifting markets. Known for quick, accurate guidance when timing matters most.",
    },
    {
        "slug": "lakshmi",
        "name": "Sreelakshmi Jasti",
        "first": "Sreelakshmi", "last": "Jasti",
        "title": "Co-Founder / Sr. Mortgage Loan Originator",
        "nmls": "2565439",
        "photo": "Lakshmi.jpeg",
        "phone": "+14699706522", "phone_display": "+1 (469) 970-6522",
        "email": "sreelakshmi@key2nesthomeloans.com",
        "whatsapp": "14699706522",
        "bio": "A Top Performer with a leading national lender — knowledgeable guidance and competitive options across all loan types, with prompt, clear, patient communication.",
    },
    {
        "slug": "rj",
        "name": "(RJ) Venkata Rajaneesh Jandhyam",
        "first": "Venkata Rajaneesh", "last": "Jandhyam",
        "title": "Co-Founder / Sr. Mortgage Loan Originator",
        "nmls": "2142434",
        "photo": "Rajaneesh_new.jpeg",
        "phone": "+15085728811", "phone_display": "+1 (508) 572-8811",
        "email": "rj@key2nesthomeloans.com",
        "whatsapp": "15085728811",
        "bio": "Extensive experience across all mortgage types, having closed millions in loans — bringing seasoned execution and broad lender knowledge to every file.",
    },
]

# --------------------------------------------------------------------------
# vCard 3.0
# --------------------------------------------------------------------------
def build_vcard(p, card_url):
    """vCard 3.0 with an embedded portrait so the saved contact shows a photo."""
    photo_path = ROOT / "assets" / p["photo"]
    photo_line = ""
    if photo_path.exists():
        b64 = base64.b64encode(photo_path.read_bytes()).decode("ascii")
        # Fold long base64 per RFC 2426 (75-octet lines, leading space on folds).
        chunks = [b64[i:i + 74] for i in range(0, len(b64), 74)]
        photo_line = "PHOTO;ENCODING=b;TYPE=JPEG:" + chunks[0]
        for c in chunks[1:]:
            photo_line += "\r\n " + c
        photo_line += "\r\n"

    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"N:{p['last']};{p['first']};;;",
        f"FN:{p['name']}",
        f"ORG:{COMPANY['name']}",
        f"TITLE:{p['title']}",
        f"TEL;TYPE=CELL,VOICE:{p['phone']}",
        f"EMAIL;TYPE=WORK,INTERNET:{p['email']}",
        f"URL:{card_url}",
        f"NOTE:NMLS #{p['nmls']} · {COMPANY['name']} NMLS #{COMPANY['nmls']} · {COMPANY['states']}",
    ]
    body = "\r\n".join(lines) + "\r\n"
    if photo_line:
        body += photo_line
    body += "END:VCARD\r\n"
    return body


# --------------------------------------------------------------------------
# Card page template
# --------------------------------------------------------------------------
def esc(s):
    return html.escape(s, quote=True)


ICONS = {
    "call": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.79 19.79 0 0 1 2.12 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>',
    "text": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>',
    "email": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg>',
    "whatsapp": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>',
}
CHEV = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="m9 6 6 6-6 6"/></svg>'


def build_contact_rows(p):
    """Refined grouped contact panel — one elegant row per channel."""
    rows = [
        ("call", "Call", p["phone_display"], f"tel:{p['phone']}", ""),
        ("text", "Text", "Send a message", f"sms:{p['phone']}", ""),
        ("email", "Email", p["email"], f"mailto:{p['email']}", ""),
    ]
    if p.get("whatsapp"):
        rows.append(("whatsapp", "WhatsApp", "Chat on WhatsApp",
                     f"https://wa.me/{p['whatsapp']}", ' target="_blank" rel="noopener"'))
    html_rows = []
    for key, label, value, href, attrs in rows:
        html_rows.append(f'''      <a class="row" href="{href}"{attrs} aria-label="{label} {esc(p['name'])}">
        <span class="row-ic" aria-hidden="true">{ICONS[key]}</span>
        <span class="row-main">
          <span class="row-label">{label}</span>
          <span class="row-value">{esc(value)}</span>
        </span>
        <span class="row-chev" aria-hidden="true">{CHEV}</span>
      </a>''')
    return "\n".join(html_rows)


def build_page(p, card_url):
    # "Co-Founder / Sr. Mortgage Loan Originator" → eyebrow + role, presented cleanly.
    if " / " in p["title"]:
        eyebrow, role = [s.strip() for s in p["title"].split(" / ", 1)]
    else:
        eyebrow, role = "", p["title"]
    contact_rows = build_contact_rows(p)

    meta_desc = f"{esc(p['name'])} — {esc(p['title'])} at {esc(COMPANY['name'])}. NMLS #{p['nmls']}. Save contact, call, text, or email directly."

    return f'''<!doctype html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <meta name="theme-color" content="#0B1A2E" media="(prefers-color-scheme: dark)" />
  <meta name="theme-color" content="#F4EFE3" media="(prefers-color-scheme: light)" />
  <meta name="description" content="{meta_desc}" />
  <meta name="format-detection" content="telephone=no" />
  <title>{esc(p['name'])} — {esc(COMPANY['name'])}</title>

  <link rel="icon" href="../assets/favicon.ico" sizes="any" />
  <link rel="icon" type="image/svg+xml" href="../assets/favicon.svg" />
  <link rel="icon" type="image/png" sizes="32x32" href="../assets/favicon-32.png" />
  <link rel="apple-touch-icon" sizes="180x180" href="../assets/apple-touch-icon.png" />
  <link rel="canonical" href="{esc(card_url)}" />

  <meta property="og:type" content="profile" />
  <meta property="og:title" content="{esc(p['name'])} — {esc(COMPANY['name'])}" />
  <meta property="og:description" content="{meta_desc}" />
  <meta property="og:image" content="{esc(BASE_URL)}/assets/{esc(p['photo'])}" />
  <meta property="og:url" content="{esc(card_url)}" />
  <meta name="twitter:card" content="summary" />

  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:ital,wght@0,300..700;1,300..700&family=Source+Serif+4:ital,opsz,wght@0,8..60,300..700;1,8..60,300..700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../card.css" />

  <script>
    // No-flash theme: follow the OS, honor a saved manual override.
    (function () {{
      try {{
        var t = localStorage.getItem('k2n-theme');
        document.documentElement.dataset.theme =
          t || (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
      }} catch (e) {{ document.documentElement.dataset.theme = 'dark'; }}
    }})();
  </script>

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Person",
    "name": "{esc(p['name'])}",
    "jobTitle": "{esc(p['title'])}",
    "telephone": "{p['phone']}",
    "email": "{p['email']}",
    "image": "{esc(BASE_URL)}/assets/{esc(p['photo'])}",
    "url": "{esc(card_url)}",
    "identifier": "NMLS #{p['nmls']}",
    "worksFor": {{
      "@type": "Organization",
      "name": "{esc(COMPANY['name'])}",
      "identifier": "NMLS #{COMPANY['nmls']}",
      "url": "{esc(COMPANY['site_url'])}"
    }}
  }}
  </script>
</head>
<body>
  <div class="bg-orbs" aria-hidden="true"><span class="orb orb-a"></span><span class="orb orb-b"></span></div>

  <button class="theme-toggle" type="button" aria-label="Toggle light and dark theme" data-theme-toggle>
    <svg class="ic-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
    <svg class="ic-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
  </button>

  <main class="card" role="main">

    <a class="brand" href="{esc(COMPANY['site_url'])}" aria-label="Key2Nest Home Loans home">
      <img src="../assets/logo-gold.png" alt="Key2Nest Home Loans" class="brand-logo" width="132" height="40" />
    </a>

    <header class="identity">
      <div class="portrait-ring">
        <img class="portrait" src="../assets/{esc(p['photo'])}" alt="Portrait of {esc(p['name'])}" width="360" height="360" loading="eager" decoding="async" />
      </div>
      {f'<p class="eyebrow">{esc(eyebrow)}</p>' if eyebrow else ''}
      <h1 class="name">{esc(p['name'])}</h1>
      <p class="role">{esc(role)}</p>
      <p class="nmls"><a href="https://www.nmlsconsumeraccess.org/EntityDetails.aspx/INDIVIDUAL/{p['nmls']}" target="_blank" rel="noopener">NMLS&nbsp;#{p['nmls']}</a></p>
    </header>

    <div class="rule" aria-hidden="true"></div>

    <a class="save" href="../vcards/{esc(p['slug'])}.vcf" download="{esc(p['first'])}-{esc(p['last'])}.vcf">
      <span class="save-ic" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M19 8v6M22 11h-6"/></svg>
      </span>
      <span class="save-tx">Save to Contacts</span>
    </a>

    <nav class="contacts" aria-label="Contact {esc(p['name'])}">
{contact_rows}
    </nav>

    <a class="apply" href="{esc(COMPANY['apply_url'])}" target="_blank" rel="noopener">
      <span class="apply-tx">Apply Now</span>
      <span class="apply-ar" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
      </span>
    </a>

    <footer class="foot">
      <p class="foot-org">{esc(COMPANY['name'])}</p>
      <p class="foot-lic">{esc(COMPANY['states'])}</p>
      <p class="foot-nmls"><a href="{esc(COMPANY['nmls_url'])}" target="_blank" rel="noopener">Company NMLS&nbsp;#{COMPANY['nmls']}</a> · Equal Housing Lender</p>
    </footer>
  </main>

  <script>
    // Manual theme override (persists, then wins over the OS).
    (function () {{
      var btn = document.querySelector('[data-theme-toggle]');
      if (!btn) return;
      btn.addEventListener('click', function () {{
        var next = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
        document.documentElement.dataset.theme = next;
        try {{ localStorage.setItem('k2n-theme', next); }} catch (e) {{}}
      }});
    }})();
  </script>
</body>
</html>
'''


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------
def main():
    global BASE_URL
    ap = argparse.ArgumentParser(description="Generate Key2Nest digital business cards.")
    ap.add_argument("--base-url", help="Host the QR codes / canonical links point to.")
    args = ap.parse_args()
    if args.base_url:
        BASE_URL = args.base_url.rstrip("/")

    (ROOT / "vcards").mkdir(exist_ok=True)
    (ROOT / "qr").mkdir(exist_ok=True)

    index_rows = []
    for p in PEOPLE:
        card_url = f"{BASE_URL}/{p['slug']}"

        # 1) Card page
        page_dir = ROOT / p["slug"]
        page_dir.mkdir(exist_ok=True)
        (page_dir / "index.html").write_text(build_page(p, card_url), encoding="utf-8")

        # 2) vCard
        (ROOT / "vcards" / f"{p['slug']}.vcf").write_text(build_vcard(p, card_url), encoding="utf-8")

        # 3) QR codes (SVG vector + PNG raster), gold on transparent, high ECC.
        qr = segno.make(card_url, error="h")
        qr.save(ROOT / "qr" / f"{p['slug']}.svg", scale=10, border=2,
                dark="#0B1A2E", light=None)
        qr.save(ROOT / "qr" / f"{p['slug']}.png", scale=16, border=2,
                dark="#0B1A2E", light="#F4EFE3")

        index_rows.append((p, card_url))
        print(f"  ✓ {p['slug']:<9} {card_url}")

    # Directory landing page listing all cards (useful for QA / sharing).
    write_index(index_rows)
    print(f"\nDone — {len(PEOPLE)} cards generated against base URL: {BASE_URL}")


def write_index(rows):
    items = "\n".join(
        f'''      <li><a href="./{p['slug']}/">
        <img src="./assets/{p['photo']}" alt="" width="56" height="56" />
        <span><strong>{esc(p['name'])}</strong><em>{esc(p['title'])}</em></span>
        <code>/{p['slug']}</code></a></li>'''
        for p, _ in rows
    )
    doc = f'''<!doctype html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <meta name="robots" content="noindex" />
  <title>Key2Nest — Team Cards</title>
  <link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@300..700&family=Source+Serif+4:opsz,wght@8..60,300..700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="./card.css" />
</head>
<body class="index-body">
  <main class="index-wrap">
    <img src="./assets/logo-gold.png" alt="Key2Nest Home Loans" width="150" height="46" class="index-logo" />
    <h1>Digital Business Cards</h1>
    <p class="index-sub">Tap a name to preview that member's card.</p>
    <ul class="index-list">
{items}
    </ul>
  </main>
</body>
</html>
'''
    (ROOT / "index.html").write_text(doc, encoding="utf-8")


if __name__ == "__main__":
    main()
