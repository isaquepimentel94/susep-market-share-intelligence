const byId = (id) => document.getElementById(id);
const svgNS = "http://www.w3.org/2000/svg";
const blank = "—";
const decimal = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const simpleDecimal = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const currency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const ramp = [[179, 216, 242], [88, 166, 229], [36, 111, 174]];
const statePaths = new Map();
const mapHost = byId("uf-map");
let geometry;
let map;
let tooltip;
let renderState;

function create(tag, classname, text) {
  const element = document.createElement(tag);
  if (classname) element.className = classname;
  if (text !== undefined) element.textContent = text;
  return element;
}

function numeric(value) {
  return value === null || value === undefined ? null : Number(value);
}

function text(value, formatter) {
  const number = numeric(value);
  return number !== null && Number.isFinite(number) ? formatter(number) : blank;
}

function compact(value) {
  const unit = [[1e9, "Bi"], [1e6, "Mi"], [1e3, "mil"]].find(([size]) => Math.abs(value) >= size);
  return unit ? simpleDecimal.format(value / unit[0]) + " " + unit[1] : currency.format(value);
}

function percentage(value) {
  return text(value, (number) => decimal.format(number) + "%");
}

function points(value) {
  return text(value, (number) => decimal.format(number) + " p.p.");
}

function mapColor(value, min, max) {
  const ratio = max === min ? 0 : Math.max(0, Math.min(1, (value - min) / (max - min)));
  const step = ratio > 0.5 ? 1 : 0;
  const amount = ratio * 2 - step;
  const shade = ramp[step].map((base, i) => Math.round(base + (ramp[step + 1][i] - base) * amount));
  return "rgb(" + shade.join(",") + ")";
}

function hideTooltip() {
  if (tooltip) tooltip.hidden = true;
}

function setTooltipPosition(event, path) {
  const hostRect = mapHost.getBoundingClientRect();
  const pathRect = path.getBoundingClientRect();
  const x = (event?.clientX ?? pathRect.left + pathRect.width / 2) - hostRect.left;
  const y = (event?.clientY ?? pathRect.top + pathRect.height / 2) - hostRect.top;
  const tipWidth = tooltip.offsetWidth;
  const tipHeight = tooltip.offsetHeight;
  tooltip.style.left = Math.max(4, Math.min(hostRect.width - tipWidth - 4, x + 12)) + "px";
  tooltip.style.top = Math.max(4, Math.min(hostRect.height - tipHeight - 4, y + 10)) + "px";
}

function showTooltip(code, path, event) {
  const state = renderState?.states.get(code);
  if (!state) return;
  const description = create("dl");
  const fields = [
    ["Market Share Comparável UF (%)", percentage(state.share)],
    ["Posição Comparável UF", text(state.mapPosition, (value) => value + "º")],
    ["Prêmios Seguradora Comparável UF", text(state.premium, (value) => currency.format(value))],
  ];
  for (const [label, value] of fields) {
    description.append(create("dt", null, label), create("dd", null, value));
  }
  tooltip.replaceChildren(create("strong", null, state.mapName || state.name || code), description);
  tooltip.hidden = false;
  setTooltipPosition(event, path);
}

function buildMap(shape) {
  const image = document.createElementNS(svgNS, "svg");
  image.setAttribute("viewBox", shape.viewBox);
  image.setAttribute("role", "group");
  image.setAttribute("aria-label", "Mapa do Brasil por unidade federativa");
  image.classList.add("uf-map-image");
  image.addEventListener("click", (event) => {
    if (event.target === image && renderState?.selection) renderState.onSelect(null);
  });
  for (const { uf, d } of shape.paths) {
    const path = document.createElementNS(svgNS, "path");
    path.setAttribute("d", d);
    path.setAttribute("fill-rule", "evenodd");
    path.setAttribute("vector-effect", "non-scaling-stroke");
    path.classList.add("uf-shape");
    if (uf) {
      path.setAttribute("role", "button");
      path.setAttribute("tabindex", "0");
      path.dataset.uf = uf;
      statePaths.set(uf, path);
      path.addEventListener("pointerenter", (event) => showTooltip(uf, path, event));
      path.addEventListener("pointermove", (event) => {
        if (!tooltip.hidden) setTooltipPosition(event, path);
      });
      path.addEventListener("pointerleave", () => {
        if (document.activeElement !== path) hideTooltip();
      });
      path.addEventListener("focus", () => showTooltip(uf, path));
      path.addEventListener("blur", hideTooltip);
      path.addEventListener("click", () => toggleUf(uf, "map"));
      path.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          toggleUf(uf, "map");
        } else if (event.key === "Escape") {
          hideTooltip();
        }
      });
    } else {
      path.classList.add("uf-disputed");
      path.setAttribute("aria-hidden", "true");
    }
    image.append(path);
  }
  tooltip = create("div", "uf-map-tooltip");
  tooltip.hidden = true;
  tooltip.setAttribute("role", "tooltip");
  mapHost.replaceChildren(image, tooltip);
  return image;
}

