# Recipe Search

Extracts recipes from a folder of cookbook PDFs, rewrites each into a consistent
Markdown format, and generates a **searchable static HTML site** with a recipe
index, an ingredient index, and a source trace showing which PDF(s) each recipe
came from (all sources are listed when a recipe appears in more than one file).
For Tania and her friends.

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

One command runs extraction, the authoring check, the index build and the site
build in order:

```powershell
python scripts\run_pipeline.py
```

It extracts every PDF in `raw/`, then **stops if any cookbook has no recipes
yet**, listing which ones still need authoring (step 2 below) so the index is
never silently out of date. Once everything is authored, build with:

```powershell
python scripts\run_pipeline.py --skip-extract   # rebuild index + site
python scripts\run_pipeline.py --serve          # build, then serve on localhost
python scripts\run_pipeline.py --force          # build even if some are unauthored
```

### Adding a new cookbook (repeatable process)

1. Drop the cookbook PDF(s) into `raw/`.
2. Run `python scripts\run_pipeline.py` — it extracts the text and tells you
   which cookbooks still need recipes.
3. **Author** one `recipes/*.md` per recipe from the matching
   `extracted/*.txt` (see "Recipe format" below). Layouts vary between
   cookbooks, so this step is done with AI assistance rather than brittle rules
   — the reusable prompt in
   [.github/prompts/process-cookbook-pdfs.prompt.md](.github/prompts/process-cookbook-pdfs.prompt.md)
   captures the full workflow and conventions.
4. Re-run `python scripts\run_pipeline.py --skip-extract` to rebuild
   `data/index.json` and the `site/`.

The individual steps can still be run on their own:

```powershell
python scripts\extract_text.py   # 1. raw/*.pdf  -> extracted/*.txt
#                                 # 2. author extracted text into recipes/*.md
python scripts\build_index.py    # 3. recipes/   -> data/index.json
python scripts\build_site.py     # 4. index.json -> site/
```

## Viewing the site

The client-side search loads `data/index.json` via `fetch`, so serve the folder
over HTTP (opening `index.html` directly via `file://` will block the fetch):

```powershell
python -m http.server -d site 8000 --bind 127.0.0.1
# then open http://localhost:8000
```

`--bind 127.0.0.1` keeps the server reachable only from this machine. Without it,
`http.server` listens on all network interfaces, exposing the `site/` folder to
anyone on the same network. `http.server` is a development server only — do not
expose it to the public internet.

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
description: Spiced cumin potatoes, served as an Indian side dish. # optional
author: The Secret Jozi Chef # optional
prep_time: PT15M # optional ISO 8601 duration
cook_time: PT30M # optional ISO 8601 duration
total_time: PT45M # optional ISO 8601 duration
image: https://example.com/aloo-jeera.jpg # optional absolute URL
url: https://example.com/recipes/aloo-jeera # optional canonical URL
---

## Ingredients

- 6 medium potatoes

## Method

1. ...

## Notes (optional)
```

The optional rich metadata fields are emitted in the Schema.org recipe JSON and
embedded as JSON-LD in each generated recipe page. Use ISO 8601 durations for
times, for example `PT45M` (45 minutes) or `PT1H30M` (1 hour, 30 minutes).

To also export one Schema.org Recipe JSON file per recipe for Mealie:

```powershell
python scripts\export_mealie_json.py
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
