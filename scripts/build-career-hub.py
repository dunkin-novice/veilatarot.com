#!/usr/bin/env python3
"""Generate the Career vertical hub at /career/ (EN) and /th/career/ (TH).

Mirrors the portal (index.html) brand system + header/vertical-nav/footer/i18n.
Lists all 18 career questions grouped by pillar, each deep-linking into the
/career/reading/ app via ?q=<slug>. Bilingual via the same in-page T-dict
toggle the portal uses (localStorage 'veila-lang'); EN and TH files differ only
in lang default, canonical/hreflang/og, and the locale-specific hrefs.

Re-runnable. Reads the question set from assets/career-questions.js.
"""
import json, os, re

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
QJS = os.path.join(REPO, "assets/career-questions.js")

# ---- question set ----
def load_questions():
    raw = open(QJS, encoding="utf-8").read()
    m = re.search(r"\[(.*)\]", raw, re.S)
    arr = json.loads("[" + m.group(1) + "]")
    return arr

# ---- pillar metadata (display order + bilingual labels/blurbs) ----
PILLARS = [
    ("decision", "Decisions & crossroads", "การตัดสินใจและทางแยก",
     "For the yes-or-no you keep circling — take it, leave it, or move now.",
     "สำหรับคำถามใช่หรือไม่ที่คุณวนคิดอยู่ — รับ ลาออก หรือขยับตอนนี้"),
    ("money", "Money & worth", "เงินและคุณค่า",
     "For pay, value, and the worry underneath — read as direction, not a number.",
     "สำหรับเรื่องค่าตอบแทน คุณค่า และความกังวลที่อยู่ข้างใต้ — อ่านเป็นทิศทาง ไม่ใช่ตัวเลข"),
    ("growth", "Growth & momentum", "การเติบโตและจังหวะ",
     "For the work that feels stuck, and where the next step actually is.",
     "สำหรับงานที่รู้สึกหยุดนิ่ง และก้าวต่อไปที่อยู่ตรงไหนจริง ๆ"),
    ("fit", "Fit & calling", "ความใช่และเส้นทาง",
     "For whether this is yours — the role, the recognition, the real calling.",
     "สำหรับคำถามว่าสิ่งนี้ใช่ของคุณไหม — บทบาท การยอมรับ และเส้นทางที่ใช่จริง"),
    ("change", "Change & direction", "การเปลี่ยนแปลงและทิศทาง",
     "For the pull toward something different — and what each path opens.",
     "สำหรับแรงดึงไปสู่สิ่งที่ต่างออกไป — และสิ่งที่แต่ละทางเปิดให้"),
]

def build_questions_html(questions, lang, reading_base):
    """Grouped <section>s, EN or TH visible default text + data-i18n for toggle."""
    by = {}
    for q in questions:
        by.setdefault(q["pillar"], []).append(q)
    seo_base = reading_base.replace("reading/", "")  # /career/reading/ -> /career/
    out = []
    for pkey, en_label, th_label, en_blurb, th_blurb in PILLARS:
        items = by.get(pkey, [])
        if not items:
            continue
        rows = []
        for q in items:
            text = q[lang]
            rows.append(
                f'        <li><a href="{reading_base}?q={q["key"]}" '
                f'data-i18n="q_{q["key"]}">{text}</a>'
                f' <a class="qg-about" href="{seo_base}{q["key"]}/" '
                f'data-i18n="q_about">About this question &rarr;</a></li>'
            )
        rows_html = "\n".join(rows)
        out.append(
f'''      <section class="qgroup">
        <h2 class="qg-title" data-i18n="pillar_{pkey}">{en_label if lang=="en" else th_label}</h2>
        <p class="qg-blurb" data-i18n="pillarb_{pkey}">{en_blurb if lang=="en" else th_blurb}</p>
        <ul class="qg-list">
{rows_html}
        </ul>
      </section>''')
    return "\n".join(out)

