/* Veila — Career & Money vertical: static, crawlable per-question SEO pages.
   Mirrors the love playbook (/love-readings/<slug>/ EN + /th/scenarios/ TH) but:
   - bilingual with RECIPROCAL hreflang: EN /career/<slug>/  +  TH /th/career/<slug>/
   - sources the REAL per-question 3-position labels from each reading JSON, so
     every page carries unique content (not a doorway template)
   - career VOICE: money is read as direction & timing, never exact amounts.
   Idempotent. Regenerate from assets/career-questions.js after any question edit.
   Usage: node scripts/build-career-seo-pages.mjs
*/
import fs from 'node:fs'
import path from 'node:path'
import vm from 'node:vm'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const rootDir = path.resolve(__dirname, '..')
const questionsFile = path.join(rootDir, 'assets', 'career-questions.js')
const readingsDir = path.join(rootDir, 'assets', 'data', 'career-readings')
const siteUrl = 'https://veilatarot.com'
const buildDate = '2026-06-28'
const thaiBuildDate = '28 มิถุนายน 2026'

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

// Keep meta/og/twitter descriptions ≤165 chars (search snippet limit);
// the full lede still appears in the page body and JSON-LD.
function metaTrim(value, max = 165) {
  const s = String(value ?? '')
  if (s.length <= max) return s
  let cut = s.slice(0, max - 1)
  const sp = cut.lastIndexOf(' ')
  if (sp > 80) cut = cut.slice(0, sp)
  return cut.replace(/[\s,;:·—–-]+$/u, '') + '…'
}

function readQuestions() {
  const code = fs.readFileSync(questionsFile, 'utf8')
  const context = { module: { exports: {} } }
  vm.createContext(context)
  vm.runInContext(`${code}\nthis.__OUT = (typeof CAREER_QUESTIONS!=='undefined') ? CAREER_QUESTIONS : (module.exports.CAREER_QUESTIONS||[]);`, context, { filename: questionsFile })
  const arr = context.__OUT
  if (!Array.isArray(arr) || arr.length === 0) throw new Error('CAREER_QUESTIONS not found / empty.')
  return arr.filter((q) => q && q.key && q.en && q.th && q.pillar)
}

// Pull the unique 3 position labels for a question from its reading JSON.
function readingPositions(slug) {
  const fp = path.join(readingsDir, `${slug}-reading.json`)
  try {
    const d = JSON.parse(fs.readFileSync(fp, 'utf8'))
    const pos = d?.spread?.positions
    if (Array.isArray(pos) && pos.length) {
      return pos.map((p) => ({ en: p?.label?.en || '', th: p?.label?.th || '' })).filter((p) => p.en && p.th)
    }
  } catch { /* fall through */ }
  return null
}

const pillarLabel = {
  en: { decision: 'A career crossroads', money: 'Money & worth', growth: 'Growth & momentum', fit: 'Fit & calling', change: 'Change & transition' },
  th: { decision: 'ทางแยกของการงาน', money: 'เงินและคุณค่า', growth: 'การเติบโตและจังหวะ', fit: 'ความใช่และเส้นทาง', change: 'การเปลี่ยนผ่าน' }
}

