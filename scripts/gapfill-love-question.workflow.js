export const meta = {
  name: 'gapfill-love-question',
  description: 'Generate only the missing cards for one love-reading question (low concurrency)',
  phases: [{ title: 'Gapfill' }],
}

let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { throw new Error('args not JSON: ' + e.message) } }
if (!A || !A.missing || !A.positions) throw new Error('args need {slug,en,th,positions,missing}')

const VOICE = `Veila is a bilingual love-tarot site positioned for REFLECTION, not prediction.
Voice: quiet, considered, warm, second-person ("you"). Never predict events/dates. TH is a natural
Thai localization (reflective, gentle), NOT a literal translation. Each answer 2-4 sentences.`

const positionBrief = A.positions.map(p => `- ${p.key}: ${p.label_en} / ${p.label_th}`).join('\n')

const POS_BLOCK = {
  type: 'array', minItems: 3, maxItems: 3,
  items: { type: 'object', additionalProperties: false,
    properties: { position: { type: 'string' }, en: { type: 'string' }, th: { type: 'string' } },
    required: ['position', 'en', 'th'] },
}
const BATCH_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: { cards: { type: 'array', items: {
    type: 'object', additionalProperties: false,
    properties: { key: { type: 'string' }, upright: POS_BLOCK, reversed: POS_BLOCK },
    required: ['key', 'upright', 'reversed'] } } },
  required: ['cards'],
}

phase('Gapfill')
const cards = {}
function ingest(r) {
  if (!r || !r.cards) return
  for (const c of r.cards) {
    const up = {}, rev = {}
    for (const p of c.upright)  up[p.position]  = { en: p.en, th: p.th }
    for (const p of c.reversed) rev[p.position] = { en: p.en, th: p.th }
    cards[c.key] = { upright: up, reversed: rev }
  }
}
function gen(keys) {
  return agent(
    `${VOICE}

QUESTION  EN: "${A.en}"
QUESTION  TH: "${A.th}"

3 SPREAD POSITIONS (use these exact keys in "position"):
${positionBrief}

For EACH tarot card below, write BOTH upright and reversed, one answer per spread position (3),
in EN and TH, interpreting the card through this question/position.

Cards (use exact key):
${keys.map(k => '- ' + k).join('\n')}

Return all ${keys.length} cards.`,
    { label: `gapfill:${keys[0]}…`, phase: 'Gapfill', schema: BATCH_SCHEMA })
}

// sequential, small batches, several rounds — never floods the server
const BATCH = 3
for (let round = 0; round < 6; round++) {
  const todo = A.missing.filter(k => !cards[k])
  if (!todo.length) break
  log(`round ${round + 1}: ${todo.length} missing`)
  for (let i = 0; i < todo.length; i += BATCH) {
    try { ingest(await gen(todo.slice(i, i + BATCH))) } catch (e) { log('chunk failed: ' + e.message) }
  }
}

return { slug: A.slug, cards, stillMissing: A.missing.filter(k => !cards[k]) }
