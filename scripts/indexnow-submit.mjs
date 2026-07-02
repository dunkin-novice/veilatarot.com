#!/usr/bin/env node
/* Submit URLs to IndexNow (Bing, Yandex, Seznam, Naver...).
 *
 * RUN ONLY AFTER DEPLOY — the engines fetch https://veilatarot.com/<key>.txt
 * to verify ownership, so the key file must be live first.
 *
 * Usage:
 *   node scripts/indexnow-submit.mjs                 # all URLs from sitemap.xml
 *   node scripts/indexnow-submit.mjs urls.txt        # one URL per line
 *
 * Expected responses: 200 OK / 202 Accepted. 403 = key file not reachable yet.
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const HOST = 'veilatarot.com';
const KEY = '07bff57e1cc48db9a0e3f9fbc608c623';
const KEY_LOCATION = `https://${HOST}/${KEY}.txt`;
const ENDPOINT = 'https://api.indexnow.org/indexnow';
const CHUNK = 10000; // IndexNow max per request

function urlsFromSitemap() {
  const xml = fs.readFileSync(path.join(ROOT, 'sitemap.xml'), 'utf8');
  return [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m => m[1].trim());
}

function urlsFromFile(file) {
  return fs.readFileSync(file, 'utf8').split('\n').map(s => s.trim()).filter(Boolean);
}

const urls = process.argv[2] ? urlsFromFile(process.argv[2]) : urlsFromSitemap();
if (!urls.length) {
  console.error('No URLs to submit.');
  process.exit(1);
}
console.log(`Submitting ${urls.length} URLs for ${HOST} ...`);

for (let i = 0; i < urls.length; i += CHUNK) {
  const batch = urls.slice(i, i + CHUNK);
  const res = await fetch(ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
    body: JSON.stringify({
      host: HOST,
      key: KEY,
      keyLocation: KEY_LOCATION,
      urlList: batch,
    }),
  });
  console.log(`Batch ${i / CHUNK + 1} (${batch.length} URLs): HTTP ${res.status} ${res.statusText}`);
  if (!res.ok && res.status !== 202) {
    console.error(await res.text());
    process.exit(1);
  }
}
console.log('Done.');
