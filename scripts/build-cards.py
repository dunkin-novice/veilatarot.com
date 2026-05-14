#!/usr/bin/env python3
"""Build the static SEO tree for veilatarot.com from cards.json.

Generates:
- /cards/<slug>/                 (78 EN card pages)
- /th/cards/<slug>/              (78 TH card pages)
- /major-arcana/                 + /th/...
- /minor-arcana/                 + /th/...
- /cups-tarot-meanings/          + /th/...
- /swords-tarot-meanings/        + /th/...
- /wands-tarot-meanings/         + /th/...
- /pentacles-tarot-meanings/     + /th/...
- /tarot-love-readings/          + /th/...
- /career-tarot-reading/         + /th/...
- /yes-no-tarot/                 + /th/...
- /sitemap.xml                   (every URL above + the 5 existing statics)

Card pages also receive a "Related cards" module + an "Explore related
readings" section. All pages include BreadcrumbList JSON-LD.

Re-run anytime cards.json changes:
    python3 scripts/build-cards.py
"""
import json
import re
import shutil
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DECK_PATH = ROOT / 'cards.json'
DECK = json.loads(DECK_PATH.read_text(encoding='utf-8'))

BUILD_DATE = '2026-05-14'
LANGS = ('en', 'th')

# ---------------------------------------------------------------------------
# DATA STRUCTURES
# ---------------------------------------------------------------------------

POSITIONS = [
    {'n': 1,  'key': 'present',     'short_en': 'The Present',         'short_th': 'ปัจจุบัน'},
    {'n': 2,  'key': 'challenge',   'short_en': 'The Challenge',       'short_th': 'อุปสรรค'},
    {'n': 3,  'key': 'past',        'short_en': 'The Past',            'short_th': 'อดีต'},
    {'n': 4,  'key': 'future',      'short_en': 'The Future',          'short_th': 'อนาคต'},
    {'n': 5,  'key': 'above',       'short_en': 'Above · Conscious',   'short_th': 'เบื้องบน · จิตสำนึก'},
    {'n': 6,  'key': 'below',       'short_en': 'Below · Unconscious', 'short_th': 'เบื้องล่าง · จิตใต้สำนึก'},
    {'n': 7,  'key': 'self',        'short_en': 'Advice · Self',       'short_th': 'คำชี้แนะ · ตัวคุณ'},
    {'n': 8,  'key': 'environment', 'short_en': 'External Influences', 'short_th': 'ปัจจัยภายนอก'},
    {'n': 9,  'key': 'hopes_fears', 'short_en': 'Hopes & Fears',       'short_th': 'ความหวังและความกลัว'},
    {'n': 10, 'key': 'outcome',     'short_en': 'Outcome',             'short_th': 'ผลลัพธ์'},
]
ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']

SUIT_EN = {'wands': 'Wands', 'cups': 'Cups', 'swords': 'Swords', 'pentacles': 'Pentacles'}
SUIT_TH = {'wands': 'ไม้เท้า', 'cups': 'ถ้วย', 'swords': 'ดาบ', 'pentacles': 'เหรียญ'}

SUIT_HUB_SLUG = {
    'wands': 'wands-tarot-meanings',
    'cups':  'cups-tarot-meanings',
    'swords': 'swords-tarot-meanings',
    'pentacles': 'pentacles-tarot-meanings',
}

# Curated card lists for topical hubs (id is the cards.json id field).
TOPICAL_CARD_IDS = {
    'love': [
        '07-the-lovers', '04-the-empress', '03-the-high-priestess',
        '37-ace-of-cups', '38-two-of-cups', '39-three-of-cups',
        '42-six-of-cups', '46-ten-of-cups',
        '48-knight-of-cups', '49-queen-of-cups',
        '26-four-of-wands',
    ],
    'career': [
        '02-the-magician', '05-the-emperor', '08-the-chariot',
        '11-wheel-of-fortune',
        '65-ace-of-pentacles', '67-three-of-pentacles', '68-four-of-pentacles',
        '72-eight-of-pentacles', '74-ten-of-pentacles',
        '75-page-of-pentacles', '76-knight-of-pentacles', '78-king-of-pentacles',
    ],
    'yes': [
        '20-the-sun', '18-the-star', '22-the-world',
        '04-the-empress', '03-the-high-priestess',
        '23-ace-of-wands', '28-six-of-wands',
        '37-ace-of-cups', '39-three-of-cups', '46-ten-of-cups',
    ],
    'no': [
        '17-the-tower', '14-death', '16-the-devil',
        '53-three-of-swords', '54-four-of-swords', '60-ten-of-swords',
        '41-five-of-cups', '69-five-of-pentacles',
    ],
}

STATIC_URLS = [
    ('/',                       '1.0', 'monthly'),
    ('/celtic-cross-tarot/',    '0.8', 'monthly'),
    ('/th/celtic-cross-tarot/', '0.7', 'monthly'),
    ('/daily-tarot-card/',      '0.8', 'daily'),
    ('/th/daily-tarot-card/',   '0.7', 'daily'),
    ('/all-tarot-pages/',       '0.5', 'monthly'),
    ('/th/all-tarot-pages/',    '0.4', 'monthly'),
]

# Long-form date for visible "Last updated" footer line.
BUILD_DATE_LONG_EN = '14 May 2026'
BUILD_DATE_LONG_TH = '14 พฤษภาคม 2026'
# RFC 822 for RSS pubDate / lastBuildDate
BUILD_DATE_RFC822 = 'Wed, 14 May 2026 00:00:00 +0000'

HUB_SLUGS = [
    'major-arcana', 'minor-arcana',
    'cups-tarot-meanings', 'swords-tarot-meanings',
    'wands-tarot-meanings', 'pentacles-tarot-meanings',
    'tarot-love-readings', 'career-tarot-reading', 'yes-no-tarot',
]

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def card_slug(card):
    """01-the-fool -> the-fool"""
    return re.sub(r'^\d{2}-', '', card['id'])

def card_path(card, lang):
    return f'/{("th/" if lang == "th" else "")}cards/{card_slug(card)}/'

def hub_path(slug, lang):
    return f'/{("th/" if lang == "th" else "")}{slug}/'

def deck_by_id():
    return {c['id']: c for c in DECK}

def arcana_label(card, lang):
    if card['arcana'] == 'major':
        return f"Major Arcana · {card['roman']}" if lang == 'en' else f"ไพ่ชุดเมเจอร์ · {card['roman']}"
    suit = (SUIT_EN if lang == 'en' else SUIT_TH)[card['suit']]
    return f"Minor Arcana · {suit}" if lang == 'en' else f"ไพ่ชุดไมเนอร์ · {suit}"

def card_meta_desc(card, lang):
    name = card['name'][lang]
    kw_up = (card['upright'].get('keywords') or {}).get(lang, '') or ''
    if lang == 'en':
        return f"{name} tarot card meaning: {kw_up}. Upright, reversed, and all ten Celtic Cross positions explained."
    return f"ความหมายไพ่ {name}: {kw_up} คำทำนายไพ่ตั้งตรง ไพ่กลับหัว และทั้งสิบตำแหน่งของผังเซลติกครอส"

def topical_link_for_card(card, lang):
    if card['arcana'] == 'minor' and card['suit'] == 'cups':
        return ('love', hub_path('tarot-love-readings', lang),
                'Tarot for Love' if lang == 'en' else 'ไพ่ความรัก')
    if card['arcana'] == 'minor' and card['suit'] == 'pentacles':
        return ('career', hub_path('career-tarot-reading', lang),
                'Tarot for Career' if lang == 'en' else 'ไพ่อาชีพ')
    return ('yesno', hub_path('yes-no-tarot', lang),
            'Yes/No Readings' if lang == 'en' else 'ไพ่ใช่/ไม่ใช่')

def related_cards(card, n=6):
    """Other cards in the same arcana/suit, ordered as the n following peers
    (cyclic) — gives a 'next in the suit/major journey' feel."""
    if card['arcana'] == 'major':
        peers = sorted([c for c in DECK if c['arcana'] == 'major'], key=lambda c: c['id'])
    else:
        peers = sorted([c for c in DECK if c.get('suit') == card['suit']], key=lambda c: c['id'])
    idx = next(i for i, c in enumerate(peers) if c['id'] == card['id'])
    return [peers[(idx + k) % len(peers)] for k in range(1, n + 1)]

def category_hub_link(card, lang):
    if card['arcana'] == 'major':
        return (hub_path('major-arcana', lang),
                'The Major Arcana' if lang == 'en' else 'ไพ่ชุดเมเจอร์')
    return (hub_path(SUIT_HUB_SLUG[card['suit']], lang),
            f"The Suit of {SUIT_EN[card['suit']]}" if lang == 'en' else f"ไพ่ชุด{SUIT_TH[card['suit']]}")

# ---------------------------------------------------------------------------
# BREADCRUMBS
# ---------------------------------------------------------------------------

def home_crumb(lang):
    return (('Home' if lang == 'en' else 'หน้าแรก'),
            'https://veilatarot.com/')

