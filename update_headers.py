# Project Name: Thronestead©
# File Name: update_headers.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
    ],
    '.js': [
        '// Project Name: Thronestead\u00a9\n',
        '// File Name: {name}\n',
        '// Version:  7/1/2025 10:38\n',
        '// Developer: Deathsgift66\n',
    ],
    '.css': [
        '/*\n',
        'Project Name: Thronestead\u00a9\n',
        'File Name: {name}\n',
        'Version:  7/1/2025 10:38\n',
        'Developer: Deathsgift66\n',
        '*/\n',
    ],
    '.html': [
        '<!--\n',
        'Project Name: Thronestead\u00a9\n',
        'File Name: {name}\n',
        'Version:  7/1/2025 10:38\n',
        'Developer: Deathsgift66\n',
        '-->\n',
    ],
    '.yaml': [
        '# Project Name: Thronestead\u00a9\n',
        '# File Name: {name}\n',
        '# Version:  7/1/2025 10:38\n',
        '# Developer: Deathsgift66\n',
    ],
}

# gather files
files = []
for ext in header_template.keys():
    files.extend(Path('.').rglob(f'*{ext}'))

count = 0
for path in files:
    try:
        text = path.read_text(encoding='utf-8').splitlines(keepends=True)
    except Exception:
        continue
    if not text:
        continue
    found = False
    # check if header present
    if 'Project Name: Thronestead' in ''.join(text[:6]):
        found = True
    if not found:
        continue
    # remove existing header lines until after 'Developer' line
    idx = 0
    while idx < len(text):
        line = text[idx]
        if 'Developer' in line:
            idx += 1
            # if html/css close comment next line is '-->' or '*/'
            if path.suffix in ['.html', '.css'] and idx < len(text) and text[idx].strip() in ['-->', '*/']:
                idx += 1
            break
        idx += 1
    new_header = [ln.format(name=path.name) for ln in header_template[path.suffix]]
    text = new_header + text[idx:]
    path.write_text(''.join(text), encoding='utf-8')
    count += 1
print('updated', count, 'files')
