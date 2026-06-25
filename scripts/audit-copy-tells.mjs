import fs from 'fs';
import path from 'path';

const files = ['cards.json'];
const loveReadings = fs.readdirSync('assets/data/love-readings').filter(f => f.endsWith('.json')).map(f => 'assets/data/love-readings/' + f);
files.push(...loveReadings);

const tellsTH = ['เหมียว', 'แมว', 'อุ้งเท้า', 'ขนฟู', 'ผลัดขน', 'ครางครือ'];
const regexEN = /\b(meow|purr|whisker|kitten|feline|catnip|paw|paws|furry|your fur|your tail|nine lives|cat|cats)\b/i;
const regexTH = new RegExp('(' + tellsTH.join('|') + ')');

let hasErrors = false;
let issues = [];

for (const file of files) {
  try {
    const data = JSON.parse(fs.readFileSync(file, 'utf8'));
    const items = Array.isArray(data) ? data : [data];
    
    function search(obj, pathStr) {
      if (typeof obj === 'string') {
        if (regexTH.test(obj)) {
          issues.push(`[TH] ${file} @ ${pathStr} - Found tell: "${obj}"`);
          hasErrors = true;
        }
        if (regexEN.test(obj)) {
          issues.push(`[EN] ${file} @ ${pathStr} - Found tell: "${obj}"`);
          hasErrors = true;
        }
      } else if (typeof obj === 'object' && obj !== null) {
        for (const k in obj) {
          search(obj[k], pathStr ? pathStr + '.' + k : k);
        }
      }
    }
    
    for (let i = 0; i < items.length; i++) {
      search(items[i], Array.isArray(data) ? '['+i+']' : '');
    }
  } catch (e) {
    console.error(`Error reading ${file}:`, e);
  }
}

if (hasErrors) {
  console.error('❌ VeilaTarot Cat-Residue Audit FAILED! Found the following cat-language slips:');
  issues.forEach(issue => console.error('  ' + issue));
  process.exit(1);
} else {
  console.log('✅ VeilaTarot Cat-Residue Audit passed. No cat-language slips found.');
  process.exit(0);
}
