"""
Validates every JSON file in benchmark/examples/ against benchmark/schema.json.
Run this before committing any new benchmark examples.
"""
import json
import sys
from pathlib import Path
from jsonschema import validate, ValidationError

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schema.json"
EXAMPLES_DIR = ROOT / "examples"


def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_all():
    schema = load_schema()
    example_files = sorted(EXAMPLES_DIR.glob("*.json"))

    if not example_files:
        print("No example files found yet in benchmark/examples/.")
        return True

    all_valid = True
    seen_ids = set()

    for filepath in example_files:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        try:
            validate(instance=data, schema=schema)
        except ValidationError as e:
            print(f"[INVALID] {filepath.name}: {e.message}")
            all_valid = False
            continue

        if data["id"] in seen_ids:
            print(f"[DUPLICATE ID] {filepath.name}: id '{data['id']}' already used")
            all_valid = False
        seen_ids.add(data["id"])

    if all_valid:
        print(f"All {len(example_files)} examples are valid. Total unique IDs: {len(seen_ids)}")
    return all_valid


if __name__ == "__main__":
    success = validate_all()
    sys.exit(0 if success else 1)