def breadcrumb_for_card(card, lang):
    base = 'https://veilatarot.com'
    crumbs = [home_crumb(lang)]
    if card['arcana'] == 'major':
        crumbs.append((
            'Major Arcana' if lang == 'en' else 'ไพ่ชุดเมเจอร์',
            base + hub_path('major-arcana', lang)
        ))
    else:
        crumbs.append((
            'Minor Arcana' if lang == 'en' else 'ไพ่ชุดไมเนอร์',
            base + hub_path('minor-arcana', lang)
        ))
        suit = card['suit']
        crumbs.append((
            f"The Suit of {SUIT_EN[suit]}" if lang == 'en' else f"ไพ่ชุด{SUIT_TH[suit]}",
            base + hub_path(SUIT_HUB_SLUG[suit], lang)
        ))
    crumbs.append((card['name'][lang], base + card_path(card, lang)))
    return crumbs

def breadcrumb_for_hub(slug, lang):
    base = 'https://veilatarot.com'
    crumbs = [home_crumb(lang)]
    title_en = HUB_DEFS[slug]['title_plain_en']
    title_th = HUB_DEFS[slug]['title_plain_th']
    if slug in ('cups-tarot-meanings', 'swords-tarot-meanings',
                'wands-tarot-meanings', 'pentacles-tarot-meanings'):
        crumbs.append((
            'Minor Arcana' if lang == 'en' else 'ไพ่ชุดไมเนอร์',
            base + hub_path('minor-arcana', lang)
        ))
    crumbs.append((
        title_en if lang == 'en' else title_th,
        base + hub_path(slug, lang)
    ))
    return crumbs

def render_breadcrumb_html(crumbs):
    """Visible <nav class='breadcrumb'> rendering. Last crumb is non-link."""
    parts = []
    for i, (name, item) in enumerate(crumbs):
        is_last = (i == len(crumbs) - 1)
        if is_last:
            parts.append(f'<span class="bc-current">{escape(name)}</span>')
        else:
            # strip the absolute prefix for visible href
            href = item.replace('https://veilatarot.com', '')
            parts.append(f'<a href="{href}">{escape(name)}</a>')
    sep = '<span class="bc-sep">›</span>'
    return f'<nav class="breadcrumb" aria-label="Breadcrumb">{sep.join(parts)}</nav>'

def breadcrumb_jsonld(crumbs):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": item}
            for i, (name, item) in enumerate(crumbs)
        ]
    }

# ---------------------------------------------------------------------------
# SHARED HEAD / FOOTER
# ---------------------------------------------------------------------------

def render_head_block(title, desc, canonical, en_path, th_path,
                      og_image='https://veilatarot.com/og.png',
                      og_type='article', lang='en', extra_jsonld=None):
    """Common <head> contents minus the surrounding <head></head>."""
    og_locale = 'en_US' if lang == 'en' else 'th_TH'
    og_locale_alt = 'th_TH' if lang == 'en' else 'en_US'
    in_language = 'en-US' if lang == 'en' else 'th-TH'
    jsonld_blocks = extra_jsonld or []

    head = f'''<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{escape(title)}</title>
<meta name="description" content="{escape(desc, quote=True)}" />
<meta name="author" content="Veila Tarot" />
<meta name="robots" content="index, follow, max-image-preview:large" />
<meta name="theme-color" content="#0a0a0c" />
<meta name="color-scheme" content="dark" />

<link rel="canonical" href="https://veilatarot.com{canonical}" />
<link rel="alternate" hreflang="en" href="https://veilatarot.com{en_path}" />
<link rel="alternate" hreflang="th" href="https://veilatarot.com{th_path}" />
<link rel="alternate" hreflang="x-default" href="https://veilatarot.com{en_path}" />

<meta property="og:type" content="{og_type}" />
<meta property="og:site_name" content="Veila" />
<meta property="og:title" content="{escape(title, quote=True)}" />
<meta property="og:description" content="{escape(desc, quote=True)}" />
<meta property="og:url" content="https://veilatarot.com{canonical}" />
<meta property="og:image" content="{og_image}" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:locale" content="{og_locale}" />
<meta property="og:locale:alternate" content="{og_locale_alt}" />

<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{escape(title, quote=True)}" />
<meta name="twitter:description" content="{escape(desc, quote=True)}" />
<meta name="twitter:image" content="{og_image}" />

<link rel="icon" href="/favicon.svg" type="image/svg+xml" />
<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png" />
<link rel="apple-touch-icon" href="/apple-touch-icon.png" sizes="180x180" />
<link rel="manifest" href="/manifest.webmanifest" />
<link rel="alternate" type="application/rss+xml" title="Veila Tarot — Feed" href="/feed.xml" />

<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,400&family=IBM+Plex+Sans+Thai:wght@300;400;500;600&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="/assets/page.css" />

<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2823470980745945"
     crossorigin="anonymous"></script>
<meta name="google-adsense-account" content="ca-pub-2823470980745945">

<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQWWZ3HT2S"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-NQWWZ3HT2S');
</script>

<script src="/assets/analytics.js" defer></script>
'''
    for block in jsonld_blocks:
        head += f'\n<script type="application/ld+json">\n{json.dumps(block, ensure_ascii=False, indent=2)}\n</script>\n'
    return head


def render_header(en_path, th_path, lang):
    if lang == 'en':
        brand_sub = 'A Tarot Practice'
        brand_aria = 'Veila — return to home'
        lang_aria = 'Language'
    else:
        brand_sub = 'การทำสมาธิกับไพ่'
        brand_aria = 'Veila — กลับสู่หน้าแรก'
        lang_aria = 'ภาษา'
    return f'''<header class="site-header">
  <a class="brand" href="/" aria-label="{escape(brand_aria, quote=True)}">Veila<span class="dot"></span><span class="brand-sub">{escape(brand_sub)}</span></a>
  <div class="lang-toggle" role="group" aria-label="{escape(lang_aria, quote=True)}">
    <a href="{en_path}"{' class="active"' if lang == 'en' else ''}>EN</a>
    <span class="sep">·</span>
    <a href="{th_path}"{' class="active"' if lang == 'th' else ''}>TH</a>
  </div>
</header>'''


def render_footer(lang):
    if lang == 'en':
        link_celtic, link_daily = '/celtic-cross-tarot/', '/daily-tarot-card/'
        link_index = '/all-tarot-pages/'
        nav_celtic, nav_daily, nav_index = 'Celtic Cross Guide', 'Daily Tarot Card', 'All Pages'
        fineprint = 'For reflection, not prediction.'
        last_updated = f'Last updated · {BUILD_DATE_LONG_EN}'
    else:
        link_celtic, link_daily = '/th/celtic-cross-tarot/', '/th/daily-tarot-card/'
        link_index = '/th/all-tarot-pages/'
        nav_celtic, nav_daily, nav_index = 'คู่มือเซลติกครอส', 'ไพ่ประจำวัน', 'ทุกหน้า'
        fineprint = 'เพื่อการใคร่ครวญ ไม่ใช่การพยากรณ์'
        last_updated = f'ปรับปรุงล่าสุด · {BUILD_DATE_LONG_TH}'
    return f'''<footer>
  <div class="fineprint">{escape(fineprint)}</div>
  <div class="last-updated">{escape(last_updated)}</div>
  <nav class="footer-nav">
    <a href="{link_celtic}">{escape(nav_celtic)}</a>
    <span class="sep">·</span>
    <a href="{link_daily}">{escape(nav_daily)}</a>
    <span class="sep">·</span>
    <a href="{link_index}">{escape(nav_index)}</a>
  </nav>
  <div>veilatarot.com · © MMXXVI</div>
</footer>'''

# ---------------------------------------------------------------------------
# CARD PAGE
# ---------------------------------------------------------------------------

def render_related_cards_module(card, lang):
    if card['arcana'] == 'major':
        heading = 'Other Major Arcana' if lang == 'en' else 'ไพ่ชุดเมเจอร์อื่นๆ'
    else:
        suit_en = SUIT_EN[card['suit']]
        suit_th = SUIT_TH[card['suit']]
        heading = f"Other cards in the Suit of {suit_en}" if lang == 'en' else f"ไพ่ใบอื่นในชุด{suit_th}"
    items = []
    for peer in related_cards(card):
        items.append(f'''      <a href="{card_path(peer, lang)}">
        <div class="rc-rom">{peer['roman']}</div>
        <div class="rc-name">{escape(peer['name'][lang])}</div>
      </a>''')
    return f'''  <aside class="related-cards">
    <h2>{escape(heading)}</h2>
    <div class="related-cards-grid">
{chr(10).join(items)}
    </div>
  </aside>'''


