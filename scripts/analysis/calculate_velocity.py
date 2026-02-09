#!/usr/bin/env python3
"""
Calculate star velocity for trending detection.
Compares current stars with historical snapshot from 7 days ago.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path


def calculate_velocity(days_back=7, trending_threshold=10):
    """
    Calculate star velocity and update repos.json with trending data.

    Args:
        days_back: How many days to look back for comparison
        trending_threshold: Minimum stars gained to be considered trending
    """
    data_dir = Path('data')
    historical_dir = data_dir / 'historical'

    # Load current repos
    with open(data_dir / 'repos.json', 'r', encoding='utf-8') as f:
        repos = json.load(f)

    # Find historical snapshot
    target_date = datetime.now() - timedelta(days=days_back)
    historical_file = historical_dir / f"{target_date.strftime('%Y-%m-%d')}.json"

    if not historical_file.exists():
        # Try to find closest available snapshot
        available = sorted(historical_dir.glob('*.json'))
        if not available:
            print(f"No historical data available. Need to wait for {days_back} days of collection.")
            return False

        # Use oldest available
        historical_file = available[0]
        print(f"Using oldest available snapshot: {historical_file.name}")

    # Load historical data
    with open(historical_file, 'r', encoding='utf-8') as f:
        historical_repos = json.load(f)

    # Build lookup by repo_id
    historical_stars = {r['repo_id']: r['metadata'].get('stars', 0) for r in historical_repos}

    # Calculate velocity for each repo
    trending_count = 0
    for repo in repos:
        repo_id = repo['repo_id']
        current_stars = repo['metadata'].get('stars', 0)
        old_stars = historical_stars.get(repo_id, current_stars)

        velocity = current_stars - old_stars
        repo['tracking']['star_velocity_7d'] = velocity
        repo['tracking']['trending'] = velocity >= trending_threshold

        if repo['tracking']['trending']:
            trending_count += 1
            print(f"  TRENDING: {repo['metadata'].get('name', repo_id)} (+{velocity} stars)")

    # Save updated repos
    with open(data_dir / 'repos.json', 'w', encoding='utf-8') as f:
        json.dump(repos, f, indent=2, ensure_ascii=False)

    print(f"\nUpdated {len(repos)} repos. {trending_count} trending.")
    return True


if __name__ == "__main__":
    print("Calculating star velocity...")
    print("=" * 50)
    calculate_velocity()
