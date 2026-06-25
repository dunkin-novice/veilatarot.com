import fs from 'node:fs'
import path from 'node:path'
import vm from 'node:vm'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const rootDir = path.resolve(__dirname, '..')
const questionsFile = path.join(rootDir, 'assets', '100-questions.js')
const outDirBase = path.join(rootDir, 'th', 'scenarios')
const siteUrl = 'https://veilatarot.com'
const buildDate = '2026-06-25'
const thaiBuildDate = '25 มิถุนายน 2026'

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

  return context.HUNDRED_QUESTIONS.filter((q) => q && q.key && q.th)
}

const pillarLabels = {
  predictive: 'คำถามทำนายความรัก',
  healing: 'บทอ่านเพื่อเยียวยาใจ',
  self: 'คำถามเพื่อเข้าใจตัวเอง',
  relationship: 'คำถามความสัมพันธ์',
  default: 'คำถามดูดวงความรัก'
}

function labelFor(q) {
  return pillarLabels[q.pillar] || pillarLabels.default
}

function pageIntro(q) {
  if (q.pillar === 'predictive') {
    return `ดูดวงความรักด้วยไพ่ยิปซี 3 ใบสำหรับคำถาม “${q.th}” ไพ่จะชี้ให้เห็นทิศทางที่เด่นที่สุดในตอนนี้ ทั้งสิ่งที่เขาแสดง สิ่งที่เขาซ่อน และจุดที่คุณควรวางใจให้ชัดก่อนตัดสินใจ`
  }

  return `ดูดวงความรักด้วยไพ่ยิปซี 3 ใบสำหรับคำถาม “${q.th}” เพื่ออ่านสถานการณ์ปัจจุบัน สิ่งที่อยู่ใต้ผิวน้ำ และคำแนะนำที่ช่วยให้คุณกลับมาเห็นหัวใจตัวเองชัดขึ้น`
}

function interpretationFrame(q) {
  if (q.pillar === 'predictive') {
    return 'ไพ่ใบแรกสะท้อนพลังหลักของสถานการณ์ตอนนี้ ใบที่สองเปิดสิ่งที่อีกฝ่ายหรือความสัมพันธ์กำลังเก็บไว้ใต้ผิวน้ำ ใบที่สามคือแนวโน้มและคำเตือน ไพ่ไม่ได้บังคับอนาคต แต่บอกว่าถ้าพลังปัจจุบันยังเดินแบบเดิม เรื่องนี้มีแนวโน้มจะไหลไปทางไหน'
  }

  return 'ไพ่ใบแรกสะท้อนสภาพใจและสถานการณ์ตรงหน้า ใบที่สองเปิดสิ่งที่ยังไม่ถูกพูดหรือยังไม่ถูกมองตรง ๆ ใบที่สามคือคำแนะนำสำหรับการก้าวต่อไป ไพ่ไม่ได้ตัดสินแทนคุณ แต่ช่วยให้คุณเห็นความจริงที่ใจพยายามเรียบเรียงอยู่แล้ว'
}

