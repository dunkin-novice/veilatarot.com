#!/usr/bin/env python3
"""Generate /cards/<slug>/ and /th/cards/<slug>/ pages from cards.json
plus a fresh sitemap.xml covering every URL on the site.

Re-run anytime cards.json changes; the cards/ trees and sitemap are
fully regenerated.

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

# Non-card URLs that also appear in the sitemap.
STATIC_URLS = [
    ('/',                       '1.0', 'monthly'),
    ('/celtic-cross-tarot/',    '0.8', 'monthly'),
    ('/th/celtic-cross-tarot/', '0.7', 'monthly'),
    ('/daily-tarot-card/',      '0.8', 'daily'),
    ('/th/daily-tarot-card/',   '0.7', 'daily'),
]


def card_slug(card):
    """01-the-fool -> the-fool"""
    return re.sub(r'^\d{2}-', '', card['id'])


def arcana_label(card, lang):
    if card['arcana'] == 'major':
        if lang == 'en':
            return f"Major Arcana · {card['roman']}"
        return f"ไพ่ชุดเมเจอร์ · {card['roman']}"
    suit = (SUIT_EN if lang == 'en' else SUIT_TH)[card['suit']]
    if lang == 'en':
        return f"Minor Arcana · {suit}"
    return f"ไพ่ชุดไมเนอร์ · {suit}"


def meta_description(card, lang):
    name = card['name'][lang]
    kw_up = (card['upright'].get('keywords') or {}).get(lang, '') or ''
    if lang == 'en':
        return f"{name} tarot card meaning: {kw_up}. Upright, reversed, and all ten Celtic Cross positions explained."
    return f"ความหมายไพ่ {name}: {kw_up} คำทำนายไพ่ตั้งตรง ไพ่กลับหัว และทั้งสิบตำแหน่งของผังเซลติกครอส"


def i18n(lang):
    if lang == 'en':
        return {
            'h2_up_suffix': '— Upright',
            'h2_rev_suffix': '— Reversed',
            'h2_cc': 'In the Celtic Cross spread',
            'cc_lede_tmpl': 'How {name} reads in each of the ten Celtic Cross positions.',
            'prev_label': 'Previous',
            'next_label': 'Next',
            'cta_main': 'Begin a Reading',
            'cta_about': 'About the Spread',
            'cta_daily': 'Daily Card',
            'fineprint': 'For reflection, not prediction.',
            'brand_sub': 'A Tarot Practice',
            'brand_aria': 'Veila — return to home',
            'lang_aria': 'Language',
            'up_label': 'Upright',
            'rev_label': 'Reversed',
            'nav_celtic': 'Celtic Cross Guide',
            'nav_daily': 'Daily Tarot Card',
            'adj_aria': 'Adjacent cards',
            'title_tail': 'Tarot Card — Upright, Reversed & Celtic Cross | Veila',
        }
    return {
        'h2_up_suffix': '— ตั้งตรง',
        'h2_rev_suffix': '— กลับหัว',
        'h2_cc': 'ในผังเซลติกครอส',
        'cc_lede_tmpl': 'การอ่านไพ่ {name} ในแต่ละตำแหน่งของผังเซลติกครอสทั้งสิบตำแหน่ง',
        'prev_label': 'ก่อนหน้า',
        'next_label': 'ถัดไป',
        'cta_main': 'เริ่มอ่านไพ่',
        'cta_about': 'เกี่ยวกับผังการอ่าน',
        'cta_daily': 'ไพ่ประจำวัน',
        'fineprint': 'เพื่อการใคร่ครวญ ไม่ใช่การพยากรณ์',
        'brand_sub': 'การทำสมาธิกับไพ่',
        'brand_aria': 'Veila — กลับสู่หน้าแรก',
        'lang_aria': 'ภาษา',
        'up_label': 'ตั้งตรง',
        'rev_label': 'กลับหัว',
        'nav_celtic': 'คู่มือเซลติกครอส',
        'nav_daily': 'ไพ่ประจำวัน',
        'adj_aria': 'ไพ่ข้างเคียง',
        'title_tail': 'ความหมายไพ่ทาโรต์ — ตั้งตรง กลับหัว และเซลติกครอส | Veila',
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
    desc = meta_description(card, lang)
    t = i18n(lang)
    title = (
        f"{name} {t['title_tail']}" if lang == 'en'
        else f"{t['title_tail'].replace('ความหมายไพ่ทาโรต์', f'ความหมายไพ่ {name}')}"
    )
    en_path = f"/cards/{sl}/"
    th_path = f"/th/cards/{sl}/"
    canonical = en_path if lang == 'en' else th_path
    page_url = f"https://veilatarot.com{canonical}"

    # Celtic Cross blocks
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

    prev_sl = card_slug(prev_card)
    next_sl = card_slug(next_card)
    prev_name = prev_card['name'][lang]
    next_name = next_card['name'][lang]
    base_path = '/th/cards/' if lang == 'th' else '/cards/'
    prev_url = f"{base_path}{prev_sl}/"
    next_url = f"{base_path}{next_sl}/"

    link_celtic = '/th/celtic-cross-tarot/' if lang == 'th' else '/celtic-cross-tarot/'
    link_daily = '/th/daily-tarot-card/' if lang == 'th' else '/daily-tarot-card/'

    og_locale = 'en_US' if lang == 'en' else 'th_TH'
    og_locale_alt = 'th_TH' if lang == 'en' else 'en_US'
    in_language = 'en-US' if lang == 'en' else 'th-TH'

    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8" />
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

<meta property="og:type" content="article" />
<meta property="og:site_name" content="Veila" />
<meta property="og:title" content="{escape(title, quote=True)}" />
<meta property="og:description" content="{escape(desc, quote=True)}" />
<meta property="og:url" content="{page_url}" />
<meta property="og:image" content="https://veilatarot.com/og.png" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:locale" content="{og_locale}" />
<meta property="og:locale:alternate" content="{og_locale_alt}" />

<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{escape(title, quote=True)}" />
<meta name="twitter:description" content="{escape(desc, quote=True)}" />
<meta name="twitter:image" content="https://veilatarot.com/og.png" />

<link rel="icon" href="/favicon.svg" type="image/svg+xml" />
<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png" />
<link rel="apple-touch-icon" href="/apple-touch-icon.png" sizes="180x180" />
<link rel="manifest" href="/manifest.webmanifest" />

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

<script type="application/ld+json">
{json.dumps({
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": title,
    "description": desc,
    "image": "https://veilatarot.com/og.png",
    "inLanguage": in_language,
    "datePublished": BUILD_DATE,
    "dateModified": BUILD_DATE,
    "publisher": {
        "@type": "Organization",
        "name": "Veila",
        "url": "https://veilatarot.com/"
    },
    "mainEntityOfPage": page_url
}, ensure_ascii=False, indent=2)}
</script>
</head>
<body>

<header class="site-header">
  <a class="brand" href="/" aria-label="{escape(t['brand_aria'], quote=True)}">Veila<span class="dot"></span><span class="brand-sub">{escape(t['brand_sub'])}</span></a>
  <div class="lang-toggle" role="group" aria-label="{escape(t['lang_aria'], quote=True)}">
    <a href="{en_path}"{' class="active"' if lang == 'en' else ''}>EN</a>
    <span class="sep">·</span>
    <a href="{th_path}"{' class="active"' if lang == 'th' else ''}>TH</a>
  </div>
</header>

<main class="article card-page">
  <div class="eyebrow">{escape(label)}</div>
  <h1 class="title">{escape(name)}</h1>
  <p class="archetype">{escape(archetype)}</p>

  <section class="meaning-block">
    <h2>{escape(name)} {escape(t['h2_up_suffix'])}</h2>
    <p class="card-keywords">{escape(up_kw)}</p>
    <p>{escape(up_text)}</p>
  </section>

  <section class="meaning-block">
    <h2>{escape(name)} {escape(t['h2_rev_suffix'])}</h2>
    <p class="card-keywords">{escape(rev_kw)}</p>
    <p>{escape(rev_text)}</p>
  </section>

  <section class="cc-section">
    <h2>{escape(t['h2_cc'])}</h2>
    <p class="cc-lede">{escape(t['cc_lede_tmpl'].format(name=name))}</p>
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

  <div class="cta-row">
    <a href="/" class="cta-btn">{escape(t['cta_main'])}</a>
    <a href="{link_celtic}" class="cta-btn ghost">{escape(t['cta_about'])}</a>
    <a href="{link_daily}" class="cta-btn ghost">{escape(t['cta_daily'])}</a>
  </div>
</main>

<footer>
  <div class="fineprint">{escape(t['fineprint'])}</div>
  <nav class="footer-nav">
    <a href="{link_celtic}">{escape(t['nav_celtic'])}</a>
    <span class="sep">·</span>
    <a href="{link_daily}">{escape(t['nav_daily'])}</a>
  </nav>
  <div>veilatarot.com · © MMXXVI</div>
</footer>

</body>
</html>
'''


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
    for sl in card_slugs:
        out.append(url_block(f'/cards/{sl}/', '0.6', 'monthly'))
        out.append(url_block(f'/th/cards/{sl}/', '0.5', 'monthly'))
    out.append('</urlset>')
    return '\n'.join(out) + '\n'


def main():
    deck = sorted(DECK, key=lambda c: c['id'])
    n = len(deck)
    print(f'Generating {n} cards × 2 languages = {n * 2} pages...')

    # Clean previous output so removed cards leave no orphans.
    for base in [ROOT / 'cards', ROOT / 'th' / 'cards']:
        if base.exists():
            shutil.rmtree(base)

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
                render_card(card, prev_card, next_card, lang),
                encoding='utf-8'
            )

    sitemap_path = ROOT / 'sitemap.xml'
    sitemap_path.write_text(build_sitemap(slugs), encoding='utf-8')

    total_urls = len(STATIC_URLS) + 2 * n
    print(f'  wrote {n * 2} card pages')
    print(f'  wrote sitemap with {total_urls} URLs')


if __name__ == '__main__':
    main()
