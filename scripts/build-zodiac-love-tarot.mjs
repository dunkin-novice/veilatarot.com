/* Veila — Zodiac Love Tarot pillar generator (Love Domination Plan, Phase 2).
   Builds the monthly zodiac love-tarot hub + 12 sign pages, EN + TH with
   reciprocal hreflang. Each sign page carries a UNIQUE 3-card love spread
   drawn for the month (see draw-zodiac-month.mjs) → fresh, non-doorway
   content that triggers FreshnessScore + Topic Authority.

   Reads:  assets/data/zodiac-love/<monthKey>.json  (cards + filled readings)
           cards.json                                 (deck meta: name/roman)
   Writes: /zodiac-love-tarot/{,<sign>/}index.html    (EN)
           /th/zodiac-love-tarot/{,<sign>/}index.html  (TH, primary)

   Usage: node scripts/build-zodiac-love-tarot.mjs [YYYY-MM]   (default: latest)
*/
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { SIGNS, monthLabels } from './zodiac-signs.mjs'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const rootDir = path.resolve(__dirname, '..')
const dataDir = path.join(rootDir, 'assets', 'data', 'zodiac-love')
const siteUrl = 'https://veilatarot.com'

// pick month: arg, else newest <YYYY-MM>.json on disk
let monthKey = process.argv[2]
if (!monthKey) {
  const months = fs.readdirSync(dataDir).filter((f) => /^\d{4}-\d{2}\.json$/.test(f)).map((f) => f.replace('.json', '')).sort()
  monthKey = months[months.length - 1]
}
if (!monthKey) { console.error('No month data found in', dataDir); process.exit(1) }

const month = JSON.parse(fs.readFileSync(path.join(dataDir, `${monthKey}.json`), 'utf8'))
const deck = Object.fromEntries(JSON.parse(fs.readFileSync(path.join(rootDir, 'cards.json'), 'utf8')).map((c) => [c.id, c]))
const labels = monthLabels(monthKey)
const isoDate = `${monthKey}-01`
const thaiDate = `1 ${labels.th}`

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#39;')
}
function jsonLd(value) {
  return JSON.stringify(value, null, 2).replaceAll('</script', '<\\/script').replaceAll('<!--', '<\\!--')
}

const SIGN_BY = Object.fromEntries(SIGNS.map((s) => [s.slug, s]))

