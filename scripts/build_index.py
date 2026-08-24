"""Build data/index.json from the recipe markdown files in recipes/.

Responsibilities:
  * Parse YAML frontmatter + Markdown body for every recipe.
  * Apply AGGRESSIVE duplicate detection: recipes are merged when their titles
    match after aggressive normalization (accent-insensitive, ``&`` treated as
    ``and``, common stop-words dropped, word order ignored). Ingredient lists
    do NOT have to match. Merged recipes collapse into a single entry whose
    ``sources`` lists every originating PDF (the source trace) and whose
    metadata (tags, key ingredients, cuisine, course, servings) is unioned.
  * Build an ingredient index mapping each key ingredient to the recipes
    that use it.
  * Emit data/index.json consumed by the static site + client-side search.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required. Run: pip install -r requirements.txt")

ROOT = Path(__file__).resolve().parent.parent
RECIPES_DIR = ROOT / "recipes"
DATA_DIR = ROOT / "data"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)

# Words ignored when comparing titles for de-duplication.
TITLE_STOPWORDS = {
    "the", "a", "an", "of", "with", "and", "in", "on", "to", "for",
    "my", "your", "our", "style", "classic", "quick", "easy", "fresh",
    "homemade", "simple",
}


def strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(c)
    )


def title_key(title: str) -> frozenset[str]:
    """Aggressive, order-independent title key used for de-duplication.

    Strips accents, treats ``&`` as ``and``, removes punctuation and common
    stop-words, and returns the remaining words as an unordered set so that
    e.g. "Pear & Walnut Salad" and "Walnut and Pear Salad" match.
    """
    text = strip_accents(title).lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    words = [w for w in text.split() if w and w not in TITLE_STOPWORDS]
    # Fall back to the full word set if stop-word removal emptied the title.
    if not words:
        words = [w for w in text.split() if w]
    return frozenset(words)


def normalize_ingredient(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def parse_recipe(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(raw)
    if not match:
        raise ValueError(f"{path.name}: missing YAML frontmatter block")

    meta = yaml.safe_load(match.group(1)) or {}
    body = match.group(2).strip()

    required = ("id", "title", "sources")
    for field in required:
        if not meta.get(field):
            raise ValueError(f"{path.name}: missing required field '{field}'")

    sources = meta["sources"]
    if isinstance(sources, str):
        sources = [sources]

    key_ingredients = meta.get("key_ingredients") or []
    tags = meta.get("tags") or []

    return {
        "id": str(meta["id"]).strip(),
        "title": str(meta["title"]).strip(),
        "sources": [str(s).strip() for s in sources],
        "cuisine": meta.get("cuisine"),
        "course": meta.get("course"),
        "servings": meta.get("servings"),
        "tags": [str(t).strip() for t in tags],
        "key_ingredients": [normalize_ingredient(i) for i in key_ingredients],
        "body": body,
        "_file": path.name,
    }


def merge_recipes(recipes: list[dict]) -> list[dict]:
    """Aggressive merge: recipes whose titles match after normalization.

    Ingredient lists are not required to match. Merged recipes union their
    sources, tags and key ingredients, and fill in any missing cuisine /
    course / servings from the duplicates.
    """
    merged: dict[frozenset[str], dict] = {}
    for recipe in recipes:
        key = title_key(recipe["title"])
        if key in merged:
            existing = merged[key]
            for src in recipe["sources"]:
                if src not in existing["sources"]:
                    existing["sources"].append(src)
            for ingredient in recipe["key_ingredients"]:
                if ingredient not in existing["key_ingredients"]:
                    existing["key_ingredients"].append(ingredient)
            for tag in recipe["tags"]:
                if tag not in existing["tags"]:
                    existing["tags"].append(tag)
            for field in ("cuisine", "course", "servings"):
                if not existing.get(field) and recipe.get(field):
                    existing[field] = recipe[field]
            existing.setdefault("merged_from", []).append(recipe["_file"])
            print(
                f"  merged duplicate: '{recipe['title']}' "
                f"({recipe['_file']}) -> {existing['_file']}"
            )
        else:
            merged[key] = recipe
    for recipe in merged.values():
        recipe["sources"].sort()
    return list(merged.values())


def build_ingredient_index(recipes: list[dict]) -> dict[str, list[str]]:
    index: dict[str, set[str]] = {}
    for recipe in recipes:
        for ingredient in recipe["key_ingredients"]:
            index.setdefault(ingredient, set()).add(recipe["id"])
    return {
        ingredient: sorted(ids)
        for ingredient, ids in sorted(index.items())
    }


def main() -> int:
    if not RECIPES_DIR.is_dir():
        sys.exit(f"Missing recipes directory: {RECIPES_DIR}")

    files = sorted(RECIPES_DIR.glob("*.md"))
    if not files:
        sys.exit(f"No recipe markdown files in {RECIPES_DIR}")

    recipes: list[dict] = []
    errors: list[str] = []
    for path in files:
        try:
            recipes.append(parse_recipe(path))
        except ValueError as exc:
            errors.append(str(exc))

    if errors:
        print("Validation errors:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    print(f"Parsed {len(recipes)} recipe file(s).")
    recipes = merge_recipes(recipes)
    recipes.sort(key=lambda r: r["title"].lower())
    print(f"{len(recipes)} unique recipe(s) after de-duplication.")

    ingredient_index = build_ingredient_index(recipes)

    all_sources = sorted({s for r in recipes for s in r["sources"]})
    all_cuisines = sorted({r["cuisine"] for r in recipes if r["cuisine"]})
    all_courses = sorted({r["course"] for r in recipes if r["course"]})

    payload = {
        "recipes": recipes,
        "ingredients": ingredient_index,
        "facets": {
            "sources": all_sources,
            "cuisines": all_cuisines,
            "courses": all_courses,
        },
        "counts": {
            "recipes": len(recipes),
            "ingredients": len(ingredient_index),
            "sources": len(all_sources),
        },
    }

    DATA_DIR.mkdir(exist_ok=True)
    out_path = DATA_DIR / "index.json"
    out_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Wrote {out_path.relative_to(ROOT)}")
    print(
        f"  {payload['counts']['recipes']} recipes, "
        f"{payload['counts']['ingredients']} ingredients, "
        f"{payload['counts']['sources']} source files"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
