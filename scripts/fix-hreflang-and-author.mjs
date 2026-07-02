#!/usr/bin/env node
/**
 * fix-hreflang-and-author.mjs
 *
 * 1) Repairs broken hreflang across /love-readings/, /guides/, /th/scenarios/:
 *    - love-readings pages previously declared hreflang="th" pointing at their
 *      OWN English URL (a self-reference lie). Where a real Thai twin exists at
 *      /th/scenarios/<key>/ (same question — matched by identical slug or via
 *      the assets/100-questions.js key whose EN text equals the slug), the th
 *      tag now points at the real Thai URL and the Thai page gets reciprocal
 *      en + x-default (x-default = the EN page). Where no twin exists, the fake
 *      th tag is removed (en self + x-default self remain).
 *    - guides pages have no Thai versions: fake th tag removed.
 *    - remaining th/scenarios pages (TH-only, no EN pair): normalized to
 *      th self + x-default self. Redirect stubs (noindex + meta refresh) are
 *      left untouched.
 * 2) Adds "author": {"@id": "https://veilatarot.com/#person"} to the
 *    Article / CollectionPage JSON-LD on every love-readings page, then
 *    re-validates that every JSON-LD block on touched files still parses.
 *
 * Idempotent: safe to re-run.
 */
import fs from 'node:fs';
import path from 'node:path';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const SITE = 'https://veilatarot.com';
const AUTHOR_LINE = '  "author": { "@id": "https://veilatarot.com/#person" },';

const read = (p) => fs.readFileSync(p, 'utf8');
const write = (p, s) => fs.writeFileSync(p, s);