def render_explore_related_readings(card, lang):
    cat_href, cat_name = category_hub_link(card, lang)
    _, topic_href, topic_name = topical_link_for_card(card, lang)
    if lang == 'en':
        h2 = 'Explore related readings'
        lede = "When you want context beyond this single card, try one of these."
        labels = {'spread': 'The Spread', 'daily': 'Daily', 'category': 'Category', 'topic': 'Topic'}
        spread_name = 'The Celtic Cross'
        daily_name = "Today's Card"
        celtic_href, daily_href = '/celtic-cross-tarot/', '/daily-tarot-card/'
    else:
        h2 = 'อ่านเพิ่มเติม'
        lede = 'เมื่อต้องการบริบทมากกว่าไพ่ใบเดียว ลองดูจุดเริ่มต้นเหล่านี้'
        labels = {'spread': 'ผังการอ่าน', 'daily': 'ประจำวัน', 'category': 'หมวด', 'topic': 'หัวข้อ'}
        spread_name = 'เซลติกครอส'
        daily_name = 'ไพ่วันนี้'
        celtic_href, daily_href = '/th/celtic-cross-tarot/', '/th/daily-tarot-card/'
    items = [
        (labels['spread'], spread_name, celtic_href),
        (labels['daily'], daily_name, daily_href),
        (labels['category'], cat_name, cat_href),
        (labels['topic'], topic_name, topic_href),
    ]
    cells = '\n'.join(
        f'''      <a href="{href}">
        <div class="rl-label">{escape(lbl)}</div>
        <div class="rl-name">{escape(name)}</div>
      </a>''' for (lbl, name, href) in items
    )
    return f'''  <aside class="related-readings">
    <h2>{escape(h2)}</h2>
    <p class="related-lede">{escape(lede)}</p>
    <div class="related-grid">
{cells}
    </div>
  </aside>'''


def card_i18n(lang, name):
    if lang == 'en':
        return {
            'title': f"{name} Tarot Card — Upright, Reversed & Celtic Cross | Veila",
            'h2_up': f"{name} — Upright",
            'h2_rev': f"{name} — Reversed",
            'h2_cc': 'In the Celtic Cross spread',
            'cc_lede': f"How {name} reads in each of the ten Celtic Cross positions.",
            'prev_label': 'Previous', 'next_label': 'Next',
            'cta_main': 'Begin a Reading',
            'cta_about': 'About the Spread',
            'cta_daily': 'Daily Card',
            'up_label': 'Upright', 'rev_label': 'Reversed',
            'adj_aria': 'Adjacent cards',
        }
    return {
        'title': f"ความหมายไพ่ {name} — ตั้งตรง กลับหัว และเซลติกครอส | Veila",
        'h2_up': f"{name} — ตั้งตรง",
        'h2_rev': f"{name} — กลับหัว",
        'h2_cc': 'ในผังเซลติกครอส',
        'cc_lede': f"การอ่านไพ่ {name} ในแต่ละตำแหน่งของผังเซลติกครอสทั้งสิบตำแหน่ง",
        'prev_label': 'ก่อนหน้า', 'next_label': 'ถัดไป',
        'cta_main': 'เริ่มอ่านไพ่',
        'cta_about': 'เกี่ยวกับผังการอ่าน',
        'cta_daily': 'ไพ่ประจำวัน',
        'up_label': 'ตั้งตรง', 'rev_label': 'กลับหัว',
        'adj_aria': 'ไพ่ข้างเคียง',
    }


def render_card(card, prev_card, next_card, lang):
    sl = card_slug(card)
    name = card['name'][lang]
    archetype = (card.get('archetype') or {}).get(lang, '') or ''
    up = card.get('upright') or {}
    rev = card.get('reversed') or {}
    up_kw = (up.get('keywords') or {}).get(lang, '') or ''
    rev_kw = (rev.get('keywords') or {}).get(lang, '') or ''
    up_text = (up.get('standalone') or {}).get(lang, '') or ''
    rev_text = (rev.get('standalone') or {}).get(lang, '') or ''

    label = arcana_label(card, lang)
    desc = card_meta_desc(card, lang)
    t = card_i18n(lang, name)
    title = t['title']
    en_path = card_path(card, 'en')
    th_path = card_path(card, 'th')
    canonical = en_path if lang == 'en' else th_path
    page_url = f"https://veilatarot.com{canonical}"

    cc_blocks = []
    for pos in POSITIONS:
        pkey = pos['key']
        short = pos[f'short_{lang}']
        up_cc = ((up.get('celtic_cross') or {}).get(pkey) or {}).get(lang, '') or up_text
        rev_cc = ((rev.get('celtic_cross') or {}).get(pkey) or {}).get(lang, '') or rev_text
        cc_blocks.append(f'''        <article class="cc-pos">
          <div class="cc-pos-label"><span class="rn">{ROMAN[pos['n'] - 1]}.</span> {escape(short)}</div>
          <div class="cc-pair"><h3>{escape(t['up_label'])}</h3><p>{escape(up_cc)}</p></div>
          <div class="cc-pair"><h3>{escape(t['rev_label'])}</h3><p>{escape(rev_cc)}</p></div>
        </article>''')
    cc_html = '\n'.join(cc_blocks)

    prev_url = card_path(prev_card, lang)
    next_url = card_path(next_card, lang)
    prev_name = prev_card['name'][lang]
    next_name = next_card['name'][lang]

    link_celtic = '/th/celtic-cross-tarot/' if lang == 'th' else '/celtic-cross-tarot/'
    link_daily = '/th/daily-tarot-card/' if lang == 'th' else '/daily-tarot-card/'

    article_jsonld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": desc,
        "image": "https://veilatarot.com/og.png",
        "inLanguage": 'en-US' if lang == 'en' else 'th-TH',
        "datePublished": BUILD_DATE,
        "dateModified": BUILD_DATE,
        "publisher": {"@type": "Organization", "name": "Veila", "url": "https://veilatarot.com/"},
        "mainEntityOfPage": page_url
    }
    crumbs = breadcrumb_for_card(card, lang)
    breadcrumb_html = render_breadcrumb_html(crumbs)
    crumbs_jsonld = breadcrumb_jsonld(crumbs)
    related_html = render_related_cards_module(card, lang)
    explore_html = render_explore_related_readings(card, lang)

    head = render_head_block(
        title=title, desc=desc, canonical=canonical,
        en_path=en_path, th_path=th_path, lang=lang,
        extra_jsonld=[article_jsonld, crumbs_jsonld]
    )

    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
{head}</head>
<body>

{render_header(en_path, th_path, lang)}

<main class="article card-page">
  {breadcrumb_html}
  <div class="eyebrow">{escape(label)}</div>
  <h1 class="title">{escape(name)}</h1>
  <p class="archetype">{escape(archetype)}</p>

  <section class="meaning-block">
    <h2>{escape(t['h2_up'])}</h2>
    <p class="card-keywords">{escape(up_kw)}</p>
    <p>{escape(up_text)}</p>
  </section>

  <section class="meaning-block">
    <h2>{escape(t['h2_rev'])}</h2>
    <p class="card-keywords">{escape(rev_kw)}</p>
    <p>{escape(rev_text)}</p>
  </section>

  <section class="cc-section">
    <h2>{escape(t['h2_cc'])}</h2>
    <p class="cc-lede">{escape(t['cc_lede'])}</p>
    <div class="cc-grid">
{cc_html}
    </div>
  </section>

  <nav class="adjacent-nav" aria-label="{escape(t['adj_aria'], quote=True)}">
    <a class="adj prev" href="{prev_url}">
      <div class="dir">← {escape(t['prev_label'])}</div>
      <div class="adj-name">{escape(prev_name)}</div>
    </a>
    <a class="adj next" href="{next_url}">
      <div class="dir">{escape(t['next_label'])} →</div>
      <div class="adj-name">{escape(next_name)}</div>
    </a>
  </nav>

{related_html}

{explore_html}

  <div class="cta-row">
    <a href="/" class="cta-btn">{escape(t['cta_main'])}</a>
    <a href="{link_celtic}" class="cta-btn ghost">{escape(t['cta_about'])}</a>
    <a href="{link_daily}" class="cta-btn ghost">{escape(t['cta_daily'])}</a>
  </div>
</main>

{render_footer(lang)}