// shared <head>; pageType = 'article' | 'website'
function head({ title, description, canonical, enUrl, thUrl, lang, schemas }) {
  const en = lang === 'en'
  return `<!DOCTYPE html>
<html lang="${en ? 'en' : 'th'}">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>${escapeHtml(title)}</title>
<meta name="description" content="${escapeHtml(description)}" />
<meta name="author" content="Veila Tarot" />
<meta name="robots" content="index, follow, max-image-preview:large" />
<meta name="theme-color" content="#0a0a0c" />
<meta name="color-scheme" content="dark" />
<meta name="google-adsense-account" content="ca-pub-2823470980745945" />

<link rel="canonical" href="${canonical}" />
<link rel="alternate" hreflang="en" href="${enUrl}" />
<link rel="alternate" hreflang="th" href="${thUrl}" />
<link rel="alternate" hreflang="x-default" href="${enUrl}" />

<meta property="og:type" content="${schemas.some((s) => s['@type'] === 'Article') ? 'article' : 'website'}" />
<meta property="og:site_name" content="Veila" />
<meta property="og:title" content="${escapeHtml(title)}" />
<meta property="og:description" content="${escapeHtml(description)}" />
<meta property="og:url" content="${canonical}" />
<meta property="og:image" content="${siteUrl}/og.png" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:locale" content="${en ? 'en_US' : 'th_TH'}" />
<meta property="og:locale:alternate" content="${en ? 'th_TH' : 'en_US'}" />

<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="${escapeHtml(title)}" />
<meta name="twitter:description" content="${escapeHtml(description)}" />
<meta name="twitter:image" content="${siteUrl}/og.png" />

<link rel="icon" href="/favicon.svg" type="image/svg+xml" />
<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png" />
<link rel="apple-touch-icon" href="/apple-touch-icon.png" sizes="180x180" />
<link rel="manifest" href="/manifest.webmanifest" />
<link rel="alternate" type="application/rss+xml" title="Veila Tarot — Feed" href="/feed.xml" />

<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,400&family=IBM+Plex+Sans+Thai:wght@300;400;500;600&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="/assets/page.css" />
<style>
  .zodiac-spread { list-style: none; padding: 0; margin: 1.4rem 0; display: grid; gap: 1rem; }
  .zc-card { border: 1px solid var(--hairline, #23232b); border-radius: 14px; padding: 1.1rem 1.2rem; background: rgba(255,255,255,.015); }
  .zc-head { display: flex; align-items: baseline; gap: .6rem; flex-wrap: wrap; margin-bottom: .5rem; }
  .zc-pos { font-size: .72rem; letter-spacing: .12em; text-transform: uppercase; color: var(--text-muted, #858ba3); }
  .zc-name { font-family: "Cormorant Garamond", serif; font-size: 1.32rem; font-weight: 600; }
  html[lang="th"] .zc-name { font-family: "IBM Plex Sans Thai", serif; }
  .zc-roman { font-size: .8rem; color: var(--text-muted, #858ba3); }
  .zc-rev { font-size: .66rem; letter-spacing: .1em; text-transform: uppercase; color: #c98b6b; border: 1px solid #7a5743; border-radius: 999px; padding: .08rem .5rem; }
  .zc-read { margin: 0; line-height: 1.7; }
  .sign-grid { list-style: none; padding: 0; margin: 1.4rem 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: .9rem; }
  .sign-grid a { display: block; border: 1px solid var(--hairline, #23232b); border-radius: 14px; padding: 1rem 1.1rem; text-decoration: none; color: inherit; transition: border-color .15s ease; }
  .sign-grid a:hover { border-color: var(--accent-strong, #3d63e0); }
  .sg-top { display: flex; align-items: center; gap: .5rem; }
  .sg-glyph { font-size: 1.3rem; }
  .sg-name { font-family: "Cormorant Garamond", serif; font-size: 1.2rem; font-weight: 600; }
  html[lang="th"] .sg-name { font-family: "IBM Plex Sans Thai", serif; }
  .sg-dates { font-size: .72rem; color: var(--text-muted, #858ba3); margin: .15rem 0 .5rem; }
  .sg-cards { font-size: .8rem; color: var(--text-muted, #aab); line-height: 1.5; }
</style>

${schemas.map((s) => `<script type="application/ld+json">${jsonLd(s)}</script>`).join('\n')}

<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2823470980745945" crossorigin="anonymous"></script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQWWZ3HT2S"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('set', 'user_properties', { site_lang: '${en ? 'en' : 'th'}' });
  gtag('config', 'G-NQWWZ3HT2S');
</script>
<script src="/assets/analytics.js" defer></script>
</head>`
}

function siteHeader(lang, enUrl, thUrl) {
  const en = lang === 'en'
  return `<header class="site-header">
  <a class="brand" href="/${en ? '' : 'th/'}" aria-label="Veila">Veila<span class="dot"></span><span class="brand-sub">${en ? 'tarot for reflection' : 'การทำสมาธิกับไพ่'}</span></a>
  <div class="lang-toggle" role="group" aria-label="${en ? 'Language' : 'ภาษา'}">
    <a href="${enUrl}"${en ? ' class="active"' : ''}>EN</a>
    <a href="${thUrl}"${en ? '' : ' class="active"'}>TH</a>
  </div>
</header>`
}

