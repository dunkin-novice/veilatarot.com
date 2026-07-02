#!/usr/bin/env python3
"""Build the static SEO tree for veilatarot.com from cards.json.

Generates:
- /cards/<slug>/                 (78 EN card pages)
- /th/cards/<slug>/              (78 TH card pages)
- /major-arcana/                 + /th/...
- /minor-arcana/                 + /th/...
- /cups-tarot-meanings/          + /th/...
- /swords-tarot-meanings/        + /th/...
- /wands-tarot-meanings/         + /th/...
- /pentacles-tarot-meanings/     + /th/...
- /tarot-love-readings/          + /th/...
- /career-tarot-reading/         + /th/...
- /yes-no-tarot/                 + /th/...
- /sitemap.xml                   (every URL above + the 5 existing statics)

Card pages also receive a "Related cards" module + an "Explore related
readings" section. All pages include BreadcrumbList JSON-LD.

Re-run anytime cards.json changes:
    python3 scripts/build-cards.py
"""
import json
import re
import shutil
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DECK_PATH = ROOT / 'cards.json'
DECK = json.loads(DECK_PATH.read_text(encoding='utf-8'))

BUILD_DATE = '2026-06-17'
SCENARIO_MIGRATION_DATE = '2026-06-23'
CARD_CONTENT_UPDATE_DATE = '2026-07-02'  # FAQ expansion + schema cleanup (SEO/AEO audit)
LANGS = ('en', 'th')

def aeo_block(title_en, title_th, desc_en, desc_th, lang):
    """Bilingual Answer-First block for AI extractability."""
    is_th = (lang == 'th')
    label = 'Verdict Summary / บทสรุป' if is_th else 'Verdict Summary'
    return f'''  <!-- AEO: Answer-First Block (2026 Strategy) -->
  <section class="aeo-answer-block" style="border-left:2px solid var(--gold); padding:20px; margin:28px 0; background:rgba(184,153,104,0.03); border-radius:0 12px 12px 0; text-align:left;">
    <p style="font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:0.2em; color:var(--gold); margin-bottom:10px;">{escape(label)}</p>
    <p style="font-family:var(--serif); font-size:19px; line-height:1.5; color:var(--ivory); font-style:italic;">{escape(desc_en)}</p>
    <p style="font-family:var(--sans); font-size:16px; line-height:1.5; color:var(--ivory-dim); margin-top:10px;">{escape(desc_th)}</p>
  </section>'''

# NOTE (2026-07-02): the former medical_schema() / MedicalWebPage block was
# removed site-wide — tarot pages are not medical content, and the schema was
# flagged as abuse in the SEO/AEO audit. Do not reintroduce it.

# ---------------------------------------------------------------------------
# DATA STRUCTURES
# ---------------------------------------------------------------------------

POSITIONS = [
    {'n': 1,  'key': 'present',     'short_en': 'The Present',         'short_th': 'ปัจจุบัน'},
    {'n': 2,  'key': 'challenge',   'short_en': 'The Challenge',       'short_th': 'อุปสรรค'},
    {'n': 3,  'key': 'past',        'short_en': 'The Past',            'short_th': 'อดีต'},
    {'n': 4,  'key': 'future',      'short_en': 'The Future',          'short_th': 'อนาคต'},
    {'n': 5,  'key': 'above',       'short_en': 'Above · Conscious',   'short_th': 'เบื้องบน · จิตสำนึก'},
    {'n': 6,  'key': 'below',       'short_en': 'Below · Unconscious', 'short_th': 'เบื้องล่าง · จิตใต้สำนึก'},
    {'n': 7,  'key': 'self',        'short_en': 'Advice · Self',       'short_th': 'คำชี้แนะ · ตัวคุณ'},
    {'n': 8,  'key': 'environment', 'short_en': 'External Influences', 'short_th': 'ปัจจัยภายนอก'},
    {'n': 9,  'key': 'hopes_fears', 'short_en': 'Hopes & Fears',       'short_th': 'ความหวังและความกลัว'},
    {'n': 10, 'key': 'outcome',     'short_en': 'Outcome',             'short_th': 'ผลลัพธ์'},
]
ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']

SUIT_EN = {'wands': 'Wands', 'cups': 'Cups', 'swords': 'Swords', 'pentacles': 'Pentacles'}
SUIT_TH = {'wands': 'ไม้เท้า', 'cups': 'ถ้วย', 'swords': 'ดาบ', 'pentacles': 'เหรียญ'}

SUIT_HUB_SLUG = {
    'wands': 'wands-tarot-meanings',
    'cups':  'cups-tarot-meanings',
    'swords': 'swords-tarot-meanings',
    'pentacles': 'pentacles-tarot-meanings',
}

# Curated card lists for topical hubs (id is the cards.json id field).
TOPICAL_CARD_IDS = {
    'love': [
        '07-the-lovers', '04-the-empress', '03-the-high-priestess',
        '37-ace-of-cups', '38-two-of-cups', '39-three-of-cups',
        '42-six-of-cups', '46-ten-of-cups',
        '48-knight-of-cups', '49-queen-of-cups',
        '26-four-of-wands',
    ],
    'career': [
        '02-the-magician', '05-the-emperor', '08-the-chariot',
        '11-wheel-of-fortune',
        '65-ace-of-pentacles', '67-three-of-pentacles', '68-four-of-pentacles',
        '72-eight-of-pentacles', '74-ten-of-pentacles',
        '75-page-of-pentacles', '76-knight-of-pentacles', '78-king-of-pentacles',
    ],
    'yes': [
        '20-the-sun', '18-the-star', '22-the-world',
        '04-the-empress', '03-the-high-priestess',
        '23-ace-of-wands', '28-six-of-wands',
        '37-ace-of-cups', '39-three-of-cups', '46-ten-of-cups',
    ],
    'no': [
        '17-the-tower', '14-death', '16-the-devil',
        '53-three-of-swords', '54-four-of-swords', '60-ten-of-swords',
        '41-five-of-cups', '69-five-of-pentacles',
    ],
}

STATIC_URLS = [
    ('/',                       '1.0', 'monthly'),
    ('/celtic-cross-tarot/',    '0.8', 'monthly'),
    ('/th/celtic-cross-tarot/', '0.7', 'monthly'),
    ('/daily-tarot-card/',      '0.8', 'daily'),
    ('/th/daily-tarot-card/',   '0.7', 'daily'),
    ('/all-tarot-pages/',       '0.5', 'monthly'),
    ('/th/all-tarot-pages/',    '0.4', 'monthly'),
    ('/th/about/',              '0.6', 'monthly'),
    ('/th/faq/',                '0.6', 'monthly'),
]

# ---------------------------------------------------------------------------
# TH EMOTIONAL SCENARIO PAGES
# ---------------------------------------------------------------------------
# 10 curated Thai emotional scenarios. Each maps to a 3-card spread,
# an editorial framing, and 5-6 relevant card slugs (linking targets).
# Hand-curated — not generated. These should not feel like AI listicles.

