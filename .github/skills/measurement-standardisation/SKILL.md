---
name: measurement-standardisation
description: 'Standardise units and measurements when authoring or cleaning up recipe Markdown in recipes/. Use when converting abbreviated units to full words (tbsp → tablespoons, g → grams, ml → millilitres, °C, etc.), normalising quantities and fractions, or making ingredient/method wording consistent across recipes. Trigger when writing a new recipe, importing text from extracted/*.txt, or asked to "standardise", "normalise units", or "tidy the measurements".'
---

# Measurement Standardisation

Recipes in this project (`recipes/*.md`) come from many different cookbooks with
inconsistent unit styles. This skill defines the single house style so every
recipe reads the same way.

## When to Use

- Authoring a new recipe from `extracted/*.txt` (pipeline step 2).
- Cleaning up or reviewing an existing `recipes/*.md` file.
- Anytime you are asked to "standardise", "normalise", or "tidy" measurements.

## House Style Rules

1. **Spell out units in full**, singular or plural as appropriate for the
   quantity (1 gram, 200 grams). Do not use abbreviations in ingredient lines
   or the method.
2. **Number then unit, separated by one space**: `200 grams`, not `200g` or
   `200 g.`.
3. **Use words for small counts of whole items** only where natural
   (`2 eggs`), otherwise keep the numeral.
4. **Fractions**: use plain ASCII fractions written with `/`
   (`1/2`, `1/4`, `3/4`), not Unicode glyphs (½, ¼, ¾).
5. **Ranges** use an en dash with spaces converted to a hyphen for plain text:
   `2-3 tablespoons`.
6. **Temperatures**: `180°C` (no space, degree symbol, capital C). If a fan
   oven value is given, keep it in brackets: `180°C (160°C fan)`.
7. **Prefer metric.** If only imperial is given, keep it but you may add a
   metric equivalent in brackets where helpful.
8. Keep the quantity at the **start of the ingredient line**, e.g.
   `- 2 tablespoons olive oil`.

## Conversion Table (abbreviation → standard word)

Apply these substitutions (case-insensitive) whenever the abbreviation appears
as a unit:

| Abbreviation(s)                    | Standard form              |
| ---------------------------------- | -------------------------- |
| `tsp`, `t`, `tsp.`                 | teaspoon / teaspoons       |
| `tbsp`, `tbs`, `tbl`, `T`, `tbsp.` | tablespoon / tablespoons   |
| `g`, `gr`, `gm`, `grm`             | gram / grams               |
| `kg`, `kgs`                        | kilogram / kilograms       |
| `mg`                               | milligram / milligrams     |
| `ml`, `mL`, `mls`                  | millilitre / millilitres   |
| `l`, `L`, `ltr`                    | litre / litres             |
| `cl`                               | centilitre / centilitres   |
| `dl`                               | decilitre / decilitres     |
| `oz`                               | ounce / ounces             |
| `lb`, `lbs`, `#`                   | pound / pounds             |
| `fl oz`, `floz`                    | fluid ounce / fluid ounces |
| `pt`                               | pint / pints               |
| `qt`                               | quart / quarts             |
| `gal`                              | gallon / gallons           |
| `c`, `cup`                         | cup / cups                 |
| `pkt`, `pkg`, `pk`                 | packet / packets           |
| `tin`, `cn`, `can`                 | tin / tins                 |
| `pinch`                            | pinch (leave as-is)        |
| `doz`                              | dozen                      |
| `cm`                               | centimetre / centimetres   |
| `mm`                               | millimetre / millimetres   |
| `in`, `"`                          | inch / inches              |
| `°`, `deg`, `degrees`              | ° (use with C or F)        |
| `C`, `celsius`, `centigrade`       | °C                         |
| `F`, `fahrenheit`                  | °F                         |
| `min`, `mins`                      | minute / minutes           |
| `hr`, `hrs`, `h`                   | hour / hours               |
| `sec`, `secs`                      | second / seconds           |

### Singular vs plural

- Use the **singular** when the quantity is exactly `1` (or a fraction of 1):
  `1 tablespoon`, `1/2 teaspoon`.
- Use the **plural** for every other quantity: `2 tablespoons`, `0 grams`,
  `1.5 litres`, `200 grams`.

## Procedure

1. Read the ingredient line or method sentence.
2. Identify each `<number><unit>` or `<number> <unit>` token.
3. Replace the unit with its standard word from the table, choosing singular or
   plural based on the quantity.
4. Ensure exactly one space sits between the number and the unit.
5. Normalise fractions to ASCII `/` form and temperatures to `°C` form.
6. Leave the ingredient name and any descriptors untouched.

## Examples

| Before                       | After                           |
| ---------------------------- | ------------------------------- |
| `- 2 tbsp olive oil`         | `- 2 tablespoons olive oil`     |
| `- 200g plain flour`         | `- 200 grams plain flour`       |
| `- 1 tsp salt`               | `- 1 teaspoon salt`             |
| `- 250ml milk`               | `- 250 millilitres milk`        |
| `- ½ cup rice`               | `- 1/2 cup rice`                |
| `Bake at 180 C for 25 mins.` | `Bake at 180°C for 25 minutes.` |
| `- 1kg potatoes`             | `- 1 kilogram potatoes`         |
| `- 1 lb 4 oz beef`           | `- 1 pound 4 ounces beef`       |

## Related

- Ingredient categorisation for the shopping list: see the
  `ingredient-categorisation` skill.