def build_tdict(questions):
    en = {
        "brandSub": "A Tarot Practice",
        "navLove": "Love", "navCareer": 'Career <span class="tag">New</span>',
        "navHealth": 'Health <span class="tag">Soon</span>',
        "tagNew": "New", "tagSoon": "Soon",
        "eyebrow": "Career & money tarot",
        "headline": "The question your<br>work keeps <em>asking of you.</em>",
        "subhead": "A quiet, reflective tarot reading for crossroads, money, and the path of your work — eighteen questions, in English and Thai. For reflection, not prediction.",
        "ctaStart": "Begin a Career Reading", "ctaBack": "All verticals",
        "listEyebrow": "Eighteen questions to sit with",
        "aeoLabel": "Career Tarot Summary / บทสรุปไพ่การงาน",
        "footerOverview": "Overview", "footerReading": "Career Reading",
        "footerLoveOverview": "Love readings", "footerQuickLove": "Quick Love Reading",
        "footerExplore": "Explore", "footerCeltic": "Celtic Cross",
        "footerDaily": "Daily Card", "footerAll": "All Pages",
        "enter": "Enter →", "comingSoon": "Coming soon",
        "fineprint": "For reflection, not prediction.",
        "q_about": "About this question →",
    }
    th = {
        "brandSub": "พื้นที่ดูไพ่ทาโรต์",
        "navLove": "ความรัก", "navCareer": 'การงาน <span class="tag">ใหม่</span>',
        "navHealth": 'สุขภาพ <span class="tag">เร็ว ๆ นี้</span>',
        "tagNew": "ใหม่", "tagSoon": "เร็ว ๆ นี้",
        "eyebrow": "ไพ่ทาโรต์เรื่องงานและเงิน",
        "headline": "คำถามที่งานของคุณ<br><em>ถามคุณอยู่เสมอ</em>",
        "subhead": "บทอ่านไพ่ทาโรต์อย่างสงบ สำหรับทางแยก เรื่องเงิน และเส้นทางการงานของคุณ — สิบแปดคำถาม ทั้งภาษาไทยและอังกฤษ เพื่อการทบทวนใจ ไม่ใช่การทำนาย",
        "ctaStart": "เริ่มดูไพ่การงาน", "ctaBack": "ดูทุกหมวด",
        "listEyebrow": "สิบแปดคำถามให้ใคร่ครวญ",
        "aeoLabel": "บทสรุปไพ่การงาน / Career Tarot Summary",
        "footerOverview": "ภาพรวม", "footerReading": "ดูไพ่การงาน",
        "footerLoveOverview": "บทอ่านความรัก", "footerQuickLove": "ดูไพ่ความรักแบบเร็ว",
        "footerExplore": "สำรวจ", "footerCeltic": "เซลติกครอส",
        "footerDaily": "ไพ่ประจำวัน", "footerAll": "ทุกหน้า",
        "enter": "เข้าสู่ →", "comingSoon": "เร็ว ๆ นี้",
        "fineprint": "เพื่อการใคร่ครวญ ไม่ใช่การทำนาย",
        "q_about": "อ่านรายละเอียด →",
    }
    for pkey, en_label, th_label, en_blurb, th_blurb in PILLARS:
        en[f"pillar_{pkey}"] = en_label
        th[f"pillar_{pkey}"] = th_label
        en[f"pillarb_{pkey}"] = en_blurb
        th[f"pillarb_{pkey}"] = th_blurb
    for q in questions:
        en[f"q_{q['key']}"] = q["en"]
        th[f"q_{q['key']}"] = q["th"]
    return en, th

# AEO bilingual block (static, both languages always shown)
AEO_EN = ("Veila's Career tarot is a quiet, bilingual 3-card reading for the "
          "turning points of work — whether to take a job or leave it, whether "
          "you're valued or underpaid, what's blocking your growth, and what "
          "your real calling is. Money is read as direction — rising, "
          "tightening, opening — never as amounts or dates. Eighteen questions, "
          "each drawn from the 78 Rider–Waite–Smith cards, for reflection, not "
          "prediction.")
AEO_TH = ("ไพ่การงานของ Veila คือบทอ่านไพ่ 3 ใบสองภาษาอย่างสงบ สำหรับจังหวะสำคัญ"
          "ของการทำงาน — จะรับงานหรือลาออก ถูกเห็นค่าหรือถูกจ่ายน้อย อะไรขวาง"
          "การเติบโต และเส้นทางที่ใช่ของคุณคืออะไร เรื่องเงินถูกอ่านเป็นทิศทาง — "
          "กำลังขยับขึ้น ตึงตัว หรือเปิดออก ไม่ใช่จำนวนเงินหรือวันเวลา สิบแปดคำถาม "
          "แต่ละคำถามทอจากไพ่ Rider–Waite–Smith ทั้ง 78 ใบ เพื่อการใคร่ครวญ ไม่ใช่การทำนาย")