TH_SCENARIOS = [
    {
        'slug': 'what-does-he-think-about-me',
        'legacy_slug': 'kao-kid-kab-rao',
        'category': 'love',
        'title': 'เขาคิดยังไงกับเรา',
        'eyebrow': 'สำหรับเรื่องของหัวใจ',
        'lede': 'เมื่อเขาเงียบ ความเงียบนั้นอาจสะท้อนสิ่งที่อยู่ในใจเขา หรืออาจสะท้อนความกลัวในใจเราเอง ไพ่ช่วยเราแยกสองอย่างออกจากกัน',
        'intro_q': 'ก่อนเปิดไพ่ ตั้งคำถามให้เฉพาะเจาะจง ไม่ใช่ "เขารักเราไหม" แต่เป็น "อะไรอยู่ระหว่างเรากับเขาตอนนี้ที่ฉันยังไม่ได้พูด" ไพ่ที่ออกมาจะตอบคำถามที่สองได้คมกว่าคำถามแรก',
        'spread': [
            ('เขามองเราอย่างไร', 'ภาพที่เขาถือไว้ในใจเกี่ยวกับคุณ — ไม่ใช่สิ่งที่เขาพูดออกมา'),
            ('เรามองเขาอย่างไร', 'ภาพที่คุณถือไว้ในใจเกี่ยวกับเขา — ซึ่งบางทีไม่ตรงกับเขาในความจริง'),
            ('ระยะห่างระหว่างเรา', 'ช่องว่างที่ต้องเรียกชื่อ ก่อนจะข้ามไปหรือถอยกลับ'),
        ],
        'framework': 'สามใบนี้พูดคุยกันได้สามทาง ถ้าไพ่ของเขาและของคุณคล้ายกัน แปลว่าคุณสองคนกำลังเดินบนถนนเดียวกัน ถ้าต่างกันมาก แปลว่าคุณกำลังเล่าเรื่องคนละเรื่อง และใบที่สามจะบอกว่าช่องว่างนั้นเล็กหรือใหญ่ ปลายเปิดหรือปิดแล้ว ใบที่สามคือใบสำคัญที่สุด — เพราะมันเป็นใบเดียวที่คุณเปลี่ยนแปลงได้',
        'cards': ['the-lovers', 'two-of-cups', 'knight-of-cups', 'page-of-cups', 'the-high-priestess', 'the-moon'],
    },
    {
        'slug': 'will-he-come-back',
        'legacy_slug': 'kao-ja-glab-ma',
        'category': 'love',
        'title': 'เขาจะกลับมาไหม',
        'eyebrow': 'สำหรับการรอ',
        'lede': 'คำถามนี้บอกมากกว่าคำตอบ การที่คุณยังถามอยู่ — บ่อยครั้งคือไพ่ใบแรกที่คุณเปิดให้ตัวเองโดยไม่รู้ตัว',
        'intro_q': 'แทนที่จะถามว่า "เขาจะกลับมาไหม" ลองถามว่า "ถ้าเขากลับมา ฉันจะกลับเป็นคนเดิมไหม" คำถามที่สองมักจะตอบทั้งสองคำถามพร้อมกัน',
        'spread': [
            ('ความรู้สึกของเขาตอนนี้', 'สิ่งที่เขาแบกอยู่จริงๆ ไม่ใช่สิ่งที่เขาเลือกจะแสดง'),
            ('สิ่งที่ขวางการกลับมา', 'อุปสรรคที่อยู่ระหว่างทาง — ของเขา ของคุณ หรือของเงื่อนเวลา'),
            ('ทิศทางที่เป็นไปได้', 'แนวโน้มถ้าทุกอย่างคงดำเนินเช่นเดิม'),
        ],
        'framework': 'ไพ่ใบที่หนึ่งบอกอุณหภูมิในใจเขา ไม่ใช่คำสัญญา ใบที่สองคือสิ่งที่คุณควรสังเกตที่สุด เพราะถ้าอุปสรรคนั้นมาจากคุณ — คุณคือคนที่ปลดล็อกได้ ใบที่สามเป็นแนวโน้ม ไม่ใช่คำพยากรณ์ ถ้าใบที่สามดูปิด ไพ่ไม่ได้บอกว่าทุกอย่างจบ — มันบอกว่าถ้าคุณไม่เปลี่ยนอะไรเลย ทุกอย่างจะอยู่อย่างนี้',
        'cards': ['six-of-cups', 'wheel-of-fortune', 'eight-of-cups', 'the-hanged-man', 'judgement', 'the-moon'],
    },
    {
        'slug': 'is-he-sincere',
        'legacy_slug': 'khon-kuy-jing-jai',
        'category': 'love',
        'title': 'คนคุยจริงใจไหม',
        'eyebrow': 'สำหรับช่วงต้นของความสัมพันธ์',
        'lede': 'ในช่วงคุย คำที่เขาพูดมีน้ำหนักน้อยกว่าจังหวะที่เขาตอบ ความสม่ำเสมอที่เขาให้ และพื้นที่ที่เขาเปิดให้คุณถาม ไพ่ช่วยอ่านจังหวะ ไม่ใช่คำ',
        'intro_q': 'ก่อนเปิดไพ่ ลองนึกถึงสามครั้งล่าสุดที่คุณรู้สึก "บางอย่างไม่ตรง" แล้วถามไพ่ว่า "สามครั้งนั้นกำลังบอกอะไรฉัน"',
        'spread': [
            ('ความตั้งใจของเขา', 'สิ่งที่เขามาหาคุณเพื่อ — รู้ตัวหรือไม่ก็ตาม'),
            ('ความจริงเบื้องหลัง', 'สิ่งที่เขาไม่ได้พูดออกมา แต่กำลังเล่าด้วยการกระทำ'),
            ('สิ่งที่คุณต้องระวัง', 'จุดที่คุณกำลังเชื่อในสิ่งที่อยากเชื่อ มากกว่าสิ่งที่เห็น'),
        ],
        'framework': 'ไพ่ในคำถามนี้มักพูดถึงสองอย่างพร้อมกัน — เขา และคุณ ใบแรกคือเขา ใบที่สองคือสิ่งที่เขาส่งสัญญาณโดยไม่รู้ตัว ใบที่สามคือกระจกที่หันมาทางคุณ — ถามคุณว่าคุณกำลังอ่านสัญญาณนั้นตามที่มันเป็น หรือตามที่คุณหวังจะเป็น',
        'cards': ['seven-of-swords', 'the-moon', 'two-of-pentacles', 'knight-of-cups', 'page-of-swords', 'the-devil'],
    },
    {
        'slug': 'should-this-relationship-continue',
        'legacy_slug': 'khwam-samphan-pai-tor',
        'category': 'love',
        'title': 'ความสัมพันธ์นี้ควรไปต่อไหม',
        'eyebrow': 'สำหรับจุดเปลี่ยน',
        'lede': 'คำถามนี้มักไม่ใช่คำถาม — มันคือคำตอบที่กำลังหาเหตุผลให้ตัวเอง ไพ่ช่วยให้คำตอบนั้นชัดเจนพอจะยอมรับ',
        'intro_q': 'ลองถามตัวเองสั้นๆ ก่อน: "ถ้าฉันรู้แน่ๆ ว่าจะไม่มีอะไรเปลี่ยน ฉันจะยังอยากอยู่ในนี้ไหม" ไพ่จะตอบคำถามที่ใหญ่กว่านั้นได้ ก็ต่อเมื่อคุณตอบคำถามเล็กก่อน',
        'spread': [
            ('สถานะของเราตอนนี้', 'สภาพจริงของความสัมพันธ์ — เลิกแต่งหน้าให้มัน'),
            ('ความเป็นไปได้ที่จะเติบโต', 'สิ่งที่ความสัมพันธ์นี้ยังเก็บไว้ให้คุณ ถ้าทั้งสองคนเลือกที่จะอยู่'),
            ('สิ่งที่จะต้องปล่อย', 'ราคาของการไปต่อ — สิ่งที่หนึ่งหรือทั้งคู่ต้องวางลง'),
        ],
        'framework': 'สามใบนี้ทำงานเป็นกระจกสามบาน ถ้าคุณรู้สึกว่าไพ่แต่ละใบไม่ตรงกับใจ — มันอาจตรงกว่าที่คุณยอมรับ ไพ่ไม่ตัดสิน "ควร" หรือ "ไม่ควร" แต่มันเรียกชื่อสิ่งที่อยู่บนโต๊ะ การตัดสินใจยังคงเป็นของคุณเสมอ',
        'cards': ['the-lovers', 'two-of-cups', 'three-of-swords', 'the-tower', 'death', 'the-hanged-man'],
    },
    {
        'slug': 'does-he-still-miss-me',
        'legacy_slug': 'kao-yang-kid-thueng-rao',
        'category': 'love',
        'title': 'เขายังคิดถึงเราไหม',
        'eyebrow': 'สำหรับใจที่ยังค้าง',
        'lede': 'คำถามนี้ฟังดูเกี่ยวกับเขา แต่จริงๆ มันถามว่า "ฉันยังคิดถึงเขาอยู่ และฉันจะทำยังไงกับสิ่งนั้น" ไพ่ตอบทั้งสองคำถามได้',
        'intro_q': 'ก่อนเปิดไพ่ สังเกตว่าคำถาม "เขายังคิดถึงเราไหม" เกิดขึ้นบ่อยแค่ไหนในสัปดาห์ที่ผ่านมา ความถี่นั้นคือใบไพ่ใบแรกที่คุณเปิดให้ตัวเอง',
        'spread': [
            ('ความทรงจำของเขา', 'ที่ที่คุณยังอยู่ในความคิดของเขา หรือที่ที่คุณจางไปแล้ว'),
            ('ปัจจุบันของเขา', 'สิ่งที่เขากำลังเดินอยู่ — ที่อาจเปิดหรือปิดประตูสู่อดีต'),
            ('ช่องทางที่เปิดอยู่', 'สิ่งที่ยังเป็นไปได้ระหว่างคุณกับเขา ถ้ามี'),
        ],
        'framework': 'ไพ่ในคำถามนี้มักบอกว่า "คิดถึง" กับ "อยากกลับมา" เป็นคนละเรื่อง คนเราคิดถึงคนหลายคนพร้อมกันได้ การคิดถึงไม่ใช่คำตอบ เป็นแค่ข้อมูล ไพ่ใบที่สามคือสิ่งที่สำคัญที่สุด — เพราะมันบอกคุณว่าควรเปิดประตูทิ้งไว้ หรือควรเดินไปจากมันได้แล้ว',
        'cards': ['six-of-cups', 'the-hanged-man', 'four-of-cups', 'eight-of-cups', 'the-moon', 'three-of-cups'],
    },
    {
        'slug': 'should-i-reach-out',
        'legacy_slug': 'rao-thak-kao-mai',
        'category': 'love',
        'title': 'เราควรทักเขาไหม',
        'eyebrow': 'สำหรับการตัดสินใจส่งข้อความ',
        'lede': 'คำถามนี้ดูเล็ก แต่ใหญ่กว่าที่มันบอก ทักหรือไม่ทักไม่ใช่เรื่องของข้อความ มันเป็นเรื่องของเจตนา และไพ่ตอบเรื่องเจตนาได้ดีมาก',
        'intro_q': 'ลองถามตัวเองก่อน: "ฉันอยากทักเขาเพื่ออะไร" ถ้าคำตอบคือ "เพื่อให้เขารู้สึกบางอย่าง" ไพ่จะออกแบบหนึ่ง ถ้าคำตอบคือ "เพื่อให้ใจตัวเองรู้สึกบางอย่าง" ไพ่จะออกแบบที่ต่างกัน',
        'spread': [
            ('เจตนาที่แท้จริงของคุณ', 'สิ่งที่อยู่ใต้ความอยากส่งข้อความ'),
            ('สิ่งที่เขาจะรู้สึก', 'การตอบรับที่เป็นไปได้ — ไม่ใช่คำที่เขาจะส่งกลับ แต่ความรู้สึกที่ขึ้นในใจเขา'),
            ('สิ่งที่จะเกิดขึ้นถ้าคุณทำ', 'ผลลัพธ์ในระยะสัปดาห์ ไม่ใช่ระยะปีหน้า'),
        ],
        'framework': 'ใบแรกคือใบสำคัญที่สุด เพราะมันบอกว่าการกระทำนี้ดูแลคุณ หรือกำลังหนีบางอย่างในตัวคุณ ใบที่สองพูดถึงเขาในวันที่เขาเปิดข้อความ ใบที่สามคือผลพลอย ถ้าใบแรกแย่ ใบที่สองและสามจะดูดีแค่ไหนก็ไม่สำคัญ',
        'cards': ['the-magician', 'the-fool', 'two-of-pentacles', 'eight-of-cups', 'the-hermit', 'page-of-cups'],
    },
    {
        'slug': 'should-i-wait-or-let-go',
        'legacy_slug': 'ror-rue-por',
        'category': 'love',
        'title': 'ควรรอหรือควรพอ',
        'eyebrow': 'สำหรับใจที่ยังไม่ตัดสินใจ',
        'lede': 'คำถามนี้มีสองคำตอบที่ถูกทั้งคู่ การรออาจเป็นความรัก หรืออาจเป็นความกลัวที่ไม่ยอมเปลี่ยนชื่อ ไพ่ช่วยแยกสองอย่างนี้',
        'intro_q': 'ลองสมมติว่าคำตอบคือ "ควรพอ" คุณจะรู้สึกยังไง โล่งหรือร้าว ความรู้สึกที่ขึ้นมาก่อนคือคำตอบที่ซื่อสัตย์ที่สุดของคุณ ไพ่จะมายืนยันหรือสะท้อนเหตุผลให้',
        'spread': [
            ('สิ่งที่ยังเหลืออยู่', 'คุณค่าที่ยังมีในการรอ — ถ้ามี'),
            ('ราคาของการรอ', 'สิ่งที่คุณกำลังเสียไปทุกวันที่เลือกรอ'),
            ('สิ่งที่เปิดถ้าคุณพอ', 'พื้นที่ที่จะเกิดขึ้นในใจ ในเวลา และในชีวิตคุณ ถ้าคุณวางลง'),
        ],
        'framework': 'คำถาม "รอหรือพอ" บ่อยครั้งไม่ใช่คำถามสองทางเลือก แต่เป็นคำถามว่า "ฉันยังเหลือพลังพอที่จะรออีกเท่าไหร่" ถ้าใบแรกดูเบาบาง และใบที่สองหนัก แสดงว่าคุณรู้คำตอบอยู่แล้ว ไพ่แค่ช่วยให้คุณมองมันได้โดยไม่กลัว',
        'cards': ['the-hanged-man', 'eight-of-cups', 'the-tower', 'justice', 'four-of-cups', 'two-of-swords'],
    },
    {
        'slug': 'what-is-this-love-teaching-me',
        'legacy_slug': 'rak-son-arai',
        'category': 'love',
        'title': 'รักครั้งนี้สอนอะไรเรา',
        'eyebrow': 'สำหรับการมองย้อนหลัง',
        'lede': 'หลังความสัมพันธ์จบ ไพ่ไม่ตอบว่าใครผิด แต่มันช่วยให้คุณเห็นว่าคุณเป็นคนแบบไหนตอนอยู่ในความสัมพันธ์นั้น และคุณกำลังกลายเป็นคนแบบไหนหลังจากมัน',
        'intro_q': 'ก่อนเปิดไพ่ ลองถามตัวเอง: "ถ้าฉันรู้ตั้งแต่วันแรกว่ามันจะจบแบบนี้ — ฉันจะยังเข้าไปไหม" คำตอบของคุณจะบอกว่าคุณกำลังมองอดีตด้วยมุมไหน',
        'spread': [
            ('บทเรียนเรื่องตัวคุณ', 'สิ่งที่ความสัมพันธ์นี้สอนคุณเกี่ยวกับตัวเอง — ที่คนภายนอกสอนไม่ได้'),
            ('บทเรียนเรื่องการรัก', 'รูปแบบการรักที่คุณนำเข้ามา และที่คุณเรียนรู้ใหม่'),
            ('สิ่งที่ติดตัวคุณไป', 'พลังหรือบาดแผลที่จะกลายเป็นส่วนหนึ่งของคุณในรักครั้งหน้า'),
        ],
        'framework': 'ใบที่สำคัญที่สุดในผังนี้คือใบที่สาม เพราะมันบอกว่าคุณจะเข้าสู่ความสัมพันธ์ครั้งต่อไปด้วยตัวเองแบบไหน บาดแผลที่ไม่ได้เรียกชื่อจะกลายเป็นพฤติกรรม — บาดแผลที่เรียกชื่อแล้วจะกลายเป็นเข็มทิศ',
        'cards': ['the-hermit', 'strength', 'judgement', 'the-star', 'death', 'temperance'],
    },
    {
        'slug': 'is-this-job-right-for-me',
        'legacy_slug': 'ngan-nee-chai-mai',
        'category': 'career',
        'title': 'งานนี้ใช่ทางของเราไหม',
        'eyebrow': 'สำหรับการงานและอาชีพ',
        'lede': 'งานที่ใช่ไม่จำเป็นต้องเป็นงานที่สนุกทุกวัน แต่ต้องเป็นงานที่คุณรู้สึกว่าตัวเองเติบโตช้าๆ และมันไม่กินคุณกลับ ไพ่ช่วยอ่านสองความรู้สึกนี้',
        'intro_q': 'ก่อนเปิดไพ่ ลองถามตัวเอง: "ถ้าฉันลาออกพรุ่งนี้และไม่บอกใคร ฉันจะคิดถึงอะไรของงานนี้บ้าง" คำตอบนั้นคือไพ่ใบเงาที่ออกมาก่อนคุณเปิดจริง',
        'spread': [
            ('ตัวคุณในงานนี้', 'สภาพของคุณตอนนี้ในบริบทของงาน — ไม่ใช่ภาพที่คุณโพสต์ออกไป'),
            ('สิ่งที่งานนี้ขอจากคุณ', 'ราคาที่งานนี้กำลังเก็บ — เวลา พลัง ความเป็นคุณ'),
            ('ทิศทางในระยะยาว', 'แนวโน้มของความสัมพันธ์ระหว่างคุณกับงานในอีกหนึ่งถึงสามปี'),
        ],
        'framework': 'งานที่ใช่ในระยะยาวมักให้ในด้านที่งานที่ดูสนุกในระยะสั้นให้ไม่ได้ — มันให้ฝีมือ ให้คนรอบตัวที่มีคุณภาพ ให้พลังกลับเย็นๆ ใบที่สามจะบอกว่างานนี้อยู่ในประเภทไหน ถ้าใบที่สองหนักกว่าใบที่สามเสมอ คุณอาจกำลังจ่ายแพงกว่าที่ได้รับ',
        'cards': ['the-hermit', 'eight-of-pentacles', 'three-of-pentacles', 'knight-of-pentacles', 'wheel-of-fortune', 'the-emperor'],
    },
    {
        'slug': 'should-i-change-jobs',
        'legacy_slug': 'plian-ngan-mai',
        'category': 'career',
        'title': 'ควรเปลี่ยนงานไหม',
        'eyebrow': 'สำหรับจุดเปลี่ยนในอาชีพ',
        'lede': 'การเปลี่ยนงานไม่ใช่การหนี แต่ก็ไม่ใช่การก้าวเสมอไป ไพ่ช่วยแยกสองอย่างนี้ออกจากกัน เพราะมันสำคัญมากในระยะห้าปีข้างหน้า',
        'intro_q': 'ลองถามตัวเอง: "ฉันอยากเปลี่ยนงาน เพราะอยากไปสู่อะไร หรือเพราะอยากหนีจากอะไร" คำถามนี้ไม่ได้บอกว่าทางไหนถูก แต่บอกว่าคุณควรใช้ไพ่อ่านยังไง',
        'spread': [
            ('สิ่งที่คุณเก็บไว้ในงานนี้', 'คุณค่าที่ยังมีถ้าคุณเลือกอยู่ — รวมทั้งสิ่งที่ดูธรรมดาแต่หาที่อื่นยาก'),
            ('สิ่งที่ตัวคุณต้องการต่อไป', 'พลังหรือทักษะที่ตัวคุณในอีกห้าปีกำลังต้องการให้คุณเริ่มสะสมตั้งแต่วันนี้'),
            ('ราคาของการเปลี่ยน', 'สิ่งที่คุณจะวางลงเมื่อย้าย — อาจเป็นความปลอดภัย ความคุ้นเคย หรือบางความสัมพันธ์'),
        ],
        'framework': 'ไพ่ในคำถามนี้ทำงานได้ดีที่สุดเมื่อคุณยอมให้ใบที่สองเป็นใบนำ ไม่ใช่ใบแรก เพราะใบที่สองคือเสียงของตัวคุณในอนาคต ถ้าใบที่สองชัดเจน คุณรู้คำตอบแล้ว ใบที่หนึ่งและสามแค่บอกราคา',
        'cards': ['eight-of-cups', 'the-tower', 'the-chariot', 'knight-of-wands', 'king-of-pentacles', 'two-of-pentacles'],
    },
]

ZODIAC_DATA = [
    ('aries', 'ราศีเมษ'),
    ('taurus', 'ราศีพฤษภ'),
    ('gemini', 'ราศีเมถุน'),
    ('cancer', 'ราศีกรกฎ'),
    ('leo', 'ราศีสิงห์'),
    ('virgo', 'ราศีกันย์'),
    ('libra', 'ราศีตุลย์'),
    ('scorpio', 'ราศีพิจิก'),
    ('sagittarius', 'ราศีธนู'),
    ('capricorn', 'ราศีมังกร'),
    ('aquarius', 'ราศีกุมภ์'),
    ('pisces', 'ราศีมีน')
]

def render_zodiac_page(slug, th_name):
    """Render an individual zodiac love tarot page."""
    canonical = f'/th/zodiac-love-tarot/{slug}/'
    page_url = f'https://veilatarot.com{canonical}'
    title = f'ดูดวงความรัก {th_name} — ไพ่ยิปซี เลือกไพ่ แม่นๆ | Veila'
    desc = f'ดูดวงความรัก {th_name} ด้วยไพ่ยิปซีรายเดือน เลือกไพ่ 3 ใบเพื่ออ่านพลังงานความรัก ความสัมพันธ์ และสิ่งที่กำลังจะเกิดขึ้นสำหรับชาว{th_name}โดยเฉพาะ'
    
    crumbs = [
        home_crumb('th'),
        ('ดวงความรัก 12 ราศี', 'https://veilatarot.com/th/zodiac-love-tarot/'),
        (th_name, page_url),
    ]
    
    article_jsonld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": desc,
        "image": "https://veilatarot.com/og.png",
        "inLanguage": "th-TH",
        "datePublished": BUILD_DATE,
        "dateModified": BUILD_DATE,
        "publisher": {"@type": "Organization", "name": "Veila", "url": "https://veilatarot.com/"},
        "mainEntityOfPage": page_url
    }
    head = _render_head_block_th_only(
        title=title, desc=desc,
        canonical=canonical, th_path=canonical,
        extra_jsonld=[article_jsonld, breadcrumb_jsonld(crumbs)]
    )
    
    return f'''<!DOCTYPE html>
<html lang="th">
<head>
{head}</head>
<body>

{render_header(canonical, canonical, 'th')}

<main class="article">
  {render_breadcrumb_html(crumbs)}
  <div class="eyebrow">ดวงความรักรายเดือน · {th_name}</div>
  <h1 class="title">ดูดวงความรัก {th_name} — ไพ่ยิปซี เลือกไพ่ แม่นๆ</h1>
  
  <div class="aeo-snippet">
    <p>ดูดวงความรัก {th_name} ด้วยไพ่ยิปซี: สำหรับชาว{th_name}ที่กำลังมองหาคำตอบเรื่องความสัมพันธ์ เลือกไพ่ 3 ใบเพื่อเปิดรับสารจากจักรวาล บทอ่านนี้จะช่วยสะท้อนพลังงานปัจจุบัน สิ่งที่ขวางกั้น และแนวโน้มในอนาคตอันใกล้สำหรับคุณโดยเฉพาะ</p>
  </div>

  <section>
    <h2>เริ่มทำนายดวงความรักชาว{th_name}</h2>
    <p>ตั้งสมาธิ นึกถึงเรื่องราวความรักของคุณ แล้วเลือกไพ่ที่ดึงดูดใจที่สุด</p>
    <div style="margin: 40px 0; text-align: center;">
      <a href="/quick-love-reading/?q=zodiac-{slug}&lang=th" class="btn" style="display: inline-block; padding: 18px 36px; background: var(--gold); color: var(--ink); text-decoration: none; font-weight: 600; border-radius: 4px;">เลือกไพ่ {th_name}</a>
    </div>
  </section>

  <section>
    <h2>FAQ เกี่ยวกับดวงความรัก {th_name}</h2>
    <div class="faq-item">
      <h3>ดวงความรักนี้แม่นแค่ไหน?</h3>
      <p>การดูดวงด้วยไพ่ยิปซีเป็นการอ่านพลังงานในช่วงเวลาหนึ่ง ผลลัพธ์อาจเปลี่ยนแปลงได้ตามการตัดสินใจของคุณ</p>
    </div>
  </section>
</main>

{render_footer('th')}
</body>
</html>'''

