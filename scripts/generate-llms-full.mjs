#!/usr/bin/env node
/* Generate llms-full.txt — a plain-text index of every indexable page:
   URL + <title> + meta description, grouped by section, deterministic order.

   Run from anywhere:  node scripts/generate-llms-full.mjs
   Output:             llms-full.txt (repo root) — commit it. */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const BASE = 'https://veilatarot.com/';
const OUT = path.join(ROOT, 'llms-full.txt');

// ---- collect pages ---------------------------------------------------------
function* walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name.startsWith('.') || entry.name === 'node_modules') continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) yield* walk(full);
    else if (entry.name === 'index.html') yield full;
  }
}

function decode(s) {
  return s
    .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&#x27;/g, "'").replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, ' ').trim();
}

function meta(html) {
  const head = html.split('</head>')[0] || html;
  const noindex = /<meta[^>]+name=["']robots["'][^>]+content=["'][^"']*noindex/i.test(head)
    || head.toLowerCase().includes('noindex');
  const title = decode((head.match(/<title>([\s\S]*?)<\/title>/i) || [, ''])[1].replace(/\s+/g, ' '));
  const descMatch = head.match(/<meta\s+name=["']description["']\s+content=["']([\s\S]*?)["']\s*\/?>/i);
  const desc = decode((descMatch ? descMatch[1] : '').replace(/\s+/g, ' '));
  return { noindex, title, desc };
}

// ---- sections (first match wins, listed in output order) -------------------
const SECTIONS = [
  ['Reading Apps', r => r === '' || r === 'th' || r === 'quick-love-reading'
    || r === 'career/reading' || r === 'th/career/reading' || r === 'th/quick-love-reading'],
  ['Love Readings (EN)', r => r === 'love-readings' || r.startsWith('love-readings/')],
  ['Thai Love & Life Questions', r => r === 'th/scenarios' || r.startsWith('th/scenarios/')],
  ['Career Readings (EN)', r => r === 'career' || r.startsWith('career/')],
  ['Career Readings (TH)', r => r === 'th/career' || r.startsWith('th/career/')],
  ['Zodiac Love Tarot (EN, monthly)', r => r === 'zodiac-love-tarot' || r.startsWith('zodiac-love-tarot/')],
  ['Zodiac Love Tarot (TH, monthly)', r => r === 'th/zodiac-love-tarot' || r.startsWith('th/zodiac-love-tarot/')],
  ['Card Meanings (EN)', r => r === 'cards' || r.startsWith('cards/')],
  ['Card Meanings (TH)', r => r === 'th/cards' || r.startsWith('th/cards/')],
  ['Guides & Hubs (EN)', r => r !== 'th' && !r.startsWith('th/')],
  ['Guides & Hubs (TH)', () => true],
];

const groups = new Map(SECTIONS.map(([name]) => [name, []]));
let total = 0;

for (const file of walk(ROOT)) {
  const rel = path.relative(ROOT, path.dirname(file)).split(path.sep).join('/');
  const relKey = rel === '.' ? '' : rel;
  const { noindex, title, desc } = meta(fs.readFileSync(file, 'utf8'));
  if (noindex) continue;
  const url = relKey === '' ? BASE : `${BASE}${relKey}/`;
  const [name] = SECTIONS.find(([, test]) => test(relKey));
  groups.get(name).push({ url, title, desc });
  total++;
}

// ---- emit -------------------------------------------------------------------
let out = `# Veila Tarot — full page index
# Bilingual (EN/TH) tarot readings: love, career, monthly zodiac, 78 card meanings.
# One block per page: URL, title, description. See also https://veilatarot.com/llms.txt

`;
for (const [name] of SECTIONS) {
  const pages = groups.get(name);
  if (!pages.length) continue;
  pages.sort((a, b) => a.url.localeCompare(b.url));
  out += `## ${name} (${pages.length} pages)\n\n`;
  for (const p of pages) {
    out += `${p.url}\n`;
    if (p.title) out += `Title: ${p.title}\n`;
    if (p.desc) out += `Description: ${p.desc}\n`;
    out += '\n';
  }
}

fs.writeFileSync(OUT, out);
console.log(`Wrote ${OUT}: ${total} pages`);
