#!/usr/bin/env python3
"""Simple repository bloat detector.

Scans the repository for potential sources of code bloat:

1. Legacy versions of pages
2. Redundant SQL migrations
3. Test or experimental features
4. Unused JavaScript/Python modules

The script prints counts for each category and a total bloat percentage.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
from collections import defaultdict

EXCLUDE_DIRS = {".git", "node_modules", "dist"}

LEGACY_PATTERNS = (
    "old",
    "legacy",
    "backup",
    "copy",
    "v1",
    "v2",
)

TEST_PATTERNS = (
    "test",
    "tmp",
    "sample",
    "experiment",
    "experimental",
)

SQL_MIGRATION_DIRS = {"migrations"}


def iter_files(root: str):
    for path, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for name in files:
            yield os.path.join(path, name)


def detect_legacy_pages(files):
    legacy = [f for f in files if f.endswith(".html") and any(p in os.path.basename(f) for p in LEGACY_PATTERNS)]
    return legacy


def detect_sql_migrations(files):
    sql_files = [f for f in files if f.endswith(".sql") or any(part in SQL_MIGRATION_DIRS for part in f.split(os.sep))]
    # Find redundant migrations by hashing contents and looking for duplicates
    hashes = defaultdict(list)
    for f in sql_files:
        try:
            with open(f, "rb") as fh:
                digest = hashlib.sha1(fh.read()).hexdigest()
            hashes[digest].append(f)
        except OSError:
            continue
    redundant = [paths for paths in hashes.values() if len(paths) > 1]
    return sql_files, redundant


def detect_test_files(files):
    return [f for f in files if any(p in os.path.basename(f) for p in TEST_PATTERNS)]


def find_modules(files, extension):
    modules = defaultdict(list)
    for f in files:
        if f.endswith(extension):
            modules[os.path.splitext(os.path.basename(f))[0]].append(f)
    return modules


def find_imports_py(files):
    pattern = re.compile(r"^\s*(?:from|import)\s+([\w\.]+)", re.MULTILINE)
    imports = set()
    for f in files:
        if f.endswith(".py"):
            try:
                with open(f, encoding="utf-8", errors="ignore") as fh:
                    for match in pattern.findall(fh.read()):
                        imports.add(match.split(".")[0])
            except OSError:
                continue
    return imports


def find_imports_js(files):
    pattern = re.compile(r"import\s+.*?from\s+[\'\"]([^\'\"]+)[\'\"]|require\([\'\"]([^\'\"]+)[\'\"]\)")
    imports = set()
    for f in files:
        if f.endswith(".js"):
            try:
                with open(f, encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
                for mod, req in pattern.findall(content):
                    mod_name = mod or req
                    imports.add(os.path.basename(mod_name).split(".")[0])
            except OSError:
                continue
    return imports


def detect_unused_modules(files):
    py_modules = find_modules(files, ".py")
    js_modules = find_modules(files, ".js")
    py_imports = find_imports_py(files)
    js_imports = find_imports_js(files)
    unused_py = [paths for mod, paths in py_modules.items() if mod not in py_imports]
    unused_js = [paths for mod, paths in js_modules.items() if mod not in js_imports]
    return unused_py + unused_js


def main(root: str) -> None:
    all_files = list(iter_files(root))
    legacy_pages = detect_legacy_pages(all_files)
    sql_files, redundant_migrations = detect_sql_migrations(all_files)
    test_files = detect_test_files(all_files)
    unused_modules = detect_unused_modules(all_files)

    total_flagged = len(legacy_pages) + len(redundant_migrations) + len(test_files) + len(unused_modules)
    total_files = len(all_files) or 1
    bloat_percentage = 100 * total_flagged / total_files

    print("Repository Bloat Report")
    print("========================")
    print(f"Legacy pages: {len(legacy_pages)}")
    print(f"SQL migration files: {len(sql_files)} (redundant sets: {len(redundant_migrations)})")
    print(f"Test/experimental files: {len(test_files)}")
    print(f"Unused modules: {len(unused_modules)}")
    print(f"Total files scanned: {total_files}")
    print(f"Bloat percentage: {bloat_percentage:.2f}%")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Detect repository bloat")
    parser.add_argument("root", nargs="?", default=".", help="Repository root to scan")
    args = parser.parse_args()
    main(args.root)
