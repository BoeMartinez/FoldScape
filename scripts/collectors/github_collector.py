"""
GitHub collector for FoldScape.
Scrapes protein ML repositories from GitHub.
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

try:
    from github import Github, Auth, RateLimitExceededException
except ImportError:
    print("ERROR: PyGithub not installed. Run: pip install PyGithub")
    exit(1)


class ProteinMLCollector:
    """Collect protein ML repos from GitHub with rate limiting."""

    KEYWORDS = [
        "alphafold",
        "rosettafold",
        "rfdiffusion",
        "proteinmpnn",
        "esmfold",
        "protein structure prediction",
        "protein design",
        "inverse folding",
        "protein language model",
    ]

    RELEVANT_TOPICS = {
        'protein', 'biology', 'bioinformatics',
        'computational-biology', 'structural-biology',
        'deep-learning', 'machine-learning', 'alphafold',
        'protein-structure', 'protein-design'
    }

    RELEVANT_KEYWORDS = [
        'protein', 'antibody', 'structure', 'molecular',
        'alphafold', 'rosetta', 'folding', 'amino acid',
        'pdb', 'sequence', 'binder'
    ]

    def __init__(self, github_token):
        self.gh = Github(auth=Auth.Token(github_token))
        self.results = []
        self._seen_repos = set()

    def check_rate_limit(self):
        """Check remaining API calls and wait if needed."""
        rate = self.gh.get_rate_limit()
        # Handle both old and new PyGithub versions
        try:
            remaining = rate.core.remaining
            reset_time = rate.core.reset
        except AttributeError:
            remaining = rate.rate.remaining
            reset_time = rate.rate.reset

        if remaining < 50:
            wait_seconds = (reset_time - datetime.utcnow()).total_seconds()
            if wait_seconds > 0:
                print(f"Rate limit low ({remaining}). Waiting {int(wait_seconds)}s...")
                time.sleep(wait_seconds + 10)

        return remaining

    def search_repos(self, keyword, min_stars=100, max_age_months=18, max_results=None):
        """Search GitHub for repos matching keyword and criteria."""
        self.check_rate_limit()

        cutoff_date = datetime.now() - timedelta(days=max_age_months * 30)
        query = (
            f"{keyword} stars:>={min_stars} "
            f"pushed:>{cutoff_date.strftime('%Y-%m-%d')}"
        )

        print(f"Searching: {keyword}...")

        try:
            repos = self.gh.search_repositories(
                query=query,
                sort='stars',
                order='desc'
            )
        except RateLimitExceededException:
            print("Rate limit hit. Waiting 60s...")
            time.sleep(60)
            return []

        collected = []
        count = 0

        for repo in repos:
            if max_results and count >= max_results:
                break

            # Skip duplicates
            if repo.full_name in self._seen_repos:
                continue

            # Check relevance
            if not self._is_relevant(repo):
                continue

            self._seen_repos.add(repo.full_name)
            collected.append(self._extract_metadata(repo))
            count += 1

            # Rate limit protection
            time.sleep(1)

        print(f"  Found {len(collected)} relevant repos")
        return collected

    def _is_relevant(self, repo):
        """Check if repo is actually protein ML related."""
        try:
            topics = set(repo.get_topics())
        except Exception:
            topics = set()

        # Check topics
        if topics & self.RELEVANT_TOPICS:
            return True

        # Check description
        desc = (repo.description or "").lower()
        if any(kw in desc for kw in self.RELEVANT_KEYWORDS):
            return True

        # Check repo name
        name = repo.name.lower()
        if any(kw in name for kw in ['protein', 'fold', 'alphafold', 'rosetta']):
            return True

        return False

    def _extract_metadata(self, repo):
        """Extract all relevant metadata from repo."""
        try:
            topics = repo.get_topics()
        except Exception:
            topics = []

        try:
            license_name = repo.license.name if repo.license else None
        except Exception:
            license_name = None

        return {
            'repo_id': repo.full_name,
            'metadata': {
                'name': repo.name,
                'description': repo.description,
                'url': repo.html_url,
                'stars': repo.stargazers_count,
                'forks': repo.forks_count,
                'last_updated': repo.pushed_at.isoformat() if repo.pushed_at else None,
                'created_at': repo.created_at.isoformat() if repo.created_at else None,
                'language': repo.language,
                'license': license_name,
                'topics': topics,
            },
            'classification': {
                'category': None,  # To be filled manually
                'subcategory': None,
                'layer': None
            },
            'domain_specific': {
                'experimental_validation': None,
                'expression_systems': [],
                'gpu_requirement': None,
                'input_types': [],
                'output_formats': []
            },
            'tracking': {
                'first_tracked': datetime.now().isoformat(),
                'star_velocity_7d': 0,
                'star_velocity_30d': 0,
                'trending': False
            }
        }

    def collect_all(self, min_stars=100, max_per_keyword=20):
        """Run collection across all keywords."""
        print(f"Starting collection (min_stars={min_stars})...")
        print(f"Rate limit remaining: {self.check_rate_limit()}")

        for keyword in self.KEYWORDS:
            results = self.search_repos(
                keyword,
                min_stars=min_stars,
                max_results=max_per_keyword
            )
            self.results.extend(results)

        print(f"\nTotal unique repos collected: {len(self.results)}")
        return self.results

    def save_results(self, filepath):
        """Save collected repos to JSON file with atomic write."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        temp_path = filepath.with_suffix('.tmp')

        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        # Atomic rename
        temp_path.replace(filepath)
        print(f"Saved {len(self.results)} repos to {filepath}")

        # Save metadata with collection timestamp
        metadata = {
            "collected_at": datetime.now().isoformat(),
            "repo_count": len(self.results)
        }
        metadata_path = filepath.parent / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        print(f"Saved metadata to {metadata_path}")

    def save_historical_snapshot(self, directory='data/historical'):
        """Save dated snapshot for temporal analysis."""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        date_str = datetime.now().strftime('%Y-%m-%d')
        filepath = directory / f"{date_str}.json"

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"Saved historical snapshot to {filepath}")


