/* Veila — Career & Money vertical question set (MVP).
   Same shape as assets/100-questions.js: { pillar, key, en, th }.
   pillars: decision | money | growth | fit | change
   money-pillar questions are tagged so a future /money/ split is a filter, not a rebuild.
   Ship ~15, hold the last 3 as buffer; scale winners via the same pipeline. */
const CAREER_QUESTIONS = [
  { "pillar": "decision", "key": "should-i-take-this-job",     "en": "Should I take this job?",                      "th": "ฉันควรรับงานนี้ไหม?" },
  { "pillar": "decision", "key": "should-i-quit",              "en": "Should I quit my job?",                        "th": "ฉันควรลาออกจากงานไหม?" },
  { "pillar": "fit",      "key": "is-this-career-right",       "en": "Is this career right for me?",                 "th": "เส้นทางอาชีพนี้ใช่สำหรับฉันไหม?" },
  { "pillar": "money",    "key": "am-i-underpaid",             "en": "Am I being underpaid or undervalued?",         "th": "ฉันกำลังถูกจ่ายน้อยหรือถูกมองข้ามคุณค่าอยู่ไหม?" },
  { "pillar": "money",    "key": "will-money-improve",         "en": "Will my finances improve?",                    "th": "การเงินของฉันจะดีขึ้นไหม?" },
  { "pillar": "money",    "key": "should-i-ask-for-a-raise",   "en": "Should I ask for a raise?",                    "th": "ฉันควรขอขึ้นเงินเดือนไหม?" },
  { "pillar": "change",   "key": "change-careers",             "en": "Should I change careers?",                     "th": "ฉันควรเปลี่ยนสายอาชีพไหม?" },
  { "pillar": "growth",   "key": "why-is-work-stuck",          "en": "Why does my work feel stuck?",                 "th": "ทำไมงานของฉันถึงรู้สึกหยุดนิ่ง?" },
  { "pillar": "growth",   "key": "whats-blocking-my-success",  "en": "What is blocking my success?",                 "th": "อะไรคือสิ่งที่ขวางความสำเร็จของฉัน?" },
  { "pillar": "decision", "key": "should-i-start-my-own-thing","en": "Should I start my own business?",              "th": "ฉันควรเริ่มต้นธุรกิจของตัวเองไหม?" },
  { "pillar": "decision", "key": "is-this-offer-good",         "en": "Is this offer right for me?",                  "th": "ข้อเสนอนี้ใช่สำหรับฉันไหม?" },
  { "pillar": "growth",   "key": "how-to-grow-here",           "en": "How do I grow in this role?",                  "th": "ฉันจะเติบโตในบทบาทนี้ได้อย่างไร?" },
  { "pillar": "fit",      "key": "are-they-valuing-me",        "en": "Does my workplace value me?",                  "th": "ที่ทำงานเห็นคุณค่าของฉันไหม?" },
  { "pillar": "decision", "key": "should-i-wait-or-move",      "en": "Should I wait, or make a move now?",           "th": "ฉันควรรอ หรือควรขยับตอนนี้?" },
  { "pillar": "fit",      "key": "what-is-my-calling",         "en": "What is my real calling?",                     "th": "อะไรคือเส้นทางที่ใช่ของฉันจริง ๆ?" },
  { "pillar": "money",    "key": "how-to-handle-money-fear",   "en": "How do I handle money anxiety?",               "th": "ฉันจะรับมือกับความกังวลเรื่องเงินได้อย่างไร?" },
  { "pillar": "growth",   "key": "will-this-project-land",     "en": "Will this project succeed?",                   "th": "โปรเจกต์นี้จะสำเร็จไหม?" },
  { "pillar": "change",   "key": "should-i-go-back-to-study",  "en": "Should I go back to study or retrain?",        "th": "ฉันควรกลับไปเรียนหรือฝึกทักษะใหม่ไหม?" }
];
if (typeof module !== 'undefined' && module.exports) module.exports = { CAREER_QUESTIONS };
