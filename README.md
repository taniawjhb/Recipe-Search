# Recipe Search

Extracts recipes from a folder of cookbook PDFs, rewrites each into a consistent
Markdown format, and generates a **searchable static HTML site** with a recipe
index, an ingredient index, and a source trace showing which PDF(s) each recipe
came from (all sources are listed when a recipe appears in more than one file).

## Layout

```
raw/          Source cookbook PDFs (input, untouched)
extracted/    Intermediate plain-text extracted from each PDF
recipes/      One Markdown file per recipe — the source of truth
data/         Generated index.json (recipes + ingredient index)
site/         Generated static HTML site (open index.html)
scripts/      Pipeline scripts, templates and assets
```

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Pipeline

```powershell
# 1. Extract selectable text from every PDF in raw/ -> extracted/*.txt
python scripts\extract_text.py

# 2. (Authoring) Turn extracted text into structured recipes/*.md
#    See "Recipe format" below. Layouts vary between cookbooks, so this step
#    is done with AI assistance rather than brittle rules.

# 3. Build the search index (parses recipes/, de-duplicates, writes data/index.json)
python scripts\build_index.py

# 4. Generate the static site into site/
python scripts\build_site.py
```

## Viewing the site

The client-side search loads `data/index.json` via `fetch`, so serve the folder
over HTTP (opening `index.html` directly via `file://` will block the fetch):

```powershell
python -m http.server -d site 8000
# then open http://localhost:8000
```

## Recipe format

Each file in `recipes/` is Markdown with a YAML frontmatter block:

```markdown
---
id: aloo-jeera # unique slug, matches the filename
title: Aloo Jeera
sources: # every PDF this recipe was found in
  - World of Curries.pdf
cuisine: Indian # or null
course: side # starter | main | side | dessert | drink | ...
servings: 4 # integer or null
tags: [vegetarian, vegan]
key_ingredients: # normalized core ingredients, for search + index
  - potato
  - turmeric
---

## Ingredients

- 6 medium potatoes

## Method

1. ...

## Notes (optional)
```

## Duplicate handling

`build_index.py` uses **aggressive** de-duplication: recipes are merged when their
titles match after normalization (accent-insensitive, `&` treated as `and`, common
stop-words dropped, word order ignored) — the ingredient lists do not need to match.
Merged recipes appear once, with every originating PDF listed under _Sources_ on the
recipe page and their tags / key ingredients unioned.

Where the same cookbook was supplied as two identical PDF files, the duplicate copy
was removed from `raw/` and only the single remaining file is referenced.

## Search

`site/search.js` is a dependency-free client-side search over `data/index.json`,
matching recipe title, ingredients, cuisine, course, tags and source file. The
ingredient index page (`ingredients.html`) lists every key ingredient with links
to the recipes that use it.
