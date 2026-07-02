/*
  build-quick-love-seo-pages-en.mjs
  ---------------------------------
  EN mirror of build-quick-love-seo-pages.mjs (which owns /th/scenarios/).

  Generates /scenarios/<key>/index.html for every question in
  assets/100-questions.js that has a bilingual reading dataset registered in
  quick-love-reading/index.html (QUESTION_DATASETS), plus a /scenarios/ index.

  It also patches the hreflang lines in each generated page's TH twin at
  th/scenarios/<key>/index.html (and th/scenarios/index.html) so the pair is
  reciprocal: en -> /scenarios/<key>/, th -> /th/scenarios/<key>/,
  x-default -> the EN url. The patch is idempotent and touches nothing else.

  SKIPPED KEYS: 'moving-on-hard' and 'should-i-reach-out' already have
  hand-built EN pages under /love-readings/ that are hreflang-paired to the
  TH scenario pages. No EN scenario page is generated for them, and their
  TH twins are left untouched.

  Prose boilerplate is written in 4 variants per section and rotated
  deterministically by a hash of the question key, so no single sentence
  repeats across the whole corpus of pages.
*/

import fs from 'node:fs'
import path from 'node:path'
import vm from 'node:vm'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const rootDir = path.resolve(__dirname, '..')
const questionsFile = path.join(rootDir, 'assets', '100-questions.js')
const qlrFile = path.join(rootDir, 'quick-love-reading', 'index.html')
const outDirBase = path.join(rootDir, 'scenarios')
const thDirBase = path.join(rootDir, 'th', 'scenarios')
const siteUrl = 'https://veilatarot.com'
const buildDate = '2026-07-02'
const humanBuildDate = '2 July 2026'

const SKIP_KEYS = new Set(['moving-on-hard', 'should-i-reach-out'])

/* ---------------------------------------------------------------- utils */

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

function jsonLd(value) {
  return JSON.stringify(value, null, 2)
    .replaceAll('</script', '<\\/script')
    .replaceAll('<!--', '<\\!--')
}

// djb2 — deterministic variant rotation per question key
function hashKey(str) {
  let h = 5381
  for (let i = 0; i < str.length; i++) h = ((h << 5) + h + str.charCodeAt(i)) >>> 0
  return h
}

function pick(variants, hash, salt) {
  return variants[(hash + salt) % variants.length]
}

function lcLabel(label) {
  // Position labels are generic phrases ("What still holds you"); safe to
  // lowercase the first letter for mid-sentence use.
  return label.charAt(0).toLowerCase() + label.slice(1)
}

function wordCount(s) {
  return s.split(/\s+/).filter(Boolean).length
}

/* ------------------------------------------------------------- loaders */

function readQuestions() {
  const code = fs.readFileSync(questionsFile, 'utf8')
  const context = {}
  vm.createContext(context)
  vm.runInContext(`${code}\nthis.HUNDRED_QUESTIONS = HUNDRED_QUESTIONS;`, context, {
    filename: questionsFile
  })
  if (!Array.isArray(context.HUNDRED_QUESTIONS)) {
    throw new Error('HUNDRED_QUESTIONS was not found or was not an array.')
  }
  return context.HUNDRED_QUESTIONS.filter((q) => q && q.key && q.en)
}

function readDatasetMap() {
  const html = fs.readFileSync(qlrFile, 'utf8')
  const m = html.match(/const QUESTION_DATASETS = \{[\s\S]*?\};/)
  if (!m) throw new Error('QUESTION_DATASETS not found in quick-love-reading/index.html')
  const context = {}
  vm.createContext(context)
  vm.runInContext(m[0].replace('const QUESTION_DATASETS', 'this.DS'), context)
  return context.DS
}