LOCALES = {
    "en": {
        "out": os.path.join(REPO, "career/index.html"),
        "lang": "en", "saved": "en",
        "canonical": "https://veilatarot.com/career/",
        "og_locale": "en_US", "og_locale_alt": "th_TH",
        "brand_href": "/",
        "nav_love": "/love-readings/", "nav_career": "/career/",
        "reading_base": "/career/reading/",
        "f_love": "/love-readings/", "f_quicklove": "/quick-love-reading/",
        "f_celtic": "/celtic-cross-reading/", "f_daily": "/daily-tarot-card/",
        "f_all": "/all-tarot-pages/", "back_href": "/",
    },
    "th": {
        "out": os.path.join(REPO, "th/career/index.html"),
        "lang": "th", "saved": "th",
        "canonical": "https://veilatarot.com/th/career/",
        "og_locale": "th_TH", "og_locale_alt": "en_US",
        "brand_href": "/th/",
        "nav_love": "/th/love-tarot/", "nav_career": "/th/career/",
        "reading_base": "/th/career/reading/",
        "f_love": "/th/love-tarot/", "f_quicklove": "/th/tarot-love-readings/",
        "f_celtic": "/th/celtic-cross-reading/", "f_daily": "/th/daily-tarot-card/",
        "f_all": "/th/all-tarot-pages/", "back_href": "/th/",
    },
}

