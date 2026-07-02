#!/usr/bin/env node
/* Generate feed.xml — RSS 2.0 with the ~30 most recently updated content pages.
   pubDate = last git commit date of each page (fallback: file mtime).
   Candidate pool: zodiac sign pages (current month), career question pages,
   th/scenarios pages, guides, love-readings. noindex pages are excluded.

   Run:  node scripts/generate-feed.mjs        → writes feed.xml (repo root) */

import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const BASE = 'https://veilatarot.com/';
const OUT = path.join(ROOT, 'feed.xml');
const MAX_ITEMS = 30;
const MAX_PER_SECTION = 7;   // keep one section from crowding out the rest

// Sections eligible for feed items (dated content).
const SECTIONS = [
  'zodiac-love-tarot', 'th/zodiac-love-tarot',
  'career', 'th/career',
  'th/scenarios',
  'guides', 'th/guides',
  'love-readings',
];

// ---- git lastmod map (one git call) ----------------------------------------
function gitDates() {
  const map = new Map();
  const log = execSync('git log --pretty=format:@%cI --name-only -- .', {
    cwd: ROOT, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024,
  });
  let current = null;
  for (const line of log.split('\n')) {
    if (line.startsWith('@')) current = line.slice(1);
    else if (line && current && !map.has(line)) map.set(line, current);
  }
  return map;
}
const dates = gitDates();

function lastmod(relFile, absFile) {
  const iso = dates.get(relFile);
  if (iso) return new Date(iso);
  return fs.statSync(absFile).mtime;
}

// ---- page metadata ----------------------------------------------------------
function decode(s) {
  return s.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&#x27;/g, "'").replace(/&#39;/g, "'").trim();
}
function esc(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#x27;');
}
function meta(html) {
  const head = html.split('</head>')[0] || html;
  const noindex = head.toLowerCase().includes('noindex');
  const title = decode((head.match(/<title>([\s\S]*?)<\/title>/i) || [, ''])[1].replace(/\s+/g, ' '));
  const d = head.match(/<meta\s+name=["']description["']\s+content=["']([\s\S]*?)["']\s*\/?>/i);
  return { noindex, title, desc: decode((d ? d[1] : '').replace(/\s+/g, ' ')) };
}

// ---- collect candidates -----------------------------------------------------
const items = [];
for (const section of SECTIONS) {
  const dir = path.join(ROOT, section);
  if (!fs.existsSync(dir)) continue;
  const stack = [dir];
  while (stack.length) {
    const d = stack.pop();
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      const full = path.join(d, e.name);
      if (e.isDirectory()) stack.push(full);
      else if (e.name === 'index.html') {
        const rel = path.relative(ROOT, d).split(path.sep).join('/');
        const m = meta(fs.readFileSync(full, 'utf8'));
        if (m.noindex || !m.title) continue;
        items.push({
          section,
          url: `${BASE}${rel}/`,
          title: m.title,
          desc: m.desc,
          date: lastmod(`${rel}/index.html`, full),
        });
      }
    }
  }
}

// newest first; ties broken by URL for a deterministic feed
items.sort((a, b) => (b.date - a.date) || a.url.localeCompare(b.url));

// cap items per section so one bulk-updated section can't fill the feed
const perSection = new Map();
const top = [];
for (const it of items) {
  const n = perSection.get(it.section) || 0;
  if (n >= MAX_PER_SECTION) continue;
  perSection.set(it.section, n + 1);
  top.push(it);
  if (top.length >= MAX_ITEMS) break;
}

// ---- emit -------------------------------------------------------------------
const rfc822 = d => d.toUTCString().replace('GMT', '+0000');
let xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Veila Tarot</title>
    <link>${BASE}</link>
    <description>Bilingual (EN/TH) tarot readings — love, career, and monthly zodiac love readings, for reflection, not prediction.</description>
    <language>en</language>
    <lastBuildDate>${rfc822(new Date())}</lastBuildDate>
    <atom:link href="${BASE}feed.xml" rel="self" type="application/rss+xml" />
`;
for (const it of top) {
  xml += `    <item>
      <title>${esc(it.title)}</title>
      <link>${it.url}</link>
      <description>${esc(it.desc)}</description>
      <pubDate>${rfc822(it.date)}</pubDate>
      <guid isPermaLink="true">${it.url}</guid>
    </item>
`;
}
xml += `  </channel>
</rss>
`;
fs.writeFileSync(OUT, xml);
console.log(`Wrote ${OUT}: ${top.length} items (pool ${items.length})`);
