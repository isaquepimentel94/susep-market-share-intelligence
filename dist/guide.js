const fields = ["definition", "formula", "interpretation", "source"];
const alphabetical = new Intl.Collator("pt-BR");

export function guideCards({ entries, fallback }, category, indicator) {
  const selection = entries.filter((entry) =>
    (!category || entry.category === category) && (!indicator || entry.indicator === indicator)
  );
  // SELECTEDVALUE uses distinct values of the individual column.
  return Object.fromEntries(fields.map((field) => {
    const values = new Set(selection.map((entry) => entry[field]));
    return [field, values.size === 1 ? values.values().next().value : fallback];
  }));
}

export function mountGuide(host, data) {
  const category = host.querySelector("#guide-category");
  const indicator = host.querySelector("#guide-indicator");
  const outputs = new Map(fields.map((field) =>
    [field, host.querySelector('[data-guide-field="' + field + '"]')]
  ));
  const categories = [...new Set(data.entries.map((entry) => entry.category))].sort(alphabetical.compare);
  category.replaceChildren(new Option("Todas", ""),
    ...categories.map((name) => new Option(name, name)));
  category.value = data.defaults.category;

  function renderCards() {
    const cards = guideCards(data, category.value, indicator.value);
    for (const [field, output] of outputs) output.textContent = cards[field] ?? "";
  }

  function renderIndicators(current) {
    const available = new Set(data.entries
      .filter((entry) => !category.value || entry.category === category.value)
      .map((entry) => entry.indicator));
    const visible = [...available];
    // Power BI keeps the previously selected indicator when its category changes.
    if (current && !available.has(current)) visible.push(current);
    visible.sort(alphabetical.compare);
    indicator.replaceChildren(new Option("Todos", ""), ...visible.map((name) => {
      const option = new Option(name, name);
      option.disabled = !available.has(name);
      return option;
    }));
    indicator.value = current;
    renderCards();
  }

  category.addEventListener("change", () => renderIndicators(indicator.value));
  indicator.addEventListener("change", () => renderIndicators(indicator.value));
  renderIndicators(data.defaults.indicator);
  category.disabled = false;
  indicator.disabled = false;
}
