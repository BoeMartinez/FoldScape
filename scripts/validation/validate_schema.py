"""
Schema validator for FoldScape repos.json.
Ensures data integrity after collection and updates.
"""

import json
import sys
from pathlib import Path


# Required fields at each level
REQUIRED_TOP_LEVEL = {
    'repo_id': str,
    'metadata': dict,
    'tracking': dict
}

REQUIRED_METADATA = {
    'name': str,
    'url': str,
    'stars': int,
    'last_updated': (str, type(None))  # Can be null
}

REQUIRED_TRACKING = {
    'first_tracked': str,
}

# Optional but validated if present
OPTIONAL_FIELDS = {
    'classification': dict,
    'domain_specific': dict,
    'academic': dict
}

VALID_CATEGORIES = [
    'Infrastructure',
    'Core Methods',
    'Applications',
    None  # Not yet categorized
]

VALID_LAYERS = [
    'Layer 1: Infrastructure',
    'Layer 2: Core Methods',
    'Layer 3: Applications',
    None
]

VALID_GPU_REQUIREMENTS = [
    'CPU-only',
    '<8GB',
    '8-24GB',
    '>24GB',
    'Multi-GPU',
    None
]

VALID_EXPRESSION_SYSTEMS = [
    'E.coli',
    'HEK293',
    'Yeast',
    'Cell-free',
    'Insect',
    'CHO'
]


class ValidationError:
    def __init__(self, repo_id, field, message):
        self.repo_id = repo_id
        self.field = field
        self.message = message

    def __str__(self):
        return f"{self.repo_id} -> {self.field}: {self.message}"


def check_type(value, expected_type, allow_none=False):
    """Check if value matches expected type."""
    if allow_none and value is None:
        return True
    if isinstance(expected_type, tuple):
        return isinstance(value, expected_type)
    return isinstance(value, expected_type)


def validate_repo(repo, index):
    """Validate a single repo entry."""
    errors = []
    repo_id = repo.get('repo_id', f'repo_index_{index}')

    # Check top-level required fields
    for field, field_type in REQUIRED_TOP_LEVEL.items():
        if field not in repo:
            errors.append(ValidationError(repo_id, field, "missing required field"))
        elif not check_type(repo[field], field_type):
            errors.append(ValidationError(
                repo_id, field,
                f"wrong type: expected {field_type.__name__}, got {type(repo[field]).__name__}"
            ))

    # Check metadata subfields
    if 'metadata' in repo and isinstance(repo['metadata'], dict):
        metadata = repo['metadata']
        for field, field_type in REQUIRED_METADATA.items():
            if field not in metadata:
                errors.append(ValidationError(repo_id, f"metadata.{field}", "missing required field"))
            elif not check_type(metadata[field], field_type, allow_none=True):
                errors.append(ValidationError(
                    repo_id, f"metadata.{field}",
                    f"wrong type: expected {field_type}, got {type(metadata[field])}"
                ))

        # Validate stars is non-negative
        if 'stars' in metadata and isinstance(metadata['stars'], int):
            if metadata['stars'] < 0:
                errors.append(ValidationError(repo_id, "metadata.stars", "cannot be negative"))

        # Validate URL format
        if 'url' in metadata and metadata['url']:
            if not metadata['url'].startswith('https://github.com/'):
                errors.append(ValidationError(repo_id, "metadata.url", "must be a GitHub URL"))

    # Check tracking subfields
    if 'tracking' in repo and isinstance(repo['tracking'], dict):
        tracking = repo['tracking']
        for field, field_type in REQUIRED_TRACKING.items():
            if field not in tracking:
                errors.append(ValidationError(repo_id, f"tracking.{field}", "missing required field"))

    # Validate classification if present
    if 'classification' in repo and repo['classification']:
        classification = repo['classification']
        if 'category' in classification:
            if classification['category'] not in VALID_CATEGORIES:
                errors.append(ValidationError(
                    repo_id, "classification.category",
                    f"invalid value: {classification['category']}"
                ))

    # Validate domain_specific if present
    if 'domain_specific' in repo and repo['domain_specific']:
        domain = repo['domain_specific']

        if 'gpu_requirement' in domain and domain['gpu_requirement']:
            if domain['gpu_requirement'] not in VALID_GPU_REQUIREMENTS:
                errors.append(ValidationError(
                    repo_id, "domain_specific.gpu_requirement",
                    f"invalid value: {domain['gpu_requirement']}"
                ))

        if 'expression_systems' in domain and domain['expression_systems']:
            for system in domain['expression_systems']:
                if system not in VALID_EXPRESSION_SYSTEMS:
                    errors.append(ValidationError(
                        repo_id, "domain_specific.expression_systems",
                        f"invalid value: {system}"
                    ))

    return errors


def validate_json_file(filepath):
    """Validate entire repos.json file."""
    filepath = Path(filepath)

    print(f"Validating: {filepath}")
    print("-" * 50)

    # Check file exists
    if not filepath.exists():
        print(f"ERROR: File not found: {filepath}")
        return False

    # Parse JSON
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}")
        return False

    # Handle both list and dict formats
    if isinstance(data, list):
        repos = data
    elif isinstance(data, dict):
        repos = list(data.values())
    else:
        print(f"ERROR: Root must be list or dict, got {type(data).__name__}")
        return False

    if len(repos) == 0:
        print("WARNING: No repos in file")
        return True

    # Validate each repo
    all_errors = []
    repo_ids = set()

    for i, repo in enumerate(repos):
        # Check for duplicate repo_ids
        repo_id = repo.get('repo_id')
        if repo_id:
            if repo_id in repo_ids:
                all_errors.append(ValidationError(repo_id, "repo_id", "duplicate"))
            repo_ids.add(repo_id)

        # Validate repo structure
        errors = validate_repo(repo, i)
        all_errors.extend(errors)

    # Report results
    if all_errors:
        print(f"\nFOUND {len(all_errors)} ERROR(S):\n")
        for error in all_errors[:20]:  # Show first 20
            print(f"  - {error}")
        if len(all_errors) > 20:
            print(f"  ... and {len(all_errors) - 20} more")
        print()
        return False
    else:
        print(f"VALID: {len(repos)} repos, no errors")

        # Print summary stats
        categorized = sum(1 for r in repos if r.get('classification', {}).get('category'))
        with_gpu = sum(1 for r in repos if r.get('domain_specific', {}).get('gpu_requirement'))
        with_expr = sum(1 for r in repos if r.get('domain_specific', {}).get('expression_systems'))

        print(f"\nCoverage:")
        print(f"  - Categorized: {categorized}/{len(repos)} ({100*categorized//len(repos)}%)")
        print(f"  - GPU requirements: {with_gpu}/{len(repos)} ({100*with_gpu//len(repos)}%)")
        print(f"  - Expression systems: {with_expr}/{len(repos)} ({100*with_expr//len(repos)}%)")

        return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_schema.py <json_file>")
        print("\nExample:")
        print("  python validate_schema.py data/repos.json")
        print("  python validate_schema.py data/test_output.json")
        sys.exit(1)

    filepath = sys.argv[1]
    is_valid = validate_json_file(filepath)
    sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()
