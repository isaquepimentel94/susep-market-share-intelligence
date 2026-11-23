const decimal = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const percent = new Intl.NumberFormat("pt-BR", {
  style: "percent", minimumFractionDigits: 2, maximumFractionDigits: 2,
});
const signedPoints = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 3, maximumFractionDigits: 3, signDisplay: "exceptZero",
});
const signedInteger = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0, signDisplay: "exceptZero" });
const currency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const alphabetical = new Intl.Collator("pt-BR", { numeric: true });
const asPoints = (value) => signedPoints.format(value) + " pts";
const asPosition = (value) => String(value) + "°";

function compact(value, units) {
  const unit = units.find(([minimum]) => Math.abs(value) >= minimum);
  return unit ? decimal.format(value / unit[0]) + " " + unit[1] : decimal.format(value);
}

const cardGroups = [
  ["01. Impacto sobre a referência", [
    ["referencePositionBefore", "Posição atual", asPosition],
    ["referencePositionAfter", "Posição após M&A", asPosition],
    ["positionImpact", "Variação de posições", (value) => signedInteger.format(value) + "°"],
  ]],
  ["02. Entidade resultante", [
    ["combinedPremium", "Prêmios combinados", (value) => compact(value, [[1e9, "Bi"], [1e6, "Mi"], [1e3, "Mil"]]), currency.format],
    ["combinedShare", "Participação combinada", percent.format],
    ["combinedPosition", "Posição resultante", String],
  ]],
  ["03. Concentração do mercado", [
    ["hhiBefore", "HHI atual", (value) => compact(value, [[1e3, "Mil"]]), decimal.format],
    ["hhiAfter", "HHI após M&A", (value) => compact(value, [[1e3, "Mil"]]), decimal.format],
    ["hhiImpact", "Variação do HHI", asPoints],
  ]],
];

const geographicColumns = [
  ["code", "UF"],
  ["combinedPremium", "Prêmios combinados (R$)", decimal.format],
  ["marketPremium", "Mercado da UF (R$)", decimal.format],
  ["combinedShare", "Market Share combinado (%)", percent.format],
  ["hhiImpact", "Δ HHI", asPoints],
];

const branchColumns = [
  ["name", "Grupo de ramos"],
  ["referencePremium", "Referência (R$)", decimal.format],
  ["premiumA", "Seguradora A (R$)", decimal.format],
  ["premiumB", "Seguradora B (R$)", decimal.format],
  ["combinedPremium", "Prêmios combinados (R$)", decimal.format],
  ["competitivePressure", "Combinado / Referência (%)", percent.format],
  ["marketPremium", "Mercado Grupo M&A", decimal.format],
  ["combinedShare", "Participação combinada (%)", percent.format],
  ["hhiImpact", "Δ HHI", asPoints],
];

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function format(value, formatter, empty = "") {
  return value == null ? empty : formatter(Number(value));
}

function cardsPanel() {
  const node = element("div", "ma-card-groups");
  const renderers = [];
  for (const [index, [title, fields]] of cardGroups.entries()) {
    const group = element("section", "ma-card-group");
    const heading = element("h2", "", title);
    heading.id = "ma-group-" + index;
    group.setAttribute("aria-labelledby", heading.id);
    const cards = element("dl", "ma-cards");
    for (const [key, label, formatter, precise] of fields) {
      const item = element("div", "card");
      const value = element("dd", "", "—");
      value.dataset.maCard = key;
      item.append(element("dt", "", label), value);
      cards.append(item);
      renderers.push((newCards) => {
        const raw = newCards?.[key];
        value.textContent = format(raw, formatter, "—");
        if (raw != null && precise) value.title = precise(Number(raw));
        else value.removeAttribute("title");
      });
    }
    group.append(heading, cards);
    node.append(group);
  }
  return { node, render: (data) => renderers.forEach((update) => update(data)) };
}

