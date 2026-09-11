"""Export recipes/*.md as individual schema.org Recipe JSON documents for Mealie."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required. Run: pip install -r requirements.txt")


ROOT = Path(__file__).resolve().parent.parent
RECIPES_DIR = ROOT / "recipes"
DEFAULT_OUTPUT_DIR = ROOT / "mealie-import-json"
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)
HEADING_RE = re.compile(r"^(#{2,3})\s+(.+?)\s*$")
BULLET_RE = re.compile(r"^[-*]\s+(.+?)\s*$")
ORDERED_ITEM_RE = re.compile(r"^\d+[.)]\s+(.+?)\s*$")


def parse_recipe(path: Path) -> tuple[dict, str]:
    match = FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"{path.name}: missing YAML frontmatter block")

    metadata = yaml.safe_load(match.group(1)) or {}
    if not metadata.get("title"):
        raise ValueError(f"{path.name}: missing required field 'title'")
    return metadata, match.group(2).strip()


def parse_body(body: str) -> tuple[list[str], list[dict], list[str]]:
    ingredients: list[str] = []
    instruction_sections: list[dict[str, object]] = []
    notes: list[str] = []
    current_part: str | None = None
    current_section: dict[str, object] | None = None

    for raw_line in body.splitlines():
        line = raw_line.strip()
        heading = HEADING_RE.match(line)
        if heading:
            level, heading_text = heading.groups()
            normalized_heading = heading_text.lower()
            if level == "##":
                current_part = normalized_heading if normalized_heading in {"ingredients", "method", "notes"} else None
                current_section = None
            elif current_part == "method":
                current_section = {"@type": "HowToSection", "name": heading_text, "itemListElement": []}
                instruction_sections.append(current_section)
            continue

        if not line:
            continue

        if current_part == "ingredients":
            item = BULLET_RE.match(line)
            if item:
                ingredients.append(item.group(1))
        elif current_part == "method":
            item = ORDERED_ITEM_RE.match(line) or BULLET_RE.match(line)
            if item:
                if current_section is None:
                    current_section = {"@type": "HowToSection", "itemListElement": []}
                    instruction_sections.append(current_section)
                steps = current_section["itemListElement"]
                assert isinstance(steps, list)
                steps.append({"@type": "HowToStep", "text": item.group(1)})
            elif current_section is not None:
                steps = current_section["itemListElement"]
                assert isinstance(steps, list)
                if steps:
                    steps[-1]["text"] = f"{steps[-1]['text']} {line}"
        elif current_part == "notes":
            item = BULLET_RE.match(line) or ORDERED_ITEM_RE.match(line)
            notes.append(item.group(1) if item else line)

    return ingredients, instruction_sections, notes


def to_schema_recipe(metadata: dict, body: str) -> dict:
    ingredients, instruction_sections, notes = parse_body(body)
    instructions: list[dict] = []
    for section in instruction_sections:
        steps = section["itemListElement"]
        if steps:
            instructions.append(section)

    recipe: dict[str, object] = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": str(metadata["title"]).strip(),
        "recipeIngredient": ingredients,
        "recipeInstructions": instructions,
    }

    optional_fields = {
        "description": metadata.get("description"),
        "author": metadata.get("author"),
        "recipeCuisine": metadata.get("cuisine"),
        "recipeCategory": metadata.get("course"),
        "keywords": ", ".join(str(tag).strip() for tag in metadata.get("tags") or []),
        "recipeYield": f"{metadata['servings']} servings" if metadata.get("servings") else None,
        "prepTime": metadata.get("prep_time"),
        "cookTime": metadata.get("cook_time"),
        "totalTime": metadata.get("total_time"),
        "image": metadata.get("image"),
        "url": metadata.get("url"),
        "comment": "\n".join(notes) if notes else None,
    }
    recipe.update({key: value for key, value in optional_fields.items() if value})
    return recipe


def export_recipes(output_dir: Path) -> int:
    if not RECIPES_DIR.is_dir():
        raise FileNotFoundError(f"Missing recipes directory: {RECIPES_DIR}")

    source_files = sorted(RECIPES_DIR.glob("*.md"))
    if not source_files:
        raise FileNotFoundError(f"No recipe Markdown files found in: {RECIPES_DIR}")

    output_dir.mkdir(parents=True, exist_ok=True)
    for output_file in output_dir.glob("*.json"):
        output_file.unlink()

    for source_file in source_files:
        metadata, body = parse_recipe(source_file)
        recipe = to_schema_recipe(metadata, body)
        output_file = output_dir / f"{source_file.stem}.json"
        output_file.write_text(json.dumps(recipe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Exported {len(source_files)} recipe JSON files to {output_dir.relative_to(ROOT)}")
    return len(source_files)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for individual Mealie JSON files (default: mealie-import-json)",
    )
    args = parser.parse_args()

    try:
        export_recipes(args.output_dir.resolve())
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())