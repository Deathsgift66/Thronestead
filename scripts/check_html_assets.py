import os
import re

# Files that are partials and intentionally lack assets
SKIP = {'navbar.html', os.path.join('public', 'navbar.html')}

missing = []

for filename in sorted(os.listdir('.')):
    if not filename.endswith('.html'):
        continue
    if filename in SKIP:
        continue
    with open(filename, 'r', encoding='utf-8') as f:
        html = f.read()
    has_head = bool(re.search(r'<head>', html, re.IGNORECASE))
    has_body = bool(re.search(r'<body[^>]*>', html, re.IGNORECASE))
    has_css = bool(re.search(r'<link[^>]+rel="stylesheet"', html, re.IGNORECASE))
    has_js = bool(re.search(r'<script', html, re.IGNORECASE))
    if not (has_head and has_body and has_css and has_js):
        missing.append(filename)

if missing:
    print('Files missing required structure or assets:')
    for m in missing:
        print(' -', m)
    exit(1)
else:
    print('All HTML files have required CSS and JS links.')