def run_self_test(token):
    """Self-verification test suite."""
    print("=" * 50)
    print("Running self-tests...")
    print("=" * 50)

    errors = []

    # Test 1: API connection
    print("\n[Test 1] API connection...")
    try:
        collector = ProteinMLCollector(token)
        user = collector.gh.get_user().login
        print(f"  OK - Authenticated as: {user}")
    except Exception as e:
        errors.append(f"API connection failed: {e}")
        print(f"  FAIL - {e}")
        return False

    # Test 2: Rate limit check
    print("\n[Test 2] Rate limit check...")
    try:
        remaining = collector.check_rate_limit()
        print(f"  OK - {remaining} requests remaining")
    except Exception as e:
        errors.append(f"Rate limit check failed: {e}")
        print(f"  FAIL - {e}")

    # Test 3: Search functionality
    print("\n[Test 3] Search (alphafold, max 5)...")
    try:
        results = collector.search_repos('alphafold', min_stars=100, max_results=5)
        if len(results) > 0:
            print(f"  OK - Found {len(results)} repos")
            for r in results:
                print(f"      - {r['repo_id']}: {r['metadata']['stars']} stars")
        else:
            errors.append("No results found for 'alphafold'")
            print("  FAIL - No results")
    except Exception as e:
        errors.append(f"Search failed: {e}")
        print(f"  FAIL - {e}")
        return False

    # Test 4: Data structure validation
    print("\n[Test 4] Data structure...")
    try:
        for r in results:
            assert 'repo_id' in r, "Missing repo_id"
            assert 'metadata' in r, "Missing metadata"
            assert 'stars' in r['metadata'], "Missing stars"
            assert 'tracking' in r, "Missing tracking"
        print("  OK - All required fields present")
    except AssertionError as e:
        errors.append(f"Data structure invalid: {e}")
        print(f"  FAIL - {e}")

    # Test 5: Save functionality
    print("\n[Test 5] Save to file...")
    try:
        collector.results = results
        test_path = Path('data/test_output.json')
        collector.save_results(test_path)

        if test_path.exists():
            print(f"  OK - Saved to {test_path}")
        else:
            errors.append("File not created")
            print("  FAIL - File not created")
    except Exception as e:
        errors.append(f"Save failed: {e}")
        print(f"  FAIL - {e}")

    # Summary
    print("\n" + "=" * 50)
    if errors:
        print(f"FAILED - {len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        return False
    else:
        print("ALL TESTS PASSED")
        print("Ready to run full collection.")
        return True


if __name__ == '__main__':
    token = os.getenv('GITHUB_TOKEN')

    if not token:
        print("ERROR: GITHUB_TOKEN environment variable not set")
        print("\nTo set it:")
        print("  1. Go to https://github.com/settings/tokens")
        print("  2. Generate token with 'public_repo' scope")
        print("  3. Run: export GITHUB_TOKEN='ghp_your_token_here'")
        exit(1)

    # Run self-test first
    if not run_self_test(token):
        print("Self-test failed, exiting.")
        exit(1)

    # Run full collection
    print("\n" + "=" * 50)
    print("Running full collection...")
    print("=" * 50)

    collector = ProteinMLCollector(token)
    collector.collect_all(min_stars=100)
    collector.save_results('data/repos.json')
    collector.save_historical_snapshot('data/historical')
