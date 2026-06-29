/* Veila — draw one month's zodiac love spreads.
   Deterministic + reproducible: the same monthKey always yields the same
   draw (seeded PRNG), so a rebuild never silently reshuffles. Draws 36
   DISTINCT cards (12 signs × 3) from the 78-card deck, so no card repeats
   across the month → every page is unique content.

   Writes assets/data/zodiac-love/<monthKey>.json with each card's id +
   orientation + EMPTY reading slots (en/th). The per-sign interpretations
   are filled in afterward (by agents / postprocess), then the page
   generator (build-zodiac-love-tarot.mjs) renders from this file.

   Usage: node scripts/draw-zodiac-month.mjs 2026-07
*/
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { SIGNS, POSITIONS, monthLabels } from './zodiac-signs.mjs'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const rootDir = path.resolve(__dirname, '..')

const monthKey = process.argv[2]
if (!monthKey || !/^\d{4}-\d{2}$/.test(monthKey)) {
  console.error('Usage: node scripts/draw-zodiac-month.mjs YYYY-MM'); process.exit(1)
}

// --- seeded PRNG (xfnv1a hash -> mulberry32), no Date/Math.random ---
function xfnv1a(str) {
  let h = 2166136261 >>> 0
  for (let i = 0; i < str.length; i++) { h = Math.imul(h ^ str.charCodeAt(i), 16777619) }
  return h >>> 0
}
function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}
const rand = mulberry32(xfnv1a(`veila-zodiac-${monthKey}`))

const deck = JSON.parse(fs.readFileSync(path.join(rootDir, 'cards.json'), 'utf8'))
if (!Array.isArray(deck) || deck.length !== 78) throw new Error('cards.json not 78 cards')

// Fisher–Yates with the seeded rand → a deterministic shuffle of all 78.
const pool = deck.map((c) => c.id)
for (let i = pool.length - 1; i > 0; i--) {
  const j = Math.floor(rand() * (i + 1))
  ;[pool[i], pool[j]] = [pool[j], pool[i]]
}

const out = {
  month: monthKey,
  month_label: monthLabels(monthKey),
  spread: { card_count: 3, positions: POSITIONS },
  signs: {}
}

let k = 0
for (const sign of SIGNS) {
  const cards = POSITIONS.map((pos) => {
    const id = pool[k++]                       // distinct across the whole month
    const reversed = rand() < 0.3              // ~30% reversed, seeded
    return { position_key: pos.key, id, reversed, reading: { en: '', th: '' } }
  })
  out.signs[sign.slug] = { cards }
}

const dir = path.join(rootDir, 'assets', 'data', 'zodiac-love')
fs.mkdirSync(dir, { recursive: true })
const fp = path.join(dir, `${monthKey}.json`)
fs.writeFileSync(fp, JSON.stringify(out, null, 2) + '\n')
console.log(`Wrote ${fp} — 12 signs × 3 cards (${36} distinct draws), readings empty.`)