</body>
</html>
'''

# ---------------------------------------------------------------------------
# HUB PAGES
# ---------------------------------------------------------------------------

HUB_DEFS = {
    'major-arcana': {
        'title_plain_en': 'The Major Arcana',
        'title_plain_th': 'ไพ่ชุดเมเจอร์',
        'meta': {
            'en': {
                'title': 'The Major Arcana — All 22 Tarot Trumps Explained | Veila',
                'desc':  'The 22 Major Arcana tarot cards, from The Fool to The World. Brief descriptions with links to each card\'s full meaning page.',
                'eyebrow': 'The 22 Trumps',
                'h1_html': 'The <em>Major Arcana</em>',
                'lede': 'Twenty-two cards charting a journey from naive beginnings to integrated arrival. Each is an archetype, a station on the road, a turn the seeker takes whether they meant to or not.',
                'intro': "The journey of the Major Arcana is sometimes called the Fool's Journey: a young, open self meets the world's archetypal forces in sequence, is shaped by them, and arrives at completion changed. When a Major appears in a reading, it carries more weight than a Minor — the question is touching something structural.",
                'list_heading': 'The 22 Major Arcana',
            },
            'th': {
                'title': 'ไพ่ชุดเมเจอร์ — ทั้ง 22 ใบ พร้อมคำอธิบาย | Veila',
                'desc':  'ไพ่ชุดเมเจอร์ทั้ง 22 ใบ ตั้งแต่ The Fool ถึง The World คำอธิบายสั้น พร้อมลิงก์ไปยังหน้าความหมายเต็มของแต่ละใบ',
                'eyebrow': 'ทรัมป์ทั้ง 22 ใบ',
                'h1_html': 'ไพ่ชุด<em>เมเจอร์</em>',
                'lede': 'ไพ่ยี่สิบสองใบที่บันทึกการเดินทาง จากจุดเริ่มต้นอันใสซื่อ สู่การมาถึงที่หลอมรวมเป็นหนึ่ง แต่ละใบคืออาร์คีไทป์ จุดพักบนถนน และจังหวะที่ผู้แสวงต้องผ่าน ไม่ว่าจะตั้งใจหรือไม่',
                'intro': 'การเดินทางของไพ่ชุดเมเจอร์บางครั้งถูกเรียกว่า "การเดินทางของคนโง่" — ตัวตนหนุ่มสาวที่เปิดกว้าง ได้พบกับพลังต้นแบบของโลกเรียงตามลำดับ ถูกหล่อหลอมโดยพลังเหล่านั้น และมาถึงจุดสิ้นสุดในฐานะคนที่เปลี่ยนไปแล้ว เมื่อไพ่เมเจอร์ปรากฏในการอ่าน มันมีน้ำหนักมากกว่าไพ่ไมเนอร์ — คำถามกำลังสัมผัสบางอย่างที่เป็นโครงสร้าง',
                'list_heading': 'ไพ่ชุดเมเจอร์ทั้ง 22 ใบ',
            },
        },
        'card_filter': lambda c: c['arcana'] == 'major',
        'sort_key': lambda c: c['id'],
    },
    'minor-arcana': {
        'title_plain_en': 'The Minor Arcana',
        'title_plain_th': 'ไพ่ชุดไมเนอร์',
        'meta': {
            'en': {
                'title': 'The Minor Arcana — Four Suits, 56 Cards | Veila',
                'desc':  'The 56 Minor Arcana tarot cards across four suits: Cups, Wands, Swords, and Pentacles. Browse each suit and its fourteen cards.',
                'eyebrow': '56 Pip & Court Cards',
                'h1_html': 'The <em>Minor Arcana</em>',
                'lede': "If the Major Arcana names the big chapters of a life, the Minor Arcana names the days inside them. Four suits, fourteen cards each — pip cards Ace through Ten, plus the four courts.",
                'intro': "Each suit speaks to a different mode of being. Wands are fire (will, vocation), Cups are water (feeling, relationship), Swords are air (mind, conflict), and Pentacles are earth (body, craft, money). When a Minor appears in a reading, it answers in the texture of the everyday — concrete, situational, often actionable.",
                'list_heading': 'The Four Suits',
            },
            'th': {
                'title': 'ไพ่ชุดไมเนอร์ — สี่ชุด รวม 56 ใบ | Veila',
                'desc':  'ไพ่ชุดไมเนอร์ทั้ง 56 ใบในสี่ชุด: ถ้วย ไม้เท้า ดาบ และเหรียญ เลือกดูแต่ละชุดและไพ่สิบสี่ใบในชุดนั้น',
                'eyebrow': 'ไพ่พิพและไพ่ราชสำนัก 56 ใบ',
                'h1_html': 'ไพ่ชุด<em>ไมเนอร์</em>',
                'lede': 'ถ้าไพ่เมเจอร์บอกชื่อบทใหญ่ของชีวิต ไพ่ไมเนอร์บอกชื่อวันแต่ละวันในบทนั้น สี่ชุด ชุดละสิบสี่ใบ — ไพ่พิพ Ace ถึงสิบ บวกไพ่ราชสำนักอีกสี่',
                'intro': 'แต่ละชุดสะท้อนวิถีการเป็นอยู่ที่ต่างกัน ไม้เท้าคือไฟ (เจตจำนง อาชีพ) ถ้วยคือน้ำ (ความรู้สึก ความสัมพันธ์) ดาบคือลม (จิตใจ ความขัดแย้ง) เหรียญคือดิน (กาย งานฝีมือ เงิน) เมื่อไพ่ไมเนอร์ปรากฏ มันตอบในเนื้อสัมผัสของชีวิตประจำวัน — รูปธรรม เป็นสถานการณ์ และมักนำไปสู่การกระทำได้',
                'list_heading': 'สี่ชุดไพ่',
            },
        },
        'card_filter': None,  # special: lists suits not cards
        'is_suit_index': True,
    },
    'cups-tarot-meanings': {
        'title_plain_en': 'The Suit of Cups',
        'title_plain_th': 'ไพ่ชุดถ้วย',
        'meta': {
            'en': {
                'title': 'The Suit of Cups — All 14 Cups Tarot Card Meanings | Veila',
                'desc':  'The Suit of Cups in tarot — water, feeling, relationship. Meanings for all 14 Cups cards, Ace through King, with links to full readings.',
                'eyebrow': 'Water · Feeling · Relationship',
                'h1_html': 'The Suit of <em>Cups</em>',
                'lede': 'Cups are water — the element of feeling, intimacy, intuition, and what flows between people. When a Cup card lands, the question is usually emotional: who am I close to, what am I holding, what am I letting go of?',
                'intro': "Cups don't argue. They ask. They reveal the temperature of a relationship, the unspoken thing under a conversation, the longing or the disappointment that's coloring how a situation actually feels. Even the harshest Cup cards (Five of Cups, Three of Swords' cousin in feeling) are about grief, not punishment.",
                'list_heading': 'All 14 Cups Cards',
            },
            'th': {
                'title': 'ไพ่ชุดถ้วย — ความหมายไพ่ Cups ทั้ง 14 ใบ | Veila',
                'desc':  'ไพ่ชุดถ้วยในไพ่ทาโรต์ — น้ำ ความรู้สึก ความสัมพันธ์ ความหมายของไพ่ Cups ทั้ง 14 ใบ ตั้งแต่ Ace ถึง King พร้อมลิงก์ไปบทอ่านเต็ม',
                'eyebrow': 'น้ำ · ความรู้สึก · ความสัมพันธ์',
                'h1_html': 'ไพ่ชุด<em>ถ้วย</em>',
                'lede': 'ไพ่ชุดถ้วยคือธาตุน้ำ — ธาตุของความรู้สึก ความใกล้ชิด สัญชาตญาณ และสิ่งที่ไหลเวียนระหว่างผู้คน เมื่อไพ่ชุดถ้วยปรากฏ คำถามมักเป็นเรื่องอารมณ์ — ฉันใกล้ชิดกับใคร ฉันกำลังถืออะไรอยู่ ฉันกำลังปล่อยอะไรลงไป',
                'intro': 'ไพ่ชุดถ้วยไม่โต้แย้ง มันถาม มันเผยอุณหภูมิของความสัมพันธ์ สิ่งที่ไม่ได้พูดออกมาใต้บทสนทนา ความคิดถึงหรือความผิดหวังที่กำลังระบายสีให้สถานการณ์ แม้แต่ไพ่ชุดถ้วยที่ดูหนักที่สุดก็พูดถึงความเศร้า ไม่ใช่การลงโทษ',
                'list_heading': 'ไพ่ Cups ทั้ง 14 ใบ',
            },
        },
        'card_filter': lambda c: c['arcana'] == 'minor' and c['suit'] == 'cups',
        'sort_key': lambda c: c['id'],
    },
    'swords-tarot-meanings': {
        'title_plain_en': 'The Suit of Swords',
        'title_plain_th': 'ไพ่ชุดดาบ',
        'meta': {
            'en': {
                'title': 'The Suit of Swords — All 14 Swords Tarot Card Meanings | Veila',
                'desc':  'The Suit of Swords in tarot — air, mind, conflict. Meanings for all 14 Swords cards, Ace through King, with links to full readings.',
                'eyebrow': 'Air · Mind · Conflict',
                'h1_html': 'The Suit of <em>Swords</em>',
                'lede': 'Swords are air — the element of thought, language, conflict, and cutting clarity. They speak to what the mind is doing with a situation, often more than the situation itself.',
                'intro': "The Suit of Swords gets a reputation for being harsh, and many of its cards are. But Swords are not cruel — they are honest. Even at their bleakest (Three of Swords, Nine of Swords, Ten of Swords) they show you exactly what you already knew. The work of Swords is to face the truth cleanly, then act from it.",
                'list_heading': 'All 14 Swords Cards',
            },
            'th': {
                'title': 'ไพ่ชุดดาบ — ความหมายไพ่ Swords ทั้ง 14 ใบ | Veila',
                'desc':  'ไพ่ชุดดาบในไพ่ทาโรต์ — ลม จิตใจ ความขัดแย้ง ความหมายของไพ่ Swords ทั้ง 14 ใบ ตั้งแต่ Ace ถึง King พร้อมลิงก์ไปบทอ่านเต็ม',
                'eyebrow': 'ลม · จิตใจ · ความขัดแย้ง',
                'h1_html': 'ไพ่ชุด<em>ดาบ</em>',
                'lede': 'ไพ่ชุดดาบคือธาตุลม — ธาตุของความคิด ภาษา ความขัดแย้ง และความคมชัดที่บาดผ่าน มันสะท้อนสิ่งที่จิตใจกำลังทำกับสถานการณ์ บ่อยครั้งมากกว่าตัวสถานการณ์เอง',
                'intro': 'ไพ่ชุดดาบมักถูกมองว่าโหดร้าย และหลายใบก็โหดจริง แต่ดาบไม่ใช่ความโหดร้าย — มันคือความซื่อตรง แม้ในจุดที่มืดที่สุด (Three of Swords, Nine of Swords, Ten of Swords) มันก็แสดงสิ่งที่คุณรู้อยู่แล้วอย่างชัดเจน หน้าที่ของดาบคือเผชิญความจริงอย่างสะอาด แล้วทำสิ่งที่ต้องทำจากตรงนั้น',
                'list_heading': 'ไพ่ Swords ทั้ง 14 ใบ',
            },
        },
        'card_filter': lambda c: c['arcana'] == 'minor' and c['suit'] == 'swords',
        'sort_key': lambda c: c['id'],
    },
    'wands-tarot-meanings': {
        'title_plain_en': 'The Suit of Wands',
        'title_plain_th': 'ไพ่ชุดไม้เท้า',
        'meta': {
            'en': {
                'title': 'The Suit of Wands — All 14 Wands Tarot Card Meanings | Veila',
                'desc':  'The Suit of Wands in tarot — fire, will, vocation. Meanings for all 14 Wands cards, Ace through King, with links to full readings.',
                'eyebrow': 'Fire · Will · Vocation',
                'h1_html': 'The Suit of <em>Wands</em>',
                'lede': "Wands are fire — the energy of will, ambition, vocation, and the creative spark. They speak to what you are driving toward and what is driving you.",
                'intro': "A Wand in a spread is rarely passive. The question is usually about initiative, momentum, or the heat of an undertaking. Wands ask you to either light something or admit the match is already in your hand.",
                'list_heading': 'All 14 Wands Cards',
            },
            'th': {
                'title': 'ไพ่ชุดไม้เท้า — ความหมายไพ่ Wands ทั้ง 14 ใบ | Veila',
                'desc':  'ไพ่ชุดไม้เท้าในไพ่ทาโรต์ — ไฟ เจตจำนง อาชีพ ความหมายของไพ่ Wands ทั้ง 14 ใบ ตั้งแต่ Ace ถึง King พร้อมลิงก์ไปบทอ่านเต็ม',
                'eyebrow': 'ไฟ · เจตจำนง · อาชีพ',
                'h1_html': 'ไพ่ชุด<em>ไม้เท้า</em>',
                'lede': 'ไพ่ชุดไม้เท้าคือธาตุไฟ — พลังของเจตจำนง ความทะเยอทะยาน อาชีพ และประกายความคิดสร้างสรรค์ มันสะท้อนสิ่งที่คุณกำลังขับเคลื่อนไป และสิ่งที่กำลังขับเคลื่อนคุณ',
                'intro': 'ไพ่ไม้เท้าในการอ่านไม่ค่อยนิ่งเฉย คำถามมักเกี่ยวกับการริเริ่ม โมเมนตัม หรือความร้อนแรงของภารกิจ ไม้เท้าขอให้คุณจุดบางสิ่ง หรือยอมรับว่าไม้ขีดอยู่ในมือคุณอยู่แล้ว',
                'list_heading': 'ไพ่ Wands ทั้ง 14 ใบ',
            },
        },
        'card_filter': lambda c: c['arcana'] == 'minor' and c['suit'] == 'wands',
        'sort_key': lambda c: c['id'],
    },
    'pentacles-tarot-meanings': {
        'title_plain_en': 'The Suit of Pentacles',
        'title_plain_th': 'ไพ่ชุดเหรียญ',
        'meta': {
            'en': {
                'title': 'The Suit of Pentacles — All 14 Pentacles Tarot Card Meanings | Veila',
                'desc':  'The Suit of Pentacles in tarot — earth, body, craft, money. Meanings for all 14 Pentacles cards, Ace through King, with links to full readings.',
                'eyebrow': 'Earth · Body · Craft · Money',
                'h1_html': 'The Suit of <em>Pentacles</em>',
                'lede': 'Pentacles are earth — the material plane. Body, home, craft, money, the slow accumulation of skill and resource.',
                'intro': "Pentacles often look unglamorous on the surface and turn out to be the most practically useful cards in the deck. They answer questions about livelihood, health, and the kind of patient work that compounds over years.",
                'list_heading': 'All 14 Pentacles Cards',
            },
            'th': {
                'title': 'ไพ่ชุดเหรียญ — ความหมายไพ่ Pentacles ทั้ง 14 ใบ | Veila',
                'desc':  'ไพ่ชุดเหรียญในไพ่ทาโรต์ — ดิน กาย งานฝีมือ เงิน ความหมายของไพ่ Pentacles ทั้ง 14 ใบ ตั้งแต่ Ace ถึง King พร้อมลิงก์ไปบทอ่านเต็ม',
                'eyebrow': 'ดิน · กาย · งานฝีมือ · เงิน',
                'h1_html': 'ไพ่ชุด<em>เหรียญ</em>',
                'lede': 'ไพ่ชุดเหรียญคือธาตุดิน — มิติของวัตถุ ร่างกาย บ้าน งานฝีมือ เงิน และการสะสมทักษะกับทรัพยากรอย่างช้าๆ',
                'intro': 'ไพ่เหรียญมักดูไม่หรูหราในตอนแรก แต่กลายเป็นไพ่ที่นำไปใช้ในชีวิตจริงได้มากที่สุดในสำรับ มันตอบคำถามเรื่องการดำรงชีพ สุขภาพ และงานที่ต้องอดทนนานปีจึงจะเห็นผลทบต้น',
                'list_heading': 'ไพ่ Pentacles ทั้ง 14 ใบ',
            },
        },
        'card_filter': lambda c: c['arcana'] == 'minor' and c['suit'] == 'pentacles',
        'sort_key': lambda c: c['id'],
    },
    'tarot-love-readings': {
        'title_plain_en': 'Tarot for Love & Relationships',
        'title_plain_th': 'ไพ่ทาโรต์เพื่อความรักและความสัมพันธ์',
        'meta': {
            'en': {
                'title': 'Tarot for Love & Relationships | Veila',
                'desc':  'How to use tarot for love questions — common cards in love readings, what they really mean, and which spread to use.',
                'eyebrow': 'For matters of the heart',
                'h1_html': 'Tarot for <em>Love & Relationships</em>',
                'lede': 'Tarot is a poor crystal ball and an unusually good mirror. For love questions, that distinction matters — the cards rarely tell you what someone else will do, but they read with surprising clarity what you are bringing to the room.',
                'intro': "When you sit with a love question, hold it specifically. Not 'will I find love?' but 'what am I carrying into this relationship?' or 'what is between us that needs naming?' The cards below come up often in love readings — not because they predict romance, but because each names a recognizable emotional posture.",
                'list_heading': 'Common cards in love readings',
                'spread_note_en': 'For a relationship question, the full Celtic Cross is the most thorough — its tenth position (Outcome) shows the tendency if the current pattern continues, while position 9 (Hopes & Fears) often reveals what you have been silent about.',
            },
            'th': {
                'title': 'ไพ่ทาโรต์เพื่อความรักและความสัมพันธ์ | Veila',
                'desc':  'วิธีใช้ไพ่ทาโรต์สำหรับคำถามเรื่องความรัก — ไพ่ที่มักปรากฏในบทอ่านความรัก ความหมายที่แท้จริง และผังที่เหมาะกับคำถามนี้',
                'eyebrow': 'สำหรับเรื่องของหัวใจ',
                'h1_html': 'ไพ่ทาโรต์เพื่อ<em>ความรัก</em>',
                'lede': 'ไพ่ทาโรต์เป็นลูกแก้วที่อ่อนแอ แต่เป็นกระจกที่ดีอย่างน่าประหลาดใจ สำหรับคำถามเรื่องความรัก ความต่างนี้สำคัญ — ไพ่ไม่ค่อยบอกสิ่งที่คนอื่นจะทำ แต่อ่านสิ่งที่คุณนำเข้ามาในห้องได้อย่างชัดเจนผิดคาด',
                'intro': 'เมื่อคุณนั่งลงกับคำถามเรื่องความรัก ตั้งคำถามให้เฉพาะเจาะจง ไม่ใช่ "ฉันจะเจอรักไหม" แต่เป็น "ฉันกำลังนำอะไรเข้ามาในความสัมพันธ์นี้" หรือ "ระหว่างเรามีอะไรที่ต้องการการเรียกชื่อ" ไพ่ด้านล่างมักปรากฏในบทอ่านความรัก ไม่ใช่เพราะมันทำนายความโรแมนติก แต่เพราะแต่ละใบเรียกชื่อท่าทีทางอารมณ์ที่จดจำได้',
                'list_heading': 'ไพ่ที่มักปรากฏในบทอ่านความรัก',
                'spread_note_en': '',
            },
        },
        'topical_key': 'love',
    },
    'career-tarot-reading': {
        'title_plain_en': 'Tarot for Career & Calling',
        'title_plain_th': 'ไพ่ทาโรต์เพื่อการงานและอาชีพ',
        'meta': {
            'en': {
                'title': 'Tarot for Career, Work & Calling | Veila',
                'desc':  'How to use tarot for career questions — common cards in career readings, what they mean for work, and which spread fits the question.',
                'eyebrow': 'For work & vocation',
                'h1_html': 'Tarot for <em>Career & Calling</em>',
                'lede': 'Career questions sit at the intersection of will, craft, and circumstance. Tarot is well-suited to that intersection — it names the thing you have been almost-saying about your work, and sometimes the thing the work has been almost-saying back.',
                'intro': "Use tarot when you are between two options, when a project has gone quiet, when the work has begun to feel either misaligned or like it is finally arriving. The cards below come up often in career readings — Magician, Emperor, Wheel — but the most informative ones are usually the Pentacles, which speak to craft, money, and the slow plate of real work.",
                'list_heading': 'Common cards in career readings',
            },
            'th': {
                'title': 'ไพ่ทาโรต์เพื่อการงานและอาชีพ | Veila',
                'desc':  'วิธีใช้ไพ่ทาโรต์สำหรับคำถามเรื่องอาชีพ — ไพ่ที่มักปรากฏในบทอ่านอาชีพ ความหมายในบริบทการงาน และผังที่เหมาะกับคำถามนั้น',
                'eyebrow': 'สำหรับการงานและอาชีพ',
                'h1_html': 'ไพ่ทาโรต์เพื่อ<em>การงาน</em>',
                'lede': 'คำถามเรื่องอาชีพอยู่ที่จุดตัดของเจตจำนง ฝีมือ และสภาพแวดล้อม ไพ่ทาโรต์เหมาะกับจุดตัดนี้ — มันเรียกชื่อสิ่งที่คุณเกือบจะพูดเกี่ยวกับงานของคุณ และบางครั้งสิ่งที่งานกำลังเกือบจะพูดตอบกลับ',
                'intro': 'ใช้ไพ่ทาโรต์เมื่อคุณอยู่ระหว่างสองทางเลือก เมื่อโปรเจกต์หนึ่งเงียบลง เมื่องานเริ่มรู้สึกไม่เข้าที่หรือกำลังลงตัวในที่สุด ไพ่ด้านล่างมักปรากฏในบทอ่านอาชีพ — Magician, Emperor, Wheel — แต่ไพ่ที่ให้ข้อมูลมากที่สุดมักเป็นไพ่ชุดเหรียญ ซึ่งพูดถึงงานฝีมือ เงิน และจานอันค่อยเป็นค่อยไปของงานจริง',
                'list_heading': 'ไพ่ที่มักปรากฏในบทอ่านอาชีพ',
            },
        },
        'topical_key': 'career',
    },
    'yes-no-tarot': {
        'title_plain_en': 'Yes/No Tarot Readings',
        'title_plain_th': 'ไพ่ทาโรต์ใช่/ไม่ใช่',
        'meta': {
            'en': {
                'title': 'Yes/No Tarot Readings — Method & Card List | Veila',
                'desc':  'How to do a yes/no tarot reading — single-card method, which cards lean yes and which lean no, and when to use a fuller spread instead.',
                'eyebrow': 'A simpler kind of question',
                'h1_html': 'Yes/No <em>Tarot Readings</em>',
                'lede': "Yes/no is the question tarot is least built for and most often asked. The cards trade in nuance, and a binary answer flattens them. But there is a method, and used well it returns surprisingly useful results — usually by reframing the question you actually meant.",
                'intro': "The method is simple: shuffle with the question in mind, draw a single card, and read its leaning. Upright cards tend toward yes; reversed cards tend toward no. Major Arcana yes/no answers carry more weight than Minor ones. If the card is ambiguous, the reading is also telling you something — that the situation itself isn't binary, and the question may need rewording.",
                'list_heading_yes': 'Cards that lean Yes',
                'list_heading_no':  'Cards that lean No',
            },
            'th': {
                'title': 'ไพ่ทาโรต์ใช่/ไม่ใช่ — วิธีและรายการไพ่ | Veila',
                'desc':  'วิธีอ่านไพ่ทาโรต์แบบใช่/ไม่ใช่ — วิธีเปิดใบเดียว ไพ่ที่เอนไปทางใช่ ไพ่ที่เอนไปทางไม่ใช่ และเมื่อไหร่ควรใช้ผังเต็มแทน',
                'eyebrow': 'คำถามแบบเรียบง่ายกว่า',
                'h1_html': 'ไพ่ทาโรต์<em>ใช่/ไม่ใช่</em>',
                'lede': 'ใช่/ไม่ใช่คือคำถามที่ไพ่ทาโรต์ไม่ได้ถูกสร้างมาให้ตอบที่สุด แต่กลับถูกถามมากที่สุด ไพ่ทำงานด้วยความละเอียดอ่อน คำตอบสองทางจึงทำให้มันแบนลง แต่ก็มีวิธี และเมื่อใช้ดี มันให้ผลที่มีประโยชน์น่าประหลาดใจ — มักด้วยการเปลี่ยนกรอบคำถามที่คุณตั้งใจถามจริงๆ',
                'intro': 'วิธีนั้นง่าย — สับไพ่พร้อมตั้งคำถามในใจ เปิดไพ่ใบเดียว และอ่านแนวโน้มของมัน ไพ่ตั้งตรงมักโน้มไปทางใช่ ไพ่กลับหัวมักโน้มไปทางไม่ใช่ ไพ่เมเจอร์มีน้ำหนักมากกว่าไพ่ไมเนอร์ ถ้าไพ่กำกวม การอ่านก็กำลังบอกอะไรคุณอยู่เช่นกัน — ว่าสถานการณ์ไม่ใช่เรื่องสองทาง และคำถามอาจต้องการการเรียบเรียงใหม่',
                'list_heading_yes': 'ไพ่ที่เอนไปทางใช่',
                'list_heading_no':  'ไพ่ที่เอนไปทางไม่ใช่',
            },
        },
        'is_yes_no': True,
    },
}


def hub_card_item(card, lang):
    name = card['name'][lang]
    rom = card['roman']
    kw = (card['upright'].get('keywords') or {}).get(lang, '') or ''
    return f'''      <li><a href="{card_path(card, lang)}">
        <div class="hcl-rom">{rom}</div>
        <div class="hcl-body">
          <div class="hcl-name">{escape(name)}</div>
          <div class="hcl-kw">{escape(kw)}</div>
        </div>
      </a></li>'''


def hub_suit_block(suit, lang):
    """Used by /minor-arcana/ to list the four suits."""
    suit_name = SUIT_EN[suit] if lang == 'en' else SUIT_TH[suit]
    href = hub_path(SUIT_HUB_SLUG[suit], lang)
    intros = {
        ('cups', 'en'):       'Water · feeling, intimacy, relationship.',
        ('cups', 'th'):       'น้ำ · ความรู้สึก ความใกล้ชิด ความสัมพันธ์',
        ('wands', 'en'):      'Fire · will, vocation, the creative spark.',
        ('wands', 'th'):      'ไฟ · เจตจำนง อาชีพ ประกายความคิดสร้างสรรค์',
        ('swords', 'en'):     'Air · mind, language, clarity, conflict.',
        ('swords', 'th'):     'ลม · จิตใจ ภาษา ความชัดเจน ความขัดแย้ง',
        ('pentacles', 'en'):  'Earth · body, craft, money, slow accumulation.',
        ('pentacles', 'th'):  'ดิน · กาย งานฝีมือ เงิน การสะสมแบบช้าๆ',
    }
    label = 'The Suit of' if lang == 'en' else 'ไพ่ชุด'
    if lang == 'en':
        full = f'{label} {suit_name}'
    else:
        full = f'{label}{suit_name}'
    return f'''      <li><a href="{href}">
        <div class="hcl-rom">14</div>
        <div class="hcl-body">
          <div class="hcl-name">{escape(full)}</div>
          <div class="hcl-kw">{escape(intros[(suit, lang)])}</div>
        </div>
      </a></li>'''


def render_yes_no_lists(lang, by_id):
    meta = HUB_DEFS['yes-no-tarot']['meta'][lang]
    yes_ids = TOPICAL_CARD_IDS['yes']
    no_ids = TOPICAL_CARD_IDS['no']
    yes_items = '\n'.join(hub_card_item(by_id[i], lang) for i in yes_ids if i in by_id)
    no_items = '\n'.join(hub_card_item(by_id[i], lang) for i in no_ids if i in by_id)
    return f'''  <section class="hub-cards">
    <h2>{escape(meta['list_heading_yes'])}</h2>
    <ol class="hub-card-list">
{yes_items}
    </ol>
  </section>

  <section class="hub-cards">
    <h2>{escape(meta['list_heading_no'])}</h2>
    <ol class="hub-card-list">
{no_items}
    </ol>
  </section>'''


def render_hub(slug, lang):
    spec = HUB_DEFS[slug]
    meta = spec['meta'][lang]
    en_path = hub_path(slug, 'en')
    th_path = hub_path(slug, 'th')
    canonical = en_path if lang == 'en' else th_path
    by_id = deck_by_id()

    crumbs = breadcrumb_for_hub(slug, lang)
    crumbs_jsonld = breadcrumb_jsonld(crumbs)
    article_jsonld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": meta['title'],
        "description": meta['desc'],
        "image": "https://veilatarot.com/og.png",
        "inLanguage": 'en-US' if lang == 'en' else 'th-TH',
        "datePublished": BUILD_DATE,
        "dateModified": BUILD_DATE,
        "publisher": {"@type": "Organization", "name": "Veila", "url": "https://veilatarot.com/"},
        "mainEntityOfPage": f"https://veilatarot.com{canonical}"
    }
    head = render_head_block(
        title=meta['title'], desc=meta['desc'],
        canonical=canonical, en_path=en_path, th_path=th_path, lang=lang,
        extra_jsonld=[article_jsonld, crumbs_jsonld]
    )

    # Body content
    body_html = f'''  {render_breadcrumb_html(crumbs)}
  <div class="eyebrow">{escape(meta['eyebrow'])}</div>
  <h1 class="title">{meta['h1_html']}</h1>
  <p class="lede">{escape(meta['lede'])}</p>

  <div class="divider"><span class="line"></span><span class="mark"></span><span class="line"></span></div>

  <p>{escape(meta['intro'])}</p>'''

    if spec.get('is_yes_no'):
        body_html += '\n\n' + render_yes_no_lists(lang, by_id)
    elif spec.get('is_suit_index'):
        # /minor-arcana/ lists four suit hubs
        body_html += f'''

  <section class="hub-cards">
    <h2>{escape(meta['list_heading'])}</h2>
    <ol class="hub-card-list">
{chr(10).join(hub_suit_block(s, lang) for s in ('wands', 'cups', 'swords', 'pentacles'))}
    </ol>
  </section>'''
    elif 'topical_key' in spec:
        # /tarot-love-readings/, /career-tarot-reading/
        ids = TOPICAL_CARD_IDS[spec['topical_key']]
        items = '\n'.join(hub_card_item(by_id[i], lang) for i in ids if i in by_id)
        body_html += f'''

  <section class="hub-cards">
    <h2>{escape(meta['list_heading'])}</h2>
    <ol class="hub-card-list">
{items}
    </ol>
  </section>'''
    else:
        # Generic card listing (Major Arcana, four suit hubs)
        cards = [c for c in DECK if spec['card_filter'](c)]
        cards.sort(key=spec.get('sort_key', lambda c: c['id']))
        items = '\n'.join(hub_card_item(c, lang) for c in cards)
        body_html += f'''

  <section class="hub-cards">
    <h2>{escape(meta['list_heading'])}</h2>
    <ol class="hub-card-list">
{items}
    </ol>
  </section>'''

    # CTA row
    if lang == 'en':
        cta_main = 'Begin a Celtic Cross Reading'
        cta_about = 'About the Spread'
        cta_daily = 'Daily Card'
        celtic_href, daily_href = '/celtic-cross-tarot/', '/daily-tarot-card/'
    else:
        cta_main = 'เริ่มอ่านเซลติกครอส'
        cta_about = 'เกี่ยวกับผังการอ่าน'
        cta_daily = 'ไพ่ประจำวัน'
        celtic_href, daily_href = '/th/celtic-cross-tarot/', '/th/daily-tarot-card/'

    cta_html = f'''
  <div class="cta-row">
    <a href="/" class="cta-btn">{escape(cta_main)}</a>
    <a href="{celtic_href}" class="cta-btn ghost">{escape(cta_about)}</a>
    <a href="{daily_href}" class="cta-btn ghost">{escape(cta_daily)}</a>
  </div>'''

    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
{head}</head>
<body>

{render_header(en_path, th_path, lang)}

<main class="article hub-page">
{body_html}
{cta_html}
</main>

{render_footer(lang)}

</body>
</html>
'''