function loadReading(datasetPath) {
  const abs = path.join(rootDir, datasetPath.replace(/^\//, ''))
  if (!fs.existsSync(abs)) return null
  const raw = JSON.parse(fs.readFileSync(abs, 'utf8'))
  // Canonical shape
  if (raw.spread && Array.isArray(raw.spread.positions)) return raw
  // Variant root shape (spread_structure)
  if (raw.spread_structure && typeof raw.spread_structure === 'object') {
    const positions = Object.keys(raw.spread_structure).map((k) => ({
      key: k,
      label: raw.spread_structure[k]
    }))
    return {
      question: { key: raw.question_key || '', en: raw.question_en || '', th: raw.question_th || '' },
      spread: { card_count: positions.length, positions },
      cards: raw.cards
    }
  }
  return null
}

/* ---------------------------------------------------------- pillar meta */

const pillarMeta = {
  single: { eyebrow: 'Single & Searching', heading: 'When you are single', anchor: 'single' },
  heartbroken: { eyebrow: 'Healing After Heartbreak', heading: 'When you are healing', anchor: 'healing' },
  taken: { eyebrow: 'In a Relationship', heading: 'When you are in a relationship', anchor: 'relationship' },
  predictive: { eyebrow: 'Predictive Love Questions', heading: 'When you want to see ahead', anchor: 'predictive' },
  default: { eyebrow: 'Love Tarot Question', heading: 'More love questions', anchor: 'more' }
}

function metaFor(q) {
  return pillarMeta[q.pillar] || pillarMeta.default
}

/* ------------------------------------------------------ prose variants */

function buildTitle(q) {
  const full = `${q.en} Love Tarot Reading | Veila`
  if (full.length <= 60) return full
  const mid = `${q.en} Love Tarot | Veila`
  if (mid.length <= 60) return mid
  return `${q.en} | Veila`
}

function buildDescription(q, hash) {
  const variants = [
    `A free three-card love tarot reading for “${q.en}” Each card opens an answer written for this question.`,
    `Draw three cards for “${q.en}” and read an answer written for this question, not a generic card meaning.`,
    `“${q.en}” A three-card tarot reading that answers this directly: what is present, what is hidden, where it can go.`,
    `Three cards, one question: “${q.en}” A love tarot reading interpreted for this exact situation, free to open.`
  ]
  const chosen = pick(variants, hash, 0)
  if (chosen.length <= 160) return chosen
  const fallback = `Three-card love tarot for “${q.en}” Answers written for this exact question.`
  return fallback.length <= 160 ? fallback : `Love tarot for “${q.en}” Free three-card reading.`
}

function buildAeo(q, labels, hash) {
  const [l1, l2, l3] = labels.map(lcLabel)
  const openers = [
    `This three-card love tarot reading takes “${q.en}” and answers it in three parts: ${l1}, ${l2}, and ${l3}.`,
    `To answer “${q.en}”, Veila draws three cards, one for ${l1}, one for ${l2}, and one for ${l3}.`,
    `This reading approaches “${q.en}” through three positions: ${l1}, ${l2}, and ${l3}.`,
    `Three cards answer this question here. The first looks at ${l1}, the second at ${l2}, and the third at ${l3}.`
  ]
  const shortClosers = [
    `Every card you draw opens an answer written for this exact question.`,
    `Each card is interpreted for this question alone, not from a generic list.`,
    `The interpretation you read is written for this question, card by card.`,
    `Whatever you draw, the reading speaks to this question directly.`
  ]
  const longClosers = [
    `Each of the seventy-eight cards carries its own written interpretation for every position, so the reading you get follows your draw rather than a script.`,
    `Every card in the deck has an answer prepared for each of the three positions, which means your reading is shaped by your own pull of the cards.`,
    `Because each card holds a written interpretation for every position of this spread, no two readings of this question come out the same.`,
    `The deck behind it carries a full written answer for every card in every position, so what you read is matched to what you draw.`
  ]
  const opener = pick(openers, hash, 1)
  const candidates = [
    `${opener} ${pick(longClosers, hash, 2)}`,
    `${opener} ${pick(shortClosers, hash, 2)}`,
    opener
  ]
  for (const c of candidates) {
    const w = wordCount(c)
    if (w >= 40 && w <= 60) return c
  }
  // Fall back to whichever is closest to the 40-60 band.
  return candidates
    .map((c) => ({ c, d: Math.max(0, 40 - wordCount(c), wordCount(c) - 60) }))
    .sort((a, b) => a.d - b.d)[0].c
}

function buildLede(hash) {
  return pick([
    `A question like this rarely wants a plain yes or no. It wants to know where to put your heart, and which signals deserve your attention.`,
    `Most people carry this question quietly for a while before they ask it out loud. The reading gives it somewhere to land.`,
    `You probably already sense part of the answer. The cards give that sense a shape you can look at directly.`,
    `This is one of those questions that sits underneath the whole day. Drawing three cards is a way of letting it speak.`
  ], hash, 3)
}

function buildHow(q, hash) {
  return pick([
    `This page connects to Veila's Quick Love Reading. When you draw your three cards, each one opens an interpretation written specifically for “${q.en}”, not a generic card meaning. Every card in the deck has its own answer for every position of this spread.`,
    `The reading runs on Veila's Quick Love Reading system. All seventy-eight cards carry interpretations written for “${q.en}” in each of the three positions, so whatever you draw, the reading speaks to this question and no other.`,
    `Behind this page sits a full set of interpretations written for “${q.en}”. Draw three cards in the Quick Love Reading and each lands in a position with its own written answer, matched to this exact question.`,
    `When you open the Quick Love Reading from this page, the deck is already tuned to “${q.en}”. Each of the three cards you choose reveals a reading composed for that card, in that position, for this question.`
  ], hash, 4)
}

function buildPositionDescs(labels, hash) {
  const [l1, l2, l3] = labels.map(lcLabel)
  const p1 = pick([
    `The first card reads ${l1}. This is the current that is strongest in the situation right now.`,
    `Your opening card speaks to ${l1}, the part of the answer that is already in motion.`,
    `The reading begins with ${l1}. It names what is most present before anything hidden is touched.`,
    `Card one holds ${l1}, the surface of the question as it stands today.`
  ], hash, 5)
  const p2 = pick([
    `The second card turns to ${l2}, the layer that has not been said out loud yet.`,
    `Next, the spread opens ${l2}. This is where the reading looks beneath the obvious.`,
    `The middle card carries ${l2}, the quieter truth sitting under the first.`,
    `Card two reaches for ${l2}, what the situation keeps just out of easy view.`
  ], hash, 6)
  const p3 = pick([
    `The third card closes with ${l3}. It points at where things can go from here.`,
    `Finally, the spread ends on ${l3}, the part that hands the choice back to you.`,
    `The last card offers ${l3}, a direction rather than a verdict.`,
    `Card three settles on ${l3}, the step the reading leaves in your hands.`
  ], hash, 7)
  return [p1, p2, p3]
}

function buildCovers(hash) {
  return pick([
    `In practice, that means the reading covers where things genuinely stand, what has been sitting underneath, and what you can do next. It will not decide for you, and it is not meant to.`,
    `Taken together, the cards describe the present, the hidden layer, and the way forward. What you do with that picture stays entirely your call.`,
    `The spread is small on purpose. Three cards are enough to show the state of things, the unspoken part, and a workable next step, without burying the question in detail.`,
    `Read as one arc, the cards move from what is visible to what is buried to what comes next. The reading describes; the deciding remains yours.`
  ], hash, 8)
}

function buildDisclaimer(hash) {
  return pick([
    `Use this reading as a mirror, not a command. The cards describe currents; you steer.`,
    `Treat what you draw as reflection, not instruction. The final word on your own heart is still yours.`,
    `Nothing here fixes the future in place. A reading shows the weather, and you choose how to walk in it.`,
    `Hold the reading lightly. It maps where things lean today, and today is not a verdict.`
  ], hash, 9)
}

function buildFaq(q, labels, hash) {
  const [l1, l2, l3] = labels.map(lcLabel)
  const a2 = pick([
    `No, it is not. The cards read the current shape and direction of the situation, and that direction can change with what you choose to do.`,
    `No. A tarot reading describes how things are leaning right now, not a locked outcome. Your choices still move the result.`,
    `It is not a verdict. The reading shows the present current of the situation so you can decide with clearer eyes.`,
    `No. What you draw reflects the energies at play today. It informs a decision; it does not make one.`
  ], hash, 10)
  const a3 = pick([
    `You do not. Every card comes with a full written interpretation for this exact question, in plain language, in English and Thai.`,
    `No prior tarot knowledge is needed. The reading explains each card for this question directly, so you read the answer, not a manual.`,
    `Not at all. Each card you choose is interpreted for you, with the meaning written specifically for this question rather than as a general definition.`,
    `No. The interpretations are already written for this question, so drawing the cards is all you are asked to do.`
  ], hash, 11)
  return [
    {
      q: `What does the reading for “${q.en}” cover?`,
      a: `It draws three cards for this question: ${l1}, ${l2}, and ${l3}. Each card you pull opens an interpretation written for that position and this question.`
    },
    { q: `Is this reading a fixed prediction?`, a: a2 },
    { q: `Do I need to know tarot to use this reading?`, a: a3 }
  ]
}

/* ----------------------------------------------------------- page HTML */

function generatePage(q, reading, siblings) {
  const hash = hashKey(q.key)
  const labels = reading.spread.positions.map((p) => p.label.en)
  const title = buildTitle(q)
  const description = buildDescription(q, hash)
  const canonical = `${siteUrl}/scenarios/${q.key}/`
  const thUrl = `${siteUrl}/th/scenarios/${q.key}/`
  const aeo = buildAeo(q, labels, hash)
  const lede = buildLede(hash)
  const how = buildHow(q, hash)
  const posDescs = buildPositionDescs(labels, hash)
  const covers = buildCovers(hash)
  const disclaimer = buildDisclaimer(hash)
  const faq = buildFaq(q, labels, hash)
  const meta = metaFor(q)
  const cta = `/quick-love-reading/?q=${encodeURIComponent(q.key)}`

  const articleSchema = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: title,
    description,
    image: `${siteUrl}/og.png`,
    inLanguage: 'en-US',
    datePublished: buildDate,
    dateModified: buildDate,
    publisher: { '@type': 'Organization', name: 'Veila', url: `${siteUrl}/` },
    mainEntityOfPage: canonical,
    author: {
      '@type': 'Person',
      '@id': `${siteUrl}/#person`,
      name: 'Veila Tarot Expert',
      url: `${siteUrl}/about/`,
      jobTitle: 'Tarot Reader & Hermit',
      description: 'Specializing in love tarot, Celtic Cross readings, and bilingual tarot interpretation.'
    }
  }
  const breadcrumbSchema = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: `${siteUrl}/` },
      { '@type': 'ListItem', position: 2, name: 'Love Questions', item: `${siteUrl}/scenarios/` },
      { '@type': 'ListItem', position: 3, name: q.en, item: canonical }
    ]
  }
  const faqSchema = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faq.map((f) => ({
      '@type': 'Question',
      name: f.q,
      acceptedAnswer: { '@type': 'Answer', text: f.a }
    }))
  }

  const positionItems = reading.spread.positions
    .map((p, i) => `      <li><strong>${escapeHtml(p.label.en)}</strong>${escapeHtml(posDescs[i])}</li>`)
    .join('\n')

  const siblingItems = siblings
    .map((s) => `      <li><a href="/scenarios/${escapeHtml(s.key)}/">${escapeHtml(s.en)}</a></li>`)
    .join('\n')

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>${escapeHtml(title)}</title>
<meta name="description" content="${escapeHtml(description)}" />
<meta name="author" content="Veila Tarot" />
<meta name="robots" content="index, follow, max-image-preview:large" />
<meta name="theme-color" content="#0a0a0c" />
<meta name="color-scheme" content="dark" />

