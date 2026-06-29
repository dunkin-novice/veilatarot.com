/* Veila — Zodiac Love Tarot pillar: shared sign + spread definitions.
   Imported by draw-zodiac-month.mjs (the monthly card draw) and
   build-zodiac-love-tarot.mjs (the page generator). Keep this the single
   source of truth for the 12 signs so the two scripts never drift. */

// Western zodiac, Thai ราศี names + glyphs + element. dates = EN/TH range string.
export const SIGNS = [
  { slug: 'aries',       glyph: '♈', en: 'Aries',       th: 'ราศีเมษ',   element: { en: 'Fire',  th: 'ไฟ' }, dates: { en: 'Mar 21 – Apr 19', th: '21 มี.ค. – 19 เม.ย.' } },
  { slug: 'taurus',      glyph: '♉', en: 'Taurus',      th: 'ราศีพฤษภ',  element: { en: 'Earth', th: 'ดิน' }, dates: { en: 'Apr 20 – May 20', th: '20 เม.ย. – 20 พ.ค.' } },
  { slug: 'gemini',      glyph: '♊', en: 'Gemini',      th: 'ราศีเมถุน',  element: { en: 'Air',   th: 'ลม' }, dates: { en: 'May 21 – Jun 20', th: '21 พ.ค. – 20 มิ.ย.' } },
  { slug: 'cancer',      glyph: '♋', en: 'Cancer',      th: 'ราศีกรกฎ',  element: { en: 'Water', th: 'น้ำ' }, dates: { en: 'Jun 21 – Jul 22', th: '21 มิ.ย. – 22 ก.ค.' } },
  { slug: 'leo',         glyph: '♌', en: 'Leo',         th: 'ราศีสิงห์',  element: { en: 'Fire',  th: 'ไฟ' }, dates: { en: 'Jul 23 – Aug 22', th: '23 ก.ค. – 22 ส.ค.' } },
  { slug: 'virgo',       glyph: '♍', en: 'Virgo',       th: 'ราศีกันย์',  element: { en: 'Earth', th: 'ดิน' }, dates: { en: 'Aug 23 – Sep 22', th: '23 ส.ค. – 22 ก.ย.' } },
  { slug: 'libra',       glyph: '♎', en: 'Libra',       th: 'ราศีตุล',   element: { en: 'Air',   th: 'ลม' }, dates: { en: 'Sep 23 – Oct 22', th: '23 ก.ย. – 22 ต.ค.' } },
  { slug: 'scorpio',     glyph: '♏', en: 'Scorpio',     th: 'ราศีพิจิก',  element: { en: 'Water', th: 'น้ำ' }, dates: { en: 'Oct 23 – Nov 21', th: '23 ต.ค. – 21 พ.ย.' } },
  { slug: 'sagittarius', glyph: '♐', en: 'Sagittarius', th: 'ราศีธนู',   element: { en: 'Fire',  th: 'ไฟ' }, dates: { en: 'Nov 22 – Dec 21', th: '22 พ.ย. – 21 ธ.ค.' } },
  { slug: 'capricorn',   glyph: '♑', en: 'Capricorn',   th: 'ราศีมังกร',  element: { en: 'Earth', th: 'ดิน' }, dates: { en: 'Dec 22 – Jan 19', th: '22 ธ.ค. – 19 ม.ค.' } },
  { slug: 'aquarius',    glyph: '♒', en: 'Aquarius',    th: 'ราศีกุมภ์',  element: { en: 'Air',   th: 'ลม' }, dates: { en: 'Jan 20 – Feb 18', th: '20 ม.ค. – 18 ก.พ.' } },
  { slug: 'pisces',      glyph: '♓', en: 'Pisces',      th: 'ราศีมีน',   element: { en: 'Water', th: 'น้ำ' }, dates: { en: 'Feb 19 – Mar 20', th: '19 ก.พ. – 20 มี.ค.' } }
]

// The fixed 3-position monthly love spread.
export const POSITIONS = [
  { key: 'heart_now',    label: { en: 'Where your heart stands now',     th: 'หัวใจคุณตอนนี้' } },
  { key: 'whats_moving', label: { en: 'What love is moving toward',       th: 'สิ่งที่ความรักกำลังเคลื่อนเข้าหา' } },
  { key: 'guidance',     label: { en: 'The cards’ guidance this month',   th: 'คำแนะนำของไพ่สำหรับเดือนนี้' } }
]

export const THAI_MONTHS = ['มกราคม','กุมภาพันธ์','มีนาคม','เมษายน','พฤษภาคม','มิถุนายน','กรกฎาคม','สิงหาคม','กันยายน','ตุลาคม','พฤศจิกายน','ธันวาคม']
export const EN_MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December']

export function monthLabels(monthKey) {
  // monthKey = 'YYYY-MM'
  const [y, m] = monthKey.split('-').map(Number)
  return { en: `${EN_MONTHS[m - 1]} ${y}`, th: `${THAI_MONTHS[m - 1]} ${y}` }
}