// Per-pillar lede — references the question. Career voice; money = direction not amounts.
const lede = {
  en: {
    decision: (q) => `“${q}” is the kind of question you can circle for weeks without landing. A three-card career reading won’t decide for you — it lays out what the choice in front of you actually is, where each direction tends to lead, and the move that stays yours to make.`,
    money: (q) => `“${q}” is rarely about a single number. This reading looks at direction and timing rather than exact amounts — what your work is really worth right now, what’s shifting underneath the surface, and where your leverage actually sits.`,
    growth: (q) => `“${q}” usually means something that used to move has gone quiet. The three cards read what is genuinely holding you, what sits underneath the stall, and the next real step back toward traction.`,
    fit: (q) => `“${q}” is a question about alignment, not just performance. The reading reflects what this path is asking of you, what it gives back, and whether the two are honestly meeting.`,
    change: (q) => `“${q}” carries weight on both sides — staying and leaving each cost something. This reading reads what you would be setting down, what you would be moving toward, and whether the timing is actually yours.`
  },
  th: {
    decision: (q) => `“${q}” เป็นคำถามที่วนอยู่ในใจได้เป็นสัปดาห์โดยไม่ลงตัวสักที ไพ่สามใบไม่ได้ตัดสินใจแทนคุณ แต่ช่วยให้เห็นว่าทางเลือกตรงหน้าคืออะไรจริง ๆ แต่ละทางมักพาไปทางไหน และจังหวะไหนที่ยังเป็นของคุณเอง`,
    money: (q) => `“${q}” แทบไม่เคยเป็นเรื่องของตัวเลขเดียว บทอ่านนี้อ่านทิศทางและจังหวะมากกว่าจำนวนเงินที่แน่นอน ทั้งคุณค่าของงานคุณตอนนี้ สิ่งที่กำลังขยับอยู่ใต้ผิว และจุดที่คุณมีน้ำหนักต่อรองจริง ๆ`,
    growth: (q) => `“${q}” มักแปลว่าบางอย่างที่เคยเดินหน้าได้กลับเงียบลง ไพ่สามใบจะอ่านว่าอะไรกำลังรั้งคุณไว้ อะไรซ่อนอยู่ใต้ความนิ่งนั้น และก้าวต่อไปที่พาคุณกลับมาขยับได้จริง`,
    fit: (q) => `“${q}” เป็นคำถามเรื่องความสอดคล้อง ไม่ใช่แค่ผลงาน บทอ่านนี้สะท้อนว่าเส้นทางนี้กำลังขออะไรจากคุณ ให้อะไรกลับมา และทั้งสองอย่างมาบรรจบกันจริงไหม`,
    change: (q) => `“${q}” มีน้ำหนักทั้งสองด้าน อยู่ต่อก็มีราคา ออกไปก็มีราคา บทอ่านนี้อ่านสิ่งที่คุณจะวางลง สิ่งที่คุณจะก้าวเข้าหา และจังหวะนั้นเป็นของคุณจริงหรือยัง`
  }
}

// Per-pillar interpretation frame paragraph.
const frame = {
  en: {
    decision: 'Read the three together: the first names what the choice really is beneath the framing, the second the direction it tends toward if nothing changes, the third the part that is still yours to steer. Cards do not lock the future — they show the shape of it clearly enough to choose from a steadier place.',
    money: 'Read the three as direction, not arithmetic: the first names where your worth actually stands, the second what is moving underneath, the third where your leverage lies. The cards speak to timing and position, not a figure — the number is yours to negotiate once you can see the ground clearly.',
    growth: 'Read the three as a path back to motion: the first names what is actually holding, the second the cause sitting underneath it, the third the next honest step. The reading does not promise momentum — it points to where it has been waiting.',
    fit: 'Read the three as a mirror of alignment: the first reflects what the path asks, the second what it returns, the third where you stand between them. The cards do not grade you — they help you see whether this is a fit you are forcing or one that is already there.',
    change: 'Read the three as both shores of the crossing: the first what you would leave, the second what you would move toward, the third the timing. The cards do not push you across — they let you weigh the leap with your eyes open.'
  },
  th: {
    decision: 'อ่านสามใบรวมกัน ใบแรกบอกว่าทางเลือกนี้คืออะไรจริง ๆ ใต้สิ่งที่เห็น ใบที่สองคือทิศทางที่มันมักไหลไปถ้าไม่มีอะไรเปลี่ยน ใบที่สามคือส่วนที่ยังเป็นของคุณให้กำหนดเอง ไพ่ไม่ได้ล็อกอนาคต แต่ทำให้เห็นรูปร่างของมันชัดพอจะเลือกอย่างมีสติ',
    money: 'อ่านสามใบในแง่ทิศทาง ไม่ใช่การคิดเลข ใบแรกบอกว่าคุณค่าของคุณยืนอยู่ตรงไหน ใบที่สองคือสิ่งที่ขยับอยู่ข้างใต้ ใบที่สามคือจุดที่คุณมีน้ำหนักต่อรอง ไพ่พูดถึงจังหวะและตำแหน่ง ไม่ใช่ตัวเลข ส่วนจำนวนนั้นเป็นของคุณที่จะต่อรองเมื่อมองพื้นได้ชัดแล้ว',
    growth: 'อ่านสามใบเป็นทางกลับสู่การขยับ ใบแรกบอกว่าอะไรกำลังรั้งไว้ ใบที่สองคือต้นเหตุที่อยู่ข้างใต้ ใบที่สามคือก้าวต่อไปที่ตรงไปตรงมา บทอ่านนี้ไม่ได้สัญญาว่าจะมีแรงส่ง แต่ชี้ว่ามันรออยู่ตรงไหน',
    fit: 'อ่านสามใบเป็นกระจกของความสอดคล้อง ใบแรกสะท้อนสิ่งที่เส้นทางขอ ใบที่สองสิ่งที่มันให้กลับ ใบที่สามคือจุดที่คุณยืนอยู่ระหว่างสองสิ่งนั้น ไพ่ไม่ได้ให้คะแนนคุณ แต่ช่วยให้เห็นว่านี่คือความใช่ที่คุณฝืน หรือความใช่ที่มีอยู่แล้ว',
    change: 'อ่านสามใบเป็นสองฝั่งของการข้าม ใบแรกคือสิ่งที่คุณจะวางลง ใบที่สองคือสิ่งที่คุณจะก้าวเข้าหา ใบที่สามคือจังหวะ ไพ่ไม่ได้ผลักให้คุณข้าม แต่ให้คุณชั่งน้ำหนักการก้าวนั้นด้วยตาที่เปิดอยู่'
  }
}