<link rel="canonical" href="${canonical}" />
<link rel="alternate" hreflang="en" href="${canonical}" />
<link rel="alternate" hreflang="th" href="${thUrl}" />
<link rel="alternate" hreflang="x-default" href="${canonical}" />

<meta property="og:type" content="article" />
<meta property="og:site_name" content="Veila" />
<meta property="og:title" content="${escapeHtml(title)}" />
<meta property="og:description" content="${escapeHtml(description)}" />
<meta property="og:url" content="${canonical}" />
<meta property="og:image" content="${siteUrl}/og.png" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:locale" content="en_US" />

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
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,400&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="/assets/page.css" />

<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2823470980745945" crossorigin="anonymous"></script>
<meta name="google-adsense-account" content="ca-pub-2823470980745945" />

<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQWWZ3HT2S"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-NQWWZ3HT2S');
</script>
<script src="/assets/analytics.js" defer></script>

<script type="application/ld+json">${jsonLd(articleSchema)}</script>
<script type="application/ld+json">${jsonLd(breadcrumbSchema)}</script>
<script type="application/ld+json">${jsonLd(faqSchema)}</script>
</head>
<body>

<header class="site-header">
  <a class="brand" href="/" aria-label="Veila — return to home">Veila<span class="dot"></span><span class="brand-sub">A Tarot Practice</span></a>
  <div class="lang-toggle" role="group" aria-label="Language">
    <a href="${canonical}" class="active">EN</a>
    <span class="sep">·</span>
    <a href="/th/scenarios/${escapeHtml(q.key)}/">TH</a>
  </div>
