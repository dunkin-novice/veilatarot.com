/* Veila — reading-corpus AI-tell scanner.
   Encodes the "Reading QA Agent" spec (~/Brain/VeilaTarot/Reading QA Agent - AI-vs-Human Audit.md):
   scans every cell of one or more reading datasets and quantifies the EN + TH
   tells that flag a corpus as machine-made, against the spec thresholds.

   Cells = cards.<key>.{upright,reversed}.<position>.{en,th}  (~468/file/lang).

   Usage:
     node scripts/audit-reading-tells.mjs                       # all career-readings
     node scripts/audit-reading-tells.mjs <slug> [<slug> ...]   # specific slugs
     node scripts/audit-reading-tells.mjs --dir assets/data/love-readings
*/
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const REPO = path.resolve(__dirname, '..')

// thresholds (share of cells unless noted) — keep in sync with the QA spec §4
const T = {
  en: { emDash: 0.30, closer: 0.25, narrator: 0.40, posOpener: 0.40, notXbutY: 0.02, triad: 0.06 },
  th: { duenan: 0, particle: 0, thoeBoss: 0, meeKhwam: 0.05, singThi: 0.30, posOpener: 0.25 },
}

const args = process.argv.slice(2)
let dir = path.join(REPO, 'assets/data/career-readings')
const slugs = []
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--dir') dir = path.resolve(REPO, args[++i])
  else slugs.push(args[i])
}
let files = fs.readdirSync(dir).filter(f => f.endsWith('-reading.json'))
if (slugs.length) files = slugs.map(s => `${s}-reading.json`)

const pct = (n, d) => d ? (100 * n / d).toFixed(0) + '%' : '0%'
const flag = (val, thresh, higherWorse = true) =>
  (higherWorse ? val > thresh : val < thresh) ? ' ⚠️' : ' ok'

function cells(d) {
  const out = []
  const pks = (d.spread?.positions || []).map(p => p.key)
  for (const [card, c] of Object.entries(d.cards || {}))
    for (const o of ['upright', 'reversed'])
      for (const pk of pks) {
        const cell = c?.[o]?.[pk]
        if (cell) out.push({ card, o, pk, en: cell.en || '', th: cell.th || '' })
      }
  return out
}

const opener = (s, n = 3) => s.trim().split(/\s+/).slice(0, n).join(' ').toLowerCase()
// TH has no spaces — use a leading-cluster heuristic for the opener
const thOpener = s => (s.trim().match(/^[฀-๿]+(\s|$)?[฀-๿]*/) || [''])[0].slice(0, 10)

function maxPositionUniformity(list, key, openFn) {
  const groups = {}
  for (const c of list) {
    const g = `${c.o}:${c.pk}`
    ;(groups[g] ||= {}).total = (groups[g]?.total || 0) + 1
    const op = openFn(c[key])
    ;(groups[g].ops ||= {})[op] = (groups[g].ops?.[op] || 0) + 1
  }
  let worst = { share: 0 }
  for (const [g, v] of Object.entries(groups)) {
    const top = Object.entries(v.ops).sort((a, b) => b[1] - a[1])[0]
    const share = top[1] / v.total
    if (share > worst.share) worst = { share, group: g, opener: top[0], n: top[1], total: v.total }
  }
  return worst
}