# ---------------------------------------------------------------------------
# HTML SITEMAP — /all-tarot-pages/
# ---------------------------------------------------------------------------

def render_all_tarot_pages(lang):
    deck = sorted(DECK, key=lambda c: c['id'])
    majors = [c for c in deck if c['arcana'] == 'major']
    suits = {
        s: [c for c in deck if c.get('suit') == s]
        for s in ('wands', 'cups', 'swords', 'pentacles')
    }
    if lang == 'en':
        meta = {
            'title': 'All Veila Tarot Pages — Site Index | Veila',
            'desc':  'A complete directory of every page on Veila Tarot — hubs, the Celtic Cross guide, daily card, and all 78 card meaning pages.',
            'eyebrow': 'Site Index',
            'h1_html': 'All <em>Veila Tarot</em> Pages',
            'lede': 'A directory of everything on the site, grouped by area. Use this as a fast index when you know roughly what you are after.',
            'sec_practice': 'The Practice',
            'sec_hubs': 'Hubs',
            'sec_topical': 'Topical Reading Guides',
            'sec_major': 'Major Arcana — 22 Cards',
            'sec_minor': 'Minor Arcana — by Suit',
            'sec_utility': 'Utility',
            'utility_self': 'All Pages (this page)',
            'practice_begin': 'Begin a Celtic Cross Reading',
            'practice_daily': "Today's Daily Card",
            'practice_guide': 'The Celtic Cross — A Beginner\'s Guide',
            'hub_major':      'The Major Arcana — 22 Trumps',
            'hub_minor':      'The Minor Arcana — Overview',
            'hub_cups':       'The Suit of Cups (14)',
            'hub_swords':     'The Suit of Swords (14)',
            'hub_wands':      'The Suit of Wands (14)',
            'hub_pentacles':  'The Suit of Pentacles (14)',
            'hub_love':       'Tarot for Love & Relationships',
            'hub_career':     'Tarot for Career & Calling',
            'hub_yesno':      'Yes/No Tarot Readings',
        }
        link_prefix = ''
    else:
        meta = {
            'title': 'ทุกหน้าของ Veila Tarot — สารบัญเว็บไซต์ | Veila',
            'desc':  'สารบัญทุกหน้าใน Veila Tarot — ฮับเนื้อหา คู่มือเซลติกครอส ไพ่ประจำวัน และหน้าความหมายไพ่ทั้ง 78 ใบ',
            'eyebrow': 'สารบัญเว็บไซต์',
            'h1_html': 'ทุกหน้าของ <em>Veila Tarot</em>',
            'lede': 'สารบัญทุกอย่างบนเว็บไซต์ จัดกลุ่มตามหมวด ใช้เป็นดัชนีอย่างรวดเร็วเมื่อรู้คร่าวๆ ว่ากำลังหาอะไร',
            'sec_practice': 'การฝึกปฏิบัติ',
            'sec_hubs': 'ฮับเนื้อหา',
            'sec_topical': 'คู่มือการอ่านตามหัวข้อ',
            'sec_major': 'ไพ่ชุดเมเจอร์ — 22 ใบ',
            'sec_minor': 'ไพ่ชุดไมเนอร์ — แยกตามชุด',
            'sec_utility': 'ยูทิลิตี',
            'utility_self': 'ทุกหน้า (หน้านี้)',
            'practice_begin': 'เริ่มอ่านเซลติกครอส',
            'practice_daily': 'ไพ่ประจำวันนี้',
            'practice_guide': 'เซลติกครอส — คู่มือสำหรับผู้เริ่มต้น',
            'hub_major':      'ไพ่ชุดเมเจอร์ — 22 ทรัมป์',
            'hub_minor':      'ไพ่ชุดไมเนอร์ — ภาพรวม',
            'hub_cups':       'ไพ่ชุดถ้วย (14)',
            'hub_swords':     'ไพ่ชุดดาบ (14)',
            'hub_wands':      'ไพ่ชุดไม้เท้า (14)',
            'hub_pentacles':  'ไพ่ชุดเหรียญ (14)',
            'hub_love':       'ไพ่ทาโรต์เพื่อความรัก',
            'hub_career':     'ไพ่ทาโรต์เพื่อการงาน',
            'hub_yesno':      'ไพ่ทาโรต์ใช่/ไม่ใช่',
        }
        link_prefix = '/th'

    def L(p):
        # Always use TH-prefixed link when lang=th
        return f'{link_prefix}{p}'

    def list_block(items):
        # items: list of (href, label) -> <ul class="all-list">
        lis = '\n'.join(
            f'      <li><a href="{href}">{escape(label)}</a></li>'
            for href, label in items
        )
        return f'    <ul class="all-list">\n{lis}\n    </ul>'

    def card_grid(cards):
        lis = '\n'.join(
            f'      <li><a href="{L(card_path(c, "en"))}">{escape(c["name"][lang])}</a></li>'
            for c in cards
        )
        return f'    <ul class="all-list cols">\n{lis}\n    </ul>'

    en_path = hub_path('all-tarot-pages', 'en')
    th_path_url = hub_path('all-tarot-pages', 'th')
    canonical = en_path if lang == 'en' else th_path_url

    crumbs = [
        home_crumb(lang),
        (('Site Index' if lang == 'en' else 'สารบัญเว็บไซต์'),
         f'https://veilatarot.com{canonical}'),
    ]
    article_jsonld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": meta['title'],
        "description": meta['desc'],
        "image": "https://veilatarot.com/og.png",
        "inLanguage": 'en-US' if lang == 'en' else 'th-TH',
        "datePublished": BUILD_DATE,
        "dateModified": BUILD_DATE,
        "publisher": {"@type": "Organization", "name": "Veila", "url": "https://veilatarot.com/"},
        "mainEntityOfPage": f"https://veilatarot.com{canonical}"
    }
    head = render_head_block(
        title=meta['title'], desc=meta['desc'],
        canonical=canonical, en_path=en_path, th_path=th_path_url, lang=lang,
        extra_jsonld=[article_jsonld, breadcrumb_jsonld(crumbs)]
    )

    body = f'''  {render_breadcrumb_html(crumbs)}
  <div class="eyebrow">{escape(meta['eyebrow'])}</div>
  <h1 class="title">{meta['h1_html']}</h1>
  <p class="lede">{escape(meta['lede'])}</p>

  <div class="divider"><span class="line"></span><span class="mark"></span><span class="line"></span></div>

  <section>
    <h2>{escape(meta['sec_practice'])}</h2>
{list_block([
    (L('/'), meta['practice_begin']),
    (L('/daily-tarot-card/'), meta['practice_daily']),
    (L('/celtic-cross-tarot/'), meta['practice_guide']),
])}
  </section>

  <section>
    <h2>{escape(meta['sec_hubs'])}</h2>
{list_block([
    (L('/major-arcana/'), meta['hub_major']),
    (L('/minor-arcana/'), meta['hub_minor']),
    (L('/cups-tarot-meanings/'), meta['hub_cups']),
    (L('/swords-tarot-meanings/'), meta['hub_swords']),
    (L('/wands-tarot-meanings/'), meta['hub_wands']),
    (L('/pentacles-tarot-meanings/'), meta['hub_pentacles']),
])}
  </section>

  <section>
    <h2>{escape(meta['sec_topical'])}</h2>
{list_block([
    (L('/tarot-love-readings/'), meta['hub_love']),
    (L('/career-tarot-reading/'), meta['hub_career']),
    (L('/yes-no-tarot/'), meta['hub_yesno']),
])}
  </section>

  <section>
    <h2>{escape(meta['sec_major'])}</h2>
{card_grid(majors)}
  </section>

  <section>
    <h2>{escape(meta['sec_minor'])}</h2>
    <h3>{escape(meta['hub_wands'])}</h3>
{card_grid(suits['wands'])}
    <h3>{escape(meta['hub_cups'])}</h3>
{card_grid(suits['cups'])}
    <h3>{escape(meta['hub_swords'])}</h3>
{card_grid(suits['swords'])}
    <h3>{escape(meta['hub_pentacles'])}</h3>
{card_grid(suits['pentacles'])}
  </section>

  <section>
    <h2>{escape(meta['sec_utility'])}</h2>
{list_block([
    (canonical, meta['utility_self']),
])}
  </section>'''

    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
{head}</head>
<body>