</header>

<main class="article scenario-page">
  <nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Home</a><span class="bc-sep">›</span><a href="/scenarios/">Love Questions</a><span class="bc-sep">›</span><span class="bc-current">${escapeHtml(q.en)}</span></nav>
  <div class="eyebrow">${escapeHtml(meta.eyebrow)}</div>
  <h1 class="title">${escapeHtml(q.en)}</h1>

  <div class="aeo-snippet">
    <p>${escapeHtml(aeo)}</p>
  </div>

  <p class="lede">${escapeHtml(lede)}</p>

  <div class="divider"><span class="line"></span><span class="mark"></span><span class="line"></span></div>

  <h2>How this reading works</h2>
  <p>${escapeHtml(how)}</p>

  <h2>The three positions of this spread</h2>
  <ol class="positions">
${positionItems}
  </ol>

  <h2>What this reading covers</h2>
  <p>${escapeHtml(covers)}</p>

  <section class="scenario-disclaimer">
    <p>${escapeHtml(disclaimer)}</p>
  </section>

  <div class="cta-row">
    <a href="${cta}" class="cta-btn">Draw cards for this question</a>
    <a href="/scenarios/" class="cta-btn ghost">All love questions</a>
    <a href="/tarot-love-readings/" class="cta-btn ghost">About love readings</a>
  </div>

  <section>
    <h2>Related questions</h2>
    <ul class="all-list">