function footer(lang) {
  const en = lang === 'en'
  const foot = en
    ? { f1: ['Celtic Cross guide', '/celtic-cross-tarot/'], f2: ['Love readings', '/love-readings/'], f3: ['All pages', '/all-tarot-pages/'], fine: 'For reflection and direction, not a fixed forecast.', up: 'Updated' }
    : { f1: ['คู่มือเซลติกครอส', '/th/celtic-cross-tarot/'], f2: ['บทอ่านความรัก', '/th/tarot-love-readings/'], f3: ['ทุกหน้า', '/th/all-tarot-pages/'], fine: 'เพื่อการใคร่ครวญและอ่านทิศทาง ไม่ใช่การบังคับอนาคต', up: 'อัปเดต' }
  return `<footer>
  <div class="fineprint">${foot.fine}</div>
  <div class="last-updated">${foot.up} · ${en ? labels.en : thaiDate}</div>
  <nav class="footer-nav">
    <a href="${foot.f1[1]}">${foot.f1[0]}</a><span class="sep">·</span>
    <a href="${foot.f2[1]}">${foot.f2[0]}</a><span class="sep">·</span>
    <a href="${foot.f3[1]}">${foot.f3[0]}</a>
  </nav>
  <div>veilatarot.com · © MMXXVI</div>
</footer>

</body>
</html>`
}

function cardName(card, lang) {
  const meta = deck[card.id]
  return { name: lang === 'en' ? meta.name.en : meta.name.th, roman: meta.roman }
}

// fallback AEO summary if the sign has no written summary yet
function fallbackSummary(sign, signData, lang) {
  const names = signData.cards.map((c) => cardName(c, lang).name)
  if (lang === 'en') {
    return `${sign.en}’s love tarot for ${labels.en} draws ${names[0]}, ${names[1]}, and ${names[2]} — a three-card spread reading where your heart stands now, what love is moving toward, and the guidance to carry through the month.`
  }
  return `ดูดวงความรัก${sign.th}ประจำเดือน${labels.th} เปิดไพ่ ${names[0]}, ${names[1]} และ ${names[2]} ผังสามใบที่อ่านหัวใจคุณตอนนี้ สิ่งที่ความรักกำลังเคลื่อนเข้าหา และคำแนะนำสำหรับเดือนนี้`
}

function signFaqs(sign, signData, lang) {
  const names = signData.cards.map((c) => cardName(c, lang).name)
  if (lang === 'en') {
    return [
      { q: `Which tarot cards did ${sign.en} draw for ${labels.en}?`, a: `${names.join(', ')}, read across three positions: where your heart stands now, what love is moving toward, and the cards’ guidance for the month.` },
      { q: `How often does the ${sign.en} love tarot update?`, a: `Once a month. Each new month brings a fresh three-card love spread for ${sign.en}, so it is worth checking back at the start of the month.` },
      { q: `Is this a fixed prediction of my love life?`, a: `No. It reads the present shape and direction of your love life for reflection, not a verdict. What you do with it stays yours.` }
    ]
  }
  return [
    { q: `${sign.th} เปิดไพ่อะไรบ้างในเดือน${labels.th}?`, a: `${names.join(', ')} อ่านผ่านสามตำแหน่ง คือหัวใจคุณตอนนี้ สิ่งที่ความรักกำลังเคลื่อนเข้าหา และคำแนะนำของไพ่สำหรับเดือนนี้` },
    { q: `ดูดวงความรัก${sign.th}อัปเดตบ่อยแค่ไหน?`, a: `เดือนละครั้ง ทุกต้นเดือนจะมีผังไพ่ความรักสามใบใหม่สำหรับ${sign.th} จึงควรกลับมาดูใหม่เมื่อขึ้นเดือนใหม่` },
    { q: `บทอ่านนี้เป็นคำทำนายตายตัวไหม?`, a: `ไม่ใช่ ไพ่อ่านรูปร่างและทิศทางของความรักตอนนี้เพื่อการใคร่ครวญ ไม่ใช่คำตัดสิน สิ่งที่จะทำต่อยังเป็นของคุณเสมอ` }
  ]
}