{render_header(en_path, th_path_url, lang)}

<main class="article">
{body}
</main>

{render_footer(lang)}

</body>
</html>
'''

# ---------------------------------------------------------------------------
# RSS FEED — /feed.xml
# ---------------------------------------------------------------------------

def build_feed():
    """RSS 2.0 feed of the homepage + 5 standalone evergreens + all 9 hubs."""
    items_data = [
        ('/', 'Veila Tarot — Begin a Celtic Cross Reading',
         'A quiet bilingual Celtic Cross tarot reading.'),
        ('/celtic-cross-tarot/',
         "The Celtic Cross Tarot Spread — A Beginner's Guide",
         "The most enduring ten-card tarot spread. History, position meanings, and how to read it."),
        ('/daily-tarot-card/',
         'Daily Tarot Card — A One-Card Practice',
         'One tarot card drawn fresh each day. A small, considered practice for reflection.'),
        ('/all-tarot-pages/',
         'All Veila Tarot Pages — Site Index',
         'A directory of every page on Veila Tarot, grouped by area.'),
    ]
    for slug in HUB_SLUGS:
        spec = HUB_DEFS[slug]
        items_data.append((
            f'/{slug}/',
            spec['meta']['en']['title'],
            spec['meta']['en']['desc'],
        ))

    items_xml = []
    for path, title, desc in items_data:
        url = f'https://veilatarot.com{path}'
        items_xml.append(
            f'    <item>\n'
            f'      <title>{escape(title)}</title>\n'
            f'      <link>{url}</link>\n'
            f'      <description>{escape(desc)}</description>\n'
            f'      <pubDate>{BUILD_DATE_RFC822}</pubDate>\n'
            f'      <guid isPermaLink="true">{url}</guid>\n'
            f'    </item>'
        )

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Veila Tarot</title>
    <link>https://veilatarot.com/</link>
    <description>A quiet bilingual Celtic Cross tarot reading.</description>
    <language>en</language>
    <lastBuildDate>{BUILD_DATE_RFC822}</lastBuildDate>
    <atom:link href="https://veilatarot.com/feed.xml" rel="self" type="application/rss+xml" />
{chr(10).join(items_xml)}
  </channel>
</rss>
'''