${siblingItems}
    </ul>
  </section>
</main>

<footer>
  <div class="fineprint">For reflection and direction, not a fixed future.</div>
  <div class="last-updated">Last updated · ${humanBuildDate}</div>
  <nav class="footer-nav">
    <a href="/celtic-cross-tarot/">Celtic Cross Guide</a>
    <span class="sep">·</span>
    <a href="/daily-tarot-card/">Daily Card</a>
    <span class="sep">·</span>
    <a href="/all-tarot-pages/">All Pages</a>
  </nav>
  <div>veilatarot.com · © MMXXVI</div>
</footer>

<script src="/assets/chrome.js" defer></script>
</body>
</html>`
}

/* ----------------------------------------------------------- index page */

function generateIndex(questions) {
  const canonical = `${siteUrl}/scenarios/`
  const thUrl = `${siteUrl}/th/scenarios/`
  const order = ['single', 'taken', 'heartbroken', 'predictive']
  const grouped = new Map()
  for (const p of order) grouped.set(p, [])
  for (const q of questions) {
    const p = grouped.has(q.pillar) ? q.pillar : order[0]
    grouped.get(p).push(q)
  }

  const sections = order
    .filter((p) => grouped.get(p).length > 0)
    .map((p) => {
      const meta = pillarMeta[p]
      const items = grouped.get(p)
      const links = items
        .map((q) => `      <li><a href="/scenarios/${escapeHtml(q.key)}/">${escapeHtml(q.en)}</a></li>`)
        .join('\n')
      return `  <section id="${meta.anchor}">
    <h2>${escapeHtml(meta.heading)} (${items.length})</h2>
    <ul class="all-list">