function toggleUf(uf, source) {
  if (!renderState?.states.has(uf)) return;
  const { selection, onSelect } = renderState;
  const current = selection?.uf === uf && selection.source === source;
  onSelect(current ? null : { uf, source });
}

function drawMap() {
  const values = [...renderState.states.values()].map(({ share }) => numeric(share) ?? 0);
  const min = values.length ? Math.min(...values) : 0;
  const max = values.length ? Math.max(...values) : 0;
  for (const [code, path] of statePaths) {
    const row = renderState.states.get(code);
    const share = numeric(row?.share);
    const selected = renderState.selection?.uf === code;
    const selectionSource = renderState.selection?.uf && !selected ? renderState.selection.source : "";
    path.setAttribute("fill", mapColor(share ?? 0, min, max));
    path.dataset.unselected = selectionSource;
    path.setAttribute("aria-label", (row?.name || row?.mapName || code) + ", participação " + percentage(share)
      + ", prêmios " + text(row?.premium, (value) => currency.format(value))
      + ", posição " + text(row?.mapPosition, (value) => value + "º"));
    path.setAttribute("aria-pressed", String(selected));
    path.setAttribute("aria-disabled", String(!row));
  }
  const active = document.activeElement;
  if (active?.classList.contains("uf-shape")) showTooltip(active.dataset.uf, active);
}

async function ensureMap() {
  if (!geometry) {
    geometry = fetch(new URL("./uf-map.json", import.meta.url))
      .then((response) => {
        if (!response.ok) throw new Error("Mapa indisponível");
        return response.json();
      })
      .catch((error) => {
        geometry = null;
        throw error;
      });
  }
  try {
    const shape = await geometry;
    if (!renderState) return;
    if (!map || !map.isConnected) map = buildMap(shape);
    drawMap();
  } catch (error) {
    if (renderState) mapHost.replaceChildren(create("p", "status", "Não foi possível carregar o mapa do Brasil."));
  }
}

function drawLegend() {
  const legend = byId("uf-legend");
  if (legend.childElementCount) return;
  const strip = create("div", "uf-color-strip");
  strip.setAttribute("aria-hidden", "true");
  const labels = create("div", "uf-color-labels");
  labels.append(create("span", null, "Menor participação"), create("span", null, "Maior participação"));
  legend.append(strip, labels);
}

function drawCards(cards, total) {
  byId("uf-coverage").textContent = text(cards?.coverage, (value) => value + " de " + total + " UFs");
  byId("uf-leadership").textContent = text(cards?.leadership, (value) => value + (value === 1 ? " UF" : " UFs"));
  byId("uf-top3").textContent = text(cards?.top3, (value) => value + (value === 1 ? " UF" : " UFs"));
  byId("uf-best-share").textContent = cards?.bestUf && numeric(cards.bestShare) !== null
    ? percentage(cards.bestShare) + " em " + cards.bestUf
    : blank;
}

