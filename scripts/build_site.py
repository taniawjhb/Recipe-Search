"""Generate the static HTML site in site/ from data/index.json.

Produces:
  site/index.html            browse + client-side search
  site/ingredients.html      ingredient index
  site/recipes/<id>.html      one page per recipe (with source trace)
  site/styles.css, search.js  static assets
  site/data/index.json        search index consumed by the browser

Run scripts/build_index.py first.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

try:
    import markdown as md
    import nh3
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:  # pragma: no cover
    sys.exit("Jinja2, markdown and nh3 are required. Run: pip install -r requirements.txt")

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
TEMPLATES = SCRIPTS / "templates"
ASSETS = SCRIPTS / "assets"
DATA = ROOT / "data" / "index.json"
SITE = ROOT / "site"

# Tags/attributes recipe Markdown is allowed to produce. Anything else (e.g.
# raw <script>, <iframe>, event-handler attributes) is stripped by nh3 before
# the HTML is marked safe for the template. Recipes are authored from PDF
# extractions, so this guards against untrusted HTML slipping into a page.
ALLOWED_TAGS = {
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "br", "hr",
    "ul", "ol", "li",
    "strong", "em", "b", "i", "u", "s", "sup", "sub", "small",
    "blockquote", "code", "pre",
    "a", "span", "div",
    "table", "thead", "tbody", "tfoot", "tr", "th", "td",
}
ALLOWED_ATTRIBUTES = {
    "a": {"href", "title"},
    "th": {"align"},
    "td": {"align"},
}


def sanitize_html(html: str) -> str:
    """Strip any tags/attributes not on the recipe allow-list."""
    return nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes={"http", "https", "mailto"},
        link_rel="noopener noreferrer",
    )


def load_index() -> dict:
    if not DATA.is_file():
        sys.exit(f"Missing {DATA}. Run scripts/build_index.py first.")
    return json.loads(DATA.read_text(encoding="utf-8"))


def main() -> int:
    data = load_index()
    recipes = data["recipes"]
    ingredients = data["ingredients"]
    facets = data["facets"]
    counts = data["counts"]

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(["html"]),
    )
    md_renderer = md.Markdown(extensions=["extra", "sane_lists"])

    # Reset output directory.
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "recipes").mkdir(parents=True)
    (SITE / "data").mkdir(parents=True)

    recipe_titles = {r["id"]: r["title"] for r in recipes}

    # Per-recipe pages.
    recipe_tmpl = env.get_template("recipe.html")
    for recipe in recipes:
        md_renderer.reset()
        body_html = sanitize_html(md_renderer.convert(recipe["body"]))
        recipe = {**recipe, "body_html": body_html}
        html = recipe_tmpl.render(recipe=recipe, root="../", counts=counts)
        (SITE / "recipes" / f"{recipe['id']}.html").write_text(html, encoding="utf-8")

    # Browse / search index.
    index_html = env.get_template("index.html").render(
        root="", counts=counts, facets=facets
    )
    (SITE / "index.html").write_text(index_html, encoding="utf-8")

    # Ingredient index.
    ingredients_html = env.get_template("ingredients.html").render(
        root="",
        counts=counts,
        ingredients=ingredients,
        recipe_titles=recipe_titles,
    )
    (SITE / "ingredients.html").write_text(ingredients_html, encoding="utf-8")

    # Menu / shopping list (populated client-side from localStorage).
    menu_html = env.get_template("menu.html").render(root="", counts=counts)
    (SITE / "menu.html").write_text(menu_html, encoding="utf-8")

    # Static assets + client search index.
    shutil.copy2(ASSETS / "styles.css", SITE / "styles.css")
    shutil.copy2(ASSETS / "search.js", SITE / "search.js")
    shutil.copy2(ASSETS / "menu.js", SITE / "menu.js")
    shutil.copy2(DATA, SITE / "data" / "index.json")

    print(f"Built site/ with {len(recipes)} recipe page(s).")
    print(f"  Open: {(SITE / 'index.html')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
