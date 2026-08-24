// Client-side "menu" (meal plan) + shopping list — no external dependencies.
// The menu is a list of recipe ids persisted in localStorage so it survives
// navigation and reloads. Any [data-menu-toggle="<id>"] button adds/removes a
// recipe; the menu page (#menu-page) aggregates the ingredients of every chosen
// recipe into a single, de-duplicated shopping list.

(function () {
  const STORAGE_KEY = "recipe-menu";

  function loadIds() {
    try {
      const ids = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
      return Array.isArray(ids) ? ids.filter((x) => typeof x === "string") : [];
    } catch (e) {
      return [];
    }
  }

  const RecipeMenu = {
    ids: loadIds(),
    has(id) {
      return this.ids.includes(id);
    },
    add(id) {
      if (!this.has(id)) {
        this.ids.push(id);
        this._save();
      }
    },
    remove(id) {
      this.ids = this.ids.filter((x) => x !== id);
      this._save();
    },
    toggle(id) {
      if (this.has(id)) this.remove(id);
      else this.add(id);
      return this.has(id);
    },
    clear() {
      this.ids = [];
      this._save();
    },
    count() {
      return this.ids.length;
    },
    _save() {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.ids));
      updateBadges();
      document.dispatchEvent(new CustomEvent("menu:changed"));
    },
  };
  window.RecipeMenu = RecipeMenu;

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    }[c]));
  }

  function reflectButton(btn, inMenu) {
    if (btn.hasAttribute("data-menu-keep-label")) return;
    btn.classList.toggle("in-menu", inMenu);
    btn.textContent = inMenu ? "\u2713 In menu" : "+ Add to menu";
    btn.setAttribute("aria-pressed", inMenu ? "true" : "false");
  }

  function updateBadges() {
    const n = RecipeMenu.count();
    document.querySelectorAll("[data-menu-count]").forEach((el) => {
      el.textContent = n ? " (" + n + ")" : "";
    });
    document.querySelectorAll("[data-menu-toggle]").forEach((btn) => {
      reflectButton(btn, RecipeMenu.has(btn.getAttribute("data-menu-toggle")));
    });
  }
  RecipeMenu.updateBadges = updateBadges;

  // Delegate clicks for every add/remove button on the page.
  document.addEventListener("click", (ev) => {
    const btn = ev.target.closest("[data-menu-toggle]");
    if (!btn) return;
    ev.preventDefault();
    RecipeMenu.toggle(btn.getAttribute("data-menu-toggle"));
  });

  // --- Ingredient extraction ------------------------------------------------

  // Pull the bullet lines out of the "Ingredients" section of a recipe body,
  // including any sub-sections (e.g. "### For the sauce") nested beneath it.
  function extractIngredients(body) {
    const out = [];
    let inSection = false;
    let sectionLevel = 0;
    for (const line of String(body).split(/\r?\n/)) {
      const heading = line.match(/^(#{1,6})\s+(.*)$/);
      if (heading) {
        const level = heading[1].length;
        if (inSection && level <= sectionLevel) inSection = false;
        if (/ingredient/i.test(heading[2])) {
          inSection = true;
          sectionLevel = level;
        }
        continue;
      }
      if (!inSection) continue;
      const item = line.match(/^\s*[-*+]\s+(.*\S)\s*$/);
      if (item) out.push(item[1].trim());
    }
    return out;
  }

  // --- Ingredient categorisation -------------------------------------------
  // Mirrors .github/skills/ingredient-categorisation/SKILL.md. Each ingredient
  // line is assigned to the FIRST matching category; "Fruit and Vegetables" is
  // the catch-all default. Categories are displayed in CATEGORY_ORDER.

  const CATEGORY_ORDER = [
    "Fruit and Vegetables",
    "Meat",
    "Fish",
    "Dairy and Eggs",
    "Carbs and grains",
    "Protein",
    "Tins, Jars & bottles",
    "Seasonings",
  ];

  // Rule 1 — anything clearly canned/jarred/bottled or a pantry condiment.
  const TINS_RE = /\b(tinned|canned|tin of|can of|jarred|jar of|bottled|bottle of|passata|tomato paste|tomato pur[e\u00e9]e|tomato sauce|paste|pesto|capers?|olives|pickle[ds]?|gherkins?|soy sauce|fish sauce|oyster sauce|hoisin|worcestershire|sriracha|hot sauce|chilli sauce|sweet chilli|vinegar|oil|honey|maple syrup|syrup|treacle|molasses|jam|marmalade|chutney|mustard(?! seeds?| powder)|mayonnaise|mayo|ketchup|stock|broth|bouillon|coconut milk|coconut cream|condensed milk|evaporated milk|wine)\b/;
  // House convention for fresh vs dried aromatics.
  const AROMATIC_RE = /\b(garlic|ginger|chilli|chili|chile|chillies|chilies)\b/;
  const DRIED_RE = /\b(ground|powder|powdered|granules|flakes|dried|salt)\b/;
  const NUTBUTTER_RE = /\b(nut butter|peanut butter|almond butter|cashew butter|tahini|butter beans?)\b/;
  const VEGBEAN_RE = /\b(green|runner|french|string|snake|broad)\s+beans?\b|\bbean ?sprouts?\b/;

  const CATEGORY_RULES = [
    ["Meat", /\b(chicken|beef|pork|lamb|turkey|duck|mince|bacon|ham|sausages?|chorizo|pancetta|prosciutto|veal|offal|steaks?|ribeye|sirloin|tenderloin|meatballs?|brisket|rump|salami|pepperoni|guanciale|lardons?|rashers?|cutlets?|drumsticks?)\b/],
    ["Fish", /\b(salmon|cod|tuna|prawns?|shrimps?|squid|calamari|mussels?|clams?|crab|anchov(?:y|ies)|haddock|halibut|sea ?bass|trout|mackerel|sardines?|snapper|scallops?|lobster|octopus|white ?fish)\b/],
    ["Dairy and Eggs", /\b(milk|cream|butter|ghee|yoghurt|yogurt|cheese|cheddar|mozzarella|parmesan|parmigiano|feta|ricotta|mascarpone|paneer|halloumi|eggs?|buttermilk|cr[e\u00e8]me fra[i\u00ee]che|creme fraiche|sour cream|custard|gruy[e\u00e8]re|brie|gouda|pecorino|goats? ?cheese)\b/],
    ["Carbs and grains", /\b(flour|rice|pasta|noodles?|couscous|cous cous|bulg[ua]r|quinoa|oats?|bread|breadcrumbs?|tortillas?|polenta|semolina|sugar|cornflour|cornstarch|corn ?meal|baking powder|baking soda|bicarbonate|yeast|spaghetti|penne|macaroni|lasagne|lasagna|orzo|gnocchi|pastry|filo|phyllo|vermicelli|chocolate|cocoa)\b/],
    ["Protein", /\b(lentils?|chickpeas?|beans?|cannellini|borlotti|tofu|tempeh|edamame|seitan|almonds?|walnuts?|cashews?|pistachios?|peanuts?|hazelnuts?|pecans?|pine ?nuts?|nuts?|pumpkin seeds?|sunflower seeds?|sesame seeds?|chia|flaxseed|linseed)\b/],
    ["Seasonings", /\b(salt|pepper|peppercorns?|cumin|coriander|turmeric|paprika|cinnamon|cardamom|cloves?|bay lea(?:f|ves)|oregano|thyme|rosemary|basil|parsley|mint|dill|sage|tarragon|nutmeg|saffron|curry powder|garam masala|stock cube|spices?|herbs?|za'?atar|sumac|fenugreek|fennel seeds?|mustard seeds?|caraway|nigella|star anise|allspice)\b/],
  ];

  function categoriseIngredient(text) {
    const s = " " + String(text).toLowerCase() + " ";
    if (TINS_RE.test(s)) return "Tins, Jars & bottles";
    if (AROMATIC_RE.test(s)) {
      return DRIED_RE.test(s) ? "Seasonings" : "Fruit and Vegetables";
    }
    if (NUTBUTTER_RE.test(s)) return "Protein";
    if (VEGBEAN_RE.test(s)) return "Fruit and Vegetables";
    if (/\bvanilla\b/.test(s)) return "Seasonings";
    for (const [cat, re] of CATEGORY_RULES) {
      if (re.test(s)) return cat;
    }
    // Any remaining dry "... powder" spice (mustard, onion, five-spice, ...);
    // baking/cocoa/custard powders are already caught as Carbs/Dairy above.
    if (/\bpowder\b/.test(s)) return "Seasonings";
    return "Fruit and Vegetables";
  }

  // --- Menu page ------------------------------------------------------------


  function initMenuPage() {
    const page = document.getElementById("menu-page");
    if (!page) return;

    const recipesEl = document.getElementById("menu-recipes");
    const countEl = document.getElementById("menu-recipe-count");
    const shoppingEl = document.getElementById("shopping-list");
    const clearBtn = document.getElementById("menu-clear");
    const copyBtn = document.getElementById("shopping-copy");
    const printBtn = document.getElementById("shopping-print");

    const byId = {};

    function renderShopping(chosen) {
      const counts = new Map();
      for (const r of chosen) {
        for (const line of extractIngredients(r.body || "")) {
          const key = line.toLowerCase().replace(/\s+/g, " ").trim();
          const cur = counts.get(key);
          if (cur) cur.n += 1;
          else counts.set(key, { text: line, n: 1 });
        }
      }
      shoppingEl.innerHTML = "";
      const items = [...counts.values()];
      if (!items.length) {
        shoppingEl.innerHTML =
          '<li class="result-count">No ingredient lines found for the recipes in your menu.</li>';
        return;
      }
      // Bucket every ingredient into its supermarket category.
      const buckets = new Map();
      for (const it of items) {
        const cat = categoriseIngredient(it.text);
        if (!buckets.has(cat)) buckets.set(cat, []);
        buckets.get(cat).push(it);
      }
      const frag = document.createDocumentFragment();
      let idx = 0;
      for (const cat of CATEGORY_ORDER) {
        const bucket = buckets.get(cat);
        if (!bucket || !bucket.length) continue;
        bucket.sort((a, b) => a.text.localeCompare(b.text));
        const head = document.createElement("li");
        head.className = "shopping-category";
        head.textContent = cat;
        frag.appendChild(head);
        for (const it of bucket) {
          const li = document.createElement("li");
          const id = "sl-" + idx++;
          li.innerHTML =
            '<input type="checkbox" id="' + id + '">' +
            '<label for="' + id + '">' +
            escapeHtml(it.text) +
            (it.n > 1 ? ' <span class="qty">\u00d7' + it.n + "</span>" : "") +
            "</label>";
          frag.appendChild(li);
        }
      }
      shoppingEl.appendChild(frag);
    }

    function renderMenu() {
      const chosen = RecipeMenu.ids.map((id) => byId[id]).filter(Boolean);
      countEl.textContent = chosen.length
        ? chosen.length + (chosen.length === 1 ? " recipe" : " recipes")
        : "No recipes yet";
      recipesEl.innerHTML = "";
      if (!chosen.length) {
        recipesEl.innerHTML =
          '<li class="result-count">Your menu is empty. Browse <a href="index.html">recipes</a> and click \u201cAdd to menu\u201d.</li>';
        shoppingEl.innerHTML = "";
        return;
      }
      const frag = document.createDocumentFragment();
      for (const r of chosen) {
        const meta = [
          r.cuisine,
          r.course,
          r.servings ? "serves " + r.servings : null,
        ]
          .filter(Boolean)
          .map(escapeHtml)
          .join(" &middot; ");
        const li = document.createElement("li");
        li.innerHTML =
          '<div class="recipe-card menu-card">' +
          '<a href="recipes/' +
          encodeURIComponent(r.id) +
          '.html"><h3>' +
          escapeHtml(r.title) +
          "</h3></a>" +
          (meta ? '<div class="card-meta">' + meta + "</div>" : "") +
          '<button type="button" class="menu-toggle in-menu" data-menu-toggle="' +
          escapeHtml(r.id) +
          '" data-menu-keep-label>Remove</button>' +
          "</div>";
        frag.appendChild(li);
      }
      recipesEl.appendChild(frag);
      renderShopping(chosen);
    }

    if (copyBtn) {
      copyBtn.addEventListener("click", () => {
        const lines = [];
        shoppingEl.querySelectorAll("li").forEach((li) => {
          if (li.classList.contains("shopping-category")) {
            lines.push((lines.length ? "\n" : "") + li.textContent.trim());
          } else {
            const label = li.querySelector("label");
            if (label) lines.push("- " + label.textContent.trim());
          }
        });
        const text = lines.join("\n");
        if (!text) return;
        if (navigator.clipboard) {
          navigator.clipboard.writeText(text).then(() => {
            copyBtn.textContent = "Copied!";
            setTimeout(() => (copyBtn.textContent = "Copy"), 1500);
          });
        }
      });
    }
    if (printBtn) printBtn.addEventListener("click", () => window.print());
    if (clearBtn) {
      clearBtn.addEventListener("click", () => {
        if (RecipeMenu.count() && confirm("Clear all recipes from your menu?")) {
          RecipeMenu.clear();
        }
      });
    }

    document.addEventListener("menu:changed", renderMenu);

    fetch("data/index.json")
      .then((res) => res.json())
      .then((data) => {
        (data.recipes || []).forEach((r) => (byId[r.id] = r));
        renderMenu();
      })
      .catch((err) => {
        countEl.textContent = "Failed to load recipes: " + err;
      });
  }

  document.addEventListener("DOMContentLoaded", () => {
    updateBadges();
    initMenuPage();
  });
})();
