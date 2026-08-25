---
name: ingredient-categorisation
description: 'Classify recipe ingredients / shopping-list items into supermarket categories (Dairy and Eggs; Fruit and Vegetables; Seasonings; Carbs and grains; Meat; Fish; Protein; Tins, Jars & bottles). Use when grouping a shopping list, organising the menu page ingredients, tagging key_ingredients, or when asked to "categorise", "classify", or "group the shopping list" by aisle/section.'
---

# Ingredient Categorisation

The menu page (`site/menu.html` / `scripts/assets/menu.js`) aggregates the
ingredients of every chosen recipe into a single shopping list. This skill
assigns each ingredient to one of the fixed categories below so the list can be
grouped by supermarket section.

## When to Use

- Grouping or ordering a shopping list by aisle.
- Deciding the category for a `key_ingredients` entry.
- Anytime you are asked to "categorise", "classify", or "group" ingredients.

## Categories (use these exact labels, in this order)

1. **Fruit and Vegetables**
2. **Meat**
3. **Fish**
4. **Dairy and Eggs**
5. **Carbs and grains**
6. **Protein**
7. **Tins, Jars & bottles**
8. **Wine & Spirits**
9. **Seasonings**

## Classification Rules

Assign each ingredient to the **first** matching category, checking in the order
below. This ordering resolves overlaps (e.g. canned beans → _Tins, Jars &
bottles_ wins over _Protein_ only when the item is clearly tinned/jarred; a fresh
or dried item goes to its natural category).

1. **Tins, Jars & bottles** — anything explicitly canned, tinned, jarred or
   bottled, or a pantry liquid/condiment sold in a bottle or jar:
   _chopped tomatoes (tin), tinned chickpeas, coconut milk (can), passata,
   tomato paste/purée, jarred pesto, olives (jar), capers, pickles, soy sauce,
   fish sauce, oyster sauce, vinegar, olive/vegetable oil, honey (jar),
   jam, mustard, mayonnaise, ketchup, stock/broth (carton or cube), wine used
   for cooking._

   > If the recipe clearly uses a **fresh** version (fresh tomatoes, fresh
   > beans), classify by the natural category instead.

   > Anything described as a **paste** (tomato paste, curry paste, truffle
   > paste, miso paste, garlic paste) is treated as jarred/tubed → here. Dry
   > spice **powders** are the exception — see Seasonings.

2. **Meat** — poultry and red/other land meats, fresh or frozen, and
   meat-based deli items: _chicken, beef, pork, lamb, turkey, duck, mince,
   bacon, ham, sausages, chorizo, pancetta, prosciutto, veal, offal._

3. **Fish** — fish and seafood, fresh, frozen or fresh from the counter:
   _salmon, cod, tuna (fresh), prawns/shrimp, squid, mussels, clams, crab,
   anchovies (fresh), white fish, smoked salmon._

   > Tinned tuna / tinned anchovies → **Tins, Jars & bottles**.

4. **Dairy and Eggs** — _milk, cream, butter, ghee, yoghurt, cheese (all
   kinds), crème fraîche, sour cream, mascarpone, ricotta, paneer, eggs,
   buttermilk, condensed/evaporated milk (unless clearly canned — then Tins)._

5. **Carbs and grains** — starches, flours, baking staples and bread:
   _flour, rice, pasta, noodles, couscous, bulgur, quinoa, oats, bread,
   breadcrumbs, tortillas, potatoes_ (see note), _polenta, semolina, sugar,
   cornflour, baking powder, baking soda, yeast, cornmeal._

   > **Nuts belong here** by house convention — almonds, walnuts, cashews,
   > pistachios, peanuts, hazelnuts, pecans, pine nuts (whole/flaked/ground).
   > Loose **nut butters** (peanut/almond butter, tahini) stay under Protein.

   > **Sweet sponge bases** used in trifles/desserts sit here too — savoiardi
   > (ladyfingers), sponge fingers, madeira cake, sponge cake, biscuits,
   > cookies.

   > Potatoes may sit under **Fruit and Vegetables** if you prefer produce
   > grouping; default them to **Fruit and Vegetables**.

6. **Protein** — plant proteins and dry legumes not sold tinned:
   _dried lentils, dried beans/chickpeas, tofu, tempeh, edamame, seeds
   (pumpkin/sunflower/sesame/chia/flax), seitan._ (Nuts → Carbs and grains.)