# ---------------------------------------------------------------------------
# SITEMAP
# ---------------------------------------------------------------------------

def build_sitemap(card_slugs):
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']

    def url_block(loc, priority, changefreq):
        return (f'  <url>\n'
                f'    <loc>https://veilatarot.com{loc}</loc>\n'
                f'    <lastmod>{BUILD_DATE}</lastmod>\n'
                f'    <changefreq>{changefreq}</changefreq>\n'
                f'    <priority>{priority}</priority>\n'
                f'  </url>')

    for loc, priority, changefreq in STATIC_URLS:
        out.append(url_block(loc, priority, changefreq))
    for slug in HUB_SLUGS:
        out.append(url_block(f'/{slug}/', '0.7', 'monthly'))
        out.append(url_block(f'/th/{slug}/', '0.6', 'monthly'))
    for sl in card_slugs:
        out.append(url_block(f'/cards/{sl}/', '0.6', 'monthly'))
        out.append(url_block(f'/th/cards/{sl}/', '0.5', 'monthly'))
    out.append('</urlset>')
    return '\n'.join(out) + '\n'

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    deck = sorted(DECK, key=lambda c: c['id'])
    n = len(deck)

    # Clean previous output so removed cards/hubs leave no orphans.
    for path in [ROOT / 'cards', ROOT / 'th' / 'cards']:
        if path.exists():
            shutil.rmtree(path)
    for slug in HUB_SLUGS + ['all-tarot-pages']:
        for path in [ROOT / slug, ROOT / 'th' / slug]:
            if path.exists():
                shutil.rmtree(path)

    # Cards
    print(f'Cards: writing {n} × 2 = {n * 2} pages...')
    slugs = []
    for i, card in enumerate(deck):
        prev_card = deck[(i - 1) % n]
        next_card = deck[(i + 1) % n]
        sl = card_slug(card)
        slugs.append(sl)
        for lang in LANGS:
            out_dir = (ROOT if lang == 'en' else ROOT / 'th') / 'cards' / sl
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / 'index.html').write_text(
                render_card(card, prev_card, next_card, lang), encoding='utf-8'
            )

    # Hubs
    print(f'Hubs:  writing {len(HUB_SLUGS)} × 2 = {len(HUB_SLUGS) * 2} pages...')
    for slug in HUB_SLUGS:
        for lang in LANGS:
            out_dir = (ROOT if lang == 'en' else ROOT / 'th') / slug
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / 'index.html').write_text(render_hub(slug, lang), encoding='utf-8')

    # HTML sitemap (/all-tarot-pages/)
    for lang in LANGS:
        out_dir = (ROOT if lang == 'en' else ROOT / 'th') / 'all-tarot-pages'
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / 'index.html').write_text(render_all_tarot_pages(lang), encoding='utf-8')

    # RSS feed
    (ROOT / 'feed.xml').write_text(build_feed(), encoding='utf-8')

    # XML sitemap
    (ROOT / 'sitemap.xml').write_text(build_sitemap(slugs), encoding='utf-8')

    total_urls = len(STATIC_URLS) + 2 * len(HUB_SLUGS) + 2 * n
    print(f'  cards: {n * 2}')
    print(f'  hubs:  {len(HUB_SLUGS) * 2}')
    print(f'  all-tarot-pages: 2')
    print(f'  feed.xml + sitemap.xml')
    print(f'  sitemap URLs: {total_urls}')


if __name__ == '__main__':
    main()