function generateSignPage(sign, lang) {
  const en = lang === 'en'
  const signData = month.signs[sign.slug]
  const enUrl = `${siteUrl}/zodiac-love-tarot/${sign.slug}/`
  const thUrl = `${siteUrl}/th/zodiac-love-tarot/${sign.slug}/`
  const canonical = en ? enUrl : thUrl
  const hubHref = en ? '/zodiac-love-tarot/' : '/th/zodiac-love-tarot/'
  const ctaHref = en ? '/quick-love-reading/' : '/quick-love-reading/?lang=th'
  const signName = en ? sign.en : sign.th
  const summary = (signData.summary && (en ? signData.summary.en : signData.summary.th)) || fallbackSummary(sign, signData, lang)

  const title = en
    ? `${sign.en} Love Tarot — ${labels.en} 3-Card Reading | Veila`
    : `ดูดวงความรัก ${sign.th} ${labels.th} ไพ่ยิปซี เลือกไพ่ 3 ใบ | Veila`
  const eyebrow = en
    ? `${sign.element.en} · ${sign.dates.en}`
    : `ธาตุ${sign.element.th} · ${sign.dates.th}`
  const h1 = en ? `${sign.glyph} ${sign.en} Love Tarot — ${labels.en}` : `${sign.glyph} ดูดวงความรัก${sign.th} — ${labels.th}`

  const faqs = signFaqs(sign, signData, lang)
  const t = en
    ? { bcHome: 'Home', bcHub: 'Zodiac Love Tarot', spreadH: `Your three cards for ${labels.en}`, frameH: 'How to read this month’s spread',
        frame: 'Read the three together. The first names where your heart genuinely stands right now, under the noise. The second shows the direction love is drifting if you keep doing what you are doing. The third is the steadying word to carry, a pointer rather than an order. Nothing here is fixed; it is the shape of the month, clear enough to move through with your eyes open.',
        disclaimer: 'A monthly love reading is a mirror for reflection, not a forecast to hand your heart to. The choices stay yours.',
        cta: 'Pull your own love cards', ctaHub: 'All 12 signs', faqH: 'Questions about this reading', moreH: 'Other signs this month' }
    : { bcHome: 'หน้าแรก', bcHub: 'ดูดวงความรักตามราศี', spreadH: `ไพ่สามใบของคุณประจำเดือน${labels.th}`, frameH: 'อ่านผังเดือนนี้อย่างไร',
        frame: 'อ่านสามใบรวมกัน ใบแรกบอกว่าหัวใจคุณยืนอยู่ตรงไหนจริง ๆ ใต้เสียงรบกวนทั้งหมด ใบที่สองคือทิศทางที่ความรักกำลังเลื่อนไปถ้าคุณยังทำแบบเดิม ใบที่สามคือคำที่ช่วยให้ใจนิ่ง ไม่ใช่คำสั่ง แต่เป็นเข็มชี้ ไม่มีอะไรตายตัว มันคือรูปร่างของเดือนนี้ที่ชัดพอจะก้าวผ่านด้วยตาที่เปิดอยู่',
        disclaimer: 'บทอ่านความรักรายเดือนคือกระจกสำหรับใคร่ครวญ ไม่ใช่คำทำนายที่ต้องฝากหัวใจไว้ การเลือกยังเป็นของคุณ',
        cta: 'เปิดไพ่ความรักของคุณเอง', ctaHub: 'ราศีทั้ง 12', faqH: 'คำถามเกี่ยวกับบทอ่านนี้', moreH: 'ราศีอื่นในเดือนนี้' }

  const spreadItems = signData.cards.map((c) => {
    const { name, roman } = cardName(c, lang)
    const pos = month.spread.positions.find((p) => p.key === c.position_key)
    const posLabel = en ? pos.label.en : pos.label.th
    const revBadge = c.reversed ? `<span class="zc-rev">${en ? 'Reversed' : 'ไพ่กลับหัว'}</span>` : ''
    const reading = (en ? c.reading.en : c.reading.th) || ''
    return `    <li class="zc-card">
      <div class="zc-head">
        <span class="zc-pos">${escapeHtml(posLabel)}</span>
      </div>
      <div class="zc-head">
        <span class="zc-name">${escapeHtml(name)}</span><span class="zc-roman">${escapeHtml(roman)}</span>${revBadge}
      </div>
      <p class="zc-read">${escapeHtml(reading)}</p>
    </li>`
  }).join('\n')

  const otherSigns = SIGNS.filter((s) => s.slug !== sign.slug)
    .map((s) => `      <li><a href="${en ? `/zodiac-love-tarot/${s.slug}/` : `/th/zodiac-love-tarot/${s.slug}/`}">${s.glyph} ${escapeHtml(en ? s.en : s.th)}</a></li>`)
    .join('\n')

  const faqBlocks = faqs.map((f) => `    <div class="faq-item">\n      <h3>${escapeHtml(f.q)}</h3>\n      <p>${escapeHtml(f.a)}</p>\n    </div>`).join('\n')

  const articleSchema = {
    '@context': 'https://schema.org', '@type': 'Article',
    headline: title, description: summary, image: `${siteUrl}/og.png`,
    inLanguage: en ? 'en-US' : 'th-TH', datePublished: isoDate, dateModified: isoDate,
    publisher: { '@type': 'Organization', name: 'Veila', url: `${siteUrl}/` },
    mainEntityOfPage: canonical,
    author: { '@type': 'Person', '@id': `${siteUrl}/#person`, name: 'Veila Tarot Expert', url: en ? `${siteUrl}/about/` : `${siteUrl}/th/about/`, jobTitle: 'Tarot Reader & Hermit', description: 'Specializing in love and career tarot, Celtic Cross readings, and bilingual tarot interpretation.' }
  }
  const breadcrumbSchema = {
    '@context': 'https://schema.org', '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: t.bcHome, item: `${siteUrl}/${en ? '' : 'th/'}` },
      { '@type': 'ListItem', position: 2, name: t.bcHub, item: `${siteUrl}${hubHref}` },
      { '@type': 'ListItem', position: 3, name: signName, item: canonical }
    ]
  }
  const faqSchema = {
    '@context': 'https://schema.org', '@type': 'FAQPage',
    mainEntity: faqs.map((f) => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } }))
  }

  return `${head({ title, description: summary, canonical, enUrl, thUrl, lang, schemas: [articleSchema, breadcrumbSchema, faqSchema] })}
<body>

${siteHeader(lang, enUrl, thUrl)}

<main class="article scenario-page">
  <nav class="breadcrumb" aria-label="Breadcrumb"><a href="/${en ? '' : 'th/'}">${t.bcHome}</a><span class="bc-sep">›</span><a href="${hubHref}">${t.bcHub}</a><span class="bc-sep">›</span><span class="bc-current">${escapeHtml(signName)}</span></nav>
  <div class="eyebrow">${escapeHtml(eyebrow)}</div>
  <h1 class="title">${escapeHtml(h1)}</h1>

  <div class="aeo-snippet">
    <p>${escapeHtml(summary)}</p>
  </div>

  <div class="divider"><span class="line"></span><span class="mark"></span><span class="line"></span></div>

  <h2>${t.spreadH}</h2>
  <ul class="zodiac-spread">
${spreadItems}
  </ul>

  <h2>${t.frameH}</h2>
  <p>${escapeHtml(t.frame)}</p>

  <section class="scenario-disclaimer">
    <p>${escapeHtml(t.disclaimer)}</p>
  </section>

  <div class="cta-row">
    <a href="${ctaHref}" class="cta-btn">${t.cta}</a>
    <a href="${hubHref}" class="cta-btn ghost">${t.ctaHub}</a>
  </div>

  <h2>${t.faqH}</h2>
  <div class="faq-list">
${faqBlocks}
  </div>

  <h2>${t.moreH}</h2>
  <ul class="all-list zsign-list">
${otherSigns}
  </ul>
</main>

${footer(lang)}`
}