function drawBars(host, rows, options) {
  if (!rows.length) {
    host.replaceChildren(create("p", "status", "Sem dados para a seleção e o período informados."));
    return;
  }
  const preservedScroll = host.scrollTop;
  const previousFocus = host.contains(document.activeElement) ? document.activeElement.dataset.barId : null;
  const list = create("ul", "ranking-list uf-bar-list");
  const values = rows.map(({ value }) => value);
  const min = Math.min(0, ...values);
  const max = Math.max(0, ...values);
  const range = max - min || 1;
  const zero = -min / range * 100;
  for (const row of rows) {
    const item = create("li");
    const barRow = create(options.activate ? "button" : "div", "rank-row uf-bar-row");
    const end = (row.value - min) / range * 100;
    const label = create("span", "rank-company", row.name);
    const lane = create("span", "rank-plot uf-bar-lane");
    const fill = create("span", "rank-bar uf-bar-fill");
    const highlighted = numeric(row.highlight);
    const displayValue = options.highlight ? highlighted : row.value;
    const displayEnd = displayValue === null ? zero
      : Math.min(100, Math.max(0, (displayValue - min) / range * 100));
    const value = create("span", "rank-value uf-bar-value",
      displayValue === null ? "" : options.display(displayValue));
    barRow.dataset.barId = row.id;
    barRow.title = row.name + " · " + options.tooltip(row);
    if (options.activate) {
      barRow.type = "button";
      barRow.setAttribute("aria-pressed", String(row.active));
      barRow.setAttribute("aria-label", row.name + ", " + options.tooltip(row));
      barRow.addEventListener("click", () => options.activate(row.id));
    } else {
      barRow.tabIndex = 0;
    }
    if (row.selected) barRow.dataset.reference = "";
    if (displayValue < 0) barRow.dataset.negative = "";
    if (row.muted) barRow.classList.add("uf-bar-muted");
    fill.style.left = Math.min(zero, end) + "%";
    fill.style.width = Math.abs(end - zero) + "%";
    if (options.color) fill.style.backgroundColor = options.color(row);
    lane.append(fill);
    if (options.highlight) {
      fill.classList.add("rank-dimmed");
      const overlay = create("span", "rank-bar rank-highlight uf-bar-overlay");
      overlay.style.left = Math.min(zero, displayEnd) + "%";
      overlay.style.width = Math.abs(displayEnd - zero) + "%";
      overlay.hidden = highlighted === null;
      lane.append(overlay);
    }
    value.style.left = displayEnd + "%";
    lane.append(value);
    barRow.append(label, lane);
    item.append(barRow);
    list.append(item);
  }
  host.replaceChildren(list);
  host.scrollTop = preservedScroll;
  if (previousFocus) {
    [...host.querySelectorAll("[data-bar-id]")].find((element) => element.dataset.barId === previousFocus)?.focus({ preventScroll: true });
  }
}

function drawRanking(result, selection, onSelect) {
  const highlighted = Boolean(selection?.uf && result.baseRanking);
  const baseRanking = highlighted ? result.baseRanking : result.ranking;
  byId("uf-ranking-title").textContent = (highlighted ? result.baseRankingTitle : result.rankingTitle)
    || "Ranking Competitivo | Brasil";
  const rows = baseRanking.filter(({ premium }) => numeric(premium) !== null).map((row) => ({
    ...row,
    value: Number(row.premium),
    highlight: row.highlightPremium,
    active: selection?.source === "ranking" && selection.insurer === row.id,
  }));
  drawBars(byId("uf-ranking"), rows, {
    display: compact,
    highlight: highlighted,
    tooltip: (row) => highlighted
      ? "Brasil: " + currency.format(row.value) + " · " + selection.uf + ": "
        + text(row.highlight, (value) => currency.format(value))
      : currency.format(row.value),
    activate: (insurer) => onSelect(selection?.source === "ranking" && selection.insurer === insurer
      ? null
      : { insurer, source: "ranking" }),
  });
}

function drawVariance(states, selection) {
  const rows = states.filter(({ changePp }) => numeric(changePp) !== null)
    .map((state) => ({
      id: state.uf,
      name: state.uf,
      value: Number(state.changePp),
      active: selection?.uf === state.uf,
      muted: Boolean(selection?.uf && selection.uf !== state.uf),
      state,
    }))
    .sort((a, b) => b.value - a.value || a.id.localeCompare(b.id));
  drawBars(byId("uf-variance"), rows, {
    display: (value) => simpleDecimal.format(value),
    tooltip: ({ value, state }) => points(value) + " · Atual: " + percentage(state.share)
      + " · Ano anterior: " + percentage(state.previousShare),
    color: ({ value }) => value > 0 ? "#18865B" : value < 0 ? "#C62828" : "#9CA3AF",
    activate: (uf) => toggleUf(uf, "variance"),
  });
}

export function render(result, selection, onSelect) {
  renderState = { states: new Map(result.states.map((row) => [row.uf, row])), selection, onSelect };
  drawCards(result.cards, result.states.length);
  drawLegend();
  drawRanking(result, selection, onSelect);
  drawVariance(result.states, selection);
  if (map?.isConnected) drawMap();
  else return ensureMap();
}

export function empty(message = "Sem dados para a seleção e o período informados.") {
  renderState = null;
  hideTooltip();
  drawCards(null, 0);
  byId("uf-ranking-title").textContent = "Ranking Competitivo | Brasil";
  for (const id of ["uf-ranking", "uf-variance"]) {
    const host = byId(id);
    if (message) host.replaceChildren(create("p", "status", message));
    else host.replaceChildren();
  }
  if (map?.isConnected) {
    for (const path of statePaths.values()) {
      path.setAttribute("fill", mapColor(0, 0, 0));
      path.dataset.unselected = "";
      path.setAttribute("aria-pressed", "false");
      path.setAttribute("aria-disabled", "true");
    }
  } else if (message) {
    mapHost.replaceChildren(create("p", "status", message));
  } else {
    mapHost.replaceChildren();
  }
}