function faqFor(q, lang, positions) {
  const isMoney = q.pillar === 'money'
  if (lang === 'en') {
    const list = [
      {
        q: `How many cards does the “${q.en}” reading use?`,
        a: `Three. ${positions ? `They read ${positions.map((p) => p.en.toLowerCase()).join(', ')} — written for this question, not generic positions.` : 'Each card is written specifically for this question rather than a generic position.'}`
      },
      isMoney
        ? { q: 'Will the cards tell me an exact amount?', a: 'No. A career reading reads direction, worth, and timing — not a figure. It helps you see your position clearly so the number stays something you decide and negotiate.' }
        : { q: 'Is this a fixed prediction?', a: 'No. The cards reflect the present shape of the situation and where it tends to lead, not a verdict. The decision stays yours.' }
    ]
    return list
  }
  const list = [
    {
      q: `บทอ่าน “${q.th}” ใช้ไพ่กี่ใบ?`,
      a: `สามใบ ${positions ? `อ่าน${positions.map((p) => p.th).join(' · ')} ซึ่งเขียนไว้สำหรับคำถามนี้โดยเฉพาะ ไม่ใช่ตำแหน่งทั่วไป` : 'แต่ละใบเขียนไว้สำหรับคำถามนี้โดยเฉพาะ ไม่ใช่ตำแหน่งทั่วไป'}`
    },
    isMoney
      ? { q: 'ไพ่จะบอกจำนวนเงินที่แน่นอนไหม?', a: 'ไม่ บทอ่านการงานอ่านทิศทาง คุณค่า และจังหวะ ไม่ใช่ตัวเลข ช่วยให้คุณเห็นตำแหน่งของตัวเองชัด ส่วนจำนวนยังเป็นสิ่งที่คุณตัดสินและต่อรองเอง' }
      : { q: 'บทอ่านนี้เป็นคำทำนายตายตัวไหม?', a: 'ไม่ใช่คำตัดสินตายตัว ไพ่สะท้อนรูปร่างของสถานการณ์ตอนนี้และทิศทางที่มันมักไป การตัดสินใจสุดท้ายยังเป็นของคุณ' }
  ]
  return list
}

// sibling questions in the same pillar (for internal linking / de-orphaning)
function siblings(q, all) {
  return all.filter((x) => x.pillar === q.pillar && x.key !== q.key).slice(0, 4)
}

