#!/usr/bin/env python3
"""Clone /quick-love-reading/index.html -> /career/reading/index.html with all
career re-pointing. Re-runnable (regenerates from the love app each time).

Swaps: data source (career-questions.js / CAREER_QUESTIONS), empties love
ORIGINAL_PRESETS + QUESTION_ALIASES, replaces QUESTION_DATASETS with the 18
career entries, rewrites head SEO + the prominent visible love copy.
"""
import json, os, re, sys

REPO = "/Users/kitikornrakhangthong/projects/veilatarot.com"
SRC = os.path.join(REPO, "quick-love-reading/index.html")
OUT_DIR = os.path.join(REPO, "career/reading")
OUT = os.path.join(OUT_DIR, "index.html")

# 18 career question keys (order = career-questions.js)
KEYS = [
    "should-i-take-this-job","should-i-quit","is-this-career-right","am-i-underpaid",
    "will-money-improve","should-i-ask-for-a-raise","change-careers","why-is-work-stuck",
    "whats-blocking-my-success","should-i-start-my-own-thing","is-this-offer-good",
    "how-to-grow-here","are-they-valuing-me","should-i-wait-or-move","what-is-my-calling",
    "how-to-handle-money-fear","will-this-project-land","should-i-go-back-to-study",
]

def replace_block(html, start_pat, close, new_text, label):
    """Replace from start_pat through its terminating '\n' + close (']' or '}') + ';'."""
    m = re.search(start_pat + r".*?\n" + re.escape(close) + ";", html, re.S)
    if not m:
        raise SystemExit(f"could not locate block: {label}")
    return html[:m.start()] + new_text + html[m.end():]

