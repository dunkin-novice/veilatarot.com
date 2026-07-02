#!/usr/bin/env node
/**
 * build-daily-reading.mjs
 *
 * Injects the LATEST data/daily-readings/<date>.json (a 3-card collective
 * love/life reading, produced daily by the scheduled cloud task) into
 * daily-tarot-card/index.html as a server-rendered, crawlable section.
 *
 * - The section lives between <!-- DAILY-READING:START --> / END markers,
 *   so re-runs replace it in place (idempotent: same input -> byte-identical
 *   output).
 * - Also updates the page's Article JSON-LD: dateModified = the reading's
 *   date, and adds author @id https://veilatarot.com/#person if absent.
 * - The interactive client-side draw (#daily-card + its inline JS) is left
 *   untouched.
 *
 * TH note: th/daily-love-tarot/index.html is a matching Thai surface, but the
 * daily JSON currently carries English text only, so no Thai section is
 * injected. If the cloud task starts emitting Thai fields, extend this script
 * rather than hand-editing that page.
 *
 * Usage: node scripts/build-daily-reading.mjs
 * No dependencies. Node >= 16.
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const DATA_DIR = path.join(ROOT, 'data', 'daily-readings');
const PAGE = path.join(ROOT, 'daily-tarot-card', 'index.html');

const START = '<!-- DAILY-READING:START -->';
const END = '<!-- DAILY-READING:END -->';

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'];

function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function humanDate(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  if (!m) throw new Error(`Bad date: ${iso}`);
  return `${MONTHS[Number(m[2]) - 1]} ${Number(m[3])}, ${m[1]}`;
}

// ---------------------------------------------------------------------------
// 1. Find the newest reading JSON.
// ---------------------------------------------------------------------------
const files = fs.readdirSync(DATA_DIR)
  .filter((f) => /^\d{4}-\d{2}-\d{2}\.json$/.test(f))
  .sort(); // ISO dates sort lexicographically
if (files.length === 0) {
  console.error(`No reading JSONs found in ${DATA_DIR}`);
  process.exit(1);
}
const latestFile = files[files.length - 1];
const reading = JSON.parse(fs.readFileSync(path.join(DATA_DIR, latestFile), 'utf8'));
const date = reading.date || latestFile.replace(/\.json$/, '');

// ---------------------------------------------------------------------------
// 2. Split interpretation_markdown into its "## Heading" sections.
// ---------------------------------------------------------------------------
const sections = []; // { heading, text }
for (const block of String(reading.interpretation_markdown || '').split(/^## +/m)) {
  const trimmed = block.trim();
  if (!trimmed) continue;
  const nl = trimmed.indexOf('\n');
  if (nl === -1) continue;
  sections.push({
    heading: trimmed.slice(0, nl).trim(),
    text: trimmed.slice(nl + 1).trim(),
  });
}

// Pair each drawn card with its section via the position keyword
// (Anchor / Current / Trajectory), falling back to document order.
function sectionFor(card, idx) {
  const key = String(card.position || '').toLowerCase();
  const hit = sections.find((s) => key && s.heading.toLowerCase().includes(key));
  return hit || sections[idx] || null;
}

const synthesis = sections.find((s) => /synthesis/i.test(s.heading)) || null;

// ---------------------------------------------------------------------------
// 3. Assemble a 40-60-word direct-answer summary from the reading's own
//    text (deterministic): the first sentence of each card's section, padded
//    with Synthesis sentences if that lands under 40 words.
// ---------------------------------------------------------------------------
function sentencesOf(text) {
  const flat = String(text).replace(/\s+/g, ' ').trim();
  return (flat.match(/[^.!?]+[.!?]+(?:["')\]]+)?/g) || [flat]).map((s) => s.trim());
}
function wordCount(s) {
  return s.split(/\s+/).filter(Boolean).length;
}

const cards = Array.isArray(reading.cards_drawn) ? reading.cards_drawn : [];
const summaryParts = [];
let summaryWords = 0;
for (let i = 0; i < cards.length; i++) {
  const sec = sectionFor(cards[i], i);
  if (!sec) continue;
  const first = sentencesOf(sec.text)[0];
  if (!first) continue;
  summaryParts.push(first);
  summaryWords += wordCount(first);
}
if (synthesis) {
  for (const s of sentencesOf(synthesis.text)) {
    if (summaryWords >= 40) break;
    if (summaryWords + wordCount(s) > 62 && summaryWords >= 40) break;
    summaryParts.push(s);
    summaryWords += wordCount(s);
  }
}
const summary = summaryParts.join(' ');

// ---------------------------------------------------------------------------
// 4. Render the section HTML.
// ---------------------------------------------------------------------------
const cardBlocks = cards.map((card, i) => {
  const sec = sectionFor(card, i);
  const label = `${esc(card.name)} (${esc(card.orientation)})` +
    (card.position ? ` — ${esc(card.position)}` : '');
  const paras = sec
    ? sec.text.split(/\n{2,}/).map((p) => `    <p>${esc(p.trim())}</p>`).join('\n')
    : '';
  return `    <h3>${label}</h3>\n${paras}`;
}).join('\n');

const synthesisBlock = synthesis
  ? `    <h3>${esc(synthesis.heading)}</h3>\n` +
    synthesis.text.split(/\n{2,}/).map((p) => `    <p>${esc(p.trim())}</p>`).join('\n') + '\n'
  : '';

const sectionHtml = `${START}
  <!-- Generated by scripts/build-daily-reading.mjs from data/daily-readings/${latestFile} — do not edit by hand. -->
  <section class="daily-collective-reading" id="todays-collective-reading">
    <h2>Today's collective reading — ${esc(humanDate(date))}</h2>
    <p class="reading-summary"><strong>${esc(summary)}</strong></p>
${cardBlocks}
${synthesisBlock}    <p class="reading-note"><em>A new collective reading is published each morning, Bangkok time (UTC+7). The card drawn above is your personal one-card pull; this section is the shared three-card reading for ${esc(humanDate(date))}.</em></p>
  </section>
  ${END}`;

// ---------------------------------------------------------------------------
// 5. Inject into the page (replace between markers, or insert after the
//    interactive #daily-card section on first run).
// ---------------------------------------------------------------------------
let html = fs.readFileSync(PAGE, 'utf8');

const startIdx = html.indexOf(START);
const endIdx = html.indexOf(END);
if (startIdx !== -1 && endIdx !== -1) {
  html = html.slice(0, startIdx) + sectionHtml + html.slice(endIdx + END.length);
} else {
  // First run: insert right after the interactive draw section closes.
  const anchor = /(<section class="daily-card"[\s\S]*?<\/section>)/;
  if (!anchor.test(html)) {
    console.error('Could not find the #daily-card section to anchor the injection.');
    process.exit(1);
  }
  html = html.replace(anchor, `$1\n\n  ${sectionHtml}`);
}

// ---------------------------------------------------------------------------
// 6. Update the Article JSON-LD: dateModified + author @id.
// ---------------------------------------------------------------------------
html = html.replace(
  /(<script type="application\/ld\+json">)([\s\S]*?)(<\/script>)/g,
  (whole, open, body, close) => {
    let obj;
    try { obj = JSON.parse(body); } catch { return whole; }
    if (obj['@type'] !== 'Article') return whole;
    obj.dateModified = date;
    if (!obj.author) {
      obj.author = { '@id': 'https://veilatarot.com/#person' };
    }
    return `${open}\n${JSON.stringify(obj, null, 2)}\n${close}`;
  }
);

const before = fs.existsSync(PAGE) ? fs.readFileSync(PAGE, 'utf8') : '';
if (before === html) {
  console.log(`No changes: ${path.relative(ROOT, PAGE)} already reflects ${latestFile}.`);
} else {
  fs.writeFileSync(PAGE, html);
  console.log(`Injected ${latestFile} into ${path.relative(ROOT, PAGE)} (dateModified=${date}).`);
}
