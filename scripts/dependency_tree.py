#!/usr/bin/env python3
"""Generate dependency trees for JS and Python entry points.

- JS entry points are discovered by scanning HTML files for local <script src="...">
- Python entry point is backend/main.py.

Outputs a JSON report and a list of unused files.
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Dict, List, Set

REPO_ROOT = Path(__file__).resolve().parent.parent
JS_DIR = REPO_ROOT / "Javascript"
PY_DIR = REPO_ROOT / "backend"

SCRIPT_SRC_RE = re.compile(r'<script[^>]+src=["\']([^"\']+\.js)["\']', re.I)
JS_IMPORT_RE = re.compile(
    r"import[^\n]*?from\s+[\'\"](.+?)[\'\"]|"  # import x from '...'
    r"import\(\s*[\'\"](.+?)[\'\"]\s*\)"      # dynamic import('...')
)


def find_html_js_entries() -> List[Path]:
    entries: Set[Path] = set()
    for html in REPO_ROOT.rglob("*.html"):
        text = html.read_text(encoding="utf-8", errors="ignore")
        for src in SCRIPT_SRC_RE.findall(text):
            if src.startswith("http") or src.startswith("https"):
                continue
            src_path = REPO_ROOT / src.lstrip("/")
            if src_path.exists():
                entries.add(src_path.resolve())
    return sorted(entries)


def parse_js_imports(file_path: Path) -> List[Path]:
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    imports: List[Path] = []
    for spec1, spec2 in JS_IMPORT_RE.findall(text):
        spec = spec1 or spec2
        if not spec or not (spec.startswith('.') or spec.startswith('/')):
            continue
        target = (REPO_ROOT / spec.lstrip('/')) if spec.startswith('/') else (file_path.parent / spec).resolve()
        candidates = [target, target.with_suffix('.js'), target / 'index.js']
        for c in candidates:
            if c.exists() and c.is_file():
                imports.append(c.resolve())
                break
    return imports


def build_js_tree(path: Path, visited: Dict[Path, Dict]) -> Dict:
    if path in visited:
        return visited[path]
    node = {"file": str(path.relative_to(REPO_ROOT)), "deps": []}
    visited[path] = node
    for dep in parse_js_imports(path):
        node["deps"].append(build_js_tree(dep, visited))
    return node


def parse_py_imports(file_path: Path) -> List[Path]:
    imports: List[Path] = []
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod_path = resolve_py_module(alias.name, file_path.parent, 0)
                if mod_path:
                    imports.append(mod_path)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            mod_path = resolve_py_module(mod, file_path.parent, node.level)
            if mod_path:
                imports.append(mod_path)
    return imports


def resolve_py_module(name: str, current_dir: Path, level: int) -> Path | None:
    base = REPO_ROOT if level == 0 else current_dir
    for _ in range(level):
        base = base.parent
    if name:
        candidate = base / (name.replace('.', '/') + '.py')
        if candidate.exists():
            return candidate.resolve()
        pkg_init = base / name.replace('.', '/') / '__init__.py'
        if pkg_init.exists():
            return pkg_init.resolve()
    else:
        init = base / '__init__.py'
        if init.exists():
            return init.resolve()
    return None


def build_py_tree(path: Path, visited: Dict[Path, Dict]) -> Dict:
    if path in visited:
        return visited[path]
    node = {"file": str(path.relative_to(REPO_ROOT)), "deps": []}
    visited[path] = node
    for dep in parse_py_imports(path):
        if dep.suffix == '.py' and REPO_ROOT in dep.parents:
            node["deps"].append(build_py_tree(dep, visited))
    return node


def gather_nodes(node: Dict) -> List[Dict]:
    nodes = [node]
    for child in node.get("deps", []):
        nodes.extend(gather_nodes(child))
    return nodes


def gather_nodes_dict(tree: Dict[str, Dict]) -> List[Dict]:
    nodes: List[Dict] = []
    for root in tree.values():
        nodes.extend(gather_nodes(root))
    return nodes


def main() -> None:
    js_entries = find_html_js_entries()
    js_tree: Dict[str, Dict] = {}
    js_visited: Dict[Path, Dict] = {}
    for entry in js_entries:
        js_tree[str(entry.relative_to(REPO_ROOT))] = build_js_tree(entry, js_visited)

    py_entry = PY_DIR / 'main.py'
    py_tree = build_py_tree(py_entry, {}) if py_entry.exists() else {}

    js_nodes = {(REPO_ROOT / n["file"]).resolve() for n in gather_nodes_dict(js_tree)}
    py_nodes = {(REPO_ROOT / n["file"]).resolve() for n in gather_nodes(py_tree)}

    unused_js = sorted(str(p.relative_to(REPO_ROOT)) for p in JS_DIR.rglob('*.js') if p.resolve() not in js_nodes)
    unused_py = sorted(str(p.relative_to(REPO_ROOT)) for p in PY_DIR.rglob('*.py') if p.resolve() not in py_nodes)

    report = {
        "js": {"entry_points": [str(p.relative_to(REPO_ROOT)) for p in js_entries], "tree": js_tree, "unused_files": unused_js},
        "python": {"entry_points": ["backend/main.py"], "tree": py_tree, "unused_files": unused_py},
    }
    (REPO_ROOT / 'dependency_report.json').write_text(json.dumps(report, indent=2))
    with open(REPO_ROOT / 'unused_files.txt', 'w') as fh:
        for f in unused_js + unused_py:
            fh.write(f"DELETE {f}\n")
    print("Dependency report written to dependency_report.json")
    print("Unused file list written to unused_files.txt")


if __name__ == "__main__":
    main()
