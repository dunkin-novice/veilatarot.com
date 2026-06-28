export const meta = {
  name: 'build-career-question',
  description: 'Generate a full bilingual (EN/TH) 78-card career-reading dataset for one question',
  phases: [
    { title: 'Design spread' },
    { title: 'Generate cards' },
  ],
}

// ---- args: { qkey, slug, en, th, pillar } ----
let Q = args
if (typeof Q === 'string') { try { Q = JSON.parse(Q) } catch (e) { throw new Error('args string not JSON: ' + e.message) } }
if (!Q || !Q.en || !Q.slug) throw new Error('args must include {qkey, slug, en, th, pillar}; got: ' + JSON.stringify(args))

const CARD_KEYS = [
  "01-the-fool","02-the-magician","03-the-high-priestess","04-the-empress","05-the-emperor","06-the-hierophant","07-the-lovers","08-the-chariot","09-strength","10-the-hermit","11-wheel-of-fortune","12-justice","13-the-hanged-man","14-death","15-temperance","16-the-devil","17-the-tower","18-the-star","19-the-moon","20-the-sun","21-judgement","22-the-world","23-ace-of-wands","24-two-of-wands","25-three-of-wands","26-four-of-wands","27-five-of-wands","28-six-of-wands","29-seven-of-wands","30-eight-of-wands","31-nine-of-wands","32-ten-of-wands","33-page-of-wands","34-knight-of-wands","35-queen-of-wands","36-king-of-wands","37-ace-of-cups","38-two-of-cups","39-three-of-cups","40-four-of-cups","41-five-of-cups","42-six-of-cups","43-seven-of-cups","44-eight-of-cups","45-nine-of-cups","46-ten-of-cups","47-page-of-cups","48-knight-of-cups","49-queen-of-cups","50-king-of-cups","51-ace-of-swords","52-two-of-swords","53-three-of-swords","54-four-of-swords","55-five-of-swords","56-six-of-swords","57-seven-of-swords","58-eight-of-swords","59-nine-of-swords","60-ten-of-swords","61-page-of-swords","62-knight-of-swords","63-queen-of-swords","64-king-of-swords","65-ace-of-pentacles","66-two-of-pentacles","67-three-of-pentacles","68-four-of-pentacles","69-five-of-pentacles","70-six-of-pentacles","71-seven-of-pentacles","72-eight-of-pentacles","73-nine-of-pentacles","74-ten-of-pentacles","75-page-of-pentacles","76-knight-of-pentacles","77-queen-of-pentacles","78-king-of-pentacles"
]

const VOICE = `Veila is a bilingual career-tarot ORACLE. She SEES and TELLS — confident and certain, like a trusted Thai หมอดู who looks you in the eye and says it straight about your work, your path, and your money.
Voice: warm but DIRECT and DECLARATIVE, second-person ("you" / TH "คุณ" for the querent; for a boss, employer, client, or colleague use "เขา" / "ที่ทำงาน" — NEVER "เธอ"). The cards SEE what the querent cannot: where the work is really heading, what is being blocked, whether they are valued, where the money is moving. State it with authority ("The cards show that this role…" / "ไพ่เห็นว่างานนี้…"), NOT hedged mirrors ("maybe you feel…" / "ลองสังเกตว่า…").
Be CERTAIN about the present and the DIRECTION things are moving ("this is moving toward…" / "กำลังมุ่งไปทาง…") — that certainty is the whole point of being แม่น. Speak of MONEY as conditions, momentum, and direction (rising, tightening, opening, well-earned) — NEVER invent literal amounts, salary figures, calendar dates, or fixed timeframes ("a raise within 3 months", "฿50,000").
Always EMPOWERING and AGENTIC — work is something the querent acts on, not fate: tell the truth AND what they can do about it ("…and the move is yours to make" / "…และจังหวะนี้คุณเป็นคนกำหนดเอง"). Grounded in craft, effort, and circumstance, never doom or get-rich fantasy. Warm, not cruel — a hard truth delivered kindly.
TH is a natural Thai oracle voice (confident, gypsy-card หมอดู tone, คุณ for the querent / เขา or ที่ทำงาน for the other party) — NOT a literal translation of the EN. Each answer 2-4 sentences.
Do NOT end TH sentences with polite particles (ค่ะ / นะคะ / ครับ / ค่า) — keep the Thai clean, direct, and declarative, not chatty or service-desk polite.`

// ---------- Phase 1: design the spread ----------
phase('Design spread')
const SPREAD_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    positions: {
      type: 'array', minItems: 3, maxItems: 3,
      items: {
        type: 'object', additionalProperties: false,
        properties: {
          key:      { type: 'string', description: 'lowercase snake_case, e.g. your_block' },
          label_en: { type: 'string' },
          label_th: { type: 'string' },
        },
        required: ['key', 'label_en', 'label_th'],
      },
    },
    tone: { type: 'string', description: 'one sentence of extra tonal guidance specific to this question' },
  },
  required: ['positions', 'tone'],
}

