#!/usr/bin/env python3
"""
Embed repos.json data into HTML files for static site.
"""

import json
import os
import re

def load(path, default=None):
    """Optional data file. Announcements may not exist on a first run."""
    if not os.path.exists(path):
        return default
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_tag(html, pattern, script_tag):
    """Replace the existing tag or insert one before </body>.

    The replacement is passed as a function on purpose: re.sub treats
    backslashes in a replacement string as escapes, and the embedded JSON
    carries them in abstracts and titles.
    """
    if re.search(pattern, html):
        return re.sub(pattern, lambda m: script_tag, html)
    return html.replace('</body>', f'    {script_tag}\n</body>')

def embed_data():
    # Load repos data
    with open('data/repos.json', 'r', encoding='utf-8') as f:
        repos = json.load(f)

    # Load metadata
    with open('data/metadata.json', 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    # Entries with no repository, so no stars. Absent until the collector runs.
    announcements = load('data/announcements.json', [])

    # Minified JSON for embedding
    data_json = json.dumps(repos, ensure_ascii=False, separators=(',', ':'))
    metadata_json = json.dumps(metadata, ensure_ascii=False, separators=(',', ':'))
    news_json = json.dumps(announcements, ensure_ascii=False, separators=(',', ':'))
    script_tag = f'<script>window.REPOS_DATA={data_json};window.REPOS_METADATA={metadata_json};</script>'
    news_tag = f'<script>window.ANNOUNCEMENTS_DATA={news_json};</script>'

    # Patterns to match the existing script tags
    pattern = r'<script>window\.REPOS_DATA=.*?</script>'
    news_pattern = r'<script>window\.ANNOUNCEMENTS_DATA=.*?</script>'

    # Update index.html
    with open('site/index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    html = write_tag(html, pattern, script_tag)
    html = write_tag(html, news_pattern, news_tag)

    with open('site/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Updated site/index.html")

    # Update tools.html
    with open('site/tools.html', 'r', encoding='utf-8') as f:
        html = f.read()

    html = write_tag(html, pattern, script_tag)

    with open('site/tools.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Updated site/tools.html")

    print(f"Embedded {len(announcements)} announcements")

    # Summary
    from collections import Counter
    categories = Counter(r['classification']['category'] for r in repos if r['classification'].get('category'))
    print(f"\nEmbedded {len(repos)} repos:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

if __name__ == "__main__":
    embed_data()