def render_zodiac_hub():
    """Render the main zodiac love tarot hub."""
    canonical = '/th/zodiac-love-tarot/'
    page_url = f'https://veilatarot.com{canonical}'
    title = 'ดูดวงความรัก 12 ราศี — ไพ่ยิปซี เลือกไพ่ แม่นๆ ครบทุกราศี | Veila'
    desc = 'เช็คดวงความรัก 12 ราศี ด้วยไพ่ยิปซี เลือกราศีของคุณเพื่อเริ่มทำนายดวงความรัก แม่นๆ ทั้งคนโสดและคนมีคู่'
    
    crumbs = [
        home_crumb('th'),
        ('ดวงความรัก 12 ราศี', page_url),
    ]
    
    head = _render_head_block_th_only(
        title=title, desc=desc,
        canonical=canonical, th_path=canonical,
        extra_jsonld=[breadcrumb_jsonld(crumbs)]
    )
    
    links = ""
    for slug, th_name in ZODIAC_DATA:
        links += f'<a href="/th/zodiac-love-tarot/{slug}/" style="padding: 20px; border: 1px solid var(--rule); text-decoration: none; color: var(--ivory);">{th_name}</a>\n'

    return f'''<!DOCTYPE html>
<html lang="th">
<head>
{head}</head>
<body>

{render_header(canonical, canonical, 'th')}

<main class="article">
  {render_breadcrumb_html(crumbs)}
  <h1 class="title">ดูดวงความรัก 12 ราศี</h1>
  <div class="aeo-snippet">
    <p>ดูดวงความรัก 12 ราศี ด้วยไพ่ยิปซี: ค้นหาคำตอบเรื่องหัวใจสำหรับราศีของคุณ เลือกไพ่แม่นๆ เพื่ออ่านทิศทางความรักและความสัมพันธ์ประจำเดือนนี้</p>
  </div>
  <div class="hub-card-list" style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 40px;">
    {links}
  </div>
</main>

{render_footer('th')}
</body>
</html>'''

def render_scenario(scenario):
    """Render a /th/scenarios/<slug>/ page."""
    slug = scenario['slug']
    title = scenario['title']
    canonical = f'/th/scenarios/{slug}/'
    page_url = f'https://veilatarot.com{canonical}'
    by_id_map = deck_by_id()
    # Build card link list from card slugs
    cards = []
    for sl in scenario['cards']:
        for c in DECK:
            if card_slug(c) == sl:
                cards.append(c)
                break

    desc = (scenario['lede'][:120] + '… บทใคร่ครวญสำหรับ ' + title.lower()
            + ' ผังสามใบและไพ่ที่มักปรากฏ จาก Veila ไพ่ทาโรต์เพื่อการใคร่ครวญ')
    # tighten if too long
    if len(desc) > 175:
        desc = scenario['lede'][:140] + '… จาก Veila'

    meta_title = f'{title} — ดูดวงความรัก ไพ่ยิปซี เลือกไพ่ แม่นๆ | Veila'

    category_hub = ('/th/tarot-love-readings/' if scenario['category'] == 'love'
                    else '/th/career-tarot-reading/')
    category_label = ('ไพ่เพื่อความรัก' if scenario['category'] == 'love'
                      else 'ไพ่เพื่อการงาน')

    crumbs = [
        home_crumb('th'),
        (category_label, f'https://veilatarot.com{category_hub}'),
        (title, page_url),
    ]
    article_jsonld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": meta_title,
        "description": desc,
        "image": "https://veilatarot.com/og.png",
        "inLanguage": "th-TH",
        "datePublished": BUILD_DATE,
        "dateModified": SCENARIO_MIGRATION_DATE,
        "publisher": {"@type": "Organization", "name": "Veila", "url": "https://veilatarot.com/"},
        "mainEntityOfPage": page_url
    }
    if slug in {'what-does-he-think-about-me', 'will-he-come-back'}:
        article_jsonld['author'] = {
            "@type": "Person",
            "@id": "https://veilatarot.com/#person",
            "name": "Veila Tarot Expert",
            "url": "https://veilatarot.com/th/about/",
            "jobTitle": "Tarot Reader & Hermit",
            "description": "Specializing in the Celtic Cross spread and bilingual tarot reflection.",
            "sameAs": ["https://veilatarot.com/th/about/"]
        }
    crumbs_jsonld = breadcrumb_jsonld(crumbs)

    # head_block expects en_path + th_path. For TH-only pages we omit
    # the hreflang en alternate entirely to avoid pointing at a 404.
    head = _render_head_block_th_only(
        title=meta_title, desc=desc,
        canonical=canonical, th_path=canonical,
        extra_jsonld=[article_jsonld, crumbs_jsonld]
    )

    spread_items = '\n'.join(
        f'      <li><strong>{escape(name)}</strong>{escape(meaning)}</li>'
        for name, meaning in scenario['spread']
    )

    related_links = '\n'.join(
        f'        <a href="{card_path(c, "th")}">'
        f'<div class="rc-rom">{c["roman"]}</div>'
        f'<div class="rc-name">{escape(c["name"]["th"])}</div>'
        f'</a>'
        for c in cards
    )

    return f'''<!DOCTYPE html>
<html lang="th">
<head>
{head}</head>
<body>

{render_header(canonical, canonical, 'th')}

<main class="article scenario-page">
  {render_breadcrumb_html(crumbs)}
  <div class="eyebrow">{escape(scenario['eyebrow'])}</div>
  <h1 class="title">{escape(title)}</h1>

  <div class="aeo-snippet">
    <p>ดูดวงความรัก ไพ่ยิปซี เพื่อหาคำตอบว่า{escape(title)} เลือกไพ่ 3 ใบเพื่ออ่านความจริงที่ซ่อนอยู่ บทอ่านแม่นๆ นี้ช่วยวิเคราะห์สถานการณ์ปัจจุบันเพื่อให้คุณเห็นภาพชัดเจนที่สุด</p>
  </div>

  <p class="lede">{escape(scenario['lede'])}</p>

  <div class="divider"><span class="line"></span><span class="mark"></span><span class="line"></span></div>

  <h2>คำถามที่ควรถามใจก่อน</h2>
  <p>{escape(scenario['intro_q'])}</p>

  <h2>ผังการอ่านสามใบ</h2>
  <ol class="positions">
{spread_items}
  </ol>

  <h2>กรอบการตีความ</h2>
  <p>{escape(scenario['framework'])}</p>

  <aside class="related-cards">
    <h2>ไพ่ที่มักปรากฏในคำถามนี้</h2>
    <div class="related-cards-grid">
{related_links}
    </div>
  </aside>

  <section class="scenario-disclaimer">
    <p>นี่คือบทใคร่ครวญ ไม่ใช่คำพยากรณ์ ไพ่คือเครื่องมือสะท้อนสิ่งที่คุณรู้อยู่แล้วในใจ ความหมายเป็นของคุณ</p>
  </section>

  <div class="cta-row">
    <a href="/" class="cta-btn">เปิดเซลติกครอสเต็ม</a>
    <a href="/th/daily-tarot-card/" class="cta-btn ghost">ไพ่ประจำวัน</a>
    <a href="{category_hub}" class="cta-btn ghost">{escape(category_label)}</a>
  </div>
</main>

{render_footer('th')}

</body>
</html>
'''


def render_scenario_redirect(scenario):
    """Compatibility redirect retained at a scenario's former Thai-transliterated URL."""
    target = f'/th/scenarios/{scenario["slug"]}/'
    target_url = f'https://veilatarot.com{target}'
    return f'''<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <meta name="robots" content="noindex,follow" />
  <meta http-equiv="refresh" content="0; url={target}" />
  <link rel="canonical" href="{target_url}" />
  <title>ย้ายหน้าแล้ว | Veila</title>
  <script>window.location.replace('{target}' + window.location.search + window.location.hash);</script>
</head>
<body>
  <p>หน้านี้ย้ายแล้ว <a href="{target}">ไปยังหน้าปัจจุบัน</a></p>
</body>
</html>'''


def _render_head_block_th_only(title, desc, canonical, th_path, extra_jsonld=None):
    """Head block for TH-only pages — no en hreflang alternate."""
    jsonld_blocks = extra_jsonld or []
    head = f'''<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{escape(title)}</title>
<meta name="description" content="{escape(desc, quote=True)}" />
<meta name="author" content="Veila Tarot" />
<meta name="robots" content="index, follow, max-image-preview:large" />
<meta name="theme-color" content="#0a0a0c" />
<meta name="color-scheme" content="dark" />

<link rel="canonical" href="https://veilatarot.com{canonical}" />
<link rel="alternate" hreflang="th" href="https://veilatarot.com{th_path}" />

<meta property="og:type" content="article" />
<meta property="og:site_name" content="Veila" />
<meta property="og:title" content="{escape(title, quote=True)}" />
<meta property="og:description" content="{escape(desc, quote=True)}" />
<meta property="og:url" content="https://veilatarot.com{canonical}" />
<meta property="og:image" content="https://veilatarot.com/og.png" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:locale" content="th_TH" />

<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{escape(title, quote=True)}" />
<meta name="twitter:description" content="{escape(desc, quote=True)}" />
<meta name="twitter:image" content="https://veilatarot.com/og.png" />

<link rel="icon" href="/favicon.svg" type="image/svg+xml" />
<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png" />
<link rel="apple-touch-icon" href="/apple-touch-icon.png" sizes="180x180" />
<link rel="manifest" href="/manifest.webmanifest" />
<link rel="alternate" type="application/rss+xml" title="Veila Tarot — Feed" href="/feed.xml" />

<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,400&family=IBM+Plex+Sans+Thai:wght@300;400;500;600&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="/assets/page.css" />

<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2823470980745945"
     crossorigin="anonymous"></script>
<meta name="google-adsense-account" content="ca-pub-2823470980745945">

<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQWWZ3HT2S"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-NQWWZ3HT2S');
</script>

<script src="/assets/analytics.js" defer></script>
'''
    for block in jsonld_blocks:
        head += f'\n<script type="application/ld+json">\n{json.dumps(block, ensure_ascii=False, indent=2)}\n</script>\n'
    return head


def scenarios_for_card(card):
    """Return up to 3 scenario slugs whose 'cards' list contains this card."""
    sl = card_slug(card)
    hits = [s for s in TH_SCENARIOS if sl in s['cards']]
    return hits[:3]


# Long-form date for visible "Last updated" footer line.

# Long-form date for visible "Last updated" footer line.
BUILD_DATE_LONG_EN = '14 May 2026'
BUILD_DATE_LONG_TH = '14 พฤษภาคม 2026'
# RFC 822 for RSS pubDate / lastBuildDate
BUILD_DATE_RFC822 = 'Wed, 14 May 2026 00:00:00 +0000'

HUB_SLUGS = [
    'major-arcana', 'minor-arcana',
    'cups-tarot-meanings', 'swords-tarot-meanings',
    'wands-tarot-meanings', 'pentacles-tarot-meanings',
    'tarot-love-readings', 'career-tarot-reading', 'yes-no-tarot',
]

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def card_slug(card):
    """01-the-fool -> the-fool"""
    return re.sub(r'^\d{2}-', '', card['id'])

def card_path(card, lang):
    return f'/{("th/" if lang == "th" else "")}cards/{card_slug(card)}/'

def hub_path(slug, lang):
    return f'/{("th/" if lang == "th" else "")}{slug}/'

def deck_by_id():
    return {c['id']: c for c in DECK}

def arcana_label(card, lang):
    if card['arcana'] == 'major':
        return f"Major Arcana · {card['roman']}" if lang == 'en' else f"ไพ่ชุดเมเจอร์ · {card['roman']}"
    suit = (SUIT_EN if lang == 'en' else SUIT_TH)[card['suit']]
    return f"Minor Arcana · {suit}" if lang == 'en' else f"ไพ่ชุดไมเนอร์ · {suit}"

def card_meta_desc(card, lang):
    name = card['name'][lang]
    kw_up = (card['upright'].get('keywords') or {}).get(lang, '') or ''
    if lang == 'en':
        return f"{name} tarot card meaning: {kw_up}. Upright, reversed, and all ten Celtic Cross positions explained."
    return f"ความหมายไพ่ {name}: {kw_up} ดูดวงความรัก ไพ่ยิปซี เลือกไพ่ แม่นๆ พร้อมคำทำนายทั้งสิบตำแหน่งของผังเซลติกครอส"

def topical_link_for_card(card, lang):
    if card['arcana'] == 'minor' and card['suit'] == 'cups':
        return ('love', hub_path('tarot-love-readings', lang),
                'Tarot for Love' if lang == 'en' else 'ไพ่ความรัก')
    if card['arcana'] == 'minor' and card['suit'] == 'pentacles':
        return ('career', hub_path('career-tarot-reading', lang),
                'Tarot for Career' if lang == 'en' else 'ไพ่อาชีพ')
    return ('yesno', hub_path('yes-no-tarot', lang),
            'Yes/No Readings' if lang == 'en' else 'ไพ่ใช่/ไม่ใช่')

def related_cards(card, n=6):
    """Other cards in the same arcana/suit, ordered as the n following peers
    (cyclic) — gives a 'next in the suit/major journey' feel."""
    if card['arcana'] == 'major':
        peers = sorted([c for c in DECK if c['arcana'] == 'major'], key=lambda c: c['id'])
    else:
        peers = sorted([c for c in DECK if c.get('suit') == card['suit']], key=lambda c: c['id'])
    idx = next(i for i, c in enumerate(peers) if c['id'] == card['id'])
    return [peers[(idx + k) % len(peers)] for k in range(1, n + 1)]

def category_hub_link(card, lang):
    if card['arcana'] == 'major':
        return (hub_path('major-arcana', lang),
                'The Major Arcana' if lang == 'en' else 'ไพ่ชุดเมเจอร์')
    return (hub_path(SUIT_HUB_SLUG[card['suit']], lang),
            f"The Suit of {SUIT_EN[card['suit']]}" if lang == 'en' else f"ไพ่ชุด{SUIT_TH[card['suit']]}")

# ---------------------------------------------------------------------------
# BREADCRUMBS
# ---------------------------------------------------------------------------

def home_crumb(lang):
    return (('Home' if lang == 'en' else 'หน้าแรก'),
            'https://veilatarot.com/')

def breadcrumb_for_card(card, lang):
    base = 'https://veilatarot.com'
    crumbs = [home_crumb(lang)]
    if card['arcana'] == 'major':
        crumbs.append((
            'Major Arcana' if lang == 'en' else 'ไพ่ชุดเมเจอร์',
            base + hub_path('major-arcana', lang)
        ))
    else:
        crumbs.append((
            'Minor Arcana' if lang == 'en' else 'ไพ่ชุดไมเนอร์',
            base + hub_path('minor-arcana', lang)
        ))
        suit = card['suit']
        crumbs.append((
            f"The Suit of {SUIT_EN[suit]}" if lang == 'en' else f"ไพ่ชุด{SUIT_TH[suit]}",
            base + hub_path(SUIT_HUB_SLUG[suit], lang)
        ))
    crumbs.append((card['name'][lang], base + card_path(card, lang)))
    return crumbs

def breadcrumb_for_hub(slug, lang):
    base = 'https://veilatarot.com'
    crumbs = [home_crumb(lang)]
    title_en = HUB_DEFS[slug]['title_plain_en']
    title_th = HUB_DEFS[slug]['title_plain_th']
    if slug in ('cups-tarot-meanings', 'swords-tarot-meanings',
                'wands-tarot-meanings', 'pentacles-tarot-meanings'):
        crumbs.append((
            'Minor Arcana' if lang == 'en' else 'ไพ่ชุดไมเนอร์',
            base + hub_path('minor-arcana', lang)
        ))
    crumbs.append((
        title_en if lang == 'en' else title_th,
        base + hub_path(slug, lang)
    ))
    return crumbs

def render_breadcrumb_html(crumbs):
    """Visible <nav class='breadcrumb'> rendering. Last crumb is non-link."""
    parts = []
    for i, (name, item) in enumerate(crumbs):
        is_last = (i == len(crumbs) - 1)
        if is_last:
            parts.append(f'<span class="bc-current">{escape(name)}</span>')
        else:
            # strip the absolute prefix for visible href
            href = item.replace('https://veilatarot.com', '')
            parts.append(f'<a href="{href}">{escape(name)}</a>')
    sep = '<span class="bc-sep">›</span>'
    return f'<nav class="breadcrumb" aria-label="Breadcrumb">{sep.join(parts)}</nav>'

def breadcrumb_jsonld(crumbs):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": item}
            for i, (name, item) in enumerate(crumbs)
        ]
    }

# ---------------------------------------------------------------------------
# SHARED HEAD / FOOTER
# ---------------------------------------------------------------------------

