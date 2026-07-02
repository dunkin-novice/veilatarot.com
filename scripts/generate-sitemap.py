#!/usr/bin/env python3
"""Generate sitemap.xml for veilatarot.com.

- One <url> per directory containing index.html.
- lastmod = last git commit date of that page's index.html
  (fallback: file mtime for uncommitted/new files).
- Pages whose <head> carries a robots "noindex" are EXCLUDED
  (redirect stubs etc. must not appear in the sitemap).

Usage:
  python3 scripts/generate-sitemap.py            # writes sitemap.xml
  python3 scripts/generate-sitemap.py --out /tmp/sitemap-dry.xml   # dry run
"""
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
base_url = 'https://veilatarot.com/'

# Optional --out <path> for dry runs.
sitemap_path = os.path.join(project_dir, 'sitemap.xml')
if '--out' in sys.argv:
    sitemap_path = sys.argv[sys.argv.index('--out') + 1]

# ---------------------------------------------------------------------------
# Last-commit date per file, in ONE git call (walk the log newest-first and
# keep the first date seen for each path).
# ---------------------------------------------------------------------------
def git_lastmod_map():
    dates = {}
    try:
        out = subprocess.run(
            ['git', 'log', '--pretty=format:@%cI', '--name-only', '--', '.'],
            cwd=project_dir, capture_output=True, text=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return dates
    current = None
    for line in out.splitlines():
        if line.startswith('@'):
            current = line[1:]
        elif line and current and line not in dates:
            dates[line] = current
    return dates


def is_dirty(rel_file):
    """True if the file has uncommitted changes (or is untracked)."""
    try:
        out = subprocess.run(
            ['git', 'status', '--porcelain', '--', rel_file],
            cwd=project_dir, capture_output=True, text=True, check=True,
        ).stdout
        return bool(out.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return True


NOINDEX_RE = re.compile(
    r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex', re.I)


def head_has_noindex(path):
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            head = f.read(8192)
    except OSError:
        return False
    head = head.split('</head>')[0]
    if NOINDEX_RE.search(head):
        return True
    # Be safe: any literal "noindex" in the head (robots meta variants).
    return 'noindex' in head.lower()


git_dates = git_lastmod_map()

pages = []
skipped = []
for root, dirs, files in os.walk(project_dir):
    dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
    if 'index.html' not in files:
        continue
    rel_path = os.path.relpath(root, project_dir)
    index_file = os.path.join(root, 'index.html')
    rel_file = 'index.html' if rel_path == '.' else f'{rel_path}/index.html'

    if head_has_noindex(index_file):
        skipped.append(rel_file)
        continue

    url = base_url if rel_path == '.' else f'{base_url}{rel_path}/'

    # lastmod: git commit date; mtime for uncommitted/untracked changes.
    lastmod = None
    if rel_file in git_dates and not is_dirty(rel_file):
        lastmod = git_dates[rel_file][:10]           # YYYY-MM-DD from ISO8601
    else:
        mtime = os.path.getmtime(index_file)
        lastmod = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime('%Y-%m-%d')

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
    elif 'zodiac-love-tarot' in rel_path:
        # Monthly-refreshed pillar — keep changefreq monthly to signal freshness.
        priority = '0.7'
        changefreq = 'monthly'
    elif rel_path.startswith('th/'):
        priority = '0.6'

    pages.append({
        'loc': url,
        'lastmod': lastmod,
        'changefreq': changefreq,
        'priority': priority,
    })

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

print(f"Generated sitemap with {len(pages)} URLs at {sitemap_path}")
print(f"Skipped {len(skipped)} noindex pages:")
for s in skipped:
    print(f"  - {s}")