function auditFile(file) {
  const d = JSON.parse(fs.readFileSync(path.join(dir, file), 'utf8'))
  const list = cells(d)
  const N = list.length
  const en = list.map(c => c.en), th = list.map(c => c.th)

  // EN
  const emDash = en.filter(s => s.includes('—')).length
  const closer = en.filter(s => /(yours to \w+|in your hands|your hands)[.”"']*\s*$/i.test(s.trim())).length
  const narrator = en.filter(s => /\bthe cards?\b/i.test(s)).length
  const notXbutY = en.filter(s => /not just .+,? but |isn['’]t about .+,? it['’]s/i.test(s)).length
  const triad = en.filter(s => /\b\w+, \w+,? and \w+\b/.test(s)).length
  const enPos = maxPositionUniformity(list, 'en', s => opener(s, 3))

  // TH
  const duenan = th.filter(s => /ดังนั้น|อย่างไรก็ตาม|ในขณะที่/.test(s)).length
  const particle = th.filter(s => /(ค่ะ|นะคะ|ครับ)[\s"”']*$/.test(s.trim())).length
  const thoe = th.filter(s => /เธอ/.test(s)).length
  const meeKhwam = th.filter(s => /มีความ[฀-๿]/.test(s)).length
  const singThi = th.filter(s => /สิ่งที่/.test(s)).length
  const thPos = maxPositionUniformity(list, 'th', thOpener)

  return { file, N, emDash, closer, narrator, notXbutY, triad, enPos,
           duenan, particle, thoe, meeKhwam, singThi, thPos }
}

const results = files.map(auditFile)
const agg = results.reduce((a, r) => {
  for (const k of ['N','emDash','closer','narrator','notXbutY','triad','duenan','particle','thoe','meeKhwam','singThi'])
    a[k] = (a[k] || 0) + r[k]
  return a
}, {})

console.log(`\n=== Reading tell-scan: ${files.length} file(s), ${agg.N} cells/lang ===\n`)
for (const r of results) {
  console.log(`• ${r.file.replace('-reading.json','')}  (${r.N} cells)`)
  console.log(`   EN  em-dash ${pct(r.emDash,r.N)}${flag(r.emDash/r.N,T.en.emDash)} · closer ${pct(r.closer,r.N)}${flag(r.closer/r.N,T.en.closer)} · "the cards" ${pct(r.narrator,r.N)}${flag(r.narrator/r.N,T.en.narrator)} · pos-opener ${pct(r.enPos.n,r.enPos.total)}${flag(r.enPos.share,T.en.posOpener)} ("${r.enPos.opener}")`)
  console.log(`   TH  ดังนั้น/calque ${r.duenan}${flag(r.duenan,T.th.duenan)} · particle ${r.particle}${flag(r.particle,T.th.particle)} · เธอ ${r.thoe}${flag(r.thoe,T.th.thoeBoss)} · มีความ+adj ${pct(r.meeKhwam,r.N)}${flag(r.meeKhwam/r.N,T.th.meeKhwam)} · สิ่งที่ ${pct(r.singThi,r.N)}${flag(r.singThi/r.N,T.th.singThi)} · pos-opener ${pct(r.thPos.n,r.thPos.total)}${flag(r.thPos.share,T.th.posOpener)}`)
}
console.log(`\n=== CORPUS (${agg.N} cells) ===`)
console.log(`EN  em-dash ${pct(agg.emDash,agg.N)}${flag(agg.emDash/agg.N,T.en.emDash)} · closer-family ${pct(agg.closer,agg.N)}${flag(agg.closer/agg.N,T.en.closer)} · "the cards" ${pct(agg.narrator,agg.N)}${flag(agg.narrator/agg.N,T.en.narrator)} · not-X-but-Y ${pct(agg.notXbutY,agg.N)}${flag(agg.notXbutY/agg.N,T.en.notXbutY)} · triad ${pct(agg.triad,agg.N)}${flag(agg.triad/agg.N,T.en.triad)}`)
console.log(`TH  calque ${agg.duenan}${flag(agg.duenan,T.th.duenan)} · particle ${agg.particle}${flag(agg.particle,T.th.particle)} · เธอ ${agg.thoe} · มีความ+adj ${pct(agg.meeKhwam,agg.N)}${flag(agg.meeKhwam/agg.N,T.th.meeKhwam)} · สิ่งที่ ${pct(agg.singThi,agg.N)}${flag(agg.singThi/agg.N,T.th.singThi)}`)
console.log(`\n(⚠️ = exceeds spec threshold; see "Reading QA Agent - AI-vs-Human Audit" §4. เธอ counts include legitimate card-persona/3rd-party uses — inspect, don't blind-fix.)\n`)
