#!/bin/bash
(printf '<?xml version="1.0" encoding="UTF-8"?>\n';
printf '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n';
for f in *.html; do
  case "$f" in
    admin_*|*_log.html|*_logs.html|*changelog.html|*forgot*.html|reset-password.html|update-password.html)
      continue
      ;;
  esac
  printf '  <url><loc>https://www.thronestead.com/%s</loc></url>\n' "$f";
done;
printf '</urlset>\n') > sitemap.xml