def render_head_block(title, desc, canonical, en_path, th_path,
                      og_image='https://veilatarot.com/og.png',
                      og_type='article', lang='en', extra_jsonld=None,
                      include_share=False):
    """Common <head> contents minus the surrounding <head></head>."""
    og_locale = 'en_US' if lang == 'en' else 'th_TH'
    og_locale_alt = 'th_TH' if lang == 'en' else 'en_US'
    in_language = 'en-US' if lang == 'en' else 'th-TH'
    jsonld_blocks = extra_jsonld or []

    head = f'''<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{escape(title)}</title>
<meta name="description" content="{escape(desc, quote=True)}" />
<meta name="author" content="Veila Tarot" />
<meta name="robots" content="index, follow, max-image-preview:large" />
<meta name="theme-color" content="#0a0a0c" />
<meta name="color-scheme" content="dark" />

<link rel="canonical" href="https://veilatarot.com{canonical}" />
<link rel="alternate" hreflang="en" href="https://veilatarot.com{en_path}" />
<link rel="alternate" hreflang="th" href="https://veilatarot.com{th_path}" />
<link rel="alternate" hreflang="x-default" href="https://veilatarot.com{en_path}" />

<meta property="og:type" content="{og_type}" />
<meta property="og:site_name" content="Veila" />
<meta property="og:title" content="{escape(title, quote=True)}" />
<meta property="og:description" content="{escape(desc, quote=True)}" />
<meta property="og:url" content="https://veilatarot.com{canonical}" />
<meta property="og:image" content="{og_image}" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:locale" content="{og_locale}" />
<meta property="og:locale:alternate" content="{og_locale_alt}" />

<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{escape(title, quote=True)}" />
<meta name="twitter:description" content="{escape(desc, quote=True)}" />
<meta name="twitter:image" content="{og_image}" />

<link rel="icon" href="/favicon.svg" type="image/svg+xml" />
<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png" />
<link rel="apple-touch-icon" href="/apple-touch-icon.png" sizes="180x180" />
<link rel="manifest" href="/manifest.webmanifest" />
<link rel="alternate" type="application/rss+xml" title="Veila Tarot — Feed" href="/feed.xml" />

<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,400&family=IBM+Plex+Sans+Thai:wght@300;400;500;600&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="/assets/page.css" />

<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2823470980745945"
     crossorigin="anonymous"></script>
<meta name="google-adsense-account" content="ca-pub-2823470980745945">

<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQWWZ3HT2S"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-NQWWZ3HT2S');
</script>

<script src="/assets/analytics.js" defer></script>
'''
    if include_share:
        head += '<script src="/assets/share.js" defer></script>\n'
    for block in jsonld_blocks:
        head += f'\n<script type="application/ld+json">\n{json.dumps(block, ensure_ascii=False, indent=2)}\n</script>\n'
    return head


def render_header(en_path, th_path, lang):
    if lang == 'en':
        brand_sub = 'A Tarot Practice'
        brand_aria = 'Veila — return to home'
        lang_aria = 'Language'
    else:
        brand_sub = 'การทำสมาธิกับไพ่'
        brand_aria = 'Veila — กลับสู่หน้าแรก'
        lang_aria = 'ภาษา'
    return f'''<header class="site-header">
  <a class="brand" href="/" aria-label="{escape(brand_aria, quote=True)}">Veila<span class="dot"></span><span class="brand-sub">{escape(brand_sub)}</span></a>
  <div class="lang-toggle" role="group" aria-label="{escape(lang_aria, quote=True)}">
    <a href="{en_path}"{' class="active"' if lang == 'en' else ''}>EN</a>
    <span class="sep">·</span>
    <a href="{th_path}"{' class="active"' if lang == 'th' else ''}>TH</a>
  </div>
</header>'''


def render_footer(lang):
    if lang == 'en':
        link_celtic, link_daily = '/celtic-cross-tarot/', '/daily-tarot-card/'
        link_index = '/all-tarot-pages/'
        nav_celtic, nav_daily, nav_index = 'Celtic Cross Guide', 'Daily Tarot Card', 'All Pages'
        fineprint = 'For reflection, not prediction.'
        last_updated = f'Last updated · {BUILD_DATE_LONG_EN}'
    else:
        link_celtic, link_daily = '/th/celtic-cross-tarot/', '/th/daily-tarot-card/'
        link_index = '/th/all-tarot-pages/'
        nav_celtic, nav_daily, nav_index = 'คู่มือเซลติกครอส', 'ไพ่ประจำวัน', 'ทุกหน้า'
        fineprint = 'เพื่อการใคร่ครวญ ไม่ใช่การพยากรณ์'
        last_updated = f'ปรับปรุงล่าสุด · {BUILD_DATE_LONG_TH}'
    return f'''<footer>
  <div class="fineprint">{escape(fineprint)}</div>
  <div class="last-updated">{escape(last_updated)}</div>
  <nav class="footer-nav">
    <a href="{link_celtic}">{escape(nav_celtic)}</a>
    <span class="sep">·</span>
    <a href="{link_daily}">{escape(nav_daily)}</a>
    <span class="sep">·</span>
    <a href="{link_index}">{escape(nav_index)}</a>
  </nav>
  <div>veilatarot.com · © MMXXVI</div>
</footer>'''

# ---------------------------------------------------------------------------
# CARD PAGE
# ---------------------------------------------------------------------------

def render_related_cards_module(card, lang):
    if card['arcana'] == 'major':
        heading = 'Other Major Arcana' if lang == 'en' else 'ไพ่ชุดเมเจอร์อื่นๆ'
    else:
        suit_en = SUIT_EN[card['suit']]
        suit_th = SUIT_TH[card['suit']]
        heading = f"Other cards in the Suit of {suit_en}" if lang == 'en' else f"ไพ่ใบอื่นในชุด{suit_th}"
    items = []
    for peer in related_cards(card):
        items.append(f'''      <a href="{card_path(peer, lang)}">
        <div class="rc-rom">{peer['roman']}</div>
        <div class="rc-name">{escape(peer['name'][lang])}</div>
      </a>''')
    return f'''  <aside class="related-cards">
    <h2>{escape(heading)}</h2>
    <div class="related-cards-grid">
{chr(10).join(items)}
    </div>
  </aside>'''


def render_explore_related_readings(card, lang):
    cat_href, cat_name = category_hub_link(card, lang)
    _, topic_href, topic_name = topical_link_for_card(card, lang)
    if lang == 'en':
        h2 = 'Explore related readings'
        lede = "When you want context beyond this single card, try one of these."
        labels = {'spread': 'The Spread', 'daily': 'Daily', 'category': 'Category', 'topic': 'Topic'}
        spread_name = 'The Celtic Cross'
        daily_name = "Today's Card"
        celtic_href, daily_href = '/celtic-cross-tarot/', '/daily-tarot-card/'
    else:
        h2 = 'อ่านเพิ่มเติม'
        lede = 'เมื่อต้องการบริบทมากกว่าไพ่ใบเดียว ลองดูจุดเริ่มต้นเหล่านี้'
        labels = {'spread': 'ผังการอ่าน', 'daily': 'ประจำวัน', 'category': 'หมวด', 'topic': 'หัวข้อ'}
        spread_name = 'เซลติกครอส'
        daily_name = 'ไพ่วันนี้'
        celtic_href, daily_href = '/th/celtic-cross-tarot/', '/th/daily-tarot-card/'
    items = [
        (labels['spread'], spread_name, celtic_href),
        (labels['daily'], daily_name, daily_href),
        (labels['category'], cat_name, cat_href),
        (labels['topic'], topic_name, topic_href),
    ]
    cells = '\n'.join(
        f'''      <a href="{href}">
        <div class="rl-label">{escape(lbl)}</div>
        <div class="rl-name">{escape(name)}</div>
      </a>''' for (lbl, name, href) in items
    )
    return f'''  <aside class="related-readings">
    <h2>{escape(h2)}</h2>
    <p class="related-lede">{escape(lede)}</p>
    <div class="related-grid">
{cells}
    </div>
  </aside>'''


def card_i18n(lang, name):
    if lang == 'en':
        return {
            'title': f"{name} Tarot Card — Upright, Reversed & Celtic Cross | Veila",
            'h2_up': f"{name} — Upright",
            'h2_rev': f"{name} — Reversed",
            'h2_cc': 'In the Celtic Cross spread',
            'cc_lede': f"How {name} reads in each of the ten Celtic Cross positions.",
            'prev_label': 'Previous', 'next_label': 'Next',
            'cta_main': 'Begin a Reading',
            'cta_about': 'About the Spread',
            'cta_daily': 'Daily Card',
            'up_label': 'Upright', 'rev_label': 'Reversed',
            'adj_aria': 'Adjacent cards',
        }
    return {
        'title': f"ความหมายไพ่ {name} — ดูดวงความรัก ไพ่ยิปซี เลือกไพ่ แม่นๆ | Veila",
        'h2_up': f"{name} — ตั้งตรง",
        'h2_rev': f"{name} — กลับหัว",
        'h2_cc': 'ในผังเซลติกครอส',
        'cc_lede': f"การอ่านไพ่ {name} ในแต่ละตำแหน่งของผังเซลติกครอสทั้งสิบตำแหน่ง",
        'prev_label': 'ก่อนหน้า', 'next_label': 'ถัดไป',
        'cta_main': 'เริ่มอ่านไพ่',
        'cta_about': 'เกี่ยวกับผังการอ่าน',
        'cta_daily': 'ไพ่ประจำวัน',
        'up_label': 'ตั้งตรง', 'rev_label': 'กลับหัว',
        'adj_aria': 'ไพ่ข้างเคียง',
    }


def render_intent_sections_th(card, name):
    """Three new Thai intent sections per TH card page: love, career, finance.
    Pulls from cards.json (upright + reversed each have love/career/finance
    populated by scripts/regen-cards-json.py)."""
    up = card.get('upright') or {}
    rev = card.get('reversed') or {}

    def pair(key, heading):
        up_text = (up.get(key) or {}).get('th') or ''
        rev_text = (rev.get(key) or {}).get('th') or ''
        if not up_text and not rev_text:
            return ''
        return f'''  <section class="intent-block">
    <h2>{escape(name)} ใน{escape(heading)}</h2>
    <h3>ตั้งตรง</h3>
    <p>{escape(up_text)}</p>
    <h3>กลับหัว</h3>
    <p>{escape(rev_text)}</p>
  </section>'''

    out = [
        pair('love', 'ความรัก'),
        pair('career', 'การงาน'),
        pair('finance', 'การเงิน'),
    ]
    return '\n\n'.join(b for b in out if b)


def render_scenario_links_th(card):
    """If the card appears in any TH_SCENARIOS, add a 'related scenarios' block."""
    hits = scenarios_for_card(card)
    if not hits:
        return ''
    items = '\n'.join(
        f'      <a href="/th/scenarios/{s["slug"]}/">'
        f'<div class="rl-label">สถานการณ์</div>'
        f'<div class="rl-name">{escape(s["title"])}</div>'
        f'</a>'
        for s in hits
    )
    return f'''  <aside class="related-readings scenarios">
    <h2>คำถามที่ไพ่ใบนี้มักปรากฏ</h2>
    <p class="related-lede">บทใคร่ครวญที่ใช้ไพ่ใบนี้บ่อย</p>
    <div class="related-grid">
{items}
    </div>
  </aside>'''


def _clip_sentences(text, max_words=80):
    """Trim text at a sentence boundary so it never exceeds max_words.

    Always keeps at least one full sentence — never cuts mid-sentence.
    """
    text = (text or '').strip()
    if not text:
        return text
    sentences = re.split(r'(?<=[.!?])\s+', text)
    out = []
    words = 0
    for s in sentences:
        n = len(s.split())
        if out and words + n > max_words:
            break
        out.append(s)
        words += n
    return ' '.join(out)


def _en_name_ref(name):
    """'The Fool' -> 'The Fool'; 'Ace of Cups' -> 'the Ace of Cups'."""
    return name if name.lower().startswith('the ') else f'the {name}'


def _keyword_phrase(keywords):
    """'A, B, C' -> 'a, b, and c' for use inside an English sentence."""
    parts = [k.strip().lower() for k in (keywords or '').split(',') if k.strip()]
    if not parts:
        return ''
    if len(parts) == 1:
        return parts[0]
    return ', '.join(parts[:-1]) + ', and ' + parts[-1]


def _yes_no_lean(card):
    if card['id'] in TOPICAL_CARD_IDS['yes']:
        return 'yes'
    if card['id'] in TOPICAL_CARD_IDS['no']:
        return 'no'
    return None


def render_card_faq_jsonld(card, lang):
    """FAQPage JSON-LD (4-5 Q&As), assembled strictly from cards.json content.

    Every answer is complete sentences — no substring truncation.
    """
    name = card['name'][lang]
    up = card.get('upright') or {}
    rev = card.get('reversed') or {}
    up_text = (up.get('standalone') or {}).get(lang, '') or ''
    rev_text = (rev.get('standalone') or {}).get(lang, '') or ''
    up_love = (up.get('love') or {}).get(lang, '') or ''
    rev_love = (rev.get('love') or {}).get(lang, '') or ''
    up_career = (up.get('career') or {}).get(lang, '') or ''
    up_kw = (up.get('keywords') or {}).get(lang, '') or ''
    rev_kw = (rev.get('keywords') or {}).get(lang, '') or ''
    lean = _yes_no_lean(card)

    if lang == 'th':
        rev_love_joined = f"{up_love} หากไพ่ออกมากลับหัว {rev_love}".strip()
        questions = [
            (f"ไพ่ {name} หมายถึงอะไร?",
             f"ในตำแหน่งตั้งตรง ไพ่ {name} สื่อถึง {up_kw} {up_text}"),
            (f"ไพ่ {name} ความหมายด้านความรักคืออะไร?",
             rev_love_joined),
            (f"ไพ่ {name} กลับหัวหมายความว่าอย่างไร?",
             f"ไพ่ {name} กลับหัวสื่อถึง {rev_kw} {rev_text}"),
            (f"ไพ่ {name} บอกอะไรเกี่ยวกับการงาน?",
             up_career),
        ]
        if lean == 'yes':
            questions.append((
                f"ไพ่ {name} เป็นไพ่ใช่หรือไม่ใช่ (Yes/No)?",
                f"ในการเปิดไพ่แบบใช่/ไม่ใช่ ไพ่ {name} มักถูกอ่านว่าเอนไปทาง \"ใช่\" "
                f"คู่มือไพ่ใช่/ไม่ใช่ของ Veila จัดไพ่ใบนี้ไว้ในกลุ่มไพ่ที่เอนไปทางใช่ "
                f"สอดคล้องกับคีย์เวิร์ดตั้งตรงอย่าง {up_kw}"
            ))
        elif lean == 'no':
            questions.append((
                f"ไพ่ {name} เป็นไพ่ใช่หรือไม่ใช่ (Yes/No)?",
                f"ในการเปิดไพ่แบบใช่/ไม่ใช่ ไพ่ {name} มักถูกอ่านว่าเอนไปทาง \"ไม่ใช่\" "
                f"คู่มือไพ่ใช่/ไม่ใช่ของ Veila จัดไพ่ใบนี้ไว้ในกลุ่มไพ่ที่เอนไปทางไม่ใช่ "
                f"สอดคล้องกับคีย์เวิร์ดตั้งตรงอย่าง {up_kw}"
            ))
    else:
        ref = _en_name_ref(name)
        up_kw_phrase = _keyword_phrase(up_kw)
        rev_kw_phrase = _keyword_phrase(rev_kw)
        love_answer = up_love
        if rev_love:
            love_answer = _clip_sentences(
                f"{up_love} If the card lands reversed, {rev_love[0].lower() + rev_love[1:]}"
            )
        questions = [
            (f"What does {ref} tarot card mean?",
             _clip_sentences(f"Upright, {name} speaks to {up_kw_phrase}. {up_text}")),
            (f"What does {ref} mean in a love reading?",
             love_answer),
            (f"What does {ref} reversed mean?",
             _clip_sentences(f"Reversed, {name} points to {rev_kw_phrase}. {rev_text}")),
            (f"What does {ref} mean for career and work?",
             _clip_sentences(up_career)),
        ]
        if lean == 'yes':
            questions.append((
                f"Is {name} a yes or no card?",
                f"In a yes-or-no reading, {name} is generally read as a yes. "
                f"Veila's yes/no tarot guide lists it among the cards that lean yes, "
                f"in line with its upright themes of {up_kw_phrase}."
            ))
        elif lean == 'no':
            questions.append((
                f"Is {name} a yes or no card?",
                f"In a yes-or-no reading, {name} is generally read as a no. "
                f"Veila's yes/no tarot guide lists it among the cards that lean no, "
                f"in line with its upright themes of {up_kw_phrase}."
            ))

    faq_entities = []
    for q, a in questions:
        faq_entities.append({
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {
                "@type": "Answer",
                "text": a
            }
        })
        
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": faq_entities
    }


