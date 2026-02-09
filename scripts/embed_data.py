#!/usr/bin/env python3
"""
Embed repos.json data into HTML files for static site.
"""

import json
import re

def embed_data():
    # Load repos data
    with open('data/repos.json', 'r', encoding='utf-8') as f:
        repos = json.load(f)

    # Load metadata
    with open('data/metadata.json', 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    # Minified JSON for embedding
    data_json = json.dumps(repos, ensure_ascii=False, separators=(',', ':'))
    metadata_json = json.dumps(metadata, ensure_ascii=False, separators=(',', ':'))
    script_tag = f'<script>window.REPOS_DATA={data_json};window.REPOS_METADATA={metadata_json};</script>'

    # Pattern to match existing REPOS_DATA script tag
    pattern = r'<script>window\.REPOS_DATA=.*?</script>'

    # Update index.html
    with open('site/index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    if re.search(pattern, html):
        html = re.sub(pattern, script_tag, html)
    else:
        # Insert before closing body tag
        html = html.replace('</body>', f'    {script_tag}\n</body>')

    with open('site/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Updated site/index.html")

    # Update tools.html
    with open('site/tools.html', 'r', encoding='utf-8') as f:
        html = f.read()

    if re.search(pattern, html):
        html = re.sub(pattern, script_tag, html)
    else:
        html = html.replace('</body>', f'    {script_tag}\n</body>')

    with open('site/tools.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Updated site/tools.html")

    # Summary
    from collections import Counter
    categories = Counter(r['classification']['category'] for r in repos if r['classification'].get('category'))
    print(f"\nEmbedded {len(repos)} repos:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

if __name__ == "__main__":
    embed_data()