function generatePage(q, lang, all) {
  const positions = readingPositions(q.key)
  const en = lang === 'en'
  const qText = en ? q.en : q.th
  const enUrl = `${siteUrl}/career/${q.key}/`
  const thUrl = `${siteUrl}/th/career/${q.key}/`
  const canonical = en ? enUrl : thUrl
  const ctaHref = `/career/reading/?q=${encodeURIComponent(q.key)}`
  const hubHref = en ? '/career/' : '/th/career/'
  const readingHref = en ? '/career/reading/' : '/th/career/reading/'

  const title = en
    ? `${q.en} — Career Tarot, 3-Card Reading | Veila`
    : `${q.th} — ดูดวงการงาน ไพ่ยิปซี 3 ใบ | Veila`
  const description = lede[lang][q.pillar](qText)
  const metaDescription = metaTrim(description)
  const eyebrow = pillarLabel[lang][q.pillar]
  const sibs = siblings(q, all)

  const positionsList = positions
    ? positions.map((p) => `      <li><strong>${escapeHtml(en ? p.en : p.th)}</strong></li>`).join('\n')
    : (en
        ? '      <li><strong>What is really happening</strong></li>\n      <li><strong>What sits underneath</strong></li>\n      <li><strong>The move that stays yours</strong></li>'
        : '      <li><strong>สิ่งที่กำลังเกิดขึ้นจริง</strong></li>\n      <li><strong>สิ่งที่อยู่ข้างใต้</strong></li>\n      <li><strong>จังหวะที่เป็นของคุณ</strong></li>')

  const faqs = faqFor(q, lang, positions)

  const articleSchema = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: title,
    description,
    image: `${siteUrl}/og.png`,
    inLanguage: en ? 'en-US' : 'th-TH',
    datePublished: buildDate,
    dateModified: buildDate,
    publisher: { '@type': 'Organization', name: 'Veila', url: `${siteUrl}/` },
    mainEntityOfPage: canonical,
    author: {
      '@type': 'Person',
      '@id': `${siteUrl}/#person`,
      name: 'Veila Tarot Expert',
      url: en ? `${siteUrl}/about/` : `${siteUrl}/th/about/`,
      jobTitle: 'Tarot Reader & Hermit',
      description: 'Specializing in career and love tarot, Celtic Cross readings, and bilingual tarot interpretation.'
    }
  }
  const breadcrumbSchema = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: en ? 'Home' : 'หน้าแรก', item: `${siteUrl}/${en ? '' : 'th/'}` },
      { '@type': 'ListItem', position: 2, name: en ? 'Career & Money Tarot' : 'ดูดวงการงาน', item: `${siteUrl}${hubHref}` },
      { '@type': 'ListItem', position: 3, name: qText, item: canonical }
    ]
  }
  const faqSchema = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faqs.map((f) => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } }))
  }

  const t = en
    ? {
        bcHome: 'Home', bcHub: 'Career & Money', spreadH: 'A three-card spread for this question',
        spreadIntro: `When you open this reading, the three cards are written for “${escapeHtml(q.en)}” directly — not a generic layout. They read:`,
        frameH: 'How to read it', cta: 'Open this reading', ctaAll: 'All career questions', ctaReading: 'Career reading',
        moreH: 'Related career questions', faqH: 'Questions about this reading',
        disclaimer: 'Use this as a way to reflect and read direction, not a verdict to hand your life to. The final decision is always yours.',
        updated: 'Last updated', foot1: 'Celtic Cross guide', foot1h: '/celtic-cross-tarot/', foot2: 'Love readings', foot2h: '/love-readings/', foot3: 'All pages', foot3h: '/all-tarot-pages/'
      }
    : {
        bcHome: 'หน้าแรก', bcHub: 'ดูดวงการงาน', spreadH: 'ผังไพ่สามใบสำหรับคำถามนี้',
        spreadIntro: `เมื่อคุณเปิดบทอ่านนี้ ไพ่ทั้งสามใบถูกเขียนไว้สำหรับ “${escapeHtml(q.th)}” โดยตรง ไม่ใช่ผังทั่วไป ทั้งสามอ่านว่า:`,
        frameH: 'อ่านอย่างไร', cta: 'เปิดไพ่ตอบคำถามนี้', ctaAll: 'คำถามการงานทั้งหมด', ctaReading: 'ดูไพ่การงาน',
        moreH: 'คำถามการงานที่เกี่ยวข้อง', faqH: 'คำถามเกี่ยวกับบทอ่านนี้',
        disclaimer: 'ใช้บทอ่านนี้เพื่อใคร่ครวญและอ่านทิศทาง ไม่ใช่คำตัดสินที่ต้องฝากชีวิตไว้กับไพ่ การตัดสินใจสุดท้ายเป็นของคุณเสมอ',
        updated: 'ปรับปรุงล่าสุด', foot1: 'คู่มือเซลติกครอส', foot1h: '/th/celtic-cross-tarot/', foot2: 'บทอ่านความรัก', foot2h: '/th/tarot-love-readings/', foot3: 'ทุกหน้า', foot3h: '/th/all-tarot-pages/'
      }

  const siblingLinks = sibs
    .map((s) => `      <li><a href="${en ? `/career/${s.key}/` : `/th/career/${s.key}/`}">${escapeHtml(en ? s.en : s.th)}</a></li>`)
    .join('\n')

  const faqBlocks = faqs
    .map((f) => `    <div class="faq-item">\n      <h3>${escapeHtml(f.q)}</h3>\n      <p>${escapeHtml(f.a)}</p>\n    </div>`)
    .join('\n')

  return `<!DOCTYPE html>
<html lang="${en ? 'en' : 'th'}">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>${escapeHtml(title)}</title>
<meta name="description" content="${escapeHtml(metaDescription)}" />
<meta name="author" content="Veila Tarot" />
<meta name="robots" content="index, follow, max-image-preview:large" />
<meta name="theme-color" content="#0a0a0c" />
<meta name="color-scheme" content="dark" />
<meta name="google-adsense-account" content="ca-pub-2823470980745945" />

<link rel="canonical" href="${canonical}" />
<link rel="alternate" hreflang="en" href="${enUrl}" />
<link rel="alternate" hreflang="th" href="${thUrl}" />
<link rel="alternate" hreflang="x-default" href="${enUrl}" />

<meta property="og:type" content="article" />
<meta property="og:site_name" content="Veila" />
<meta property="og:title" content="${escapeHtml(title)}" />
<meta property="og:description" content="${escapeHtml(metaDescription)}" />
<meta property="og:url" content="${canonical}" />
<meta property="og:image" content="${siteUrl}/og.png" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:locale" content="${en ? 'en_US' : 'th_TH'}" />
<meta property="og:locale:alternate" content="${en ? 'th_TH' : 'en_US'}" />

<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="${escapeHtml(title)}" />
<meta name="twitter:description" content="${escapeHtml(metaDescription)}" />
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

<script type="application/ld+json">${jsonLd(articleSchema)}</script>
<script type="application/ld+json">${jsonLd(breadcrumbSchema)}</script>
<script type="application/ld+json">${jsonLd(faqSchema)}</script>
</head>
<body>

<header class="site-header">
  <a class="brand" href="/${en ? '' : 'th/'}" aria-label="Veila">Veila<span class="dot"></span><span class="brand-sub">${en ? 'tarot for reflection' : 'การทำสมาธิกับไพ่'}</span></a>
  <div class="lang-toggle" role="group" aria-label="${en ? 'Language' : 'ภาษา'}">
    <a href="${enUrl}"${en ? ' class="active"' : ''}>EN</a>
    <a href="${thUrl}"${en ? '' : ' class="active"'}>TH</a>
  </div>
</header>

<main class="article scenario-page">
  <nav class="breadcrumb" aria-label="Breadcrumb"><a href="/${en ? '' : 'th/'}">${t.bcHome}</a><span class="bc-sep">›</span><a href="${hubHref}">${t.bcHub}</a><span class="bc-sep">›</span><span class="bc-current">${escapeHtml(qText)}</span></nav>
  <div class="eyebrow">${escapeHtml(eyebrow)}</div>
  <h1 class="title">${escapeHtml(qText)}</h1>

  <div class="aeo-snippet">
    <p>${escapeHtml(description)}</p>
  </div>

  <div class="divider"><span class="line"></span><span class="mark"></span><span class="line"></span></div>

  <h2>${t.spreadH}</h2>
  <p>${t.spreadIntro}</p>
  <ol class="positions">
${positionsList}
  </ol>

  <h2>${t.frameH}</h2>
  <p>${escapeHtml(frame[lang][q.pillar])}</p>

  <section class="scenario-disclaimer">
    <p>${escapeHtml(t.disclaimer)}</p>
  </section>

  <div class="cta-row">
    <a href="${ctaHref}" class="cta-btn">${t.cta}</a>
    <a href="${hubHref}" class="cta-btn ghost">${t.ctaAll}</a>
    <a href="${readingHref}" class="cta-btn ghost">${t.ctaReading}</a>
  </div>

  <h2>${t.faqH}</h2>
  <div class="faq-list">
${faqBlocks}
  </div>

  <h2>${t.moreH}</h2>
  <ul class="all-list">
${siblingLinks}
  </ul>
</main>

<footer>
  <div class="fineprint">${en ? 'For reflection and direction, not a fixed forecast.' : 'เพื่อการใคร่ครวญและอ่านทิศทาง ไม่ใช่การบังคับอนาคต'}</div>
  <div class="last-updated">${t.updated} · ${en ? buildDate : thaiBuildDate}</div>
  <nav class="footer-nav">
    <a href="${t.foot1h}">${t.foot1}</a>
    <span class="sep">·</span>
    <a href="${t.foot2h}">${t.foot2}</a>
    <span class="sep">·</span>
    <a href="${t.foot3h}">${t.foot3}</a>
  </nav>
  <div>veilatarot.com · © MMXXVI</div>
</footer>

</body>
</html>`
}

const questions = readQuestions()
let count = 0
for (const q of questions) {
  const enDir = path.join(rootDir, 'career', q.key)
  const thDir = path.join(rootDir, 'th', 'career', q.key)
  fs.mkdirSync(enDir, { recursive: true })
  fs.mkdirSync(thDir, { recursive: true })
  fs.writeFileSync(path.join(enDir, 'index.html'), generatePage(q, 'en', questions))
  fs.writeFileSync(path.join(thDir, 'index.html'), generatePage(q, 'th', questions))
  count += 2
}
console.log(`Generated ${count} career SEO pages (${questions.length} questions × EN+TH) under /career/<slug>/ and /th/career/<slug>/.`)
