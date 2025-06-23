import os
import re


base = os.getcwd()
missing = []

for root, _, files in os.walk("."):
    for f in files:
        if not f.endswith(".html"):
            continue

        path = os.path.join(root, f)
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()

        tags = re.findall(
            r'<(script|link|img|a)[^>]*(?:src|href)=["\']([^"\']+)["\']',
            text,
            flags=re.I,
        )

        for tag, url in tags:
            # Skip external and anchor links
            if url.startswith(
                (
                    "http://",
                    "https://",
                    "mailto:",
                    "tel:",
                )
            ) or url.startswith("#"):
                continue

            # Ignore templating placeholders such as {{ .ConfirmationURL }}
            if "{{" in url or "{%" in url:
                continue

            # Strip query parameters for filesystem check
            clean_url = url.split("?", 1)[0]

            if clean_url.startswith("/"):
                file_path = os.path.join(base, clean_url.lstrip("/"))
            else:
                file_path = os.path.join(os.path.dirname(path), clean_url)

            if not os.path.exists(file_path):
                # Fallback to repo root for injected fragments like
                # public/navbar.html which reference files relative to the
                # consuming page rather than the fragment location.
                alt_path = os.path.join(base, clean_url.lstrip("/"))
                if not os.path.exists(alt_path):
                    missing.append((path, url))

print("missing count", len(missing))
for m in missing:
    print(f"{m[0]} => {m[1]}")
