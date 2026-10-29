---
mode: agent
description: Process new cookbook PDFs in raw/ into recipes and rebuild the searchable site.
---

# Process new cookbook PDFs

Turn one or more new cookbook PDFs into recipes and refresh the static site.
The deterministic steps are scripted; the authoring step needs your judgement.

## Inputs

New PDF(s) have been added to `raw/`. If the user named specific files, only
author recipes from those; otherwise process every cookbook in `raw/` that has
no recipes yet.

## Procedure

1. **Extract** the PDF text:
   `python scripts/run_pipeline.py` (it stops at the authoring check and lists
   any cookbooks that still need recipes). You can also run
   `python scripts/extract_text.py` directly.

2. **Read** the matching `extracted/<Cookbook>.txt` in full. Pages are separated
   by `----- PAGE n -----`. Ignore repeated boilerplate (addresses, footers).

3. **Author one `recipes/<slug>.md` per recipe** using the format below. Apply
   the repo skills:
   - `measurement-standardisation` — full-word units, ASCII fractions (`1/2`),
     temperatures like `180°C`.
   - `ingredient-categorisation` — choosing `key_ingredients`.

4. **Slugs / de-duplication**:
   - `build_index.py` merges recipes whose titles match after normalisation
     (accent-insensitive, `&`→`and`, stop-words dropped, word order ignored).
   - If a recipe is the same dish as an existing one, reuse that recipe's exact
     title so the sources merge, and give the new file the next free numeric
     suffix (`-2`, `-3`, …). The `id` must equal the filename stem.
   - `sources:` must be the **exact** PDF filename, including spaces and case.

5. **Build**: `python scripts/run_pipeline.py --skip-extract` (or `--force` once
   every cookbook is authored). Confirm the new source appears and the counts
   look right. Preview with `python scripts/run_pipeline.py --serve`.

Do not edit anything in `raw/` or `extracted/`. Do not create documentation
files unless asked.

## Recipe file format

```markdown
---
id: <slug> # unique, matches the filename stem
title: <Recipe Title>
sources:
  - <Exact Cookbook File.pdf>
cuisine: <e.g. Thai, or null>
course: starter | main | side | dessert | drink | sauce | ...
servings: <integer or null>
tags: [vegetarian, ...]
key_ingredients:
  - <normalised core ingredient>
---

## Ingredients

- <quantity> <unit> <ingredient>

## Method

1. <step>

## Notes (optional)
```