def render_card(card, prev_card, next_card, lang):
    sl = card_slug(card)
    name = card['name'][lang]
    archetype = (card.get('archetype') or {}).get(lang, '') or ''
    up = card.get('upright') or {}
    rev = card.get('reversed') or {}
    up_kw = (up.get('keywords') or {}).get(lang, '') or ''
    rev_kw = (rev.get('keywords') or {}).get(lang, '') or ''
    up_text = (up.get('standalone') or {}).get(lang, '') or ''
    rev_text = (rev.get('standalone') or {}).get(lang, '') or ''

    label = arcana_label(card, lang)
    desc = card_meta_desc(card, lang)
    t = card_i18n(lang, name)
    title = t['title']
    en_path = card_path(card, 'en')
    th_path = card_path(card, 'th')
    canonical = en_path if lang == 'en' else th_path
    page_url = f"https://veilatarot.com{canonical}"

    cc_blocks = []
    for pos in POSITIONS:
        pkey = pos['key']
        short = pos[f'short_{lang}']
        up_cc = ((up.get('celtic_cross') or {}).get(pkey) or {}).get(lang, '') or up_text
        rev_cc = ((rev.get('celtic_cross') or {}).get(pkey) or {}).get(lang, '') or rev_text
        cc_blocks.append(f'''        <article class="cc-pos">
          <div class="cc-pos-label"><span class="rn">{ROMAN[pos['n'] - 1]}.</span> {escape(short)}</div>
          <div class="cc-pair"><h3>{escape(t['up_label'])}</h3><p>{escape(up_cc)}</p></div>
          <div class="cc-pair"><h3>{escape(t['rev_label'])}</h3><p>{escape(rev_cc)}</p></div>
        </article>''')
    cc_html = '\n'.join(cc_blocks)

    prev_url = card_path(prev_card, lang)
    next_url = card_path(next_card, lang)
    prev_name = prev_card['name'][lang]
    next_name = next_card['name'][lang]

    link_app = '/th/celtic-cross-reading/' if lang == 'th' else '/celtic-cross-reading/'
    link_celtic = '/th/celtic-cross-tarot/' if lang == 'th' else '/celtic-cross-tarot/'
    link_daily = '/th/daily-tarot-card/' if lang == 'th' else '/daily-tarot-card/'

    article_jsonld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": desc,
        "image": "https://veilatarot.com/og.png",
        "inLanguage": 'en-US' if lang == 'en' else 'th-TH',
        "datePublished": BUILD_DATE,
        "dateModified": CARD_CONTENT_UPDATE_DATE,
        "author": {"@id": "https://veilatarot.com/#person"},
        "publisher": {"@type": "Organization", "name": "Veila", "url": "https://veilatarot.com/"},
        "mainEntityOfPage": page_url
    }
    crumbs = breadcrumb_for_card(card, lang)
    breadcrumb_html = render_breadcrumb_html(crumbs)
    crumbs_jsonld = breadcrumb_jsonld(crumbs)
    faq_jsonld = render_card_faq_jsonld(card, lang)
    related_html = render_related_cards_module(card, lang)
    explore_html = render_explore_related_readings(card, lang)

    head = render_head_block(
        title=title, desc=desc, canonical=canonical,
        en_path=en_path, th_path=th_path, lang=lang,
        extra_jsonld=[article_jsonld, crumbs_jsonld, faq_jsonld],
        include_share=True,
    )

    # ----- Share-this-card block ---------------------------------------------
    if lang == 'th':
        share_lede = 'บันทึกใบนี้เก็บไว้เป็นภาพ — สำหรับใคร่ครวญในวันอื่น'
        share_btn_label = 'บันทึกเป็นภาพ'
        share_sheet_eyebrow = 'บันทึกไพ่'
        share_download = 'ดาวน์โหลด'
        share_native = 'แชร์'
        share_copylink = 'คัดลอกลิงก์'
        share_copied = 'คัดลอกแล้ว'
        share_close = 'ปิด'
        share_rendering = 'กำลังสร้าง…'
        share_upright_label = 'ตั้งตรง'
        share_reversed_label = 'กลับหัว'
    else:
        share_lede = 'Save this card as an image — for a quieter moment.'
        share_btn_label = 'Save as image'
        share_sheet_eyebrow = 'Save this card'
        share_download = 'Download'
        share_native = 'Share'
        share_copylink = 'Copy link'
        share_copied = 'Copied'
        share_close = 'Close'
        share_rendering = 'Rendering…'
        share_upright_label = 'Upright'
        share_reversed_label = 'Reversed'

    card_data = {
        'id': card.get('id'),
        'lang': lang,
        'name': name,
        'roman': card.get('roman') or '',
        'arcana': card.get('arcana') or '',
        'suit': card.get('suit'),
        'eyebrow': label,
        'pageUrl': page_url,
        'upright': {'keywords': up_kw, 'text': up_text, 'label': share_upright_label},
        'reversed': {'keywords': rev_kw, 'text': rev_text, 'label': share_reversed_label},
        'labels': {
            'sheetEyebrow': share_sheet_eyebrow,
            'download': share_download,
            'share': share_native,
            'copyLink': share_copylink,
            'copied': share_copied,
            'close': share_close,
            'rendering': share_rendering,
        },
    }
    card_data_json = json.dumps(card_data, ensure_ascii=False)

    share_section_html = f'''  <aside class="share-card" aria-label="{escape(share_btn_label, quote=True)}">
    <p class="share-card-lede">{escape(share_lede)}</p>
    <button type="button" class="cta-btn ghost veila-share-btn">{escape(share_btn_label)}</button>
  </aside>'''

    share_filename_slug = (card.get('id') or 'card').replace('_', '-')
    share_inline_script = f'''<script id="veila-card-data" type="application/json">{card_data_json}</script>
<script>
(function() {{
  function init() {{
    var node = document.getElementById('veila-card-data');
    var btn = document.querySelector('.veila-share-btn');
    if (!node || !btn || !window.veilaShare) return;
    var data;
    try {{ data = JSON.parse(node.textContent); }} catch (e) {{ return; }}
    btn.addEventListener('click', function() {{
      var orientation = data.upright.label;
      var excerpt = data.upright.text || data.upright.keywords;
      window.veilaShare.shareCard({{
        lang: data.lang,
        eyebrow: data.eyebrow,
        name: data.name,
        orientation: orientation,
        excerpt: excerpt,
        pageUrl: data.pageUrl,
        filename: 'veila-{share_filename_slug}-' + data.lang + '.png',
        sheetEyebrow: data.labels.sheetEyebrow,
        downloadLabel: data.labels.download,
        shareLabel: data.labels.share,
        copyLinkLabel: data.labels.copyLink,
        copiedLabel: data.labels.copied,
        closeLabel: data.labels.close,
        renderingLabel: data.labels.rendering,
        shareTitle: data.name,
        shareText: data.name + ' — ' + data.eyebrow,
        events: {{
          exported: 'card_share_exported',
          native: 'card_share_native',
          linkCopied: 'card_share_link_copied'
        }},
        eventParams: {{ card_id: data.id, lang: data.lang }}
      }});
    }});
  }}
  if (window.veilaShare) init();
  else if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
}})();
</script>'''

    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
{head}</head>
<body>

{render_header(en_path, th_path, lang)}

<main class="article card-page">
  {breadcrumb_html}
  {aeo_block(name, card['name']['th'], up_text, (card.get('upright') or {}).get('standalone', {}).get('th', ''), lang)}
  <div class="eyebrow">{escape(label)}</div>
  <h1 class="title">{escape(name)}</h1>
  <p class="archetype">{escape(archetype)}</p>

  <section class="meaning-block">
    <h2>{escape(t['h2_up'])}</h2>
    <p class="card-keywords">{escape(up_kw)}</p>
    <p>{escape(up_text)}</p>
  </section>

  <section class="meaning-block">
    <h2>{escape(t['h2_rev'])}</h2>
    <p class="card-keywords">{escape(rev_kw)}</p>
    <p>{escape(rev_text)}</p>
  </section>

  <section class="cc-section">
    <h2>{escape(t['h2_cc'])}</h2>
    <p class="cc-lede">{escape(t['cc_lede'])}</p>
    <div class="cc-grid">
{cc_html}
    </div>
  </section>

{render_intent_sections_th(card, name) if lang == 'th' else ''}

{render_scenario_links_th(card) if lang == 'th' else ''}

  <nav class="adjacent-nav" aria-label="{escape(t['adj_aria'], quote=True)}">
    <a class="adj prev" href="{prev_url}">
      <div class="dir">← {escape(t['prev_label'])}</div>
      <div class="adj-name">{escape(prev_name)}</div>
    </a>
    <a class="adj next" href="{next_url}">
      <div class="dir">{escape(t['next_label'])} →</div>
      <div class="adj-name">{escape(next_name)}</div>
    </a>
  </nav>

{related_html}

{explore_html}

{share_section_html}

  <div class="cta-row">
    <a href="{link_app}" class="cta-btn">{escape(t['cta_main'])}</a>
    <a href="{link_celtic}" class="cta-btn ghost">{escape(t['cta_about'])}</a>
    <a href="{link_daily}" class="cta-btn ghost">{escape(t['cta_daily'])}</a>
  </div>
</main>

{render_footer(lang)}

{share_inline_script}