function generateHub(lang) {
  const en = lang === 'en'
  const enUrl = `${siteUrl}/zodiac-love-tarot/`
  const thUrl = `${siteUrl}/th/zodiac-love-tarot/`
  const canonical = en ? enUrl : thUrl
  const title = en
    ? `Zodiac Love Tarot — ${labels.en} Monthly Reading for All 12 Signs | Veila`
    : `ดูดวงความรักตามราศี ${labels.th} ไพ่ยิปซี เลือกไพ่ แม่นๆ ครบ 12 ราศี | Veila`
  const description = en
    ? `A fresh three-card love tarot spread for every zodiac sign, updated each month. Read ${labels.en}’s love reading for your sign — where your heart stands, what love is moving toward, and the guidance to carry.`
    : `ดูดวงความรักตามราศีด้วยไพ่ยิปซี ผังสามใบใหม่ทุกเดือนครบทั้ง 12 ราศี อ่านดวงความรักประจำเดือน${labels.th}ของราศีคุณ ทั้งหัวใจตอนนี้ ทิศทางความรัก และคำแนะนำของไพ่`

  const cards = SIGNS.map((s) => {
    const sd = month.signs[s.slug]
    const names = sd.cards.map((c) => cardName(c, lang).name).join(' · ')
    const href = en ? `/zodiac-love-tarot/${s.slug}/` : `/th/zodiac-love-tarot/${s.slug}/`
    return `    <li><a href="${href}">
      <span class="sg-top"><span class="sg-glyph">${s.glyph}</span><span class="sg-name">${escapeHtml(en ? s.en : s.th)}</span></span>
      <div class="sg-dates">${escapeHtml(en ? s.dates.en : s.dates.th)}</div>
      <div class="sg-cards">${escapeHtml(names)}</div>
    </a></li>`
  }).join('\n')

  const faqs = en
    ? [
        { q: 'How often is the zodiac love tarot updated?', a: 'Every month. At the start of each month, all 12 signs receive a new three-card love spread, so the reading stays current.' },
        { q: 'How is each sign’s reading drawn?', a: 'Each sign is dealt three distinct cards across three positions — where your heart stands now, what love is moving toward, and the cards’ guidance for the month — with no card repeated across the twelve signs.' },
        { q: 'Is this the same as a personal reading?', a: 'It is a monthly reading for your sign, written for reflection. For a question that is yours alone, pull your own love cards.' }
      ]
    : [
        { q: 'ดูดวงความรักตามราศีอัปเดตบ่อยแค่ไหน?', a: 'ทุกเดือน เมื่อขึ้นเดือนใหม่ ทั้ง 12 ราศีจะได้ผังไพ่ความรักสามใบชุดใหม่ บทอ่านจึงทันสมัยเสมอ' },
        { q: 'ไพ่ของแต่ละราศีเปิดอย่างไร?', a: 'แต่ละราศีได้ไพ่สามใบที่ไม่ซ้ำกัน อ่านผ่านสามตำแหน่ง คือหัวใจคุณตอนนี้ สิ่งที่ความรักกำลังเคลื่อนเข้าหา และคำแนะนำของไพ่ประจำเดือน โดยไม่มีไพ่ใบไหนซ้ำกันในทั้ง 12 ราศี' },
        { q: 'เหมือนการเปิดไพ่ส่วนตัวไหม?', a: 'นี่คือบทอ่านรายเดือนของราศีคุณ เขียนไว้เพื่อการใคร่ครวญ หากมีคำถามที่เป็นของคุณคนเดียว ลองเปิดไพ่ความรักของคุณเอง' }
      ]
  const faqBlocks = faqs.map((f) => `    <div class="faq-item">\n      <h3>${escapeHtml(f.q)}</h3>\n      <p>${escapeHtml(f.a)}</p>\n    </div>`).join('\n')

  const t = en
    ? { bcHome: 'Home', intro: `Pick your sign for ${labels.en}.`, faqH: 'About the zodiac love tarot', cta: 'Pull your own love cards', ctaHref: '/quick-love-reading/' }
    : { bcHome: 'หน้าแรก', intro: `เลือกราศีของคุณสำหรับเดือน${labels.th}`, faqH: 'เกี่ยวกับดูดวงความรักตามราศี', cta: 'เปิดไพ่ความรักของคุณเอง', ctaHref: '/quick-love-reading/?lang=th' }
  const h1 = en ? `Zodiac Love Tarot — ${labels.en}` : `ดูดวงความรักตามราศี — ${labels.th}`

  const itemListSchema = {
    '@context': 'https://schema.org', '@type': 'ItemList',
    name: title, itemListElement: SIGNS.map((s, i) => ({
      '@type': 'ListItem', position: i + 1, name: en ? `${s.en} Love Tarot` : `ดูดวงความรัก${s.th}`,
      url: `${siteUrl}${en ? '' : '/th'}/zodiac-love-tarot/${s.slug}/`
    }))
  }
  const breadcrumbSchema = {
    '@context': 'https://schema.org', '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: t.bcHome, item: `${siteUrl}/${en ? '' : 'th/'}` },
      { '@type': 'ListItem', position: 2, name: en ? 'Zodiac Love Tarot' : 'ดูดวงความรักตามราศี', item: canonical }
    ]
  }
  const faqSchema = {
    '@context': 'https://schema.org', '@type': 'FAQPage',
    mainEntity: faqs.map((f) => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } }))
  }

  return `${head({ title, description, canonical, enUrl, thUrl, lang, schemas: [itemListSchema, breadcrumbSchema, faqSchema] })}
<body>

${siteHeader(lang, enUrl, thUrl)}

<main class="article scenario-page">
  <nav class="breadcrumb" aria-label="Breadcrumb"><a href="/${en ? '' : 'th/'}">${t.bcHome}</a><span class="bc-sep">›</span><span class="bc-current">${en ? 'Zodiac Love Tarot' : 'ดูดวงความรักตามราศี'}</span></nav>
  <div class="eyebrow">${escapeHtml(en ? `Monthly · ${labels.en}` : `รายเดือน · ${labels.th}`)}</div>
  <h1 class="title">${escapeHtml(h1)}</h1>

  <div class="aeo-snippet">
    <p>${escapeHtml(description)}</p>
  </div>

  <div class="divider"><span class="line"></span><span class="mark"></span><span class="line"></span></div>

  <p>${escapeHtml(t.intro)}</p>
  <ul class="sign-grid">
${cards}
  </ul>

  <div class="cta-row">
    <a href="${t.ctaHref}" class="cta-btn">${t.cta}</a>
  </div>

  <h2>${t.faqH}</h2>
  <div class="faq-list">
${faqBlocks}
  </div>
</main>

${footer(lang)}`
}

// --- write everything ---
let count = 0
for (const lang of ['en', 'th']) {
  const hubDir = lang === 'en' ? path.join(rootDir, 'zodiac-love-tarot') : path.join(rootDir, 'th', 'zodiac-love-tarot')
  fs.mkdirSync(hubDir, { recursive: true })
  fs.writeFileSync(path.join(hubDir, 'index.html'), generateHub(lang)); count++
  for (const sign of SIGNS) {
    const dir = path.join(hubDir, sign.slug)
    fs.mkdirSync(dir, { recursive: true })
    fs.writeFileSync(path.join(dir, 'index.html'), generateSignPage(sign, lang)); count++
  }
}
console.log(`Generated ${count} zodiac pages for ${monthKey} (2 hubs + 24 sign pages, EN + TH).`)