function generatePage(q) {
  const title = `${q.th} — ดูดวงความรัก ไพ่ยิปซี 3 ใบ | Veila`
  const description = pageIntro(q)
  const canonical = `${siteUrl}/th/scenarios/${q.key}/`
  const escapedQuestion = escapeHtml(q.th)
  const escapedTitle = escapeHtml(title)
  const escapedDescription = escapeHtml(description)
  const escapedLabel = escapeHtml(labelFor(q))
  const encodedCta = `/quick-love-reading/?q=${encodeURIComponent(q.key)}`
  const articleSchema = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: title,
    description,
    image: `${siteUrl}/og.png`,
    inLanguage: 'th-TH',
    datePublished: buildDate,
    dateModified: buildDate,
    publisher: {
      '@type': 'Organization',
      name: 'Veila',
      url: `${siteUrl}/`
    },
    mainEntityOfPage: canonical,
    author: {
      '@type': 'Person',
      '@id': `${siteUrl}/#person`,
      name: 'Veila Tarot Expert',
      url: `${siteUrl}/th/about/`,
      jobTitle: 'Tarot Reader & Hermit',
      description: 'Specializing in love tarot, Celtic Cross readings, and bilingual tarot interpretation.'
    }
  }
  const breadcrumbSchema = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      {
        '@type': 'ListItem',
        position: 1,
        name: 'หน้าแรก',
        item: `${siteUrl}/`
      },
      {
        '@type': 'ListItem',
        position: 2,
        name: 'ดูดวงความรัก',
        item: `${siteUrl}/th/tarot-love-readings/`
      },
      {
        '@type': 'ListItem',
        position: 3,
        name: q.th,
        item: canonical
      }
    ]
  }
  const faqSchema = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: [
      {
        '@type': 'Question',
        name: `${q.th} ดูด้วยไพ่กี่ใบ?`,
        acceptedAnswer: {
          '@type': 'Answer',
          text: 'บทอ่านนี้ใช้ไพ่ 3 ใบเพื่อดูสถานการณ์หลัก พลังที่ซ่อนอยู่ และคำแนะนำหรือแนวโน้มที่ควรระวัง'
        }
      },
      {
        '@type': 'Question',
        name: 'บทอ่านนี้เป็นคำทำนายตายตัวไหม?',
        acceptedAnswer: {
          '@type': 'Answer',
          text: 'ไม่ใช่คำตัดสินตายตัว ไพ่สะท้อนพลังและแนวโน้มปัจจุบัน เพื่อช่วยให้คุณเห็นทางเลือกและตัดสินใจด้วยสติ'
        }
      }
    ]
  }

  return `<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>${escapedTitle}</title>
<meta name="description" content="${escapedDescription}" />
<meta name="author" content="Veila Tarot" />
<meta name="robots" content="index, follow, max-image-preview:large" />
<meta name="theme-color" content="#0a0a0c" />
<meta name="color-scheme" content="dark" />

<link rel="canonical" href="${canonical}" />
<link rel="alternate" hreflang="th" href="${canonical}" />

<meta property="og:type" content="article" />
<meta property="og:site_name" content="Veila" />
<meta property="og:title" content="${escapedTitle}" />
<meta property="og:description" content="${escapedDescription}" />
<meta property="og:url" content="${canonical}" />
<meta property="og:image" content="${siteUrl}/og.png" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:locale" content="th_TH" />

<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="${escapedTitle}" />
<meta name="twitter:description" content="${escapedDescription}" />
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
  <a class="brand" href="/" aria-label="Veila — กลับสู่หน้าแรก">Veila<span class="dot"></span><span class="brand-sub">การทำสมาธิกับไพ่</span></a>
  <div class="lang-toggle" role="group" aria-label="ภาษา">
    <a href="${canonical}" class="active">TH</a>
  </div>
</header>

<main class="article scenario-page">
  <nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">หน้าแรก</a><span class="bc-sep">›</span><a href="/th/tarot-love-readings/">ดูดวงความรัก</a><span class="bc-sep">›</span><span class="bc-current">${escapedQuestion}</span></nav>
  <div class="eyebrow">${escapedLabel}</div>
  <h1 class="title">${escapedQuestion}</h1>

  <div class="aeo-snippet">
    <p>${escapedDescription}</p>
  </div>

  <p class="lede">คำถามนี้ไม่ได้ต้องการแค่คำว่าใช่หรือไม่ใช่ แต่มักต้องการความชัดเจนว่าใจคุณควรวางตรงไหน และควรมองสัญญาณไหนเป็นพิเศษ</p>

  <div class="divider"><span class="line"></span><span class="mark"></span><span class="line"></span></div>

  <h2>ดูดวงความรักสำหรับคำถามนี้</h2>
  <p>บทอ่านนี้เชื่อมกับระบบ Quick Love Reading ของ Veila โดยใช้ไพ่ 3 ใบและบทตีความเฉพาะคำถาม เมื่อคุณเลือกไพ่ ระบบจะเปิดความหมายที่เขียนไว้สำหรับ “${escapedQuestion}” โดยตรง ไม่ใช่คำตอบทั่วไป</p>

  <h2>ผังการอ่านสามใบ</h2>
  <ol class="positions">
      <li><strong>พลังหลักของสถานการณ์</strong>สิ่งที่กำลังเด่นที่สุดในความสัมพันธ์หรือในใจคุณตอนนี้</li>
      <li><strong>สิ่งที่ซ่อนอยู่</strong>ความรู้สึก แรงต้าน หรือความจริงที่ยังไม่ได้ถูกพูดออกมาตรง ๆ</li>
      <li><strong>คำแนะนำและแนวโน้ม</strong>ทิศทางที่ควรสังเกต และจุดที่คุณยังเลือกได้</li>
  </ol>

  <h2>กรอบการตีความ</h2>
  <p>${escapeHtml(interpretationFrame(q))}</p>

  <section class="scenario-disclaimer">
    <p>ใช้บทอ่านนี้เป็นเครื่องมือสะท้อนใจและอ่านทิศทาง ไม่ใช่คำสั่งให้ฝากชีวิตไว้กับไพ่ การตัดสินใจสุดท้ายยังเป็นของคุณเสมอ</p>
  </section>

  <div class="cta-row">
    <a href="${encodedCta}" class="cta-btn">เปิดไพ่ตอบคำถามนี้</a>
    <a href="/th/scenarios/" class="cta-btn ghost">ดูคำถามทั้งหมด</a>
    <a href="/th/tarot-love-readings/" class="cta-btn ghost">ไพ่เพื่อความรัก</a>
  </div>
</main>

<footer>
  <div class="fineprint">เพื่อการใคร่ครวญและอ่านทิศทาง ไม่ใช่การบังคับอนาคต</div>
  <div class="last-updated">ปรับปรุงล่าสุด · ${thaiBuildDate}</div>
  <nav class="footer-nav">
    <a href="/th/celtic-cross-tarot/">คู่มือเซลติกครอส</a>
    <span class="sep">·</span>
    <a href="/th/daily-tarot-card/">ไพ่ประจำวัน</a>
    <span class="sep">·</span>
    <a href="/th/all-tarot-pages/">ทุกหน้า</a>
  </nav>
  <div>veilatarot.com · © MMXXVI</div>
</footer>

</body>
</html>`
}