// ---------- build the EN <-> TH pairing map ----------
const norm = (s) => s.toLowerCase().replace(/['’]/g, '').replace(/[^a-z0-9]+/g, ' ').trim();

const qSrc = read(path.join(ROOT, 'assets/100-questions.js'));
const questions = JSON.parse(qSrc.slice(qSrc.indexOf('['), qSrc.lastIndexOf(']') + 1));
const keyByEnText = new Map(questions.map((q) => [norm(q.en), q.key]));

const loveSlugs = fs.readdirSync(path.join(ROOT, 'love-readings'))
  .filter((d) => fs.existsSync(path.join(ROOT, 'love-readings', d, 'index.html')));

const isRedirectStub = (html) => /noindex/.test(html) && /http-equiv="refresh"/.test(html);

const thScenarioKeys = fs.readdirSync(path.join(ROOT, 'th/scenarios')).filter((d) => {
  const p = path.join(ROOT, 'th/scenarios', d, 'index.html');
  return fs.existsSync(p) && !isRedirectStub(read(p));
});
const thKeySet = new Set(thScenarioKeys);

// slug -> th key (only true 1:1 content pairs)
const pairs = new Map();
for (const slug of loveSlugs) {
  if (thKeySet.has(slug)) { pairs.set(slug, slug); continue; }
  const key = keyByEnText.get(slug.replace(/-/g, ' '));
  if (key && thKeySet.has(key)) pairs.set(slug, key);
}

// ---------- helpers ----------
const hreflangLine = (lang, url) => `<link rel="alternate" hreflang="${lang}" href="${url}" />`;
const rmLine = (html, re) => html.replace(re, '');

function extractJsonLdBlocks(html) {
  const blocks = [];
  const re = /<script type="application\/ld\+json">([\s\S]*?)<\/script>/g;
  let m;
  while ((m = re.exec(html))) blocks.push(m[1]);
  return blocks;
}
function assertJsonLdParses(file, html) {
  for (const b of extractJsonLdBlocks(html)) {
    try { JSON.parse(b); } catch (e) {
      throw new Error(`JSON-LD broken in ${file}: ${e.message}`);
    }
  }
}

const stats = { paired: [], unpaired: [], guides: 0, thPaired: 0, thNormalized: 0, authorAdded: 0 };

// ---------- 1a) love-readings pages (hub + slugs) ----------
for (const slug of loveSlugs) {
  const file = path.join(ROOT, 'love-readings', slug, 'index.html');
  let html = read(file);
  const enUrl = `${SITE}/love-readings/${slug}/`;
  const fakeThRe = new RegExp(
    `[ \\t]*<link rel="alternate" hreflang="th" href="${enUrl.replace(/[/.]/g, '\\$&')}"\\s*/>\\n?`
  );
  const key = pairs.get(slug);
  if (key) {
    const thUrl = `${SITE}/th/scenarios/${key}/`;
    if (fakeThRe.test(html)) {
      html = html.replace(fakeThRe, hreflangLine('th', thUrl) + '\n');
    } else if (!html.includes(`hreflang="th" href="${thUrl}"`)) {
      // insert after the en self line
      html = html.replace(hreflangLine('en', enUrl), `$&\n${hreflangLine('th', thUrl)}`);
    }
    stats.paired.push(`${slug} -> th/scenarios/${key}`);
  } else {
    if (fakeThRe.test(html)) html = rmLine(html, fakeThRe);
    stats.unpaired.push(slug);
  }

  // 2) author on Article / CollectionPage JSON-LD
  if (!html.includes('"author":')) {
    const before = html;
    html = html.replace(/("@type": "(?:Article|CollectionPage)",\n)/, `$1${AUTHOR_LINE}\n`);
    if (html !== before) stats.authorAdded++;
  }

  assertJsonLdParses(file, html);
  write(file, html);
}

// hub
{
  const file = path.join(ROOT, 'love-readings', 'index.html');
  let html = read(file);
  const enUrl = `${SITE}/love-readings/`;
  html = rmLine(html, new RegExp(`[ \\t]*<link rel="alternate" hreflang="th" href="${enUrl.replace(/[/.]/g, '\\$&')}"\\s*/>\\n?`));
  if (!html.includes('"author":')) {
    const before = html;
    html = html.replace(/("@type": "CollectionPage",\n)/, `$1${AUTHOR_LINE}\n`);
    if (html !== before) stats.authorAdded++;
  }
  assertJsonLdParses(file, html);
  write(file, html);
}

// ---------- 1b) guides pages (no Thai versions) ----------
for (const g of fs.readdirSync(path.join(ROOT, 'guides'))) {
  const file = path.join(ROOT, 'guides', g, 'index.html');
  if (!fs.existsSync(file)) continue;
  let html = read(file);
  const enUrl = `${SITE}/guides/${g}/`;
  const re = new RegExp(`[ \\t]*<link rel="alternate" hreflang="th" href="${enUrl.replace(/[/.]/g, '\\$&')}"\\s*/>\\n?`);
  if (re.test(html)) { html = rmLine(html, re); stats.guides++; write(file, html); }
}

// ---------- 1c) th/scenarios pages ----------
const enSlugByThKey = new Map([...pairs].map(([slug, key]) => [key, slug]));
for (const key of thScenarioKeys) {
  const file = path.join(ROOT, 'th/scenarios', key, 'index.html');
  let html = read(file);
  const thUrl = `${SITE}/th/scenarios/${key}/`;
  const thSelf = hreflangLine('th', thUrl);
  if (!html.includes(thSelf)) continue; // unexpected shape — leave alone
  const enSlug = enSlugByThKey.get(key);
  if (enSlug) {
    const enUrl = `${SITE}/love-readings/${enSlug}/`;
    const add = [];
    if (!html.includes(`hreflang="en"`)) add.push(hreflangLine('en', enUrl));
    if (!html.includes(`hreflang="x-default"`)) add.push(hreflangLine('x-default', enUrl));
    if (add.length) html = html.replace(thSelf, `${thSelf}\n${add.join('\n')}`);
    stats.thPaired++;
  } else if (!html.includes('hreflang="x-default"')) {
    html = html.replace(thSelf, `${thSelf}\n${hreflangLine('x-default', thUrl)}`);
    stats.thNormalized++;
  }
  write(file, html);
}

// th/scenarios hub (TH-only)
{
  const file = path.join(ROOT, 'th/scenarios', 'index.html');
  let html = read(file);
  const thUrl = `${SITE}/th/scenarios/`;
  const thSelf = hreflangLine('th', thUrl);
  if (html.includes(thSelf) && !html.includes('hreflang="x-default"')) {
    html = html.replace(thSelf, `${thSelf}\n${hreflangLine('x-default', thUrl)}`);
    write(file, html);
    stats.thNormalized++;
  }
}

// ---------- report ----------
console.log('PAIRED (%d):', stats.paired.length);
for (const p of stats.paired) console.log('  ' + p);
console.log('UNPAIRED love-readings slugs (fake th removed): %d', stats.unpaired.length);
console.log('guides th tags removed: %d', stats.guides);
console.log('th/scenarios paired (en + x-default added): %d', stats.thPaired);
console.log('th/scenarios normalized (x-default self added): %d', stats.thNormalized);
console.log('author added to JSON-LD: %d', stats.authorAdded);