<script src="/assets/chrome.js" defer></script>
</body>
</html>
'''

# ---------------------------------------------------------------------------
# HUB PAGES
# ---------------------------------------------------------------------------

HUB_DEFS = {
    'major-arcana': {
        'title_plain_en': 'The Major Arcana',
        'title_plain_th': 'ไพ่ชุดเมเจอร์',
        'meta': {
            'en': {
                'title': 'The Major Arcana — All 22 Tarot Trumps Explained | Veila',
                'desc':  'The 22 Major Arcana tarot cards, from The Fool to The World. Brief descriptions with links to each card\'s full meaning page.',
                'eyebrow': 'The 22 Trumps',
                'h1_html': 'The <em>Major Arcana</em>',
                'lede': 'Twenty-two cards charting a journey from naive beginnings to integrated arrival. Each is an archetype, a station on the road, a turn the seeker takes whether they meant to or not.',
                'intro': "The journey of the Major Arcana is sometimes called the Fool's Journey: a young, open self meets the world's archetypal forces in sequence, is shaped by them, and arrives at completion changed. When a Major appears in a reading, it carries more weight than a Minor — the question is touching something structural.",
                'list_heading': 'The 22 Major Arcana',
            },
            'th': {
                'title': 'ไพ่เมเจอร์อาร์คานา 22 ใบ ความหมาย — ดูดวงความรัก ไพ่ยิปซี | Veila',
                'desc':  'ความหมายไพ่ยิปซีชุดเมเจอร์ทั้ง 22 ใบ ตั้งแต่ The Fool ถึง The World คำอธิบายสั้นพร้อมลิงก์ไปหน้าความหมายเต็ม ใช้ดูดวงความรักและชีวิตได้ทุกใบ',
                'eyebrow': 'ทรัมป์ทั้ง 22 ใบ',
                'h1_html': 'ไพ่ชุด<em>เมเจอร์</em>',
                'lede': 'ไพ่ยี่สิบสองใบที่บันทึกการเดินทาง จากจุดเริ่มต้นอันใสซื่อ สู่การมาถึงที่หลอมรวมเป็นหนึ่ง แต่ละใบคืออาร์คีไทป์ จุดพักบนถนน และจังหวะที่ผู้แสวงต้องผ่าน ไม่ว่าจะตั้งใจหรือไม่',
                'intro': 'การเดินทางของไพ่ชุดเมเจอร์บางครั้งถูกเรียกว่า "การเดินทางของคนโง่" — ตัวตนหนุ่มสาวที่เปิดกว้าง ได้พบกับพลังต้นแบบของโลกเรียงตามลำดับ ถูกหล่อหลอมโดยพลังเหล่านั้น และมาถึงจุดสิ้นสุดในฐานะคนที่เปลี่ยนไปแล้ว เมื่อไพ่เมเจอร์ปรากฏในการอ่าน มันมีน้ำหนักมากกว่าไพ่ไมเนอร์ — คำถามกำลังสัมผัสบางอย่างที่เป็นโครงสร้าง',
                'list_heading': 'ไพ่ชุดเมเจอร์ทั้ง 22 ใบ',
            },
        },
        'card_filter': lambda c: c['arcana'] == 'major',
        'sort_key': lambda c: c['id'],
    },
    'minor-arcana': {
        'title_plain_en': 'The Minor Arcana',
        'title_plain_th': 'ไพ่ชุดไมเนอร์',
        'meta': {
            'en': {
                'title': 'The Minor Arcana — Four Suits, 56 Cards | Veila',
                'desc':  'The 56 Minor Arcana tarot cards across four suits: Cups, Wands, Swords, and Pentacles. Browse each suit and its fourteen cards.',
                'eyebrow': '56 Pip & Court Cards',
                'h1_html': 'The <em>Minor Arcana</em>',
                'lede': "If the Major Arcana names the big chapters of a life, the Minor Arcana names the days inside them. Four suits, fourteen cards each — pip cards Ace through Ten, plus the four courts.",
                'intro': "Each suit speaks to a different mode of being. Wands are fire (will, vocation), Cups are water (feeling, relationship), Swords are air (mind, conflict), and Pentacles are earth (body, craft, money). When a Minor appears in a reading, it answers in the texture of the everyday — concrete, situational, often actionable.",
                'list_heading': 'The Four Suits',
            },
            'th': {
                'title': 'ไพ่ไมเนอร์อาร์คานา 56 ใบ ความหมายไพ่ยิปซี 4 ชุด | Veila',
                'desc':  'ความหมายไพ่ยิปซีชุดไมเนอร์ทั้ง 56 ใบในสี่ชุด ถ้วย ไม้เท้า ดาบ และเหรียญ เลือกดูแต่ละชุดและไพ่สิบสี่ใบในชุดนั้น พร้อมลิงก์ไปบทอ่านเต็ม',
                'eyebrow': 'ไพ่พิพและไพ่ราชสำนัก 56 ใบ',
                'h1_html': 'ไพ่ชุด<em>ไมเนอร์</em>',
                'lede': 'ถ้าไพ่เมเจอร์บอกชื่อบทใหญ่ของชีวิต ไพ่ไมเนอร์บอกชื่อวันแต่ละวันในบทนั้น สี่ชุด ชุดละสิบสี่ใบ — ไพ่พิพ Ace ถึงสิบ บวกไพ่ราชสำนักอีกสี่',
                'intro': 'แต่ละชุดสะท้อนวิถีการเป็นอยู่ที่ต่างกัน ไม้เท้าคือไฟ (เจตจำนง อาชีพ) ถ้วยคือน้ำ (ความรู้สึก ความสัมพันธ์) ดาบคือลม (จิตใจ ความขัดแย้ง) เหรียญคือดิน (กาย งานฝีมือ เงิน) เมื่อไพ่ไมเนอร์ปรากฏ มันตอบในเนื้อสัมผัสของชีวิตประจำวัน — รูปธรรม เป็นสถานการณ์ และมักนำไปสู่การกระทำได้',
                'list_heading': 'สี่ชุดไพ่',
            },
        },
        'card_filter': None,  # special: lists suits not cards
        'is_suit_index': True,
    },
    'cups-tarot-meanings': {
        'title_plain_en': 'The Suit of Cups',
        'title_plain_th': 'ไพ่ชุดถ้วย',
        'meta': {
            'en': {
                'title': 'The Suit of Cups — All 14 Cups Tarot Card Meanings | Veila',
                'desc':  'The Suit of Cups in tarot — water, feeling, relationship. Meanings for all 14 Cups cards, Ace through King, with links to full readings.',
                'eyebrow': 'Water · Feeling · Relationship',
                'h1_html': 'The Suit of <em>Cups</em>',
                'lede': 'Cups are water — the element of feeling, intimacy, intuition, and what flows between people. When a Cup card lands, the question is usually emotional: who am I close to, what am I holding, what am I letting go of?',
                'intro': "Cups don't argue. They ask. They reveal the temperature of a relationship, the unspoken thing under a conversation, the longing or the disappointment that's coloring how a situation actually feels. Even the harshest Cup cards (Five of Cups, Three of Swords' cousin in feeling) are about grief, not punishment.",
                'list_heading': 'All 14 Cups Cards',
            },
            'th': {
                'title': 'ไพ่ถ้วย (Cups) 14 ใบ ความหมายไพ่ยิปซี ดูดวงความรัก | Veila',
                'desc':  'ไพ่ชุดถ้วยในไพ่ยิปซี — น้ำ ความรู้สึก ความสัมพันธ์ ความหมายไพ่ Cups ทั้ง 14 ใบที่เจอบ่อยเวลาดูดวงความรัก ตั้งแต่ Ace ถึง King พร้อมลิงก์ไปบทอ่านเต็ม',
                'eyebrow': 'น้ำ · ความรู้สึก · ความสัมพันธ์',
                'h1_html': 'ไพ่ชุด<em>ถ้วย</em>',
                'lede': 'ไพ่ชุดถ้วยคือธาตุน้ำ — ธาตุของความรู้สึก ความใกล้ชิด สัญชาตญาณ และสิ่งที่ไหลเวียนระหว่างผู้คน เมื่อไพ่ชุดถ้วยปรากฏ คำถามมักเป็นเรื่องอารมณ์ — ฉันใกล้ชิดกับใคร ฉันกำลังถืออะไรอยู่ ฉันกำลังปล่อยอะไรลงไป',
                'intro': 'ไพ่ชุดถ้วยไม่โต้แย้ง มันถาม มันเผยอุณหภูมิของความสัมพันธ์ สิ่งที่ไม่ได้พูดออกมาใต้บทสนทนา ความคิดถึงหรือความผิดหวังที่กำลังระบายสีให้สถานการณ์ แม้แต่ไพ่ชุดถ้วยที่ดูหนักที่สุดก็พูดถึงความเศร้า ไม่ใช่การลงโทษ',
                'list_heading': 'ไพ่ Cups ทั้ง 14 ใบ',
            },
        },
        'card_filter': lambda c: c['arcana'] == 'minor' and c['suit'] == 'cups',
        'sort_key': lambda c: c['id'],
    },
    'swords-tarot-meanings': {
        'title_plain_en': 'The Suit of Swords',
        'title_plain_th': 'ไพ่ชุดดาบ',
        'meta': {
            'en': {
                'title': 'The Suit of Swords — All 14 Swords Tarot Card Meanings | Veila',
                'desc':  'The Suit of Swords in tarot — air, mind, conflict. Meanings for all 14 Swords cards, Ace through King, with links to full readings.',
                'eyebrow': 'Air · Mind · Conflict',
                'h1_html': 'The Suit of <em>Swords</em>',
                'lede': 'Swords are air — the element of thought, language, conflict, and cutting clarity. They speak to what the mind is doing with a situation, often more than the situation itself.',
                'intro': "The Suit of Swords gets a reputation for being harsh, and many of its cards are. But Swords are not cruel — they are honest. Even at their bleakest (Three of Swords, Nine of Swords, Ten of Swords) they show you exactly what you already knew. The work of Swords is to face the truth cleanly, then act from it.",
                'list_heading': 'All 14 Swords Cards',
            },
            'th': {
                'title': 'ไพ่ดาบ (Swords) 14 ใบ ความหมายไพ่ยิปซี ครบทุกใบ | Veila',
                'desc':  'ไพ่ชุดดาบในไพ่ยิปซี — ลม จิตใจ ความขัดแย้ง ความหมายไพ่ Swords ทั้ง 14 ใบ ตั้งแต่ Ace ถึง King พร้อมลิงก์ไปบทอ่านเต็ม',
                'eyebrow': 'ลม · จิตใจ · ความขัดแย้ง',
                'h1_html': 'ไพ่ชุด<em>ดาบ</em>',
                'lede': 'ไพ่ชุดดาบคือธาตุลม — ธาตุของความคิด ภาษา ความขัดแย้ง และความคมชัดที่บาดผ่าน มันสะท้อนสิ่งที่จิตใจกำลังทำกับสถานการณ์ บ่อยครั้งมากกว่าตัวสถานการณ์เอง',
                'intro': 'ไพ่ชุดดาบมักถูกมองว่าโหดร้าย และหลายใบก็โหดจริง แต่ดาบไม่ใช่ความโหดร้าย — มันคือความซื่อตรง แม้ในจุดที่มืดที่สุด (Three of Swords, Nine of Swords, Ten of Swords) มันก็แสดงสิ่งที่คุณรู้อยู่แล้วอย่างชัดเจน หน้าที่ของดาบคือเผชิญความจริงอย่างสะอาด แล้วทำสิ่งที่ต้องทำจากตรงนั้น',
                'list_heading': 'ไพ่ Swords ทั้ง 14 ใบ',
            },
        },
        'card_filter': lambda c: c['arcana'] == 'minor' and c['suit'] == 'swords',
        'sort_key': lambda c: c['id'],
    },
    'wands-tarot-meanings': {
        'title_plain_en': 'The Suit of Wands',
        'title_plain_th': 'ไพ่ชุดไม้เท้า',
        'meta': {
            'en': {
                'title': 'The Suit of Wands — All 14 Wands Tarot Card Meanings | Veila',
                'desc':  'The Suit of Wands in tarot — fire, will, vocation. Meanings for all 14 Wands cards, Ace through King, with links to full readings.',
                'eyebrow': 'Fire · Will · Vocation',
                'h1_html': 'The Suit of <em>Wands</em>',
                'lede': "Wands are fire — the energy of will, ambition, vocation, and the creative spark. They speak to what you are driving toward and what is driving you.",
                'intro': "A Wand in a spread is rarely passive. The question is usually about initiative, momentum, or the heat of an undertaking. Wands ask you to either light something or admit the match is already in your hand.",
                'list_heading': 'All 14 Wands Cards',
            },
            'th': {
                'title': 'ไพ่ไม้เท้า (Wands) 14 ใบ ความหมายไพ่ยิปซี การงาน | Veila',
                'desc':  'ไพ่ชุดไม้เท้าในไพ่ยิปซี — ไฟ เจตจำนง อาชีพ ความหมายไพ่ Wands ทั้ง 14 ใบสำหรับดูดวงการงานและแรงขับในชีวิต ตั้งแต่ Ace ถึง King พร้อมลิงก์ไปบทอ่านเต็ม',
                'eyebrow': 'ไฟ · เจตจำนง · อาชีพ',
                'h1_html': 'ไพ่ชุด<em>ไม้เท้า</em>',
                'lede': 'ไพ่ชุดไม้เท้าคือธาตุไฟ — พลังของเจตจำนง ความทะเยอทะยาน อาชีพ และประกายความคิดสร้างสรรค์ มันสะท้อนสิ่งที่คุณกำลังขับเคลื่อนไป และสิ่งที่กำลังขับเคลื่อนคุณ',
                'intro': 'ไพ่ไม้เท้าในการอ่านไม่ค่อยนิ่งเฉย คำถามมักเกี่ยวกับการริเริ่ม โมเมนตัม หรือความร้อนแรงของภารกิจ ไม้เท้าขอให้คุณจุดบางสิ่ง หรือยอมรับว่าไม้ขีดอยู่ในมือคุณอยู่แล้ว',
                'list_heading': 'ไพ่ Wands ทั้ง 14 ใบ',
            },
        },
        'card_filter': lambda c: c['arcana'] == 'minor' and c['suit'] == 'wands',
        'sort_key': lambda c: c['id'],
    },
    'pentacles-tarot-meanings': {
        'title_plain_en': 'The Suit of Pentacles',
        'title_plain_th': 'ไพ่ชุดเหรียญ',
        'meta': {
            'en': {
                'title': 'The Suit of Pentacles — All 14 Pentacles Tarot Card Meanings | Veila',
                'desc':  'The Suit of Pentacles in tarot — earth, body, craft, money. Meanings for all 14 Pentacles cards, Ace through King, with links to full readings.',
                'eyebrow': 'Earth · Body · Craft · Money',
                'h1_html': 'The Suit of <em>Pentacles</em>',
                'lede': 'Pentacles are earth — the material plane. Body, home, craft, money, the slow accumulation of skill and resource.',
                'intro': "Pentacles often look unglamorous on the surface and turn out to be the most practically useful cards in the deck. They answer questions about livelihood, health, and the kind of patient work that compounds over years.",
                'list_heading': 'All 14 Pentacles Cards',
            },
            'th': {
                'title': 'ไพ่เหรียญ (Pentacles) 14 ใบ ความหมายไพ่ยิปซี การเงิน | Veila',
                'desc':  'ไพ่ชุดเหรียญในไพ่ยิปซี — ดิน กาย งานฝีมือ เงิน ความหมายไพ่ Pentacles ทั้ง 14 ใบสำหรับดูดวงการเงินและการงาน ตั้งแต่ Ace ถึง King พร้อมลิงก์ไปบทอ่านเต็ม',
                'eyebrow': 'ดิน · กาย · งานฝีมือ · เงิน',
                'h1_html': 'ไพ่ชุด<em>เหรียญ</em>',
                'lede': 'ไพ่ชุดเหรียญคือธาตุดิน — มิติของวัตถุ ร่างกาย บ้าน งานฝีมือ เงิน และการสะสมทักษะกับทรัพยากรอย่างช้าๆ',
                'intro': 'ไพ่เหรียญมักดูไม่หรูหราในตอนแรก แต่กลายเป็นไพ่ที่นำไปใช้ในชีวิตจริงได้มากที่สุดในสำรับ มันตอบคำถามเรื่องการดำรงชีพ สุขภาพ และงานที่ต้องอดทนนานปีจึงจะเห็นผลทบต้น',
                'list_heading': 'ไพ่ Pentacles ทั้ง 14 ใบ',
            },
        },
        'card_filter': lambda c: c['arcana'] == 'minor' and c['suit'] == 'pentacles',
        'sort_key': lambda c: c['id'],
    },
    'tarot-love-readings': {
        'title_plain_en': 'Tarot for Love & Relationships',
        'title_plain_th': 'ไพ่ทาโรต์เพื่อความรักและความสัมพันธ์',
        'meta': {
            'en': {
                'title': 'Tarot for Love & Relationships | Veila',
                'desc':  'How to use tarot for love questions — common cards in love readings, what they really mean, and which spread to use.',
                'eyebrow': 'For matters of the heart',
                'h1_html': 'Tarot for <em>Love & Relationships</em>',
                'lede': 'Tarot is a poor crystal ball and an unusually good mirror. For love questions, that distinction matters — the cards rarely tell you what someone else will do, but they read with surprising clarity what you are bringing to the room.',
                'intro': "When you sit with a love question, hold it specifically. Not 'will I find love?' but 'what am I carrying into this relationship?' or 'what is between us that needs naming?' The cards below come up often in love readings — not because they predict romance, but because each names a recognizable emotional posture.",
                'list_heading': 'Common cards in love readings',
                'spread_note_en': 'For a relationship question, the full Celtic Cross is the most thorough — its tenth position (Outcome) shows the tendency if the current pattern continues, while position 9 (Hopes & Fears) often reveals what you have been silent about.',
            },
            'th': {
                'title': 'ไพ่ทาโรต์เพื่อความรักและความสัมพันธ์ | Veila',
                'desc':  'วิธีใช้ไพ่ทาโรต์สำหรับคำถามเรื่องความรัก — ไพ่ที่มักปรากฏในบทอ่านความรัก ความหมายที่แท้จริง และผังที่เหมาะกับคำถามนี้',
                'eyebrow': 'สำหรับเรื่องของหัวใจ',
                'h1_html': 'ไพ่ทาโรต์เพื่อ<em>ความรัก</em>',
                'lede': 'ไพ่ทาโรต์เป็นลูกแก้วที่อ่อนแอ แต่เป็นกระจกที่ดีอย่างน่าประหลาดใจ สำหรับคำถามเรื่องความรัก ความต่างนี้สำคัญ — ไพ่ไม่ค่อยบอกสิ่งที่คนอื่นจะทำ แต่อ่านสิ่งที่คุณนำเข้ามาในห้องได้อย่างชัดเจนผิดคาด',
                'intro': 'เมื่อคุณนั่งลงกับคำถามเรื่องความรัก ตั้งคำถามให้เฉพาะเจาะจง ไม่ใช่ "ฉันจะเจอรักไหม" แต่เป็น "ฉันกำลังนำอะไรเข้ามาในความสัมพันธ์นี้" หรือ "ระหว่างเรามีอะไรที่ต้องการการเรียกชื่อ" ไพ่ด้านล่างมักปรากฏในบทอ่านความรัก ไม่ใช่เพราะมันทำนายความโรแมนติก แต่เพราะแต่ละใบเรียกชื่อท่าทีทางอารมณ์ที่จดจำได้',
                'list_heading': 'ไพ่ที่มักปรากฏในบทอ่านความรัก',
                'spread_note_en': '',
            },
        },
        'topical_key': 'love',
    },
    'career-tarot-reading': {
        'title_plain_en': 'Tarot for Career & Calling',
        'title_plain_th': 'ไพ่ทาโรต์เพื่อการงานและอาชีพ',
        'meta': {
            'en': {
                'title': 'Tarot for Career, Work & Calling | Veila',
                'desc':  'How to use tarot for career questions — common cards in career readings, what they mean for work, and which spread fits the question.',
                'eyebrow': 'For work & vocation',
                'h1_html': 'Tarot for <em>Career & Calling</em>',
                'lede': 'Career questions sit at the intersection of will, craft, and circumstance. Tarot is well-suited to that intersection — it names the thing you have been almost-saying about your work, and sometimes the thing the work has been almost-saying back.',
                'intro': "Use tarot when you are between two options, when a project has gone quiet, when the work has begun to feel either misaligned or like it is finally arriving. The cards below come up often in career readings — Magician, Emperor, Wheel — but the most informative ones are usually the Pentacles, which speak to craft, money, and the slow plate of real work.",
                'list_heading': 'Common cards in career readings',
            },
            'th': {
                'title': 'ไพ่ทาโรต์เพื่อการงานและอาชีพ | Veila',
                'desc':  'วิธีใช้ไพ่ทาโรต์สำหรับคำถามเรื่องอาชีพ — ไพ่ที่มักปรากฏในบทอ่านอาชีพ ความหมายในบริบทการงาน และผังที่เหมาะกับคำถามนั้น',
                'eyebrow': 'สำหรับการงานและอาชีพ',
                'h1_html': 'ไพ่ทาโรต์เพื่อ<em>การงาน</em>',
                'lede': 'คำถามเรื่องอาชีพอยู่ที่จุดตัดของเจตจำนง ฝีมือ และสภาพแวดล้อม ไพ่ทาโรต์เหมาะกับจุดตัดนี้ — มันเรียกชื่อสิ่งที่คุณเกือบจะพูดเกี่ยวกับงานของคุณ และบางครั้งสิ่งที่งานกำลังเกือบจะพูดตอบกลับ',
                'intro': 'ใช้ไพ่ทาโรต์เมื่อคุณอยู่ระหว่างสองทางเลือก เมื่อโปรเจกต์หนึ่งเงียบลง เมื่องานเริ่มรู้สึกไม่เข้าที่หรือกำลังลงตัวในที่สุด ไพ่ด้านล่างมักปรากฏในบทอ่านอาชีพ — Magician, Emperor, Wheel — แต่ไพ่ที่ให้ข้อมูลมากที่สุดมักเป็นไพ่ชุดเหรียญ ซึ่งพูดถึงงานฝีมือ เงิน และจานอันค่อยเป็นค่อยไปของงานจริง',
                'list_heading': 'ไพ่ที่มักปรากฏในบทอ่านอาชีพ',
            },
        },
        'topical_key': 'career',
    },
    'yes-no-tarot': {
        'title_plain_en': 'Yes/No Tarot Readings',
        'title_plain_th': 'ไพ่ทาโรต์ใช่/ไม่ใช่',
        'meta': {
            'en': {
                'title': 'Yes/No Tarot Readings — Method & Card List | Veila',
                'desc':  'How to do a yes/no tarot reading — single-card method, which cards lean yes and which lean no, and when to use a fuller spread instead.',
                'eyebrow': 'A simpler kind of question',
                'h1_html': 'Yes/No <em>Tarot Readings</em>',
                'lede': "Yes/no is the question tarot is least built for and most often asked. The cards trade in nuance, and a binary answer flattens them. But there is a method, and used well it returns surprisingly useful results — usually by reframing the question you actually meant.",
                'intro': "The method is simple: shuffle with the question in mind, draw a single card, and read its leaning. Upright cards tend toward yes; reversed cards tend toward no. Major Arcana yes/no answers carry more weight than Minor ones. If the card is ambiguous, the reading is also telling you something — that the situation itself isn't binary, and the question may need rewording.",
                'list_heading_yes': 'Cards that lean Yes',
                'list_heading_no':  'Cards that lean No',
            },
            'th': {
                'title': 'ไพ่ทาโรต์ใช่/ไม่ใช่ — วิธีและรายการไพ่ | Veila',
                'desc':  'วิธีอ่านไพ่ทาโรต์แบบใช่/ไม่ใช่ — วิธีเปิดใบเดียว ไพ่ที่เอนไปทางใช่ ไพ่ที่เอนไปทางไม่ใช่ และเมื่อไหร่ควรใช้ผังเต็มแทน',
                'eyebrow': 'คำถามแบบเรียบง่ายกว่า',
                'h1_html': 'ไพ่ทาโรต์<em>ใช่/ไม่ใช่</em>',
                'lede': 'ใช่/ไม่ใช่คือคำถามที่ไพ่ทาโรต์ไม่ได้ถูกสร้างมาให้ตอบที่สุด แต่กลับถูกถามมากที่สุด ไพ่ทำงานด้วยความละเอียดอ่อน คำตอบสองทางจึงทำให้มันแบนลง แต่ก็มีวิธี และเมื่อใช้ดี มันให้ผลที่มีประโยชน์น่าประหลาดใจ — มักด้วยการเปลี่ยนกรอบคำถามที่คุณตั้งใจถามจริงๆ',
                'intro': 'วิธีนั้นง่าย — สับไพ่พร้อมตั้งคำถามในใจ เปิดไพ่ใบเดียว และอ่านแนวโน้มของมัน ไพ่ตั้งตรงมักโน้มไปทางใช่ ไพ่กลับหัวมักโน้มไปทางไม่ใช่ ไพ่เมเจอร์มีน้ำหนักมากกว่าไพ่ไมเนอร์ ถ้าไพ่กำกวม การอ่านก็กำลังบอกอะไรคุณอยู่เช่นกัน — ว่าสถานการณ์ไม่ใช่เรื่องสองทาง และคำถามอาจต้องการการเรียบเรียงใหม่',
                'list_heading_yes': 'ไพ่ที่เอนไปทางใช่',
                'list_heading_no':  'ไพ่ที่เอนไปทางไม่ใช่',
            },
        },
        'is_yes_no': True,
    },
}


def hub_card_item(card, lang):
    name = card['name'][lang]
    rom = card['roman']
    kw = (card['upright'].get('keywords') or {}).get(lang, '') or ''
    return f'''      <li><a href="{card_path(card, lang)}">
        <div class="hcl-rom">{rom}</div>
        <div class="hcl-body">
          <div class="hcl-name">{escape(name)}</div>
          <div class="hcl-kw">{escape(kw)}</div>
        </div>
      </a></li>'''


def hub_suit_block(suit, lang):
    """Used by /minor-arcana/ to list the four suits."""
    suit_name = SUIT_EN[suit] if lang == 'en' else SUIT_TH[suit]
    href = hub_path(SUIT_HUB_SLUG[suit], lang)
    intros = {
        ('cups', 'en'):       'Water · feeling, intimacy, relationship.',
        ('cups', 'th'):       'น้ำ · ความรู้สึก ความใกล้ชิด ความสัมพันธ์',
        ('wands', 'en'):      'Fire · will, vocation, the creative spark.',
        ('wands', 'th'):      'ไฟ · เจตจำนง อาชีพ ประกายความคิดสร้างสรรค์',
        ('swords', 'en'):     'Air · mind, language, clarity, conflict.',
        ('swords', 'th'):     'ลม · จิตใจ ภาษา ความชัดเจน ความขัดแย้ง',
        ('pentacles', 'en'):  'Earth · body, craft, money, slow accumulation.',
        ('pentacles', 'th'):  'ดิน · กาย งานฝีมือ เงิน การสะสมแบบช้าๆ',
    }
    label = 'The Suit of' if lang == 'en' else 'ไพ่ชุด'
    if lang == 'en':
        full = f'{label} {suit_name}'
    else:
        full = f'{label}{suit_name}'
    return f'''      <li><a href="{href}">
        <div class="hcl-rom">14</div>
        <div class="hcl-body">
          <div class="hcl-name">{escape(full)}</div>
          <div class="hcl-kw">{escape(intros[(suit, lang)])}</div>
        </div>
      </a></li>'''


def render_yes_no_lists(lang, by_id):
    meta = HUB_DEFS['yes-no-tarot']['meta'][lang]
    yes_ids = TOPICAL_CARD_IDS['yes']
    no_ids = TOPICAL_CARD_IDS['no']
    yes_items = '\n'.join(hub_card_item(by_id[i], lang) for i in yes_ids if i in by_id)
    no_items = '\n'.join(hub_card_item(by_id[i], lang) for i in no_ids if i in by_id)
    return f'''  <section class="hub-cards">
    <h2>{escape(meta['list_heading_yes'])}</h2>
    <ol class="hub-card-list">
{yes_items}
    </ol>
  </section>

  <section class="hub-cards">
    <h2>{escape(meta['list_heading_no'])}</h2>
    <ol class="hub-card-list">
{no_items}
    </ol>
  </section>'''


def render_hub(slug, lang):
    spec = HUB_DEFS[slug]
    meta = spec['meta'][lang]
    en_path = hub_path(slug, 'en')
    th_path = hub_path(slug, 'th')
    canonical = en_path if lang == 'en' else th_path
    by_id = deck_by_id()

    crumbs = breadcrumb_for_hub(slug, lang)
    crumbs_jsonld = breadcrumb_jsonld(crumbs)
    article_jsonld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": meta['title'],
        "description": meta['desc'],
        "image": "https://veilatarot.com/og.png",
        "inLanguage": 'en-US' if lang == 'en' else 'th-TH',
        "datePublished": BUILD_DATE,
        "dateModified": BUILD_DATE,
        "publisher": {"@type": "Organization", "name": "Veila", "url": "https://veilatarot.com/"},
        "mainEntityOfPage": f"https://veilatarot.com{canonical}"
    }
    head = render_head_block(
        title=meta['title'], desc=meta['desc'],
        canonical=canonical, en_path=en_path, th_path=th_path, lang=lang,
        extra_jsonld=[article_jsonld, crumbs_jsonld]
    )

    # Body content
    meta_en = spec['meta']['en']
    meta_th = spec['meta']['th']
    body_html = f'''  {render_breadcrumb_html(crumbs)}
  {aeo_block(meta_en['title'], meta_th['title'], meta_en['lede'], meta_th['lede'], lang)}
  <div class="eyebrow">{escape(meta['eyebrow'])}</div>
  <h1 class="title">{meta['h1_html']}</h1>
  <p class="lede">{escape(meta['lede'])}</p>

  <div class="divider"><span class="line"></span><span class="mark"></span><span class="line"></span></div>

  <p>{escape(meta['intro'])}</p>'''

    if spec.get('is_yes_no'):
        body_html += '\n\n' + render_yes_no_lists(lang, by_id)
    elif spec.get('is_suit_index'):
        # /minor-arcana/ lists four suit hubs
        body_html += f'''

  <section class="hub-cards">
    <h2>{escape(meta['list_heading'])}</h2>
    <ol class="hub-card-list">
{chr(10).join(hub_suit_block(s, lang) for s in ('wands', 'cups', 'swords', 'pentacles'))}
    </ol>
  </section>'''
    elif 'topical_key' in spec:
        # /tarot-love-readings/, /career-tarot-reading/
        ids = TOPICAL_CARD_IDS[spec['topical_key']]
        items = '\n'.join(hub_card_item(by_id[i], lang) for i in ids if i in by_id)
        body_html += f'''

  <section class="hub-cards">
    <h2>{escape(meta['list_heading'])}</h2>
    <ol class="hub-card-list">
{items}
    </ol>
  </section>'''
        # On the TH hubs, append a section linking to the relevant scenario pages.
        if lang == 'th':
            topical_to_scenario = {'love': 'love', 'career': 'career'}
            target_cat = topical_to_scenario.get(spec['topical_key'])
            if target_cat:
                hub_scenarios = [s for s in TH_SCENARIOS if s['category'] == target_cat]
                if hub_scenarios:
                    scen_h2 = ('คำถามที่คนถามด้วยไพ่' if target_cat == 'love'
                               else 'คำถามเรื่องการงานที่คนถามด้วยไพ่')
                    scen_lede = ('บทใคร่ครวญสั้นๆ พร้อมผังการอ่านสามใบสำหรับสถานการณ์ที่พบบ่อย'
                                 if target_cat == 'love'
                                 else 'บทใคร่ครวญสำหรับจุดเปลี่ยนในการงาน')
                    scen_items = '\n'.join(
                        f'      <a href="/th/scenarios/{s["slug"]}/">'
                        f'<div class="rl-label">สถานการณ์</div>'
                        f'<div class="rl-name">{escape(s["title"])}</div>'
                        f'</a>'
                        for s in hub_scenarios
                    )
                    body_html += f'''

  <aside class="related-readings scenarios">
    <h2>{escape(scen_h2)}</h2>
    <p class="related-lede">{escape(scen_lede)}</p>
    <div class="related-grid">
{scen_items}
    </div>
  </aside>'''
    else:
        # Generic card listing (Major Arcana, four suit hubs)
        cards = [c for c in DECK if spec['card_filter'](c)]
        cards.sort(key=spec.get('sort_key', lambda c: c['id']))
        items = '\n'.join(hub_card_item(c, lang) for c in cards)
        body_html += f'''

  <section class="hub-cards">
    <h2>{escape(meta['list_heading'])}</h2>
    <ol class="hub-card-list">
{items}
    </ol>
  </section>'''

    # CTA row
    if lang == 'en':
        cta_main = 'Begin a Celtic Cross Reading'
        cta_about = 'About the Spread'
        cta_daily = 'Daily Card'
        app_href, celtic_href, daily_href = '/celtic-cross-reading/', '/celtic-cross-tarot/', '/daily-tarot-card/'
    else:
        cta_main = 'เริ่มอ่านเซลติกครอส'
        cta_about = 'เกี่ยวกับผังการอ่าน'
        cta_daily = 'ไพ่ประจำวัน'
        app_href, celtic_href, daily_href = '/th/celtic-cross-reading/', '/th/celtic-cross-tarot/', '/th/daily-tarot-card/'

    cta_html = f'''
  <div class="cta-row">
    <a href="{app_href}" class="cta-btn">{escape(cta_main)}</a>
    <a href="{celtic_href}" class="cta-btn ghost">{escape(cta_about)}</a>
    <a href="{daily_href}" class="cta-btn ghost">{escape(cta_daily)}</a>
  </div>'''

    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
{head}</head>
<body>

{render_header(en_path, th_path, lang)}

<main class="article hub-page">
{body_html}
{cta_html}
</main>

{render_footer(lang)}

<script src="/assets/chrome.js" defer></script>
</body>
</html>
'''