function generateIndex(questions) {
  const grouped = new Map()
  for (const q of questions) {
    const label = labelFor(q)
    if (!grouped.has(label)) grouped.set(label, [])
    grouped.get(label).push(q)
  }

  const sections = Array.from(grouped.entries()).map(([label, items]) => {
    const links = items
      .map((q) => `      <li><a href="/th/scenarios/${escapeHtml(q.key)}/">${escapeHtml(q.th)}</a></li>`)
      .join('\n')
    return `  <section>
    <h2>${escapeHtml(label)} (${items.length})</h2>
    <ul class="all-list">
${links}
    </ul>
  </section>`
  }).join('\n\n')

  return `<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>คำถามดูดวงความรักทั้งหมด — ไพ่ยิปซี 3 ใบ | Veila</title>
<meta name="description" content="รวมคำถามดูดวงความรัก ไพ่ยิปซี 3 ใบทั้งหมดของ Veila เลือกคำถามที่ตรงกับสถานการณ์ของคุณแล้วเปิดไพ่เพื่ออ่านคำตอบเฉพาะเรื่อง" />
<meta name="robots" content="index, follow, max-image-preview:large" />
<meta name="theme-color" content="#0a0a0c" />
<meta name="color-scheme" content="dark" />
<link rel="canonical" href="${siteUrl}/th/scenarios/" />
<link rel="alternate" hreflang="th" href="${siteUrl}/th/scenarios/" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="Veila" />
<meta property="og:title" content="คำถามดูดวงความรักทั้งหมด — ไพ่ยิปซี 3 ใบ | Veila" />
<meta property="og:description" content="รวมคำถามดูดวงความรัก ไพ่ยิปซี 3 ใบทั้งหมดของ Veila" />
<meta property="og:url" content="${siteUrl}/th/scenarios/" />
<meta property="og:image" content="${siteUrl}/og.png" />
<link rel="icon" href="/favicon.svg" type="image/svg+xml" />
<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png" />
<link rel="apple-touch-icon" href="/apple-touch-icon.png" sizes="180x180" />
<link rel="manifest" href="/manifest.webmanifest" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,400&family=IBM+Plex+Sans+Thai:wght@300;400;500;600&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="/assets/page.css" />
</head>
<body>
<header class="site-header">
  <a class="brand" href="/" aria-label="Veila — กลับสู่หน้าแรก">Veila<span class="dot"></span><span class="brand-sub">การทำสมาธิกับไพ่</span></a>
</header>
<main class="article scenario-page">
  <nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">หน้าแรก</a><span class="bc-sep">›</span><a href="/th/tarot-love-readings/">ดูดวงความรัก</a><span class="bc-sep">›</span><span class="bc-current">คำถามทั้งหมด</span></nav>
  <div class="eyebrow">Quick Love Reading</div>
  <h1 class="title">คำถามดูดวงความรักทั้งหมด</h1>
  <div class="aeo-snippet">
    <p>เลือกคำถามที่ตรงกับสถานการณ์ของคุณ แล้วเปิดไพ่ยิปซี 3 ใบเพื่ออ่านคำตอบเฉพาะเรื่องจาก Veila</p>
  </div>
${sections}
</main>
<footer>
  <div class="fineprint">เพื่อการใคร่ครวญและอ่านทิศทาง ไม่ใช่การบังคับอนาคต</div>
  <div class="last-updated">ปรับปรุงล่าสุด · ${thaiBuildDate}</div>
  <nav class="footer-nav">
    <a href="/th/tarot-love-readings/">ไพ่เพื่อความรัก</a>
    <span class="sep">·</span>
    <a href="/th/all-tarot-pages/">ทุกหน้า</a>
  </nav>
  <div>veilatarot.com · © MMXXVI</div>
</footer>
</body>
</html>`
}

const questions = readQuestions()
fs.mkdirSync(outDirBase, { recursive: true })

for (const q of questions) {
  const dirPath = path.join(outDirBase, q.key)
  fs.mkdirSync(dirPath, { recursive: true })
  fs.writeFileSync(path.join(dirPath, 'index.html'), generatePage(q))
}

fs.writeFileSync(path.join(outDirBase, 'index.html'), generateIndex(questions))

console.log(`Generated ${questions.length} quick-love scenario pages plus /th/scenarios/ index.`)
