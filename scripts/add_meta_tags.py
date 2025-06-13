# Project Name: Kingmakers Rise©
# File Name: add_meta_tags.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
import os
import re

OG_IMAGE = "https://www.kingmakersrise.com/images/og-preview.jpg"

for fname in os.listdir('.'):
    if not fname.endswith('.html') or fname == 'navbar.html':
        continue
    with open(fname, 'r', encoding='utf-8') as f:
        content = f.read()

    has_canonical = bool(re.search(r'<link[^>]+rel="canonical"', content, re.IGNORECASE))
    has_og = 'og:title' in content
    has_twitter = 'twitter:title' in content
    if has_canonical and has_og and has_twitter:
        continue

    title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
    if not title_match:
        continue
    title = title_match.group(1).strip()

    desc_match = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]*)"', content, re.IGNORECASE)
    description = desc_match.group(1).strip() if desc_match else ''

    canonical_url = f"https://www.kingmakersrise.com/{fname}"

    tags = []
    if not has_canonical:
        tags.append(f'<link rel="canonical" href="{canonical_url}" />')
    if not has_og:
        tags.extend([
            f'<meta property="og:title" content="{title}" />',
            f'<meta property="og:description" content="{description}" />',
            f'<meta property="og:image" content="{OG_IMAGE}" />',
            f'<meta property="og:url" content="{canonical_url}" />',
            '<meta property="og:type" content="website" />'
        ])
    if not has_twitter:
        tags.extend([
            '<meta name="twitter:card" content="summary_large_image" />',
            f'<meta name="twitter:title" content="{title}" />',
            f'<meta name="twitter:description" content="{description}" />',
            f'<meta name="twitter:image" content="{OG_IMAGE}" />'
        ])

    if not tags:
        continue

    # Find insertion point (after description or robots meta)
    insert_match = re.search(r'(</title>.*?)(<meta[^>]+name="description"[^>]*>)', content, re.IGNORECASE | re.DOTALL)
    if insert_match:
        insert_point = insert_match.end(2)
    else:
        head_match = re.search(r'<head>', content, re.IGNORECASE)
        insert_point = head_match.end() if head_match else 0

    new_content = content[:insert_point] + '\n  ' + '\n  '.join(tags) + content[insert_point:]

    with open(fname, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f'Updated {fname}')