${links}
    </ul>
  </section>`
    })
    .join('\n\n')

  const title = 'All Love Tarot Questions — Three-Card Readings | Veila'
  const description = 'Every love tarot question Veila answers with a three-card reading. Pick the one that matches where you are, then draw your cards for a written answer.'

  const collectionSchema = {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: title,
    description,
    url: canonical,
    inLanguage: 'en-US',
    isPartOf: { '@type': 'WebSite', name: 'Veila', url: `${siteUrl}/` },
    mainEntity: {
      '@type': 'ItemList',
      numberOfItems: questions.length,
      itemListElement: questions.map((q, i) => ({
        '@type': 'ListItem',
        position: i + 1,
        name: q.en,
        url: `${siteUrl}/scenarios/${q.key}/`
      }))
    }
  }
  const breadcrumbSchema = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: `${siteUrl}/` },
      { '@type': 'ListItem', position: 2, name: 'Love Questions', item: canonical }
    ]
  }

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>${escapeHtml(title)}</title>
<meta name="description" content="${escapeHtml(description)}" />
<meta name="robots" content="index, follow, max-image-preview:large" />
<meta name="theme-color" content="#0a0a0c" />
<meta name="color-scheme" content="dark" />
<link rel="canonical" href="${canonical}" />
<link rel="alternate" hreflang="en" href="${canonical}" />
<link rel="alternate" hreflang="th" href="${thUrl}" />
<link rel="alternate" hreflang="x-default" href="${canonical}" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="Veila" />
<meta property="og:title" content="${escapeHtml(title)}" />
<meta property="og:description" content="${escapeHtml(description)}" />
<meta property="og:url" content="${canonical}" />
<meta property="og:image" content="${siteUrl}/og.png" />
<meta property="og:locale" content="en_US" />
<link rel="icon" href="/favicon.svg" type="image/svg+xml" />
<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png" />
<link rel="apple-touch-icon" href="/apple-touch-icon.png" sizes="180x180" />
<link rel="manifest" href="/manifest.webmanifest" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,400&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="/assets/page.css" />
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQWWZ3HT2S"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-NQWWZ3HT2S');
</script>
<script src="/assets/analytics.js" defer></script>
<script type="application/ld+json">${jsonLd(collectionSchema)}</script>
<script type="application/ld+json">${jsonLd(breadcrumbSchema)}</script>
</head>
<body>
<header class="site-header">
  <a class="brand" href="/" aria-label="Veila — return to home">Veila<span class="dot"></span><span class="brand-sub">A Tarot Practice</span></a>
  <div class="lang-toggle" role="group" aria-label="Language">
    <a href="${canonical}" class="active">EN</a>
    <span class="sep">·</span>
    <a href="/th/scenarios/">TH</a>
  </div>
</header>
<main class="article scenario-page">
  <nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Home</a><span class="bc-sep">›</span><a href="/tarot-love-readings/">Love Readings</a><span class="bc-sep">›</span><span class="bc-current">All Questions</span></nav>
  <div class="eyebrow">Quick Love Reading</div>
  <h1 class="title">All Love Tarot Questions</h1>
  <div class="aeo-snippet">
    <p>These are the ${questions.length} love questions Veila answers with a three-card tarot reading. Each page describes its own spread, and every card you draw opens an interpretation written for that question. Choose the one that names where you are.</p>
  </div>
${sections}
  <div class="cta-row">
    <a href="/quick-love-reading/" class="cta-btn">Open the Quick Love Reading</a>
    <a href="/tarot-love-readings/" class="cta-btn ghost">About love readings</a>
  </div>
</main>
<footer>
  <div class="fineprint">For reflection and direction, not a fixed future.</div>
  <div class="last-updated">Last updated · ${humanBuildDate}</div>
  <nav class="footer-nav">
    <a href="/tarot-love-readings/">Love Readings</a>
    <span class="sep">·</span>
    <a href="/all-tarot-pages/">All Pages</a>
  </nav>
  <div>veilatarot.com · © MMXXVI</div>
</footer>
<script src="/assets/chrome.js" defer></script>
</body>
</html>`
}