TEMPLATE = '''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{title}</title>
<meta name="description" content="{meta_desc}" />
<meta name="keywords" content="career tarot, money tarot, job tarot reading, should I quit tarot, career change tarot, ไพ่การงาน, ดูดวงการงาน, ดูดวงการเงิน" />
<meta name="author" content="Veila Tarot" />
<meta name="robots" content="index, follow, max-image-preview:large" />
<meta name="theme-color" content="#0a0a0c" />
<meta name="color-scheme" content="dark" />
<meta name="google-adsense-account" content="ca-pub-2823470980745945">
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="format-detection" content="telephone=no" />

<link rel="canonical" href="{canonical}" />
<link rel="alternate" hreflang="en" href="https://veilatarot.com/career/" />
<link rel="alternate" hreflang="th" href="https://veilatarot.com/th/career/" />
<link rel="alternate" hreflang="x-default" href="https://veilatarot.com/career/" />

<meta property="og:type" content="website" />
<meta property="og:site_name" content="Veila" />
<meta property="og:title" content="{title}" />
<meta property="og:description" content="{meta_desc}" />
<meta property="og:url" content="{canonical}" />
<meta property="og:image" content="https://veilatarot.com/og.png" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:locale" content="{og_locale}" />
<meta property="og:locale:alternate" content="{og_locale_alt}" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{title}" />
<meta name="twitter:description" content="{meta_desc}" />
<meta name="twitter:image" content="https://veilatarot.com/og.png" />

<link rel="icon" href="/favicon.svg" type="image/svg+xml" />
<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png" />
<link rel="apple-touch-icon" href="/apple-touch-icon.png" sizes="180x180" />
<link rel="manifest" href="/manifest.webmanifest" />

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,400&family=IBM+Plex+Sans+Thai:wght@300;400;500;600&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">

<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2823470980745945" crossorigin="anonymous"></script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQWWZ3HT2S"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('set', 'user_properties', {{ site_lang: (document.documentElement.lang || 'en').slice(0,2) }});
  gtag('config', 'G-NQWWZ3HT2S');
</script>
<script src="/assets/analytics.js" defer></script>

<script type="application/ld+json">
{jsonld}
</script>

<style>
:root{{
  --crimson:#8a3a3a; --gold-dim:#7a6645; --gold:#b89968;
  --ink:#0a0a0c; --ivory-dim:#b9b3a4; --ivory-mute:#6c6a63; --ivory:#ebe4d4;
  --panel:#13141a; --rule:#2a2823;
  --sans:"Inter","IBM Plex Sans Thai",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  --serif:"Cormorant Garamond","IBM Plex Sans Thai","Garamond","Times New Roman",serif;
}}
*{{box-sizing:border-box;margin:0;padding:0;}}
html{{overflow-x:hidden;}}
body{{background:var(--ink);color:var(--ivory);font-family:var(--sans);font-weight:300;-webkit-font-smoothing:antialiased;min-height:100vh;display:flex;flex-direction:column;}}

.site-header{{border-bottom:1px solid var(--rule);padding:22px 32px;display:flex;align-items:baseline;justify-content:space-between;gap:24px;flex-wrap:wrap;}}
.brand{{font-family:var(--serif);font-weight:400;font-size:22px;letter-spacing:.16em;text-transform:uppercase;color:var(--ivory);text-decoration:none;cursor:pointer;transition:color .3s ease;}}
.brand:hover{{color:var(--gold);}}
.brand .dot{{display:inline-block;width:4px;height:4px;border-radius:50%;background:var(--gold);margin:0 8px 4px;vertical-align:middle;}}
.brand-sub{{font-family:var(--sans);font-size:10px;letter-spacing:.32em;text-transform:uppercase;color:var(--ivory-mute);font-weight:400;}}
.lang-toggle{{display:inline-flex;align-items:center;gap:8px;font-size:10px;letter-spacing:.28em;text-transform:uppercase;color:var(--ivory-mute);}}
.lang-toggle button{{background:none;border:none;padding:0;cursor:pointer;font:inherit;letter-spacing:inherit;color:var(--ivory-mute);transition:color .3s ease;}}
.lang-toggle button:hover{{color:var(--ivory);}}
.lang-toggle button.active{{color:var(--gold);}}
.lang-toggle .sep{{color:var(--rule);}}

.vertical-nav{{display:flex;align-items:center;gap:26px;padding:14px 32px;border-bottom:1px solid var(--rule);overflow-x:auto;}}
.vertical-nav a,.vertical-nav span{{font-size:12px;letter-spacing:.22em;text-transform:uppercase;text-decoration:none;color:var(--ivory-dim);white-space:nowrap;display:inline-flex;align-items:center;gap:7px;padding:6px 0;position:relative;transition:color .3s ease;}}
.vertical-nav a:hover{{color:var(--ivory);}}
.vertical-nav a[aria-current="page"]{{color:var(--gold);}}
.vertical-nav a[aria-current="page"]::after{{content:"";position:absolute;left:0;right:0;bottom:-15px;height:1px;background:var(--gold);}}
.vertical-nav .tag{{font-size:8px;letter-spacing:.18em;color:var(--ink);background:var(--gold);border-radius:2px;padding:2px 5px;}}
.vertical-nav .vn-soon{{color:var(--ivory-mute);}}
.vertical-nav .vn-soon .tag{{background:none;color:var(--ivory-mute);border:1px solid var(--rule);}}

.layout{{flex:1;}}
.landing{{max-width:820px;margin:0 auto;padding:74px 32px 26px;text-align:center;}}
.eyebrow{{font-size:10px;letter-spacing:.4em;text-transform:uppercase;color:var(--gold-dim);margin-bottom:24px;}}
.headline{{font-family:var(--serif);font-weight:300;font-size:52px;line-height:1.08;letter-spacing:.01em;color:var(--ivory);margin-bottom:22px;}}
.headline em{{font-style:italic;color:var(--gold);}}
.subhead{{font-family:var(--serif);font-size:20px;font-weight:300;line-height:1.5;color:var(--ivory-dim);max-width:580px;margin:0 auto 36px;}}
.ctas{{display:flex;gap:16px;justify-content:center;flex-wrap:wrap;}}
.cta-btn{{font-family:var(--sans);font-size:12px;font-weight:400;letter-spacing:.24em;text-transform:uppercase;padding:17px 34px;border-radius:2px;cursor:pointer;text-decoration:none;transition:all .3s ease;display:inline-block;}}
.cta-primary{{background:var(--gold);color:var(--ink);border:1px solid var(--gold);}}
.cta-primary:hover{{background:var(--ivory);border-color:var(--ivory);}}
.cta-ghost{{background:none;color:var(--ivory-dim);border:1px solid var(--rule);}}
.cta-ghost:hover{{color:var(--ivory);border-color:var(--gold-dim);}}

.questions{{max-width:900px;margin:36px auto 60px;padding:0 32px;}}
.q-eyebrow{{text-align:center;font-size:10px;letter-spacing:.34em;text-transform:uppercase;color:var(--gold-dim);margin-bottom:36px;}}
.qgroup{{margin-bottom:42px;}}
.qg-title{{font-family:var(--serif);font-weight:400;font-size:25px;letter-spacing:.02em;color:var(--ivory);margin-bottom:6px;}}
.qg-blurb{{font-family:var(--serif);font-style:italic;font-size:16px;line-height:1.5;color:var(--ivory-mute);margin-bottom:18px;}}
.qg-list{{list-style:none;display:grid;grid-template-columns:1fr;gap:10px;}}
.qg-list a{{display:block;border:1px solid var(--rule);border-radius:4px;padding:15px 18px;background:rgba(184,153,104,.03);color:var(--ivory-dim);text-decoration:none;font-family:var(--serif);font-size:18px;transition:border-color .3s ease,color .3s ease,background .3s ease;}}
.qg-list a:hover{{border-color:var(--gold-dim);color:var(--ivory);background:rgba(184,153,104,.07);}}
.qg-list li{{display:flex;flex-direction:column;}}
.qg-list a.qg-about{{display:inline-block;align-self:flex-start;border:none;border-radius:0;background:none;padding:6px 2px 0;margin-top:2px;font-family:var(--sans);font-size:11.5px;font-weight:500;letter-spacing:.08em;text-transform:uppercase;color:var(--ivory-mute);}}
.qg-list a.qg-about:hover{{border:none;background:none;color:var(--gold-dim);}}

.aeo-answer-block{{border-left:2px solid var(--gold);padding:24px;margin:10px auto 64px;background:rgba(184,153,104,.03);border-radius:0 12px 12px 0;max-width:820px;text-align:left;}}
.aeo-answer-block .label{{font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.2em;color:var(--gold);margin-bottom:12px;}}
.aeo-answer-block .en{{font-family:var(--serif);font-size:19px;line-height:1.55;color:var(--ivory);font-style:italic;}}
.aeo-answer-block .th{{font-family:var(--sans);font-size:15px;line-height:1.7;color:var(--ivory-dim);margin-top:12px;}}

footer{{border-top:1px solid var(--rule);padding:46px 32px 40px;}}
.footer-cols{{display:grid;grid-template-columns:1fr;gap:24px;max-width:1080px;margin:0 auto 30px;}}
.fc h4{{font-family:var(--serif);font-weight:400;font-size:16px;letter-spacing:.04em;color:var(--ivory);margin-bottom:12px;}}
.fc a,.fc span{{display:block;font-size:13px;letter-spacing:.02em;color:var(--ivory-mute);text-decoration:none;line-height:2;transition:color .3s ease;}}
.fc a:hover{{color:var(--gold);}}
.footer-meta{{max-width:1080px;margin:0 auto;text-align:center;color:var(--ivory-mute);font-size:11px;letter-spacing:.1em;line-height:2.2;}}
.footer-meta .fineprint{{font-family:var(--serif);font-style:italic;font-size:14px;color:var(--ivory-dim);}}

html[lang="th"] .headline,
html[lang="th"] .subhead,
html[lang="th"] .qg-title,
html[lang="th"] .qg-blurb,
html[lang="th"] .qg-list a,
html[lang="th"] .aeo-answer-block .en{{font-family:var(--sans);font-style:normal;}}
html[lang="th"] .headline{{font-size:38px;line-height:1.2;font-weight:300;}}
html[lang="th"] .headline em{{font-style:normal;}}

@media(min-width:720px){{
  .footer-cols{{grid-template-columns:repeat(4,1fr);}}
  .qg-list{{grid-template-columns:1fr 1fr;}}
}}
@media(max-width:560px){{
  .site-header{{padding:18px 22px;}}
  .vertical-nav{{gap:20px;padding:14px 22px;}}
  .landing{{padding:50px 22px 24px;}}
  .eyebrow{{font-size:9px;letter-spacing:.22em;}}
  .headline{{font-size:30px;letter-spacing:0;}}
  html[lang="th"] .headline{{font-size:25px;}}
  .subhead{{font-size:17px;max-width:100%;}}
  .questions{{padding:0 22px;}}
  .cta-btn{{width:100%;text-align:center;}}
  .aeo-answer-block{{margin:10px 22px 50px;}}
  footer{{padding:40px 22px 36px;}}
}}
</style>
</head>
<body>

<header class="site-header">
  <a class="brand" href="{brand_href}" aria-label="Veila — home">Veila<span class="dot"></span><span class="brand-sub" data-i18n="brandSub">A Tarot Practice</span></a>
  <div class="lang-toggle" role="group" aria-label="Language">
    <button type="button" data-lang="en">EN</button>
    <span class="sep">·</span>
    <button type="button" data-lang="th">TH</button>
  </div>
</header>

<nav class="vertical-nav" aria-label="Readings">
  <a href="{nav_love}" data-i18n="navLove">Love</a>
  <a href="{nav_career}" aria-current="page" data-i18n="navCareer">Career <span class="tag" data-i18n="tagNew">New</span></a>
  <span class="vn-soon" data-i18n="navHealth">Health <span class="tag" data-i18n="tagSoon">Soon</span></span>
</nav>

<div class="layout">
  <main>
    <section class="landing">
      <div class="eyebrow" data-i18n="eyebrow">Career & money tarot</div>
      <h1 class="headline" data-i18n-html="headline">{headline_default}</h1>
      <p class="subhead" data-i18n="subhead">{subhead_default}</p>
      <div class="ctas">
        <a href="{reading_base}" class="cta-btn cta-primary" data-i18n="ctaStart">Begin a Career Reading</a>
        <a href="{back_href}" class="cta-btn cta-ghost" data-i18n="ctaBack">All verticals</a>
      </div>
    </section>

    <section class="questions">
      <div class="q-eyebrow" data-i18n="listEyebrow">Eighteen questions to sit with</div>
{questions_html}
    </section>

    <section class="aeo-answer-block">
      <p class="label" data-i18n="aeoLabel">Career Tarot Summary / บทสรุปไพ่การงาน</p>
      <p class="en">{aeo_en}</p>
      <p class="th">{aeo_th}</p>
    </section>
  </main>
</div>

<footer>
  <nav class="footer-cols" aria-label="Footer">
    <div class="fc">
      <h4 data-i18n="navCareer">Career</h4>
      <a href="{nav_career}" data-i18n="footerOverview">Overview</a>
      <a href="{reading_base}" data-i18n="footerReading">Career Reading</a>
    </div>
    <div class="fc">
      <h4 data-i18n="navLove">Love</h4>
      <a href="{f_love}" data-i18n="footerLoveOverview">Love readings</a>
      <a href="{f_quicklove}" data-i18n="footerQuickLove">Quick Love Reading</a>
    </div>
    <div class="fc">
      <h4 data-i18n="navHealth">Health</h4>
      <span data-i18n="comingSoon">Coming soon</span>
    </div>
    <div class="fc">
      <h4 data-i18n="footerExplore">Explore</h4>
      <a href="{f_celtic}" data-i18n="footerCeltic">Celtic Cross</a>
      <a href="{f_daily}" data-i18n="footerDaily">Daily Card</a>
      <a href="{f_all}" data-i18n="footerAll">All Pages</a>
    </div>
  </nav>
  <div class="footer-meta">
    <div class="fineprint" data-i18n="fineprint">For reflection, not prediction.</div>
    <div>veilatarot.com · © MMXXVI</div>
  </div>
</footer>

<script>
(function(){{
  var T = {tdict};
  var HTML_KEYS = {{headline:1, navCareer:1, navHealth:1}};
  function apply(lang){{
    var dict = T[lang] || T.en;
    document.documentElement.lang = lang;
    document.querySelectorAll('[data-i18n]').forEach(function(el){{
      var k = el.getAttribute('data-i18n');
      if(!(k in dict)) return;
      if(HTML_KEYS[k] || el.hasAttribute('data-i18n-html')) el.innerHTML = dict[k];
      else el.textContent = dict[k];
    }});
    document.querySelectorAll('[data-i18n-html]').forEach(function(el){{
      var k = el.getAttribute('data-i18n-html');
      if(k in dict) el.innerHTML = dict[k];
    }});
    document.querySelectorAll('.lang-toggle button').forEach(function(b){{
      b.classList.toggle('active', b.getAttribute('data-lang') === lang);
    }});
    try {{ localStorage.setItem('veila-lang', lang); }} catch(e){{}}
  }}
  var saved = '{saved}';
  try {{ saved = localStorage.getItem('veila-lang') || '{saved}'; }} catch(e){{}}
  apply(saved);
  document.querySelectorAll('.lang-toggle button').forEach(function(b){{
    b.addEventListener('click', function(){{
      var lang = b.getAttribute('data-lang');
      apply(lang);
      if (window.veilaFire) window.veilaFire('lang_toggle', {{ lang: lang, vertical: 'career' }});
    }});
  }});
}})();
</script>

</body>
</html>
'''

