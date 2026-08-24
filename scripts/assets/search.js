// Client-side recipe search over data/index.json — no external dependencies.
// Matches on recipe title, ingredients, cuisine, course, tags and source file.

(function () {
  const listEl = document.getElementById("recipe-list");
  const countEl = document.getElementById("result-count");
  const searchInput = document.getElementById("search-input");
  const cuisineSel = document.getElementById("filter-cuisine");
  const courseSel = document.getElementById("filter-course");
  const sourceSel = document.getElementById("filter-source");

  let recipes = [];

  function haystack(r) {
    return [
      r.title,
      r.cuisine || "",
      r.course || "",
      (r.tags || []).join(" "),
      (r.key_ingredients || []).join(" "),
      (r.sources || []).join(" "),
    ]
      .join(" ")
      .toLowerCase();
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, (c) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    }[c]));
  }

  function render(items) {
    listEl.innerHTML = "";
    countEl.textContent =
      items.length + (items.length === 1 ? " recipe" : " recipes");

    if (!items.length) {
      listEl.innerHTML = '<li class="result-count">No recipes match your search.</li>';
      return;
    }

    const frag = document.createDocumentFragment();
    for (const r of items) {
      const li = document.createElement("li");
      const meta = [r.cuisine, r.course, r.sources.length > 1 ? r.sources.length + " sources" : r.sources[0]]
        .filter(Boolean)
        .map(escapeHtml)
        .join(" &middot; ");
      const ing = (r.key_ingredients || []).slice(0, 8).map(escapeHtml).join(", ");
      li.innerHTML =
        '<a class="recipe-card" href="recipes/' + encodeURIComponent(r.id) + '.html">' +
        "<h3>" + escapeHtml(r.title) + "</h3>" +
        '<div class="card-meta">' + meta + "</div>" +
        (ing ? '<div class="card-ingredients">' + ing + "</div>" : "") +
        "</a>" +
        '<button type="button" class="menu-toggle" data-menu-toggle="' +
        escapeHtml(r.id) + '">+ Add to menu</button>';
      frag.appendChild(li);
    }
    listEl.appendChild(frag);
  }

  function apply() {
    const q = (searchInput.value || "").trim().toLowerCase();
    const terms = q.split(/\s+/).filter(Boolean);
    const cuisine = cuisineSel.value;
    const course = courseSel.value;
    const source = sourceSel.value;

    const filtered = recipes.filter((r) => {
      if (cuisine && r.cuisine !== cuisine) return false;
      if (course && r.course !== course) return false;
      if (source && !(r.sources || []).includes(source)) return false;
      if (!terms.length) return true;
      const hay = r._hay;
      return terms.every((t) => hay.includes(t));
    });
    render(filtered);
    if (window.RecipeMenu) window.RecipeMenu.updateBadges();
  }

  fetch("data/index.json")
    .then((res) => res.json())
    .then((data) => {
      recipes = data.recipes || [];
      recipes.forEach((r) => (r._hay = haystack(r)));
      [searchInput, cuisineSel, courseSel, sourceSel].forEach((el) =>
        el && el.addEventListener("input", apply)
      );
      apply();
    })
    .catch((err) => {
      countEl.textContent = "Failed to load recipe index: " + err;
    });
})();