7. **Tins, Jars & bottles** — see rule 1 above (non-alcoholic pantry
   liquids/condiments). **Red/white wine vinegar stays here** — it is a
   condiment, not a drink.

8. **Wine & Spirits** — alcoholic drinks and cooking liquor:
   _red/white/rosé wine, prosecco, champagne, sherry, marsala, madeira wine,
   port, vermouth, brandy, cognac, rum, vodka, gin, whisky, tequila, liqueurs
   (amaretto, kirsch, Grand Marnier, Cointreau, limoncello), ouzo, sake, mirin,
   cider._

   > Checked **after** Tins so "red wine vinegar" is not mistaken for wine.

9. **Seasonings** — herbs, spices, salt, pepper and dry flavourings:
   _salt, black pepper, cumin, coriander (ground), turmeric, paprika, chilli
   powder/flakes, cinnamon, cardamom, cloves, bay leaves, dried herbs, fresh
   herbs (basil, parsley, coriander leaf, mint), stock cubes, vanilla, saffron,
   curry powder, garam masala._

   > **Dried/ground aromatics belong here**, e.g. ground ginger, garlic powder,
   > garlic granules, chilli flakes, chilli powder, dried chillies. Their
   > **fresh** forms (garlic, ginger, chillies) go under **Fruit and
   > Vegetables** — see rule 8.

   > **Dry spice powders default here**, e.g. mustard powder, onion powder,
   > five-spice powder. The exceptions are **baking powder** and **cocoa /
   > custard powder**, which stay under Carbs / Dairy respectively.

10. **Fruit and Vegetables** — the catch-all for fresh produce not matched
    above: _onions, tomatoes (fresh), carrots, peppers, courgettes, aubergine,
    spinach, lettuce, apples, lemons, limes, berries, mushrooms, broccoli,
    cauliflower, cabbage, cucumber, avocado, potatoes (default)._
    > **Fresh garlic, ginger and chillies live here by convention.** Only their
    > dried/ground forms (ground ginger, garlic powder, chilli flakes) go under
    > **Seasonings**.
    > **Bell peppers / capsicums are produce** and belong here, even though bare
    > "pepper" (black/white pepper) is a Seasoning.

## Procedure

1. Strip the quantity and unit from the line (reuse the
   `measurement-standardisation` skill), leaving the ingredient name.
2. Normalise to lowercase and singular where obvious.
3. Walk the rules **1 → 8** and assign the first category that matches.
4. If nothing matches, default to **Fruit and Vegetables** for produce-like
   items, otherwise **Seasonings**.
5. When outputting a grouped shopping list, list the categories in the order
   shown above and omit any empty category.

## Examples

| Ingredient                        | Category             |
| --------------------------------- | -------------------- |
| 2 tablespoons olive oil           | Tins, Jars & bottles |
| 400 grams tinned chopped tomatoes | Tins, Jars & bottles |
| 500 grams chicken thighs          | Meat                 |
| 1 salmon fillet                   | Fish                 |
| 250 grams tinned tuna             | Tins, Jars & bottles |
| 200 grams cheddar cheese          | Dairy and Eggs       |
| 2 eggs                            | Dairy and Eggs       |
| 300 grams basmati rice            | Carbs and grains     |
| 500 grams potatoes                | Fruit and Vegetables |
| 200 grams dried red lentils       | Protein              |
| 100 grams firm tofu               | Protein              |
| 1 teaspoon ground cumin           | Seasonings           |
| 2 cloves garlic                   | Fruit and Vegetables |
| 1 thumb fresh ginger              | Fruit and Vegetables |
| 2 red chillies                    | Fruit and Vegetables |
| 1 teaspoon ground ginger          | Seasonings           |
| 1 teaspoon garlic powder          | Seasonings           |
| 1 teaspoon chilli flakes          | Seasonings           |
| 3 onions                          | Fruit and Vegetables |
| 1 red bell pepper                 | Fruit and Vegetables |
| 1 lemon                           | Fruit and Vegetables |
| 100 grams flaked almonds          | Carbs and grains     |
| 18 savoiardi or madeira cake      | Carbs and grains     |
| 90 millilitres Amaretto           | Wine & Spirits       |
| 60 millilitres dry white wine     | Wine & Spirits       |
| 50 millilitres brandy             | Wine & Spirits       |

## Related

- Unit/measurement standardisation: see the `measurement-standardisation`
  skill.