# ---------------------------------------------------------------------------
# HTML SITEMAP — /all-tarot-pages/
# ---------------------------------------------------------------------------

def _render_scenarios_section_th(list_block_fn):
    """The 10 TH emotional scenarios as a sub-section on /th/all-tarot-pages/."""
    items = [(f'/th/scenarios/{s["slug"]}/', s['title']) for s in TH_SCENARIOS]
    return f'''
  <section>
    <h2>บทใคร่ครวญ — สถานการณ์ทางอารมณ์</h2>
{list_block_fn(items)}
  </section>'''


def render_all_tarot_pages(lang):
    deck = sorted(DECK, key=lambda c: c['id'])
    majors = [c for c in deck if c['arcana'] == 'major']
    suits = {
        s: [c for c in deck if c.get('suit') == s]
        for s in ('wands', 'cups', 'swords', 'pentacles')
    }
    if lang == 'en':
        meta = {
            'title': 'All Veila Tarot Pages — Site Index | Veila',
            'desc':  'A complete directory of every page on Veila Tarot — hubs, the Celtic Cross guide, daily card, and all 78 card meaning pages.',
            'eyebrow': 'Site Index',
            'h1_html': 'All <em>Veila Tarot</em> Pages',
            'lede': 'A directory of everything on the site, grouped by area. Use this as a fast index when you know roughly what you are after.',
            'sec_practice': 'The Practice',
            'sec_hubs': 'Hubs',
            'sec_topical': 'Topical Reading Guides',
            'sec_major': 'Major Arcana — 22 Cards',
            'sec_minor': 'Minor Arcana — by Suit',
            'sec_utility': 'Utility',
            'utility_self': 'All Pages (this page)',
            'practice_begin': 'Begin a Celtic Cross Reading',
            'practice_daily': "Today's Daily Card",
            'practice_guide': 'The Celtic Cross — A Beginner\'s Guide',
            'hub_major':      'The Major Arcana — 22 Trumps',
            'hub_minor':      'The Minor Arcana — Overview',
            'hub_cups':       'The Suit of Cups (14)',
            'hub_swords':     'The Suit of Swords (14)',
            'hub_wands':      'The Suit of Wands (14)',
            'hub_pentacles':  'The Suit of Pentacles (14)',
            'hub_love':       'Tarot for Love & Relationships',
            'hub_career':     'Tarot for Career & Calling',
            'hub_yesno':      'Yes/No Tarot Readings',
        }
        link_prefix = ''
    else:
        meta = {
            'title': 'สารบัญ Veila — ดูดวงความรัก ไพ่ยิปซี ความหมายไพ่ 78 ใบ | Veila',
            'desc':  'สารบัญทุกหน้าใน Veila — ดูดวงความรัก ดูดวงการงาน ไพ่ยิปซีตามราศี คู่มือเซลติกครอส ไพ่ประจำวัน และความหมายไพ่ทั้ง 78 ใบ',
            'eyebrow': 'สารบัญเว็บไซต์',
            'h1_html': 'ทุกหน้าของ <em>Veila Tarot</em>',
            'lede': 'สารบัญทุกอย่างบนเว็บไซต์ จัดกลุ่มตามหมวด ใช้เป็นดัชนีอย่างรวดเร็วเมื่อรู้คร่าวๆ ว่ากำลังหาอะไร',
            'sec_practice': 'การฝึกปฏิบัติ',
            'sec_hubs': 'ฮับเนื้อหา',
            'sec_topical': 'คู่มือการอ่านตามหัวข้อ',
            'sec_major': 'ไพ่ชุดเมเจอร์ — 22 ใบ',
            'sec_minor': 'ไพ่ชุดไมเนอร์ — แยกตามชุด',
            'sec_utility': 'ยูทิลิตี',
            'utility_self': 'ทุกหน้า (หน้านี้)',
            'practice_begin': 'เริ่มอ่านเซลติกครอส',
            'practice_daily': 'ไพ่ประจำวันนี้',
            'practice_guide': 'เซลติกครอส — คู่มือสำหรับผู้เริ่มต้น',
            'hub_major':      'ไพ่ชุดเมเจอร์ — 22 ทรัมป์',
            'hub_minor':      'ไพ่ชุดไมเนอร์ — ภาพรวม',
            'hub_cups':       'ไพ่ชุดถ้วย (14)',
            'hub_swords':     'ไพ่ชุดดาบ (14)',
            'hub_wands':      'ไพ่ชุดไม้เท้า (14)',
            'hub_pentacles':  'ไพ่ชุดเหรียญ (14)',
            'hub_love':       'ไพ่ทาโรต์เพื่อความรัก',
            'hub_career':     'ไพ่ทาโรต์เพื่อการงาน',
            'hub_yesno':      'ไพ่ทาโรต์ใช่/ไม่ใช่',
        }
        link_prefix = '/th'

    def L(p):
        # Always use TH-prefixed link when lang=th
        return f'{link_prefix}{p}'

    def list_block(items):
        # items: list of (href, label) -> <ul class="all-list">
        lis = '\n'.join(
            f'      <li><a href="{href}">{escape(label)}</a></li>'
            for href, label in items
        )
        return f'    <ul class="all-list">\n{lis}\n    </ul>'

    def card_grid(cards):
        lis = '\n'.join(
            f'      <li><a href="{L(card_path(c, "en"))}">{escape(c["name"][lang])}</a></li>'
            for c in cards
        )
        return f'    <ul class="all-list cols">\n{lis}\n    </ul>'

    en_path = hub_path('all-tarot-pages', 'en')
    th_path_url = hub_path('all-tarot-pages', 'th')
    canonical = en_path if lang == 'en' else th_path_url

    crumbs = [
        home_crumb(lang),
        (('Site Index' if lang == 'en' else 'สารบัญเว็บไซต์'),
         f'https://veilatarot.com{canonical}'),
    ]
    article_jsonld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": meta['title'],
        "description": meta['desc'],
        "image": "https://veilatarot.com/og.png",
        "inLanguage": 'en-US' if lang == 'en' else 'th-TH',
        "datePublished": BUILD_DATE,
        "dateModified": BUILD_DATE,
        "publisher": {"@type": "Organization", "name": "Veila", "url": "https://veilatarot.com/"},
        "mainEntityOfPage": f"https://veilatarot.com{canonical}"
    }
    head = render_head_block(
        title=meta['title'], desc=meta['desc'],
        canonical=canonical, en_path=en_path, th_path=th_path_url, lang=lang,
        extra_jsonld=[article_jsonld, breadcrumb_jsonld(crumbs)]
    )

    body = f'''  {render_breadcrumb_html(crumbs)}
  <div class="eyebrow">{escape(meta['eyebrow'])}</div>
  <h1 class="title">{meta['h1_html']}</h1>
  <p class="lede">{escape(meta['lede'])}</p>

  <div class="divider"><span class="line"></span><span class="mark"></span><span class="line"></span></div>

  <section>
    <h2>{escape(meta['sec_practice'])}</h2>
{list_block([
    (L('/'), meta['practice_begin']),
    (L('/daily-tarot-card/'), meta['practice_daily']),
    (L('/celtic-cross-tarot/'), meta['practice_guide']),
])}
  </section>

  <section>
    <h2>{escape(meta['sec_hubs'])}</h2>
{list_block([
    (L('/major-arcana/'), meta['hub_major']),
    (L('/minor-arcana/'), meta['hub_minor']),
    (L('/cups-tarot-meanings/'), meta['hub_cups']),
    (L('/swords-tarot-meanings/'), meta['hub_swords']),
    (L('/wands-tarot-meanings/'), meta['hub_wands']),
    (L('/pentacles-tarot-meanings/'), meta['hub_pentacles']),
])}
  </section>

  <section>
    <h2>{escape(meta['sec_topical'])}</h2>
{list_block([
    (L('/tarot-love-readings/'), meta['hub_love']),
    (L('/career-tarot-reading/'), meta['hub_career']),
    (L('/yes-no-tarot/'), meta['hub_yesno']),
])}
  </section>

  <section>
    <h2>{escape(meta['sec_major'])}</h2>
{card_grid(majors)}
  </section>

  <section>
    <h2>{escape(meta['sec_minor'])}</h2>
    <h3>{escape(meta['hub_wands'])}</h3>
{card_grid(suits['wands'])}
    <h3>{escape(meta['hub_cups'])}</h3>
{card_grid(suits['cups'])}
    <h3>{escape(meta['hub_swords'])}</h3>
{card_grid(suits['swords'])}
    <h3>{escape(meta['hub_pentacles'])}</h3>
{card_grid(suits['pentacles'])}
  </section>

  <section>
    <h2>{escape(meta['sec_utility'])}</h2>
{list_block([
    (canonical, meta['utility_self']),
] + ([
    ('/th/about/', 'เกี่ยวกับ Veila'),
    ('/th/faq/', 'คำถามที่พบบ่อย'),
] if lang == 'th' else []))}
  </section>
{(_render_scenarios_section_th(list_block) if lang == 'th' else '')}'''

    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
{head}</head>
<body>

