#!/usr/bin/env python3
"""
Auto-categorize repos based on keywords in description/topics.
Uses config.json for settings. Manual overrides take priority.
"""

import json
from pathlib import Path


def load_config():
    """Load configuration from config.json."""
    config_path = Path(__file__).parent.parent / 'config.json'
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def categorize_repo(repo, keywords_map, overrides):
    """
    Determine category for a single repo.
    Priority: manual override > keyword match > None
    """
    repo_id = repo['repo_id']

    # Check for manual override first
    if repo_id in overrides:
        return overrides[repo_id]

    # Build searchable text from repo metadata
    name = repo['metadata'].get('name', '').lower()
    desc = (repo['metadata'].get('description') or '').lower()
    topics = [t.lower() for t in repo['metadata'].get('topics', [])]
    searchable = f"{name} {desc} {' '.join(topics)}"

    # Check each category's keywords
    for category, keywords in keywords_map.items():
        for keyword in keywords:
            if keyword.lower() in searchable:
                return category

    return None


def main():
    """Categorize all repos in repos.json."""
    config = load_config()
    keywords_map = config['categories']['keywords']
    overrides = config['categories']['overrides']

    # Load repos
    data_path = Path(__file__).parent.parent / 'data' / 'repos.json'
    with open(data_path, 'r', encoding='utf-8') as f:
        repos = json.load(f)

    # Categorize each repo
    categorized = 0
    uncategorized = []

    for repo in repos:
        category = categorize_repo(repo, keywords_map, overrides)
        repo['classification']['category'] = category

        if category:
            categorized += 1
        else:
            uncategorized.append(repo['repo_id'])

    # Save updated repos
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(repos, f, indent=2, ensure_ascii=False)

    # Report results
    print(f"Categorized: {categorized}/{len(repos)} repos")

    if uncategorized:
        print(f"\nUncategorized ({len(uncategorized)}):")
        for r in uncategorized:
            print(f"  - {r}")

    # Category breakdown
    from collections import Counter
    categories = Counter(r['classification']['category'] for r in repos if r['classification']['category'])
    print("\nCategory breakdown:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