def build_jsonld(questions, lc):
    items = []
    for i, q in enumerate(questions, 1):
        items.append({
            "@type": "ListItem", "position": i,
            "name": q["en"],
            "url": "https://veilatarot.com" + lc["reading_base"] + "?q=" + q["key"],
        })
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "@id": lc["canonical"] + "#page",
                "url": lc["canonical"],
                "name": "Career & Money Tarot",
                "isPartOf": {"@id": "https://veilatarot.com/#website"},
                "inLanguage": "th-TH" if lc["lang"] == "th" else "en-US",
                "description": "A bilingual 3-card career tarot reading for work, money, and the path ahead. Eighteen questions, for reflection not prediction.",
            },
            {
                "@type": "ItemList",
                "@id": lc["canonical"] + "#questions",
                "name": "Career tarot questions",
                "numberOfItems": len(items),
                "itemListElement": items,
            },
        ],
    }
    return json.dumps(graph, ensure_ascii=False, indent=2)

def main():
    questions = load_questions()
    assert len(questions) == 18, f"expected 18 questions, got {len(questions)}"
    en_dict, th_dict = build_tdict(questions)

    titles = {
        "en": "Career & Money Tarot — 18 Readings for Work & the Path Ahead | Veila",
        "th": "ไพ่การงานและการเงิน — 18 บทอ่านสำหรับงานและเส้นทางข้างหน้า | Veila",
    }
    metas = {
        "en": "A quiet, bilingual 3-card career tarot reading for crossroads, money, and the path of your work. Eighteen questions in English and Thai. For reflection, not prediction.",
        "th": "บทอ่านไพ่ทาโรต์การงาน 3 ใบสองภาษาอย่างสงบ สำหรับทางแยก เรื่องเงิน และเส้นทางการงาน สิบแปดคำถามทั้งไทยและอังกฤษ เพื่อการใคร่ครวญ ไม่ใช่การทำนาย",
    }

    for code, lc in LOCALES.items():
        qhtml = build_questions_html(questions, code, lc["reading_base"])
        tdict = json.dumps({"en": en_dict, "th": th_dict}, ensure_ascii=False, indent=2)
        d = en_dict if code == "en" else th_dict
        html = TEMPLATE.format(
            lang=lc["lang"], saved=lc["saved"],
            title=titles[code], meta_desc=metas[code],
            canonical=lc["canonical"], og_locale=lc["og_locale"],
            og_locale_alt=lc["og_locale_alt"], brand_href=lc["brand_href"],
            nav_love=lc["nav_love"], nav_career=lc["nav_career"],
            reading_base=lc["reading_base"], back_href=lc["back_href"],
            f_love=lc["f_love"], f_quicklove=lc["f_quicklove"],
            f_celtic=lc["f_celtic"], f_daily=lc["f_daily"], f_all=lc["f_all"],
            headline_default=d["headline"], subhead_default=d["subhead"],
            aeo_en=AEO_EN, aeo_th=AEO_TH,
            questions_html=qhtml, tdict=tdict,
            jsonld=build_jsonld(questions, lc),
        )
        os.makedirs(os.path.dirname(lc["out"]), exist_ok=True)
        open(lc["out"], "w", encoding="utf-8").write(html)
        print(f"OK wrote {lc['out']} ({len(html)} bytes)")

if __name__ == "__main__":
    main()
