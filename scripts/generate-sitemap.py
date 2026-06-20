import os
from datetime import datetime

project_dir = '/Users/kitikornrakhangthong/projects/veilatarot.com'
sitemap_path = os.path.join(project_dir, 'sitemap.xml')
base_url = 'https://veilatarot.com/'

# Get current date in YYYY-MM-DD
today = datetime.now().strftime('%Y-%m-%d')

# Get pages on disk
pages = []
for root, dirs, files in os.walk(project_dir):
    if 'index.html' in files:
        rel_path = os.path.relpath(root, project_dir)
        if rel_path == '.':
            url = base_url
        else:
            url = f"{base_url}{rel_path}/"
        
        # Priority and frequency logic
        priority = '0.5'
        changefreq = 'monthly'
        
        if rel_path == '.':
            priority = '1.0'
            changefreq = 'daily'
        elif 'celtic-cross-tarot' in rel_path:
            priority = '0.8'
        elif 'daily-tarot-card' in rel_path:
            priority = '0.8'
            changefreq = 'daily'
        elif 'love-readings' in rel_path:
            priority = '0.7'
        elif rel_path.startswith('th/'):
            priority = '0.6'
            
        pages.append({
            'loc': url,
            'lastmod': today,
            'changefreq': changefreq,
            'priority': priority
        })

# Sort pages by URL for consistency
pages.sort(key=lambda x: x['loc'])

sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

for page in pages:
    sitemap_content += '  <url>\n'
    sitemap_content += f"    <loc>{page['loc']}</loc>\n"
    sitemap_content += f"    <lastmod>{page['lastmod']}</lastmod>\n"
    sitemap_content += f"    <changefreq>{page['changefreq']}</changefreq>\n"
    sitemap_content += f"    <priority>{page['priority']}</priority>\n"
    sitemap_content += '  </url>\n'

sitemap_content += '</urlset>'

with open(sitemap_path, 'w', encoding='utf-8') as f:
    f.write(sitemap_content)

print(f"Generated sitemap.xml with {len(pages)} URLs at {sitemap_path}")
