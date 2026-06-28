import fs from 'fs';
import path from 'path';

const DATA_DIR = '/Users/kitikornrakhangthong/projects/veilatarot.com/assets/data/love-readings';
const TH_ARTICLE_PATH = '/Users/kitikornrakhangthong/projects/veilatarot.com/th/career-tarot-reading/index.html';

// 1. Fix typo in the article
if (fs.existsSync(TH_ARTICLE_PATH)) {
    let html = fs.readFileSync(TH_ARTICLE_PATH, 'utf-8');
    if (html.includes('จานอันค่อยเป็นค่อยไป')) {
        html = html.replace(/จานอันค่อยเป็นค่อยไป/g, 'จังหวะอันค่อยเป็นค่อยไป');
        fs.writeFileSync(TH_ARTICLE_PATH, html, 'utf-8');
        console.log('Fixed typo in TH article.');
    }
}

// 2. Fix AI tells in JSON
const files = fs.readdirSync(DATA_DIR).filter(f => f.endsWith('.json'));

let totalFixedMiKwam = 0;
let totalFixedDangNan = 0;

const nominalizationRegex = /มีความ(อ่อนโยน|อุดมสมบูรณ์|ปลอดภัย|ลึก|ใส่ใจ|เข้มแข็ง|ซื่อสัตย์|พร้อม|หนักอึ้ง|เหนื่อยล้า|กระวนกระวาย|โล่งใจ|เมตตา|หวาน|สบายใจ|ภาคภูมิใจ|หวงแหน|กล้า|เชื่อใจ|จริงใจ|สงบ|เข้าใจ|ใกล้ชิด)/g;

for (const file of files) {
    const filePath = path.join(DATA_DIR, file);
    let content = fs.readFileSync(filePath, 'utf-8');
    
    let originalContent = content;

    // Fix nominalization (มีความ + adj)
    content = content.replace(nominalizationRegex, '$1');
    const miKwamMatches = (originalContent.match(nominalizationRegex) || []).length;
    totalFixedMiKwam += miKwamMatches;

    // Fix connectors (ดังนั้น)
    const dangNanMatches = (content.match(/ดังนั้น/g) || []).length;
    content = content.replace(/ดังนั้น/g, ''); // Just remove it to make it sound native
    totalFixedDangNan += dangNanMatches;

    if (content !== originalContent) {
        fs.writeFileSync(filePath, content, 'utf-8');
        console.log(`Updated: ${file}`);
    }
}

console.log(`\nAudit & Fix Complete!`);
console.log(`- Removed "มีความ + adj": ${totalFixedMiKwam} instances`);
console.log(`- Removed "ดังนั้น": ${totalFixedDangNan} instances`);