function detailPanel({ key, heading, description, columns, sortKey, descending, onSelect }) {
  const node = element("section", "chart-panel ma-" + key);
  const title = element("h2", "", heading);
  title.id = "ma-" + key + "-title";
  node.setAttribute("aria-labelledby", title.id);
  const scroll = element("div", "table-scroll");
  scroll.tabIndex = 0;
  scroll.setAttribute("role", "region");
  scroll.setAttribute("aria-labelledby", title.id);
  const table = element("table");
  const header = table.createTHead().insertRow();
  const body = table.createTBody();
  const footer = table.createTFoot().insertRow();
  const headers = new Map();
  let tableData;
  let active;

  for (const [field, label] of columns) {
    const cell = element("th");
    cell.scope = "col";
    const button = element("button", "", label);
    button.type = "button";
    button.addEventListener("click", () => {
      descending = sortKey === field ? !descending : false;
      sortKey = field;
      render(tableData, active);
    });
    cell.append(button);
    header.append(cell);
    headers.set(field, cell);
  }

  function render(data, selected) {
    tableData = data;
    active = selected;
    for (const [field, cell] of headers) {
      if (field === sortKey) cell.setAttribute("aria-sort", descending ? "descending" : "ascending");
      else cell.removeAttribute("aria-sort");
    }
    const previousFocus = body.contains(document.activeElement) ? document.activeElement.dataset.maRow : null;
    const rows = [...(data?.rows || [])].sort((a, b) => {
      const left = a[sortKey];
      const right = b[sortKey];
      if (left == null || right == null) return Number(left == null) - Number(right == null) || alphabetical.compare(a.code, b.code);
      const primary = columns[0][0] === sortKey ? alphabetical.compare(left, right) : Number(left) - Number(right);
      return (descending ? -primary : primary) || alphabetical.compare(a.code, b.code);
    });
    const fragment = document.createDocumentFragment();
    let restore;
    for (const row of rows) {
      const item = element("tr");
      item.toggleAttribute("data-selected", row.code === selected);
      const [field] = columns[0];
      const label = element("th");
      label.scope = "row";
      const target = element("button", "branch-button", row[field]);
      target.type = "button";
      target.dataset.maRow = row.code;
      target.setAttribute("aria-pressed", String(row.code === selected));
      if (row.code === previousFocus) restore = target;
      label.append(target);
      item.append(label);
      item.addEventListener("click", () => onSelect(row.code));
      for (const [valueKey, , formatter] of columns.slice(1)) {
        item.append(element("td", "", format(row[valueKey], formatter)));
      }
      fragment.append(item);
    }
    if (!rows.length) {
      const empty = element("tr");
      const cell = element("td", "empty-cell", "Sem dados para a seleção e o período informados.");
      cell.colSpan = columns.length;
      empty.append(cell);
      fragment.append(empty);
    }
    body.replaceChildren(fragment);
    const total = element("th", "", "Total");
    total.scope = "row";
    footer.replaceChildren(total, ...columns.slice(1).map(([field, , formatter]) => (
      element("td", "", format(data?.total[field], formatter))
    )));
    footer.hidden = !rows.length;
    restore?.focus({ preventScroll: true });
  }

  scroll.append(table);
  node.append(title, element("p", "chart-subtitle", description), scroll);
  return { node, render };
}

export function mountMa(host, onChange) {
  let selection = null;
  let current;
  function select(table, param, code) {
    selection = selection?.table === table && selection.code === code ? null : { table, param, code };
    render(current);
    onChange();
  }
  const cards = cardsPanel();
  const uf = detailPanel({
    key: "uf", heading: "Impacto geográfico da operação",
    description: "Participação da entidade resultante e variação da concentração de mercado por UF.",
    columns: geographicColumns, sortKey: "code", descending: false,
    onSelect: (code) => select("uf", "uf", code),
  });
  const branches = detailPanel({
    key: "branches", heading: "Sobreposição competitiva por grupo de ramos",
    description: "Comparação dos prêmios diretos da referência e das seguradoras envolvidas na operação hipotética.",
    columns: branchColumns, sortKey: "premiumB", descending: true,
    onSelect: (code) => select("branches", "selected_branch_group", code),
  });
  const layout = element("div", "ma-layout");
  layout.append(cards.node, uf.node, branches.node);
  host.append(layout);

  function render(data) {
    current = data;
    cards.render(data?.cards);
    uf.render(data?.uf, selection?.table === "uf" ? selection.code : null);
    branches.render(data?.branches, selection?.table === "branches" ? selection.code : null);
  }

  return {
    getSelection: () => selection,
    clearSelection: () => { selection = null; },
    render,
  };
}