{render_header(en_path, th_path_url, lang)}

<main class="article">
{body}
</main>

{render_footer(lang)}

</body>
</html>
'''

# ---------------------------------------------------------------------------
# RSS FEED — /feed.xml
# ---------------------------------------------------------------------------

def build_feed():
    """RSS 2.0 feed of the homepage + 5 standalone evergreens + all 9 hubs."""
    items_data = [
        ('/', 'Veila Tarot — Begin a Celtic Cross Reading',
         'A quiet bilingual Celtic Cross tarot reading.'),
        ('/celtic-cross-tarot/',
         "The Celtic Cross Tarot Spread — A Beginner's Guide",
         "The most enduring ten-card tarot spread. History, position meanings, and how to read it."),
        ('/daily-tarot-card/',
         'Daily Tarot Card — A One-Card Practice',
         'One tarot card drawn fresh each day. A small, considered practice for reflection.'),
        ('/all-tarot-pages/',
         'All Veila Tarot Pages — Site Index',
         'A directory of every page on Veila Tarot, grouped by area.'),
        ('/th/about/',
         'เกี่ยวกับ Veila — ไพ่ทาโรต์เพื่อการใคร่ครวญ',
         'ปรัชญาของ Veila — บทอ่านไพ่ทาโรต์เซลติกครอสเพื่อการใคร่ครวญ ไม่ใช่การพยากรณ์'),
        ('/th/faq/',
         'คำถามที่พบบ่อย — ไพ่ทาโรต์เบื้องต้น',
         'คำตอบสำหรับคำถามที่คนเริ่มดูไพ่ทาโรต์มักถาม เช่น ไพ่ทาโรต์คืออะไร ต่างจากไพ่ยิปซีไหม ไพ่กลับหัวคืออะไร'),
    ]
    for slug in HUB_SLUGS:
        spec = HUB_DEFS[slug]
        items_data.append((
            f'/{slug}/',
            spec['meta']['en']['title'],
            spec['meta']['en']['desc'],
        ))

    items_xml = []
    for path, title, desc in items_data:
        url = f'https://veilatarot.com{path}'
        items_xml.append(
            f'    <item>\n'
            f'      <title>{escape(title)}</title>\n'
            f'      <link>{url}</link>\n'
            f'      <description>{escape(desc)}</description>\n'
            f'      <pubDate>{BUILD_DATE_RFC822}</pubDate>\n'
            f'      <guid isPermaLink="true">{url}</guid>\n'
            f'    </item>'
        )

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Veila Tarot</title>
    <link>https://veilatarot.com/</link>
    <description>A quiet bilingual Celtic Cross tarot reading.</description>
    <language>en</language>
    <lastBuildDate>{BUILD_DATE_RFC822}</lastBuildDate>
    <atom:link href="https://veilatarot.com/feed.xml" rel="self" type="application/rss+xml" />
{chr(10).join(items_xml)}
  </channel>
</rss>
'''

# ---------------------------------------------------------------------------
# SITEMAP
# ---------------------------------------------------------------------------

def build_sitemap(card_slugs):
    existing_meta = {}
    sitemap_path = ROOT / 'sitemap.xml'
    if sitemap_path.exists():
        existing_xml = sitemap_path.read_text(encoding='utf-8')
        for block in re.findall(r'<url>.*?</url>', existing_xml, flags=re.DOTALL):
            fields = {}
            for tag in ('loc', 'lastmod', 'changefreq', 'priority'):
                match = re.search(fr'<{tag}>(.*?)</{tag}>', block)
                if match:
                    fields[tag] = match.group(1)
            if 'loc' in fields:
                loc = fields['loc'].removeprefix('https://veilatarot.com')
                existing_meta[loc] = fields

    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']

    def url_block(loc, priority, changefreq, lastmod=None):
        saved = existing_meta.get(loc, {})
        lastmod = lastmod or saved.get('lastmod', BUILD_DATE)
        changefreq = saved.get('changefreq', changefreq)
        priority = saved.get('priority', priority)
        return (f'  <url>\n'
                f'    <loc>https://veilatarot.com{loc}</loc>\n'
                f'    <lastmod>{lastmod}</lastmod>\n'
                f'    <changefreq>{changefreq}</changefreq>\n'
                f'    <priority>{priority}</priority>\n'
                f'  </url>')

    for loc, priority, changefreq in STATIC_URLS:
        out.append(url_block(loc, priority, changefreq))
    for slug in HUB_SLUGS:
        out.append(url_block(f'/{slug}/', '0.7', 'monthly'))
        out.append(url_block(f'/th/{slug}/', '0.6', 'monthly'))
    for sl in card_slugs:
        out.append(url_block(f'/cards/{sl}/', '0.6', 'monthly'))
        out.append(url_block(f'/th/cards/{sl}/', '0.5', 'monthly'))
    # Standalone editorial/interactive trees maintained outside this generator.
    # Discover their existing index pages so a rebuild cannot silently drop them.
    additional_roots = (
        'guides', 'love-readings', 'quick-love-reading',
        'th/daily-love-tarot', 'th/love-tarot', 'th/zodiac-love-tarot',
    )
    for root_name in additional_roots:
        for index_path in sorted((ROOT / root_name).rglob('index.html')):
            rel_dir = index_path.parent.relative_to(ROOT).as_posix()
            out.append(url_block(f'/{rel_dir}/', '0.6', 'monthly'))
    # TH emotional scenarios
    for s in TH_SCENARIOS:
        out.append(url_block(f'/th/scenarios/{s["slug"]}/', '0.6', 'monthly', SCENARIO_MIGRATION_DATE))
    blocks = sorted(out[2:], key=lambda block: re.search(r'<loc>(.*?)</loc>', block).group(1))
    return '\n'.join(out[:2] + blocks + ['</urlset>']) + '\n'

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    # Ownership guard (2026-07-02): this script's templates are only current
    # for CARDS + the 9 HUB_SLUGS pages. Everything else it can emit is now
    # owned elsewhere and a full run would REGRESS live pages:
    #   th/scenarios/        -> build-quick-love-seo-pages.mjs (+ EN twin script)
    #   th/zodiac-love-tarot -> build-zodiac-love-tarot.mjs
    #   all-tarot-pages      -> hand-maintained (zodiac + EN scenarios sections)
    #   feed.xml             -> generate-feed.mjs
    #   sitemap.xml          -> generate-sitemap.py
    #   tarot-love-readings/ + career-tarot-reading/ (EN+TH) -> repurposed BY
    #       HAND 2026-06-26 as funnel articles (career CTAs); this template
    #       is stale for them and a regen REVERTS the funnel. Excluded below.
    cards_only = '--cards-only' in sys.argv
    force_full = '--force-full' in sys.argv
    if not cards_only and not force_full:
        print(__doc__)
        print('REFUSING to run without an explicit mode:')
        print('  --cards-only   regenerate cards + card hubs only (SAFE, the normal mode)')
        print('  --force-full   legacy full rebuild — REGRESSES scenarios/zodiac/'
              'all-tarot-pages/feed.xml/sitemap.xml (stale templates). Sandbox only.')
        sys.exit(1)
    if force_full:
        print('WARNING: --force-full rebuilds scenario/zodiac/all-tarot-pages/feed/'
              'sitemap from STALE templates. Never run this in the live tree.')

    deck = sorted(DECK, key=lambda c: c['id'])
    n = len(deck)

    # Clean previous output so removed cards/hubs leave no orphans.
    for path in [ROOT / 'cards', ROOT / 'th' / 'cards']:
        if path.exists():
            shutil.rmtree(path)
    hand_repurposed = {'tarot-love-readings', 'career-tarot-reading'}
    safe_hub_slugs = [s for s in HUB_SLUGS if s not in hand_repurposed]
    hub_slugs_to_build = safe_hub_slugs if cards_only else HUB_SLUGS
    cleanup_slugs = hub_slugs_to_build if cards_only else HUB_SLUGS + ['all-tarot-pages']
    for slug in cleanup_slugs:
        for path in [ROOT / slug, ROOT / 'th' / slug]:
            if path.exists():
                shutil.rmtree(path)

    # Cards
    print(f'Cards: writing {n} × 2 = {n * 2} pages...')
    slugs = []
    for i, card in enumerate(deck):
        prev_card = deck[(i - 1) % n]
        next_card = deck[(i + 1) % n]
        sl = card_slug(card)
        slugs.append(sl)
        for lang in LANGS:
            out_dir = (ROOT if lang == 'en' else ROOT / 'th') / 'cards' / sl
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / 'index.html').write_text(
                render_card(card, prev_card, next_card, lang), encoding='utf-8'
            )

    # Hubs
    print(f'Hubs:  writing {len(hub_slugs_to_build)} × 2 = {len(hub_slugs_to_build) * 2} pages...')
    for slug in hub_slugs_to_build:
        for lang in LANGS:
            out_dir = (ROOT if lang == 'en' else ROOT / 'th') / slug
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / 'index.html').write_text(render_hub(slug, lang), encoding='utf-8')

    if cards_only:
        print(f'  cards: {n * 2}')
        print(f'  hubs:  {len(hub_slugs_to_build) * 2} '
              f'(skipped hand-repurposed: {", ".join(sorted(hand_repurposed))})')
        print('--cards-only: skipped scenarios/zodiac/all-tarot-pages/feed.xml/'
              'sitemap.xml (owned elsewhere). Re-run generate-sitemap.py + '
              'generate-feed.mjs + generate-llms-full.mjs if card titles/descriptions changed.')
        return

    # TH emotional scenario pages
    scenarios_dir = ROOT / 'th' / 'scenarios'
    if scenarios_dir.exists():
        shutil.rmtree(scenarios_dir)
    print(f'Scenarios: writing {len(TH_SCENARIOS)} TH pages + compatibility redirects...')
    for s in TH_SCENARIOS:
        out_dir = scenarios_dir / s['slug']
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / 'index.html').write_text(render_scenario(s), encoding='utf-8')
        redirect_dir = scenarios_dir / s['legacy_slug']
        redirect_dir.mkdir(parents=True, exist_ok=True)
        (redirect_dir / 'index.html').write_text(render_scenario_redirect(s), encoding='utf-8')

    # Zodiac Hub and Pages
    zodiac_dir = ROOT / 'th' / 'zodiac-love-tarot'
    if zodiac_dir.exists():
        shutil.rmtree(zodiac_dir)
    print(f'Zodiac: writing {len(ZODIAC_DATA) + 1} TH pages...')
    zodiac_dir.mkdir(parents=True, exist_ok=True)
    (zodiac_dir / 'index.html').write_text(render_zodiac_hub(), encoding='utf-8')
    for slug, th_name in ZODIAC_DATA:
        out_dir = zodiac_dir / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / 'index.html').write_text(render_zodiac_page(slug, th_name), encoding='utf-8')

    # HTML sitemap (/all-tarot-pages/)
    for lang in LANGS:
        out_dir = (ROOT if lang == 'en' else ROOT / 'th') / 'all-tarot-pages'
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / 'index.html').write_text(render_all_tarot_pages(lang), encoding='utf-8')

    # RSS feed
    (ROOT / 'feed.xml').write_text(build_feed(), encoding='utf-8')

    # XML sitemap
    (ROOT / 'sitemap.xml').write_text(build_sitemap(slugs), encoding='utf-8')

    additional_sitemap_urls = sum(
        len(list((ROOT / root_name).rglob('index.html')))
        for root_name in (
            'guides', 'love-readings', 'quick-love-reading',
            'th/daily-love-tarot', 'th/love-tarot', 'th/zodiac-love-tarot',
        )
    )
    total_urls = (len(STATIC_URLS) + 2 * len(HUB_SLUGS) + 2 * n
                  + additional_sitemap_urls + len(TH_SCENARIOS))
    print(f'  cards: {n * 2}')
    print(f'  hubs:  {len(HUB_SLUGS) * 2}')
    print(f'  scenarios: {len(TH_SCENARIOS)}')
    print(f'  all-tarot-pages: 2')
    print(f'  feed.xml + sitemap.xml')
    print(f'  sitemap URLs: {total_urls}')


if __name__ == '__main__':
    main()