def main():
    html = open(SRC).read()

    # ---- data source ----
    html = html.replace("/assets/100-questions.js", "/assets/career-questions.js")
    html = html.replace("HUNDRED_QUESTIONS", "CAREER_QUESTIONS")

    # ---- empty love presets + aliases ----
    html = replace_block(html, r"const ORIGINAL_PRESETS = \[", "]", "const ORIGINAL_PRESETS = [];", "ORIGINAL_PRESETS")
    html = replace_block(html, r"const QUESTION_ALIASES = \{", "}", "const QUESTION_ALIASES = {};", "QUESTION_ALIASES")

    # ---- career dataset map ----
    entries = ",\n".join(
        f"  '{k}': '/assets/data/career-readings/{k}-reading.json'" for k in KEYS
    )
    html = replace_block(html, r"const QUESTION_DATASETS = \{", "}",
                         "const QUESTION_DATASETS = {\n" + entries + "\n};", "QUESTION_DATASETS")

    # ---- head SEO ----
    repl = {
        "<title>Quick Love Reading — A 3-Card Tarot Reflection | Veila</title>":
            "<title>Quick Career Reading — A 3-Card Tarot Reflection | Veila</title>",
        'content="Quick Love Reading — A 3-Card Tarot Reflection | Veila"':
            'content="Quick Career Reading — A 3-Card Tarot Reflection | Veila"',
        'href="https://veilatarot.com/quick-love-reading/" />':
            'href="https://veilatarot.com/career/reading/" />',
        'content="https://veilatarot.com/quick-love-reading/" />':
            'content="https://veilatarot.com/career/reading/" />',
    }
    # hreflang th should point to the th career app
    html = html.replace(
        '<link rel="alternate" hreflang="th" href="https://veilatarot.com/career/reading/" />',
        '<link rel="alternate" hreflang="th" href="https://veilatarot.com/th/career/reading/" />')
    for a, b in repl.items():
        html = html.replace(a, b)
    # fix: the hreflang replacement above runs before quick-love-reading->career swap,
    # so re-apply th-specific after generic swap
    html = html.replace(
        '<link rel="alternate" hreflang="th" href="https://veilatarot.com/career/reading/" />\n<link rel="alternate" hreflang="x-default"',
        '<link rel="alternate" hreflang="th" href="https://veilatarot.com/th/career/reading/" />\n<link rel="alternate" hreflang="x-default"')

    # ---- prominent visible copy (EN + TH) ----
    copy = {
        ">Quick Love Reading</h1>": ">Quick Career Reading</h1>",
        "Quick Love · 3 Cards": "Quick Career · 3 Cards",
        "ไพ่ความรัก · 3 ใบ": "ไพ่การงาน · 3 ใบ",
        # hero headline
        # NOTE: keep this apostrophe-free — it lands in a single-quoted JS dict
        # value (introH1), so a "you're" would break the whole inlined script.
        "Three cards for the <em>space between</em> you.":
            "Three cards for the <em>question on your mind</em>.",
        "ไพ่สามใบ สำหรับ<em>พื้นที่ระหว่าง</em>คุณกับเขา":
            "ไพ่สามใบ สำหรับ<em>คำถามที่คุณกำลังครุ่นคิด</em>",
        # intro blurb (static) + lede EN/TH
        "A 3-card tarot reflection: their energy, your energy, and the space between you. For reflection, not prediction.":
            "A 3-card tarot reflection on where you stand, what's shifting, and where it leads. For reflection, not prediction.",
        "For when a question of the heart needs more than a moment but less than an hour. Take a breath. Hold the question. The cards reflect — they don't predict.":
            "For when a question about work, money, or your path needs more than a moment but less than an hour. Take a breath. Hold the question. The cards reflect — they don't predict.",
        "สำหรับคำถามของหัวใจที่ต้องการมากกว่าหนึ่งช่วงเวลา แต่ไม่ใช่ทั้งชั่วโมง สูดหายใจ ตั้งคำถามไว้ในใจ ไพ่สะท้อน — ไม่ใช่พยากรณ์":
            "สำหรับคำถามเรื่องงาน เงิน หรือเส้นทางของคุณ ที่ต้องการมากกว่าหนึ่งช่วงเวลา แต่ไม่ใช่ทั้งชั่วโมง สูดหายใจ ตั้งคำถามไว้ในใจ ไพ่สะท้อน — ไม่ใช่พยากรณ์",
        # readout lede EN/TH
        "Read each card in turn — what you bring, what they bring, what sits in the space between. These are reflections, not predictions.":
            "Read each card in turn — where you stand, what shifts it, where this is heading. These are reflections, not predictions.",
        "อ่านไพ่ทีละใบ — สิ่งที่คุณนำมา สิ่งที่อีกฝ่ายนำมา และสิ่งที่อยู่ในพื้นที่ระหว่างกัน นี่คือการสะท้อน ไม่ใช่การพยากรณ์":
            "อ่านไพ่ทีละใบ — จุดที่คุณยืนอยู่ สิ่งที่ทำให้มันขยับ และทิศทางที่สิ่งนี้กำลังไป นี่คือการสะท้อน ไม่ใช่การพยากรณ์",
        # nav guide link label + href
        "About love readings": "About career readings",
        "เกี่ยวกับไพ่ความรัก": "เกี่ยวกับไพ่การงาน",
        'href="/tarot-love-readings/" data-href-en="/tarot-love-readings/" data-href-th="/th/tarot-love-readings/"':
            'href="/career/" data-href-en="/career/" data-href-th="/th/career/"',
        "Explore more love readings": "Explore more career questions",
        "บทอ่านความรักอื่นๆ": "บทอ่านการงานอื่นๆ",
        "Reveal my love reading": "Reveal my career reading",
        # the 4 "explore" links (href + EN + TH labels)
        '<li><a href="/love-readings/does-he-miss-me/" data-i18n="lcQ1">Does he miss me?</a></li>':
            '<li><a href="/career/reading/?q=should-i-take-this-job" data-i18n="lcQ1">Should I take this job?</a></li>',
        '<li><a href="/love-readings/why-did-they-pull-away/" data-i18n="lcQ2">Why did they pull away?</a></li>':
            '<li><a href="/career/reading/?q=should-i-quit" data-i18n="lcQ2">Should I quit my job?</a></li>',
        '<li><a href="/love-readings/should-i-reach-out/" data-i18n="lcQ3">Should I reach out?</a></li>':
            '<li><a href="/career/reading/?q=am-i-underpaid" data-i18n="lcQ3">Am I underpaid?</a></li>',
        '<li><a href="/love-readings/what-changed-between-us/" data-i18n="lcQ4">What changed between us?</a></li>':
            '<li><a href="/career/reading/?q=what-is-my-calling" data-i18n="lcQ4">What is my real calling?</a></li>',
        "lcQ1: 'Does he miss me?'": "lcQ1: 'Should I take this job?'",
        "lcQ2: 'Why did they pull away?'": "lcQ2: 'Should I quit my job?'",
        "lcQ3: 'Should I reach out?'": "lcQ3: 'Am I underpaid?'",
        "lcQ4: 'What changed between us?'": "lcQ4: 'What is my real calling?'",
        "lcQ1: 'เขาคิดถึงเราไหม'": "lcQ1: 'ฉันควรรับงานนี้ไหม'",
        "lcQ2: 'ทำไมเขาถึงห่างไป'": "lcQ2: 'ฉันควรลาออกไหม'",
        "lcQ3: 'ควรทักไปไหม'": "lcQ3: 'ฉันถูกจ่ายน้อยไปไหม'",
        "lcQ4: 'อะไรเปลี่ยนไประหว่างเรา'": "lcQ4: 'เส้นทางที่ใช่ของฉันคืออะไร'",
        # meta description (head)
        "A 3-card tarot reading for questions of the heart. Their energy, your energy, the space between. For reflection, not prediction. Bilingual EN/TH.":
            "A 3-card tarot reading for questions of work, money, and your path. Where you stand, what shifts it, where it leads. For reflection, not prediction. Bilingual EN/TH.",
        "A 3-card tarot reading for questions of the heart. Their energy, your energy, the space between. For reflection, not prediction.":
            "A 3-card tarot reading for questions of work, money, and your path. For reflection, not prediction.",
        "A 3-card tarot reading for questions of the heart. For reflection, not prediction.":
            "A 3-card tarot reading for questions of work, money, and your path. For reflection, not prediction.",
    }
    for a, b in copy.items():
        html = html.replace(a, b)

    # ------------------------------------------------------------------
    # De-love the inherited spread machinery. The love app lets the user
    # pick a "spread mode" (connection / emotional-arc / clarity /
    # reconnection) that defines the 3 position labels. Career questions
    # each carry their OWN fixed 3 positions in their dataset, so there is
    # no lens to choose — the question IS the spread. We remove the picker
    # and drive every visible label from the selected question's dataset.
    # ------------------------------------------------------------------
    structural = {
        # 1) Remove the spread-mode picker UI from the selection screen.
        '''        <section class="mode-picker" aria-labelledby="mp-label">
          <div class="mp-label" id="mp-label" data-i18n="spreadLabel">Spread</div>
          <div class="mp-chips" id="mode-chips" role="group" aria-label="Spread mode">
            <!-- chips injected by JS so labels follow SPREAD_MODES + lang -->
          </div>
        </section>''':
        '''        <!-- spread-mode picker removed for career: each question carries its own fixed 3 positions -->''',

        # 2) currentPositions(): prefer the selected question's dataset
        #    positions so the selection "Next:" label, the draw mapping, and
        #    the share subtitle are all question-true. Falls back to the
        #    generic spread only in the brief window before a dataset loads.
        '''function currentPositions() {
  const m = SPREAD_MODES[selectedMode] || SPREAD_MODES[DEFAULT_MODE];
  return m.positions;
}''':
        '''function currentPositions() {
  // Career: each question defines its own fixed 3 positions in its dataset.
  const ds = (typeof selectedQuestionKey !== 'undefined' && selectedQuestionKey && __datasetCache[selectedQuestionKey]) || null;
  if (ds && ds.spread && Array.isArray(ds.spread.positions) && ds.spread.positions.length === 3) {
    return ds.spread.positions.map(function (p, i) {
      return {
        n: i + 1,
        key: p.key,
        cc: ['self', 'environment', 'present'][i] || 'present',
        short: { en: (p.label && p.label.en) || '', th: (p.label && (p.label.th || p.label.en)) || '' },
        long: null
      };
    });
  }
  const m = SPREAD_MODES[selectedMode] || SPREAD_MODES[DEFAULT_MODE];
  return m.positions;
}''',

        # 3) When a dataset finishes loading while the selection screen is
        #    open, refresh the "Next:" label so it reflects the real position.
        '''      __datasetCache[key] = normalized;
      return normalized;''':
        '''      __datasetCache[key] = normalized;
      try {
        var __sel = document.getElementById('selection');
        if (key === selectedQuestionKey && __sel && !__sel.classList.contains('is-hidden') && typeof updateSelectionUI === 'function') updateSelectionUI();
      } catch (e) {}
      return normalized;''',

        # 4) Share path still pointed at the love URL + filename.
        "location.origin + '/quick-love-reading/'":
            "location.origin + '/career/reading/'",
        "'veila-love-reading'": "'veila-career-reading'",

        # 5) "Spreads to try" listed LOVE-reading links — repoint to career
        #    questions (HTML hrefs + fallback text).
        '<li><a href="/quick-love-reading/emotional-arc/" data-i18n="lcSpreadArc">Emotional Arc — what shaped this, what is unfolding, what is changing</a></li>':
            '<li><a href="/career/reading/?q=will-money-improve" data-i18n="lcSpreadArc">Will my finances improve?</a></li>',
        '<li><a href="/quick-love-reading/clarity/" data-i18n="lcSpreadClarity">Clarity — what you know, what you avoid, what needs honesty</a></li>':
            '<li><a href="/career/reading/?q=why-is-work-stuck" data-i18n="lcSpreadClarity">Why does my work feel stuck?</a></li>',
        '<li><a href="/quick-love-reading/reconnection/" data-i18n="lcSpreadRecon">Reconnection — what still exists, what creates distance, what invites reconnection</a></li>':
            '<li><a href="/career/reading/?q=should-i-start-my-own-thing" data-i18n="lcSpreadRecon">Should I start my own business?</a></li>',

        # 6) i18n dict (EN) — posTrail + the repurposed "Spreads to try".
        "posTrail: 'Your energy <span>·</span> Their energy <span>·</span> Between you'":
            "posTrail: 'Three cards, read in the order you turn them.'",
        "lcSpreadsH3: 'Spreads to try'": "lcSpreadsH3: 'More questions'",
        "lcSpreadArc: 'Emotional Arc — what shaped this, what is unfolding, what is changing'":
            "lcSpreadArc: 'Will my finances improve?'",
        "lcSpreadClarity: 'Clarity — what you know, what you avoid, what needs honesty'":
            "lcSpreadClarity: 'Why does my work feel stuck?'",
        "lcSpreadRecon: 'Reconnection — what still exists, what creates distance, what invites reconnection'":
            "lcSpreadRecon: 'Should I start my own business?'",

        # 7) i18n dict (TH) — same.
        "posTrail: 'พลังของคุณ <span>·</span> พลังของเขา <span>·</span> สิ่งที่อยู่ระหว่างกัน'":
            "posTrail: 'ไพ่สามใบ อ่านทีละใบตามลำดับที่คุณเปิด'",
        "lcSpreadsH3: 'บทอ่านที่น่าลอง'": "lcSpreadsH3: 'คำถามเพิ่มเติม'",
        "lcSpreadArc: 'ห้วงอารมณ์ — สิ่งที่ก่อตัวขึ้น สิ่งที่กำลังเกิด สิ่งที่กำลังเปลี่ยน'":
            "lcSpreadArc: 'การเงินของฉันจะดีขึ้นไหม'",
        "lcSpreadClarity: 'ความชัดเจน — สิ่งที่คุณรู้ สิ่งที่คุณหลีกเลี่ยง สิ่งที่ต้องการความซื่อตรง'":
            "lcSpreadClarity: 'ทำไมงานถึงรู้สึกหยุดนิ่ง'",
        "lcSpreadRecon: 'เชื่อมโยงใหม่ — สิ่งที่ยังคงอยู่ สิ่งที่สร้างระยะ สิ่งที่เชื้อเชิญให้กลับมา'":
            "lcSpreadRecon: 'ฉันควรเริ่มธุรกิจของตัวเองไหม'",

        # 8) JSON-LD canonical url (head).
        '"url": "https://veilatarot.com/quick-love-reading/",':
            '"url": "https://veilatarot.com/career/reading/",',

        # 9) posTrail inline default (overwritten by apply(), but keep it clean
        #    for first paint + no-JS).
        '<p class="pos-trail" data-i18n-html="posTrail">Your energy <span>·</span> Their energy <span>·</span> Between you</p>':
            '<p class="pos-trail" data-i18n-html="posTrail">Three cards, read in the order you turn them.</p>',

        # 10) CONTINUE-REFLECTING block: career always runs in the default
        #     'connection' mode, so only that rec entry is ever shown. Repoint
        #     it from love pages to career questions (all guaranteed to exist).
        '''  connection: {
    intent: { slug: 'are-they-confused-about-me', url: '/love-readings/are-they-confused-about-me/' },
    spread: { slug: 'emotional-arc', url: '/quick-love-reading/emotional-arc/' },
    guide:  { slug: 'tarot-spreads-for-relationships', url: '/guides/tarot-spreads-for-relationships/' }
  },''':
        '''  connection: {
    intent: { slug: 'is-this-career-right', url: '/career/reading/?q=is-this-career-right' },
    spread: { slug: 'change-careers', url: '/career/reading/?q=change-careers' },
    guide:  { slug: 'how-to-grow-here', url: '/career/reading/?q=how-to-grow-here' }
  },''',

        # 11) Continue-block kind labels + the 3 career slug entries (EN).
        "    kindIntent: 'A question to sit with', kindSpread: 'Another spread', kindGuide: 'A guide to read slowly',":
        '''    kindIntent: 'A question to sit with', kindSpread: 'Another question', kindGuide: 'A question to grow with',
    'is-this-career-right': { title: 'Is this career right for me?', blurb: 'When the role fits on paper but something in you keeps asking anyway.' },
    'change-careers': { title: 'Should I change careers?', blurb: 'For the pull toward a different path — and what staying or leaving each opens.' },
    'how-to-grow-here': { title: 'How do I grow in this role?', blurb: 'When you want to rise where you are, not leave — and where the next step actually is.' },''',

        # 12) Same (TH).
        "    kindIntent: 'คำถามให้นั่งด้วย', kindSpread: 'บทอ่านอื่น', kindGuide: 'คู่มือให้อ่านช้าๆ',":
        '''    kindIntent: 'คำถามให้นั่งด้วย', kindSpread: 'อีกหนึ่งคำถาม', kindGuide: 'คำถามให้เติบโตไปด้วย',
    'is-this-career-right': { title: 'เส้นทางอาชีพนี้ใช่สำหรับฉันไหม', blurb: 'เมื่องานดูเข้าที่บนกระดาษ แต่มีบางอย่างในใจยังถามอยู่' },
    'change-careers': { title: 'ฉันควรเปลี่ยนสายอาชีพไหม', blurb: 'สำหรับแรงดึงไปสู่ทางใหม่ — และสิ่งที่การอยู่ต่อหรือไปเปิดให้แต่ละทาง' },
    'how-to-grow-here': { title: 'ฉันจะเติบโตในบทบาทนี้ได้อย่างไร', blurb: 'เมื่อคุณอยากก้าวขึ้นในที่ที่อยู่ ไม่ใช่จากไป — และก้าวต่อไปอยู่ตรงไหนจริงๆ' },''',

        # 13) Hide the love-authored ambient layers (Emotional Weather +
        #     Quiet Pause). Their copy banks are written for relationship
        #     readings; better absent than off-tone. Career banks = later task.
        '''function renderEmotionalWeather() {
  const panel  = document.getElementById('emotional-weather');
  const lineEl = document.getElementById('ew-line');
  if (!panel || !lineEl || !drawn.length) return;''':
        '''function renderEmotionalWeather() {
  const panel  = document.getElementById('emotional-weather');
  const lineEl = document.getElementById('ew-line');
  if (panel) { panel.hidden = true; } // career: love-authored weather lines disabled for now
  if (true) return;
  if (!panel || !lineEl || !drawn.length) return;''',

        '''function renderQuietPause() {
  const panel  = document.getElementById('quiet-pause');
  const lineEl = document.getElementById('qp-line');
  if (!panel || !lineEl || !drawn.length) return;''':
        '''function renderQuietPause() {
  const panel  = document.getElementById('quiet-pause');
  const lineEl = document.getElementById('qp-line');
  if (panel) { panel.hidden = true; } // career: love-authored pause lines disabled for now
  if (true) return;
  if (!panel || !lineEl || !drawn.length) return;''',

        # 14) Analytics provenance (cosmetic, keeps career events legible).
        "          source_page_type: 'quick_love_reading',":
            "          source_page_type: 'quick_career_reading',",
        "          source_slug: 'quick-love-reading',":
            "          source_slug: 'quick-career-reading',",
        "method: 'inline', source_page: '/quick-love-reading/' }":
            "method: 'inline', source_page: '/career/reading/' }",
    }
    missing = []
    for a, b in structural.items():
        if a not in html:
            missing.append(a[:60])
        else:
            html = html.replace(a, b)
    if missing:
        raise SystemExit("structural fixes did not match (love source drifted?):\n  - "
                         + "\n  - ".join(missing))

    os.makedirs(OUT_DIR, exist_ok=True)
    open(OUT, "w").write(html)
    print(f"OK wrote {OUT} ({len(html)} bytes); {len(KEYS)} dataset entries wired")

    # ------------------------------------------------------------------
    # Thai mirror /th/career/reading/ — same app, th-default. Surgical
    # head/brand/lang swaps only; hreflang en↔th pair stays reciprocal
    # (identical in both files). Visible copy toggles via the in-page i18n.
    # ------------------------------------------------------------------
    th = html
    th_repl = [
        ('<html lang="en">', '<html lang="th">'),
        ('<link rel="canonical" href="https://veilatarot.com/career/reading/" />',
         '<link rel="canonical" href="https://veilatarot.com/th/career/reading/" />'),
        ('<meta property="og:url" content="https://veilatarot.com/career/reading/" />',
         '<meta property="og:url" content="https://veilatarot.com/th/career/reading/" />'),
        ('<meta property="og:locale" content="en_US" />',
         '<meta property="og:locale" content="th_TH" />'),
        ('<meta property="og:locale:alternate" content="th_TH" />',
         '<meta property="og:locale:alternate" content="en_US" />'),
        ('<title>Quick Career Reading — A 3-Card Tarot Reflection | Veila</title>',
         '<title>ดูไพ่การงานแบบเร็ว — บทอ่านไพ่ทาโรต์ 3 ใบ | Veila</title>'),
        # og:title + twitter:title (identical string → both swapped)
        ('content="Quick Career Reading — A 3-Card Tarot Reflection | Veila"',
         'content="ดูไพ่การงานแบบเร็ว — บทอ่านไพ่ทาโรต์ 3 ใบ | Veila"'),
        # long meta description
        ('content="A 3-card tarot reading for questions of work, money, and your path. Where you stand, what shifts it, where it leads. For reflection, not prediction. Bilingual EN/TH."',
         'content="บทอ่านไพ่ทาโรต์ 3 ใบ สำหรับคำถามเรื่องงาน เงิน และเส้นทางของคุณ จุดที่คุณยืน สิ่งที่ทำให้มันขยับ และทิศที่มันไป เพื่อการใคร่ครวญ ไม่ใช่การทำนาย สองภาษา ไทย/อังกฤษ"'),
        # og:description + twitter:description (identical short string → both swapped)
        ('content="A 3-card tarot reading for questions of work, money, and your path. For reflection, not prediction."',
         'content="บทอ่านไพ่ทาโรต์ 3 ใบ สำหรับคำถามเรื่องงาน เงิน และเส้นทางของคุณ เพื่อการใคร่ครวญ ไม่ใช่การทำนาย"'),
        ('<a class="brand" href="/" id="brand-home"',
         '<a class="brand" href="/th/" id="brand-home"'),
        ("localStorage.getItem('veila-lang')) || 'en'",
         "localStorage.getItem('veila-lang')) || 'th'"),
        ("location.origin + '/career/reading/'",
         "location.origin + '/th/career/reading/'"),
    ]
    th_missing = []
    for a, b in th_repl:
        if a not in th:
            th_missing.append(a[:60])
        else:
            th = th.replace(a, b)
    if th_missing:
        raise SystemExit("th-mirror swaps did not match:\n  - " + "\n  - ".join(th_missing))
    TH_OUT_DIR = os.path.join(REPO, "th/career/reading")
    TH_OUT = os.path.join(TH_OUT_DIR, "index.html")
    os.makedirs(TH_OUT_DIR, exist_ok=True)
    open(TH_OUT, "w").write(th)
    print(f"OK wrote {TH_OUT} ({len(th)} bytes); th-default mirror")

if __name__ == "__main__":
    main()