const spread = await agent(
  `${VOICE}

Design a 3-card tarot spread for this career/work/money question (pillar: ${Q.pillar || 'career'}):
EN: "${Q.en}"
TH: "${Q.th}"

Return 3 spread positions that together answer the question as a small narrative arc.
Each position: a short snake_case key, an EN label, and a natural TH label.
Also return one extra sentence of tonal guidance ("tone").`,
  { label: 'spread', phase: 'Design spread', schema: SPREAD_SCHEMA }
)

const positionKeys = spread.positions.map(p => p.key)
const positionBrief = spread.positions
  .map(p => `- ${p.key}: ${p.label_en} / ${p.label_th}`)
  .join('\n')

// ---------- Phase 2: generate cards in batches ----------
phase('Generate cards')
const BATCH = 6
const batches = []
for (let i = 0; i < CARD_KEYS.length; i += BATCH) batches.push(CARD_KEYS.slice(i, i + BATCH))

const POS_BLOCK = {
  type: 'array', minItems: 3, maxItems: 3,
  items: {
    type: 'object', additionalProperties: false,
    properties: {
      position: { type: 'string' },
      en:       { type: 'string' },
      th:       { type: 'string' },
    },
    required: ['position', 'en', 'th'],
  },
}
const BATCH_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    cards: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: {
          key:      { type: 'string' },
          upright:  POS_BLOCK,
          reversed: POS_BLOCK,
        },
        required: ['key', 'upright', 'reversed'],
      },
    },
  },
  required: ['cards'],
}

const batchResults = await parallel(batches.map((b, bi) => () =>
  agent(
    `${VOICE}
Extra tone: ${spread.tone}

QUESTION  EN: "${Q.en}"
QUESTION  TH: "${Q.th}"

3 SPREAD POSITIONS (use these exact keys in "position"):
${positionBrief}

For EACH of these tarot cards, write BOTH upright and reversed readings, and for each
orientation write one answer per spread position (3 positions), in EN and TH.
Interpret each card's standard tarot meaning THROUGH the lens of this specific question and position.

Cards in this batch (use the exact key string):
${b.map(k => '- ' + k).join('\n')}

Return all ${b.length} cards.`,
    { label: `cards:${b[0]}…`, phase: 'Generate cards', schema: BATCH_SCHEMA }
  )
))

// ---------- assemble ----------
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
for (const r of batchResults) ingest(r)

// ---------- repair: re-run any missing cards SEQUENTIALLY (dodges rate limits) ----------
function genBatch(keys) {
  return agent(
    `${VOICE}
Extra tone: ${spread.tone}

QUESTION  EN: "${Q.en}"
QUESTION  TH: "${Q.th}"

3 SPREAD POSITIONS (use these exact keys in "position"):
${positionBrief}

For EACH of these tarot cards, write BOTH upright and reversed readings, and for each
orientation write one answer per spread position (3 positions), in EN and TH.
Interpret each card's standard tarot meaning THROUGH the lens of this specific question and position.

Cards in this batch (use the exact key string):
${keys.map(k => '- ' + k).join('\n')}

Return all ${keys.length} cards.`,
    { label: `repair:${keys[0]}…`, phase: 'Generate cards', schema: BATCH_SCHEMA }
  )
}
for (let round = 0; round < 4; round++) {
  const missingKeys = CARD_KEYS.filter(k => !cards[k])
  if (!missingKeys.length) break
  log(`repair round ${round + 1}: ${missingKeys.length} cards missing`)
  for (let i = 0; i < missingKeys.length; i += BATCH) {
    const chunk = missingKeys.slice(i, i + BATCH)
    try { ingest(await genBatch(chunk)) } catch (e) { log(`repair chunk failed: ${e.message}`) }
  }
}

// completeness report
const missing = []
for (const k of CARD_KEYS) {
  const c = cards[k]
  if (!c) { missing.push(k + ':absent'); continue }
  for (const o of ['upright', 'reversed'])
    for (const pk of positionKeys)
      if (!c[o] || !c[o][pk] || !c[o][pk].en || !c[o][pk].th) missing.push(`${k}:${o}:${pk}`)
}
log(`assembled ${Object.keys(cards).length}/78 cards; ${missing.length} missing slots`)

return {
  version: `${Q.slug}-reading-v1`,
  locale_support: ['en', 'th'],
  question: { key: Q.qkey || Q.slug, en: Q.en, th: Q.th },
  spread: {
    card_count: 3,
    positions: spread.positions.map(p => ({ key: p.key, label: { en: p.label_en, th: p.label_th } })),
  },
  cards,
  _meta: { missing, positionKeys },
}
