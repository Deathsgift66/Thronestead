# Project Name: Kingmakers Rise©
# File Name: update_headers.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
import os
import re
from pathlib import Path

HEADER_LINES = {
    '.py': [
        '# Project Name: Kingmakers Rise\xa9',
        '# File Name: {file}',
        '# Version 6.13.2025.19.49',
        '# Developer: Deathsgift66',
        ''
    ],
    '.js': [
        '// Project Name: Kingmakers Rise\xa9',
        '// File Name: {file}',
        '// Version 6.13.2025.19.49',
        '// Developer: Deathsgift66',
        ''
    ],
    '.css': [
        '/*',
        'Project Name: Kingmakers Rise\xa9',
        'File Name: {file}',
        'Version 6.13.2025.19.49',
        'Developer: Deathsgift66',
        '*/',
        ''
    ],
    '.html': [
        '<!--',
        'Project Name: Kingmakers Rise\xa9',
        'File Name: {file}',
        'Version 6.13.2025.19.49',
        'Developer: Deathsgift66',
        '-->',
        ''
    ]
}

EXTENSIONS = tuple(HEADER_LINES.keys())


def remove_old_header(text, ext):
    if ext in {'.css', '.html'}:
        start = r"^\s*(/\*.*?\*/\s*|<!--.*?-->\s*)"
        m = re.match(start, text, re.DOTALL)
        if m and any(key in m.group(0) for key in ['Project', 'File', 'Author', 'Version']):
            return text[m.end():]
    else:  # js or py
        pattern_line = r"^(\s*(//.*\n|#.*\n))+"
        m = re.match(pattern_line, text)
        if m and any(key in m.group(0) for key in ['Project', 'File', 'Author', 'Version']):
            return text[m.end():]
        pattern_block = r"^\s*/\*.*?\*/\s*"
        m = re.match(pattern_block, text, re.DOTALL)
        if m and any(key in m.group(0) for key in ['Project', 'File', 'Author', 'Version']):
            return text[m.end():]
    return text


def process_file(path: Path):
    ext = path.suffix.lower()
    if ext not in HEADER_LINES:
        return
    text = path.read_text(encoding='utf-8')
    text = remove_old_header(text, ext)
    header = "\n".join(line.format(file=path.name) for line in HEADER_LINES[ext])
    new_text = header + text.lstrip('\n')
    path.write_text(new_text, encoding='utf-8')


def main():
    base = Path('.')
    for p in base.rglob('*'):
        if p.is_file() and p.suffix.lower() in EXTENSIONS:
            process_file(p)


if __name__ == '__main__':
    main()
