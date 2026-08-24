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
      const items = [...counts.values()].sort((a, b) =>
        a.text.localeCompare(b.text)
      );
      shoppingEl.innerHTML = "";
      if (!items.length) {
        shoppingEl.innerHTML =
          '<li class="result-count">No ingredient lines found for the recipes in your menu.</li>';
        return;
      }
      const frag = document.createDocumentFragment();
      items.forEach((it, i) => {
        const li = document.createElement("li");
        const id = "sl-" + i;
        li.innerHTML =
          '<input type="checkbox" id="' + id + '">' +
          '<label for="' + id + '">' +
          escapeHtml(it.text) +
          (it.n > 1 ? ' <span class="qty">\u00d7' + it.n + "</span>" : "") +
          "</label>";
        frag.appendChild(li);
      });
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
        const text = [...shoppingEl.querySelectorAll("label")]
          .map((l) => "- " + l.textContent.trim())
          .join("\n");
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
