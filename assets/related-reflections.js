/* Veila Related Reflections v1 — self-contained.
 *
 * Renders a "Related reflections" rail on every standard intent page in
 * /love-readings/* (NOT on the 5 subhub pages — those have their own
 * inline rail). Each rail shows two emotionally-adjacent intent pages,
 * one spread landing, and one cornerstone guide, picked deterministically
 * from RELATED below.
 *
 * Page-side wiring (one line each, no per-page hardcoding of links):
 *   <aside class="related-rail" data-related-source="<slug>"></aside>
 *   <script src="/assets/related-reflections.js" defer></script>
 *
 * Fires love_related_reflection_clicked on click via window.veilaFire
 * (the gtag bridge in /assets/analytics.js).
 *
 * Re-renders when the page toggles language by watching <html lang>.
 */
(function () {
  // ============================================================
  // CSS injection — runs once per document
  // ============================================================
  const CSS = `
.related-rail {
  border-top: 1px solid rgba(184,153,104,0.18);
  margin: 56px auto 0;
  padding: 36px 0 0;
  max-width: 720px;
}
.related-rail .rr-heading {
  font-family: "Cormorant Garamond", "IBM Plex Sans Thai", serif;
  font-weight: 400;
  color: #ebe4d4;
  font-size: 26px;
  line-height: 1.3;
  margin: 0 0 6px;
  text-align: left;
}
.related-rail .rr-lede {
  font-family: "Cormorant Garamond", "IBM Plex Sans Thai", serif;
  font-style: italic;
  color: #b9b3a4;
  font-size: 16px;
  line-height: 1.55;
  margin: 0 0 22px;
}
.related-rail .rr-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 12px;
}
.related-rail .rr-list a {
  display: block;
  border: 1px solid #7a6645;
  border-radius: 4px;
  padding: 14px 16px;
  background: rgba(184,153,104,0.04);
  text-decoration: none;
  transition: background 0.3s ease, border-color 0.3s ease;
}
.related-rail .rr-list a:hover,
.related-rail .rr-list a:focus-visible {
  background: rgba(184,153,104,0.09);
  border-color: #b89968;
}
.related-rail .rr-item-kind {
  font-family: "Inter", "IBM Plex Sans Thai", sans-serif;
  font-size: 10px;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: #b89968;
  margin-bottom: 6px;
}
.related-rail .rr-item-title {
  font-family: "Cormorant Garamond", "IBM Plex Sans Thai", serif;
  font-size: 17px;
  color: #ebe4d4;
  margin: 0 0 4px;
  font-weight: 400;
  line-height: 1.35;
}
.related-rail .rr-item-blurb {
  font-family: "Cormorant Garamond", "IBM Plex Sans Thai", serif;
  font-style: italic;
  color: #b9b3a4;
  line-height: 1.5;
  margin: 0;
  font-size: 14.5px;
}
html[lang="th"] .related-rail .rr-item-kind {
  letter-spacing: 0;
  text-transform: none;
}
html[lang="th"] .related-rail .rr-heading,
html[lang="th"] .related-rail .rr-item-title {
  font-family: "IBM Plex Sans Thai", serif;
}
html[lang="th"] .related-rail .rr-lede,
html[lang="th"] .related-rail .rr-item-blurb {
  font-family: "IBM Plex Sans Thai", serif;
  font-style: normal;
}
@media (max-width: 600px) {
  .related-rail { padding-top: 28px; margin-top: 36px; }
  .related-rail .rr-heading { font-size: 22px; }
  .related-rail .rr-lede { font-size: 15px; }
  .related-rail .rr-item-title { font-size: 16px; }
  .related-rail .rr-list a { padding: 12px 14px; }
}
`;
  if (!document.querySelector('style[data-veila-related]')) {
    const s = document.createElement('style');
    s.setAttribute('data-veila-related', '1');
    s.textContent = CSS;
    document.head.appendChild(s);
  }

  // ============================================================
  // Static labels (rail heading + lede + per-item "kind" tags)
  // ============================================================
  const LABELS = {
    en: {
      heading: 'Related reflections',
      lede: 'People sitting with this feeling also often ask…',
      kindIntent: 'A question to sit with',
      kindSpread: 'Another spread',
      kindGuide: 'A guide to read slowly'
    },
    th: {
      heading: 'บทใคร่ครวญที่เกี่ยวข้อง',
      lede: 'ผู้คนที่กำลังอยู่กับความรู้สึกแบบนี้ มักถามต่อว่า…',
      kindIntent: 'คำถามให้นั่งด้วย',
      kindSpread: 'บทอ่านอื่น',
      kindGuide: 'คู่มือให้อ่านช้าๆ'
    }
  };

  // ============================================================
  // TARGETS — every linkable destination (44 intent + 4 spread + 3 guide).
  // Compact one-line entries: { type, url, title{en,th}, blurb{en,th} }.
  // ============================================================
  // intent_page
  const I = (slug, ten, tth, ben, bth) => ({
    type: 'intent_page',
    url: '/love-readings/' + slug + '/',
    title: { en: ten, th: tth },
    blurb: { en: ben, th: bth }
  });
  // spread_landing_page
  const S = (slug, ten, tth, ben, bth) => ({
    type: 'spread_landing_page',
    url: '/quick-love-reading/' + slug + '/',
    title: { en: ten, th: tth },
    blurb: { en: ben, th: bth }
  });
  // guide_page
  const G = (slug, ten, tth, ben, bth) => ({
    type: 'guide_page',
    url: '/guides/' + slug + '/',
    title: { en: ten, th: tth },
    blurb: { en: ben, th: bth }
  });

  const TARGETS = {
    // ---- intent pages (44) ----
    'am-i-healing-or-just-distracting-myself': I('am-i-healing-or-just-distracting-myself',
      'Am I healing or just distracting myself?', 'เรากำลังเยียวยา หรือกำลังเบี่ยงเบนตัวเอง',
      'When the busyness might be honest, or might be the way you keep the quiet out.',
      'เมื่อความวุ่นวายอาจซื่อสัตย์ หรืออาจเป็นวิธีกันความเงียบเอาไว้'),
    'am-i-holding-on-or-listening-to-my-heart': I('am-i-holding-on-or-listening-to-my-heart',
      'Am I holding on or listening to my heart?', 'เรากำลังยึดติด หรือกำลังฟังหัวใจตัวเอง',
      'For when the difference between waiting and grasping is hard to feel from the inside.',
      'สำหรับเมื่อการรอกับการยึดติดรู้สึกแยกกันยากจากภายใน'),
    'are-they-confused-about-me': I('are-they-confused-about-me',
      'Are they confused about me?', 'เขางงเราอยู่ไหม',
      'Read mixed signals as the shape of the space between, not as their transcript.',
      'อ่านสัญญาณปนๆ ในฐานะรูปร่างของพื้นที่ระหว่างกัน ไม่ใช่บันทึกของเขา'),
    'are-they-waiting-for-me-to-reach-out': I('are-they-waiting-for-me-to-reach-out',
      'Are they waiting for me to reach out?', 'เขากำลังรอให้เราทักไปก่อนหรือเปล่า',
      'For the silence that could mean waiting, distance, or something quieter than either.',
      'สำหรับความเงียบที่อาจหมายถึงการรอ การห่าง หรืออะไรที่เงียบกว่านั้น'),
    'are-we-growing-apart': I('are-we-growing-apart',
      'Are we growing apart?', 'เรากำลังห่างไกลกันหรือเปล่า',
      'For the slow drift that has no event to point to but is still real.',
      'สำหรับการห่างช้าๆ ที่ไม่มีเหตุการณ์ให้ชี้ แต่ก็จริง'),
    'can-you-miss-someone-and-still-let-go': I('can-you-miss-someone-and-still-let-go',
      'Can you miss someone and still let go?', 'คิดถึงเขาแล้วยังปล่อยได้ไหม',
      'When the missing is real and the decision is also real at the same time.',
      'เมื่อการคิดถึงเป็นเรื่องจริง และการตัดสินใจก็เป็นเรื่องจริงพร้อมกัน'),
    'do-they-regret-losing-me': I('do-they-regret-losing-me',
      'Do they regret losing me?', 'เขาเสียดายที่เสียเราไปหรือเปล่า',
      'For when knowing whether they regret it would change something you have already begun to settle.',
      'สำหรับเมื่อการรู้ว่าเขาเสียดายหรือไม่จะเปลี่ยนสิ่งที่เราเริ่มทำใจไปแล้ว'),
    'do-they-still-think-about-me': I('do-they-still-think-about-me',
      'Do they still think about me?', 'เขายังคิดถึงเราอยู่ไหม',
      'Asked when the silence has its own gravity and you want to read what is in it.',
      'ถามเมื่อความเงียบมีน้ำหนักของมันเอง และคุณอยากอ่านสิ่งที่อยู่ในนั้น'),
    'does-he-miss-me': I('does-he-miss-me',
      'Does he miss me?', 'เขาคิดถึงเราไหม',
      'For the question that wants more than yes or no — the texture of how missing happens for them.',
      'สำหรับคำถามที่อยากได้มากกว่าใช่หรือไม่ — เนื้อหาของการคิดถึงในแบบของเขา'),
    'how-do-i-know-when-its-time-to-let-go': I('how-do-i-know-when-its-time-to-let-go',
      'How do I know when it is time to let go?', 'จะรู้ได้ยังไงว่าถึงเวลาปล่อยแล้ว',
      'For the moment that wants to be named, and the question of whether you are already there.',
      'สำหรับช่วงเวลาที่อยากถูกตั้งชื่อ และคำถามว่าคุณอยู่ตรงนั้นแล้วหรือยัง'),
    'how-do-i-stop-reopening-this-wound': I('how-do-i-stop-reopening-this-wound',
      'How do I stop reopening this wound?', 'จะหยุดเปิดแผลเดิมยังไง',
      'When you keep finding yourself back at the same hurt and want a gentler way out.',
      'เมื่อคุณกลับไปอยู่กับความเจ็บเดิม และอยากหาทางออกที่อ่อนโยนกว่า'),
    'is-there-still-something-between-us': I('is-there-still-something-between-us',
      'Is there still something between us?', 'ระหว่างเรายังมีอะไรเหลืออยู่ไหม',
      'For when the bond did not end clearly and you want to read what is actually still alive.',
      'สำหรับเมื่อความผูกพันไม่ได้จบชัด และคุณอยากอ่านสิ่งที่ยังมีชีวิตอยู่จริงๆ'),
    'is-this-just-attachment-or-love': I('is-this-just-attachment-or-love',
      'Is this just attachment or love?', 'นี่คือความผูกพันหรือความรัก',
      'For when the question itself is a sign that the two feel hard to separate right now.',
      'สำหรับเมื่อคำถามเองคือสัญญาณว่าทั้งสองแยกกันยากในตอนนี้'),
    'is-this-relationship-over': I('is-this-relationship-over',
      'Is this relationship over?', 'ความสัมพันธ์นี้จบแล้วหรือยัง',
      'For the question that wants to be answered honestly, not optimistically.',
      'สำหรับคำถามที่อยากได้คำตอบอย่างซื่อตรง ไม่ใช่อย่างมองโลกในแง่ดี'),
    'should-i-let-go': I('should-i-let-go',
      'Should I let go?', 'เราควรปล่อยไหม',
      'Asked when the question is whether the bond is asking to be put down.',
      'ถามเมื่อคำถามคือความผูกพันขอให้ถูกวางลงไหม'),
    'should-i-reach-out': I('should-i-reach-out',
      'Should I reach out?', 'ควรทักไปไหม',
      'For the message that has been half-written for days and the part of you that needs to know first.',
      'สำหรับข้อความที่เขียนค้างอยู่หลายวัน และส่วนของคุณที่อยากรู้ก่อน'),
    'what-am-i-still-hoping-for': I('what-am-i-still-hoping-for',
      'What am I still hoping for?', 'เรายังหวังอะไรอยู่กันแน่',
      'For naming the hope quietly, instead of arguing with it.',
      'สำหรับการเรียกชื่อความหวังอย่างเงียบๆ แทนการเถียงกับมัน'),
    'what-are-we-to-each-other': I('what-are-we-to-each-other',
      'What are we to each other?', 'เราเป็นอะไรกัน',
      'For the bond that has no obvious label and does not want to be forced into one.',
      'สำหรับความผูกพันที่ไม่มีคำเรียกชัด และไม่อยากถูกบังคับให้มีคำเรียก'),
    'what-changed-between-us': I('what-changed-between-us',
      'What changed between us?', 'อะไรเปลี่ยนไประหว่างเรา',
      'For the shift that has no single event, only a different feel.',
      'สำหรับการเปลี่ยนที่ไม่มีเหตุการณ์เดียว มีแต่ความรู้สึกที่ต่างไป'),
    'why-are-they-hot-and-cold': I('why-are-they-hot-and-cold',
      'Why are they hot and cold?', 'ทำไมเขาเดี๋ยวร้อนเดี๋ยวเย็น',
      'For reading their swings as the shape of what they cannot say, not what they will do.',
      'สำหรับอ่านอารมณ์ขึ้นลงในฐานะรูปร่างของสิ่งที่เขาพูดไม่ได้ ไม่ใช่สิ่งที่เขาจะทำ'),
    'why-cant-i-stop-thinking-about-them': I('why-cant-i-stop-thinking-about-them',
      'Why can\'t I stop thinking about them?', 'ทำไมถึงเลิกคิดถึงเขาไม่ได้',
      'For the loop the mind makes when something is not finished — not yet a sign of love, not yet a problem.',
      'สำหรับวงจรที่ใจสร้างเมื่อบางอย่างยังไม่จบ — ยังไม่ใช่สัญญาณของรัก ยังไม่ใช่ปัญหา'),
    'why-cant-we-let-each-other-go': I('why-cant-we-let-each-other-go',
      'Why can\'t we let each other go?', 'ทำไมเราถึงปล่อยกันไม่ได้',
      'For the mutual not-letting-go — when the bond becomes its own kind of relationship.',
      'สำหรับการไม่ปล่อยกันร่วม — เมื่อความผูกพันกลายเป็นความสัมพันธ์อีกแบบของมัน'),
    'why-did-they-pull-away': I('why-did-they-pull-away',
      'Why did they pull away?', 'ทำไมเขาถึงห่างไป',
      'For the moment that already happened and the meaning that is still arriving.',
      'สำหรับช่วงเวลาที่เกิดไปแล้ว และความหมายที่ยังกำลังมา'),
    'why-do-i-feel-attached-to-them': I('why-do-i-feel-attached-to-them',
      'Why do I feel so attached to them?', 'ทำไมเราถึงผูกพันกับเขามาก',
      'For when the attachment is louder than the situation seems to warrant.',
      'สำหรับเมื่อความผูกพันดังกว่าสิ่งที่สถานการณ์ดูเหมือนจะอธิบายได้'),
    'why-do-i-feel-them-even-after-no-contact': I('why-do-i-feel-them-even-after-no-contact',
      'Why do I feel them even after no contact?', 'ทำไมยังรู้สึกถึงเขาทั้งๆ ที่ไม่ได้ติดต่อกันแล้ว',
      'For the presence that lingers in the body even after the contact has stopped.',
      'สำหรับการมีอยู่ที่ยังค้างอยู่ในตัว แม้การติดต่อจะหยุดลงแล้ว'),
    'why-do-i-keep-going-back-to-them': I('why-do-i-keep-going-back-to-them',
      'Why do I keep going back to them?', 'ทำไมเราถึงกลับไปหาเขาซ้ำๆ',
      'For the return that has a logic of its own, even when the mind disagrees.',
      'สำหรับการกลับไปที่มีตรรกะของมันเอง แม้ใจจะไม่เห็นด้วย'),
    'why-do-i-still-miss-them': I('why-do-i-still-miss-them',
      'Why do I still miss them?', 'ทำไมถึงยังคิดถึงเขา',
      'When the missing has its own season, separate from the situation.',
      'เมื่อการคิดถึงมีฤดูของมันเอง แยกจากสถานการณ์'),
    'why-do-i-still-want-closure': I('why-do-i-still-want-closure',
      'Why do I still want closure?', 'ทำไมเรายังอยากได้การปิด',
      'For the wanting that does not need an answer from them in order to finish.',
      'สำหรับความอยากที่ไม่ต้องรอคำตอบจากเขาเพื่อจะจบ'),
    'why-do-old-feelings-keep-coming-back': I('why-do-old-feelings-keep-coming-back',
      'Why do old feelings keep coming back?', 'ทำไมความรู้สึกเก่าๆ ถึงกลับมาเรื่อยๆ',
      'For the return wave that does not mean you have failed at moving on.',
      'สำหรับคลื่นที่กลับมา ซึ่งไม่ได้แปลว่าคุณก้าวต่อล้มเหลว'),
    'why-do-they-come-back-when-i-pull-away': I('why-do-they-come-back-when-i-pull-away',
      'Why do they come back when I pull away?', 'ทำไมเขาถึงกลับมาตอนเราถอย',
      'For the pattern that has its own rhythm, separate from either of you choosing it.',
      'สำหรับรูปแบบที่มีจังหวะของมันเอง แยกจากการเลือกของทั้งสองฝ่าย'),
    'why-do-they-feel-distant': I('why-do-they-feel-distant',
      'Why do they feel distant?', 'ทำไมเขาถึงห่างเหินกับเรา',
      'For the distance that has not been named yet and may not be theirs alone.',
      'สำหรับระยะห่างที่ยังไม่ถูกตั้งชื่อ และอาจไม่ใช่ของเขาฝ่ายเดียว'),
    'why-do-they-keep-coming-back-into-my-life': I('why-do-they-keep-coming-back-into-my-life',
      'Why do they keep coming back into my life?', 'ทำไมเขาถึงกลับเข้ามาในชีวิตเราซ้ำๆ',
      'For the returning that may be theirs to do and yours to choose what to do with.',
      'สำหรับการกลับมาที่อาจเป็นของเขาที่ทำ และของคุณที่จะเลือกว่าจะทำอย่างไรกับมัน'),
    'why-do-we-keep-repeating-the-same-pattern': I('why-do-we-keep-repeating-the-same-pattern',
      'Why do we keep repeating the same pattern?', 'ทำไมเราถึงวนซ้ำรูปแบบเดิม',
      'For the loop the two of you keep ending up inside, without either of you choosing it.',
      'สำหรับวงจรที่ทั้งสองคนวนกลับเข้าไป โดยที่ไม่มีใครเลือก'),
    'why-does-it-feel-like-bad-timing': I('why-does-it-feel-like-bad-timing',
      'Why does it feel like bad timing?', 'ทำไมรู้สึกเหมือนผิดจังหวะเวลา',
      'For the question of whether timing is the obstacle or the gentlest way to name something else.',
      'สำหรับคำถามว่าจังหวะเวลาเป็นอุปสรรค หรือเป็นการเรียกชื่อสิ่งอื่นในแบบที่นุ่มที่สุด'),
    'why-does-moving-on-feel-so-hard': I('why-does-moving-on-feel-so-hard',
      'Why does moving on feel so hard?', 'ทำไมการก้าวต่อถึงยากนัก',
      'For the difficulty that is not a sign of weakness — it has its own shape worth reading.',
      'สำหรับความยากที่ไม่ใช่สัญญาณของความอ่อนแอ — มีรูปร่างของมันเองที่ควรอ่าน'),
    'why-does-seeing-them-again-change-everything': I('why-does-seeing-them-again-change-everything',
      'Why does seeing them again change everything?', 'ทำไมการเห็นเขาอีกครั้งเปลี่ยนทุกอย่าง',
      'For the way a single encounter can reorganise something you thought was settled.',
      'สำหรับวิธีที่การเจอกันครั้งเดียวจัดเรียงบางสิ่งที่คิดว่าเรียบร้อยแล้วใหม่'),
    'why-does-this-connection-feel-so-hard-to-explain': I('why-does-this-connection-feel-so-hard-to-explain',
      'Why does this connection feel so hard to explain?', 'ทำไมความสัมพันธ์นี้ถึงอธิบายยาก',
      'For the bond whose shape is its own language and resists translation.',
      'สำหรับความผูกพันที่รูปร่างเป็นภาษาของมันเอง และไม่ยอมถูกแปล'),
    'why-does-this-feel-so-intense': I('why-does-this-feel-so-intense',
      'Why does this feel so intense?', 'ทำไมความรู้สึกนี้ถึงรุนแรงนัก',
      'For the intensity that wants to be read for what it is, not labelled prematurely.',
      'สำหรับความรุนแรงที่อยากถูกอ่านในสิ่งที่มันเป็น ไม่ใช่ถูกตีตราเร็วเกินไป'),
    'why-does-this-relationship-feel-unclear': I('why-does-this-relationship-feel-unclear',
      'Why does this relationship feel unclear?', 'ทำไมความสัมพันธ์นี้ถึงรู้สึกไม่ชัด',
      'For the bond that has no clear label and may not want one yet.',
      'สำหรับความผูกพันที่ไม่มีคำเรียกชัด และอาจยังไม่อยากมี'),
    'why-does-this-relationship-still-have-a-hold-on-me': I('why-does-this-relationship-still-have-a-hold-on-me',
      'Why does this relationship still have a hold on me?', 'ทำไมความสัมพันธ์นี้ถึงยังมีอิทธิพลต่อเรา',
      'For when the hold is real and you want to understand its shape rather than blame yourself for it.',
      'สำหรับเมื่ออิทธิพลเป็นเรื่องจริง และคุณอยากเข้าใจรูปร่างของมันแทนที่จะโทษตัวเอง'),
    'why-does-this-still-hurt': I('why-does-this-still-hurt',
      'Why does this still hurt?', 'ทำไมเรื่องนี้ถึงยังเจ็บอยู่',
      'For the ache that is information, not failure to heal.',
      'สำหรับความเจ็บที่เป็นข้อมูล ไม่ใช่ความล้มเหลวในการเยียวยา'),
    'why-havent-they-contacted-me': I('why-havent-they-contacted-me',
      'Why haven\'t they contacted me?', 'ทำไมเขาถึงไม่ติดต่อมา',
      'For reading the silence as its own communication rather than as a verdict.',
      'สำหรับอ่านความเงียบในฐานะการสื่อสารของมันเอง ไม่ใช่คำตัดสิน'),
    'why-is-this-connection-confusing': I('why-is-this-connection-confusing',
      'Why is this connection confusing?', 'ทำไมความสัมพันธ์นี้ถึงสับสน',
      'For the confusion that is the bond\'s shape, not a problem to solve away.',
      'สำหรับความสับสนที่เป็นรูปร่างของความผูกพัน ไม่ใช่ปัญหาที่ต้องแก้ให้หาย'),
    'will-they-come-back': I('will-they-come-back',
      'Will they come back?', 'เขาจะกลับมาไหม',
      'For the question that wants more than yes or no — what coming back would even mean now.',
      'สำหรับคำถามที่อยากได้มากกว่าใช่หรือไม่ — การกลับมาจะหมายความว่ายังไงในตอนนี้'),

    // ---- spreads (4) ----
    'connection': S('connection',
      'Connection spread', 'บทอ่านเชื่อมโยง',
      'You, them, the space between — for bonds whose shape itself is the question.',
      'คุณ เขา และพื้นที่ระหว่างกัน — สำหรับความผูกพันที่รูปร่างเองคือคำถาม'),
    'emotional-arc': S('emotional-arc',
      'Emotional Arc spread', 'บทอ่านห้วงอารมณ์',
      'What shaped this, what is unfolding, what is changing — feelings across time.',
      'สิ่งที่ก่อตัว สิ่งที่กำลังเกิด สิ่งที่กำลังเปลี่ยน — ความรู้สึกข้ามเวลา'),
    'clarity': S('clarity',
      'Clarity spread', 'บทอ่านความชัดเจน',
      'What you know, what you avoid, what needs honesty — for decisions and inner conflict.',
      'สิ่งที่คุณรู้ สิ่งที่คุณหลีกเลี่ยง สิ่งที่ต้องการความซื่อตรง — สำหรับการตัดสินใจและความขัดแย้งภายใน'),
    'reconnection': S('reconnection',
      'Reconnection spread', 'บทอ่านเชื่อมโยงใหม่',
      'What still exists, what creates distance, what invites — bonds after silence or return.',
      'สิ่งที่ยังคงอยู่ สิ่งที่สร้างระยะ สิ่งที่เชื้อเชิญ — ความผูกพันหลังความเงียบหรือการกลับ'),

    // ---- guides (3) ----
    'how-to-ask-a-tarot-question': G('how-to-ask-a-tarot-question',
      'How to ask a tarot question', 'วิธีถามคำถามไพ่ทาโรต์',
      'Softening closed questions about another person\'s mind into ones the cards can meet.',
      'ทำคำถามปิดเกี่ยวกับใจของอีกคนให้นุ่มลง เพื่อให้ไพ่มีอะไรให้พบ'),
    'tarot-spreads-for-relationships': G('tarot-spreads-for-relationships',
      'Tarot spreads for relationships', 'บทอ่านไพ่ทาโรต์สำหรับความสัมพันธ์',
      'Why three cards, and how to choose the spread that matches your question.',
      'ทำไมสามใบ และเลือกบทอ่านที่ตรงคำถามของคุณยังไง'),
    'tarot-for-reflection': G('tarot-for-reflection',
      'Tarot for reflection', 'ไพ่ทาโรต์เพื่อใคร่ครวญ',
      'The practice — what reflective tarot is for, and what it is not for.',
      'การฝึก — ไพ่ทาโรต์ชวนใคร่ครวญมีไว้เพื่ออะไร และไม่ใช่เพื่ออะไร')
  };

  // ============================================================
  // RELATED — per-source picks: [intentA, intentB, spread, guide].
  // Self-links forbidden; enforced by an assertion at the bottom of the
  // file during init. Picks are emotional adjacency, not keyword match.
  // ============================================================
  const RELATED = {
    // Cluster A — Self-inquiry / healing (clarity + tarot-for-reflection)
    'am-i-healing-or-just-distracting-myself':         ['am-i-holding-on-or-listening-to-my-heart', 'why-does-moving-on-feel-so-hard', 'clarity', 'tarot-for-reflection'],
    'am-i-holding-on-or-listening-to-my-heart':        ['am-i-healing-or-just-distracting-myself', 'why-does-this-still-hurt', 'clarity', 'tarot-for-reflection'],
    'how-do-i-stop-reopening-this-wound':              ['why-does-this-still-hurt', 'why-do-old-feelings-keep-coming-back', 'clarity', 'tarot-for-reflection'],
    'why-does-this-still-hurt':                        ['how-do-i-stop-reopening-this-wound', 'why-does-moving-on-feel-so-hard', 'clarity', 'tarot-for-reflection'],
    'why-does-moving-on-feel-so-hard':                 ['why-cant-i-stop-thinking-about-them', 'am-i-holding-on-or-listening-to-my-heart', 'clarity', 'tarot-for-reflection'],

    // Cluster B — Letting go / should I (clarity + how-to-ask-a-tarot-question)
    'should-i-let-go':                                 ['how-do-i-know-when-its-time-to-let-go', 'can-you-miss-someone-and-still-let-go', 'clarity', 'how-to-ask-a-tarot-question'],
    'how-do-i-know-when-its-time-to-let-go':           ['should-i-let-go', 'is-this-relationship-over', 'clarity', 'how-to-ask-a-tarot-question'],
    'can-you-miss-someone-and-still-let-go':           ['should-i-let-go', 'why-do-i-still-miss-them', 'clarity', 'how-to-ask-a-tarot-question'],
    'why-do-i-still-want-closure':                     ['should-i-let-go', 'how-do-i-know-when-its-time-to-let-go', 'clarity', 'how-to-ask-a-tarot-question'],
    'is-this-relationship-over':                       ['are-we-growing-apart', 'how-do-i-know-when-its-time-to-let-go', 'clarity', 'how-to-ask-a-tarot-question'],

    // Cluster C — Attachment / still holding (emotional-arc + tarot-for-reflection)
    'is-this-just-attachment-or-love':                 ['why-do-i-feel-attached-to-them', 'what-am-i-still-hoping-for', 'emotional-arc', 'tarot-for-reflection'],
    'what-am-i-still-hoping-for':                      ['why-cant-i-stop-thinking-about-them', 'why-do-old-feelings-keep-coming-back', 'emotional-arc', 'tarot-for-reflection'],
    'why-cant-i-stop-thinking-about-them':             ['why-do-i-still-miss-them', 'what-am-i-still-hoping-for', 'emotional-arc', 'tarot-for-reflection'],
    'why-do-i-feel-attached-to-them':                  ['why-do-i-keep-going-back-to-them', 'is-this-just-attachment-or-love', 'emotional-arc', 'tarot-for-reflection'],
    'why-do-i-keep-going-back-to-them':                ['why-do-i-feel-attached-to-them', 'why-cant-we-let-each-other-go', 'emotional-arc', 'tarot-for-reflection'],
    'why-do-i-still-miss-them':                        ['can-you-miss-someone-and-still-let-go', 'why-cant-i-stop-thinking-about-them', 'emotional-arc', 'tarot-for-reflection'],
    'why-do-old-feelings-keep-coming-back':            ['why-does-this-relationship-still-have-a-hold-on-me', 'what-am-i-still-hoping-for', 'emotional-arc', 'tarot-for-reflection'],
    'why-does-this-relationship-still-have-a-hold-on-me': ['why-cant-we-let-each-other-go', 'why-do-old-feelings-keep-coming-back', 'emotional-arc', 'tarot-for-reflection'],
    'why-cant-we-let-each-other-go':                   ['why-do-i-keep-going-back-to-them', 'why-does-this-relationship-still-have-a-hold-on-me', 'emotional-arc', 'tarot-for-reflection'],

    // Cluster D — Their signals (connection + how-to-ask-a-tarot-question)
    'are-they-confused-about-me':                      ['why-are-they-hot-and-cold', 'why-do-they-feel-distant', 'connection', 'how-to-ask-a-tarot-question'],
    'are-they-waiting-for-me-to-reach-out':            ['should-i-reach-out', 'why-havent-they-contacted-me', 'connection', 'how-to-ask-a-tarot-question'],
    'do-they-still-think-about-me':                    ['does-he-miss-me', 'do-they-regret-losing-me', 'connection', 'how-to-ask-a-tarot-question'],
    'does-he-miss-me':                                 ['do-they-still-think-about-me', 'do-they-regret-losing-me', 'connection', 'how-to-ask-a-tarot-question'],
    'do-they-regret-losing-me':                        ['does-he-miss-me', 'do-they-still-think-about-me', 'connection', 'how-to-ask-a-tarot-question'],
    'why-are-they-hot-and-cold':                       ['why-do-they-feel-distant', 'why-did-they-pull-away', 'connection', 'how-to-ask-a-tarot-question'],
    'why-did-they-pull-away':                          ['why-do-they-feel-distant', 'why-are-they-hot-and-cold', 'connection', 'how-to-ask-a-tarot-question'],
    'why-do-they-feel-distant':                        ['why-did-they-pull-away', 'why-are-they-hot-and-cold', 'connection', 'how-to-ask-a-tarot-question'],
    'why-havent-they-contacted-me':                    ['are-they-waiting-for-me-to-reach-out', 'why-do-they-feel-distant', 'connection', 'how-to-ask-a-tarot-question'],
    'why-do-they-come-back-when-i-pull-away':          ['why-do-they-keep-coming-back-into-my-life', 'why-are-they-hot-and-cold', 'connection', 'how-to-ask-a-tarot-question'],
    'why-do-they-keep-coming-back-into-my-life':       ['why-do-they-come-back-when-i-pull-away', 'will-they-come-back', 'connection', 'how-to-ask-a-tarot-question'],

    // Cluster E — What is this (connection + tarot-spreads-for-relationships)
    'what-are-we-to-each-other':                       ['is-there-still-something-between-us', 'why-does-this-relationship-feel-unclear', 'connection', 'tarot-spreads-for-relationships'],
    'is-there-still-something-between-us':             ['what-are-we-to-each-other', 'why-is-this-connection-confusing', 'connection', 'tarot-spreads-for-relationships'],
    'why-is-this-connection-confusing':                ['why-does-this-relationship-feel-unclear', 'why-does-this-connection-feel-so-hard-to-explain', 'connection', 'tarot-spreads-for-relationships'],
    'why-does-this-connection-feel-so-hard-to-explain':['why-is-this-connection-confusing', 'why-does-this-feel-so-intense', 'connection', 'tarot-spreads-for-relationships'],
    'why-does-this-relationship-feel-unclear':         ['what-are-we-to-each-other', 'why-is-this-connection-confusing', 'connection', 'tarot-spreads-for-relationships'],
    'why-does-this-feel-so-intense':                   ['why-does-this-connection-feel-so-hard-to-explain', 'why-cant-i-stop-thinking-about-them', 'connection', 'tarot-spreads-for-relationships'],

    // Cluster F — Relationship change (emotional-arc + tarot-spreads-for-relationships)
    'are-we-growing-apart':                            ['what-changed-between-us', 'is-this-relationship-over', 'emotional-arc', 'tarot-spreads-for-relationships'],
    'what-changed-between-us':                         ['are-we-growing-apart', 'why-do-we-keep-repeating-the-same-pattern', 'emotional-arc', 'tarot-spreads-for-relationships'],
    'why-do-we-keep-repeating-the-same-pattern':       ['what-changed-between-us', 'why-does-it-feel-like-bad-timing', 'emotional-arc', 'tarot-spreads-for-relationships'],
    'why-does-it-feel-like-bad-timing':                ['what-changed-between-us', 'why-do-we-keep-repeating-the-same-pattern', 'emotional-arc', 'tarot-spreads-for-relationships'],

    // Cluster G — Contact (reconnection + how-to-ask-a-tarot-question)
    'should-i-reach-out':                              ['are-they-waiting-for-me-to-reach-out', 'why-havent-they-contacted-me', 'reconnection', 'how-to-ask-a-tarot-question'],
    'why-do-i-feel-them-even-after-no-contact':        ['why-cant-i-stop-thinking-about-them', 'why-do-i-still-miss-them', 'reconnection', 'how-to-ask-a-tarot-question'],

    // Cluster H — Reconnection / coming back (reconnection + tarot-spreads-for-relationships)
    'will-they-come-back':                             ['why-do-they-keep-coming-back-into-my-life', 'why-does-seeing-them-again-change-everything', 'reconnection', 'tarot-spreads-for-relationships'],
    'why-does-seeing-them-again-change-everything':    ['will-they-come-back', 'why-do-they-keep-coming-back-into-my-life', 'reconnection', 'tarot-spreads-for-relationships']
  };

  // ============================================================
  // SOURCE_SPREAD_MODE — feeds the spread_mode param on analytics
  // events. Mirrors each source's primary RECOMMENDED_MODE so cluster
  // segmentation is stable across pages.
  // ============================================================
  const SOURCE_SPREAD_MODE = {
    'am-i-healing-or-just-distracting-myself':         'clarity',
    'am-i-holding-on-or-listening-to-my-heart':        'clarity',
    'how-do-i-stop-reopening-this-wound':              'clarity',
    'why-does-this-still-hurt':                        'clarity',
    'why-does-moving-on-feel-so-hard':                 'clarity',
    'should-i-let-go':                                 'clarity',
    'how-do-i-know-when-its-time-to-let-go':           'clarity',
    'can-you-miss-someone-and-still-let-go':           'clarity',
    'why-do-i-still-want-closure':                     'clarity',
    'is-this-relationship-over':                       'clarity',
    'is-this-just-attachment-or-love':                 'emotional-arc',
    'what-am-i-still-hoping-for':                      'emotional-arc',
    'why-cant-i-stop-thinking-about-them':             'emotional-arc',
    'why-do-i-feel-attached-to-them':                  'emotional-arc',
    'why-do-i-keep-going-back-to-them':                'emotional-arc',
    'why-do-i-still-miss-them':                        'emotional-arc',
    'why-do-old-feelings-keep-coming-back':            'emotional-arc',
    'why-does-this-relationship-still-have-a-hold-on-me': 'emotional-arc',
    'why-cant-we-let-each-other-go':                   'emotional-arc',
    'are-they-confused-about-me':                      'connection',
    'are-they-waiting-for-me-to-reach-out':            'connection',
    'do-they-still-think-about-me':                    'connection',
    'does-he-miss-me':                                 'connection',
    'do-they-regret-losing-me':                        'connection',
    'why-are-they-hot-and-cold':                       'connection',
    'why-did-they-pull-away':                          'connection',
    'why-do-they-feel-distant':                        'connection',
    'why-havent-they-contacted-me':                    'connection',
    'why-do-they-come-back-when-i-pull-away':          'connection',
    'why-do-they-keep-coming-back-into-my-life':       'connection',
    'what-are-we-to-each-other':                       'connection',
    'is-there-still-something-between-us':             'connection',
    'why-is-this-connection-confusing':                'connection',
    'why-does-this-connection-feel-so-hard-to-explain':'connection',
    'why-does-this-relationship-feel-unclear':         'connection',
    'why-does-this-feel-so-intense':                   'connection',
    'are-we-growing-apart':                            'emotional-arc',
    'what-changed-between-us':                         'emotional-arc',
    'why-do-we-keep-repeating-the-same-pattern':       'emotional-arc',
    'why-does-it-feel-like-bad-timing':                'emotional-arc',
    'should-i-reach-out':                              'reconnection',
    'why-do-i-feel-them-even-after-no-contact':        'reconnection',
    'will-they-come-back':                             'reconnection',
    'why-does-seeing-them-again-change-everything':    'reconnection'
  };

  // ============================================================
  // Render — populates one rail from its data-related-source slug.
  // Safe to call repeatedly (lang toggle, late-mounted DOM).
  // ============================================================
  function render(rail) {
    const source = rail.getAttribute('data-related-source');
    if (!source) return;
    const picks = RELATED[source];
    if (!picks) return;
    const lang = document.documentElement.lang === 'th' ? 'th' : 'en';
    const labels = LABELS[lang];
    const sourceMode = SOURCE_SPREAD_MODE[source] || '';

    rail.setAttribute('aria-labelledby', 'rr-h-' + source);
    rail.innerHTML = ''
      + '<h2 class="rr-heading" id="rr-h-' + source + '"></h2>'
      + '<p class="rr-lede"></p>'
      + '<ol class="rr-list"></ol>';
    rail.querySelector('.rr-heading').textContent = labels.heading;
    rail.querySelector('.rr-lede').textContent = labels.lede;

    const list = rail.querySelector('.rr-list');
    picks.forEach((slug) => {
      if (slug === source) return; // never self-link
      const t = TARGETS[slug];
      if (!t) return;
      const kindLabel = t.type === 'intent_page'
        ? labels.kindIntent
        : t.type === 'spread_landing_page'
          ? labels.kindSpread
          : labels.kindGuide;
      const title = (t.title && t.title[lang]) || (t.title && t.title.en) || slug;
      const blurb = (t.blurb && t.blurb[lang]) || (t.blurb && t.blurb.en) || '';

      const li = document.createElement('li');
      const a  = document.createElement('a');
      a.href = t.url;
      a.setAttribute('data-target-slug', slug);
      a.setAttribute('data-target-type', t.type);
      a.innerHTML = ''
        + '<div class="rr-item-kind"></div>'
        + '<div class="rr-item-title"></div>'
        + '<p class="rr-item-blurb"></p>';
      a.querySelector('.rr-item-kind').textContent = kindLabel;
      a.querySelector('.rr-item-title').textContent = title;
      a.querySelector('.rr-item-blurb').textContent = blurb;
      a.addEventListener('click', () => {
        if (typeof window.veilaFire === 'function') {
          try {
            window.veilaFire('love_related_reflection_clicked', {
              source_page_type: 'intent_page',
              target_page_type: t.type,
              source_slug: source,
              target_slug: slug,
              spread_mode: sourceMode,
              lang: document.documentElement.lang === 'th' ? 'th' : 'en'
            });
          } catch (e) {}
        }
      });
      li.appendChild(a);
      list.appendChild(li);
    });
  }

  // ============================================================
  // Init — find every rail, render, watch <html lang> for toggles.
  // ============================================================
  function init() {
    const rails = document.querySelectorAll('aside.related-rail[data-related-source]');
    if (!rails.length) return;
    rails.forEach(render);

    const obs = new MutationObserver((muts) => {
      for (const m of muts) {
        if (m.type === 'attributes' && m.attributeName === 'lang') {
          rails.forEach(render);
          return;
        }
      }
    });
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