/* --------------------------------------------- TH twin hreflang patcher */

function patchThaiHead(filePath, thUrl, enUrl) {
  if (!fs.existsSync(filePath)) return 'missing'
  let html = fs.readFileSync(filePath, 'utf8')
  const enLine = `<link rel="alternate" hreflang="en" href="${enUrl}" />`
  const thLine = `<link rel="alternate" hreflang="th" href="${thUrl}" />`
  const xdLine = `<link rel="alternate" hreflang="x-default" href="${enUrl}" />`
  const target = `${enLine}\n${thLine}\n${xdLine}`
  if (html.includes(target)) return 'ok'

  // Current Wave-1 state: th self + x-default self (no en line).
  const oldBlock = `${thLine}\n<link rel="alternate" hreflang="x-default" href="${thUrl}" />`
  if (html.includes(oldBlock)) {
    fs.writeFileSync(filePath, html.replace(oldBlock, target))
    return 'patched'
  }
  // th line only, no x-default at all.
  if (html.includes(thLine) && !html.includes('hreflang="x-default"') && !html.includes('hreflang="en"')) {
    fs.writeFileSync(filePath, html.replace(thLine, target))
    return 'patched'
  }
  return 'skipped-unrecognized'
}

/* ----------------------------------------------------------------- main */

const questions = readQuestions()
const datasets = readDatasetMap()

const eligible = []
const skipped = []
for (const q of questions) {
  if (SKIP_KEYS.has(q.key)) { skipped.push({ key: q.key, reason: 'paired to hand-built /love-readings/ page' }); continue }
  const dsPath = datasets[q.key]
  if (!dsPath) { skipped.push({ key: q.key, reason: 'no dataset registered' }); continue }
  const reading = loadReading(dsPath)
  if (!reading || !Array.isArray(reading.spread?.positions) || reading.spread.positions.length < 3) {
    skipped.push({ key: q.key, reason: 'dataset missing or unreadable' })
    continue
  }
  if (!reading.spread.positions.every((p) => p.label && p.label.en)) {
    skipped.push({ key: q.key, reason: 'no EN position labels' })
    continue
  }
  eligible.push({ q, reading })
}

// Sibling pools per pillar (eligible questions only)
const byPillar = new Map()
for (const { q } of eligible) {
  if (!byPillar.has(q.pillar)) byPillar.set(q.pillar, [])
  byPillar.get(q.pillar).push(q)
}

function siblingsFor(q) {
  const pool = byPillar.get(q.pillar) || []
  const idx = pool.findIndex((x) => x.key === q.key)
  const out = []
  for (let i = 1; out.length < 4 && i <= pool.length; i++) {
    const cand = pool[(idx + i) % pool.length]
    if (cand.key !== q.key) out.push(cand)
  }
  return out
}

fs.mkdirSync(outDirBase, { recursive: true })

let patched = 0
for (const { q, reading } of eligible) {
  const dirPath = path.join(outDirBase, q.key)
  fs.mkdirSync(dirPath, { recursive: true })
  fs.writeFileSync(path.join(dirPath, 'index.html'), generatePage(q, reading, siblingsFor(q)))
  const res = patchThaiHead(
    path.join(thDirBase, q.key, 'index.html'),
    `${siteUrl}/th/scenarios/${q.key}/`,
    `${siteUrl}/scenarios/${q.key}/`
  )
  if (res === 'patched') patched++
  else if (res !== 'ok') console.warn(`TH twin ${q.key}: ${res}`)
}

fs.writeFileSync(path.join(outDirBase, 'index.html'), generateIndex(eligible.map((e) => e.q)))
const idxRes = patchThaiHead(path.join(thDirBase, 'index.html'), `${siteUrl}/th/scenarios/`, `${siteUrl}/scenarios/`)

console.log(`Generated ${eligible.length} EN scenario pages plus /scenarios/ index.`)
console.log(`Patched ${patched} TH twin heads (+ index: ${idxRes}).`)
if (skipped.length) console.log('Skipped:', skipped.map((s) => `${s.key} (${s.reason})`).join('; '))
