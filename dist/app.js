import { render as renderUf, empty as emptyUf } from "./uf.js";
import { mountSimulation } from "./simulation.js";
import { mountMa } from "./ma.js";

const byId = (id) => document.getElementById(id);
const create = (tag, className, text) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
};

const blank = "—";
const decimal = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const percent = new Intl.NumberFormat("pt-BR", { style: "percent", minimumFractionDigits: 2, maximumFractionDigits: 2 });
const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const monthNames = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
const coverageDate = new Intl.DateTimeFormat("pt-BR", { month: "long", year: "numeric", timeZone: "UTC" });
const missing = (value) => value === null || value === undefined || !Number.isFinite(Number(value));
const format = (value, formatter) => missing(value) ? blank : formatter(Number(value));
const asPercent = (value) => format(value, (n) => percent.format(n));
const asPoints = (value) => format(value, (n) => decimal.format(n));
const asCurrency = (value) => format(value, (n) => brl.format(n));
const withPoints = (value) => format(value, (n) => decimal.format(n) + " p.p.");

const baseColumns = [
  { key: "label", label: "Grupo de ramos", formatter: (v) => v || blank },
  { key: "premium", label: "Prêmios diretos (R$)", formatter: asCurrency },
  { key: "weightPct", label: "Peso na carteira (%)", formatter: asPoints },
  { key: "premiumDeltaPct", label: "Δ Prêmios (%)", formatter: asPoints },
];
const metrics = {
  share: {
    ranking: "Ranking por Prêmios Diretos",
    subtitle: "Prêmios nos ramos da carteira de referência",
    evolution: "Evolução do Market Share",
    diagnosis: "Participação",
    rankingFormat: (n) => decimal.format(n) + " Bi",
    columns: [{ key: "indicatorPct", label: "Contribuição ao MS (p.p.)" }],
  },
  sinistralidade: {
    ranking: "Sinistralidade por Seguradora",
    subtitle: "Comparação técnica | Menor índice é preferível",
    evolution: "Evolução da Sinistralidade",
    diagnosis: "Sinistralidade",
    rankingFormat: (n) => percent.format(n),
    columns: [
      { key: "indicatorPct", label: "Sinistralidade da carteira (%)" },
      { key: "marketPct", label: "Mercado: Sinistralidade (%)" },
      { key: "deviationPp", label: "Diferença Sinistralidade (p.p.)" },
    ],
  },
  margem: {
    ranking: "Margem Técnica Parcial por Seguradora",
    subtitle: "Comparação técnica | Maior margem é preferível",
    evolution: "Evolução da Margem Técnica Parcial",
    diagnosis: "Rentabilidade Técnica",
    rankingFormat: (n) => percent.format(n),
    columns: [
      { key: "indicatorPct", label: "Margem Técnica Parcial (%)" },
      { key: "marketPct", label: "Mercado: Margem Parcial (%)" },
      { key: "deviationPp", label: "Diferença Margem (p.p.)" },
    ],
  },
};

const groupSelect = byId("group-select");
const entitySelect = byId("entity-select");
const entityOptions = byId("entity-options");
const entitySummary = byId("entity-summary");
const selectAll = byId("select-all");
const clearEntities = byId("clear-entities");
const startSelect = byId("start-select");
const endSelect = byId("end-select");
const ufStartSelect = byId("uf-start-select");
const ufEndSelect = byId("uf-end-select");
const ufAnalysis = byId("uf-analysis");
const ufStatus = byId("uf-status");
const analysis = byId("analysis");
const analysisStatus = byId("analysis-status");
const maAnalysis = byId("ma-analysis");
const maStatus = byId("ma-status");
const maReference = byId("ma-reference");
const maCompanyA = byId("ma-company-a");
const maCompanyB = byId("ma-company-b");
const catalogStatus = byId("catalog-status");
const table = byId("diagnosis-table");
const ranking = byId("ranking");
const canvas = byId("evolution-canvas");
const plot = canvas.parentElement;
const points = byId("evolution-points");
const legend = byId("evolution-legend");
const evolutionBox = byId("evolution");
const evolutionEmpty = create("p", "status", "Sem dados para o período selecionado.");
evolutionEmpty.hidden = true;
evolutionBox.append(evolutionEmpty);

const tabs = [...document.querySelectorAll(".report-tabs [data-page]")];
let catalog;
let filters;
let entityNames;
let selectedPage;
let activeRequest;
let data;
let tableSort = { key: "premium", descending: true };
let lastPlotWidth = 0;
let selection = null;
let ufSelection = null;
let guideLoad;

function compactCurrency(value) {
  return format(value, (number) => {
    const units = [[1e9, "Bi"], [1e6, "Mi"], [1e3, "mil"]];
    const unit = units.find(([limit]) => Math.abs(number) >= limit);
    return unit ? "R$ " + decimal.format(number / unit[0]) + " " + unit[1] : brl.format(number);
  });
}

function renderStatus(node, message, retry) {
  node.hidden = !message;
  node.textContent = message || "";
  node.toggleAttribute("data-error", Boolean(retry));
  if (retry) {
    const button = create("button", "", "Tentar novamente");
    button.type = "button";
    button.addEventListener("click", retry);
    node.append(" ", button);
  }
}

async function requestJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    const failure = new Error(error?.error || "Falha ao consultar os dados da SUSEP.");
    failure.status = response.status;
    throw failure;
  }
  return response.json();
}

function matchedEntities() {
  if (!filters.group) return [];
  const codes = new Set(catalog.memberships[filters.group] || []);
  return catalog.entities.filter(({ code }) => codes.has(code));
}

function renderEntitySelection() {
  const matches = matchedEntities();
  const matchedCodes = new Set(matches.map(({ code }) => code));
  const entities = catalog.entities.filter(({ code }) => matchedCodes.has(code) || filters.entities.includes(code));
  entityOptions.replaceChildren();
  for (const { code, name } of entities) {
    const label = create("label", "check");
    const control = create("input");
    control.type = "checkbox";
    control.value = code;
    label.append(control, matchedCodes.has(code) ? name : name + " (referência atual)");
    entityOptions.append(label);
  }
  if (!entities.length) {
    const text = filters.group ? "Este grupo não tem seguradoras disponíveis." : "Selecione um grupo para listar suas seguradoras.";
    entityOptions.append(create("p", "status", text));
  }
  selectAll.disabled = !matches.length;
  syncEntitySelection();
}

function syncEntitySelection() {
  const selected = new Set(filters.entities);
  const controls = [...entityOptions.querySelectorAll("input")];
  for (const control of controls) control.checked = selected.has(control.value);
  const matches = matchedEntities();
  selectAll.checked = matches.length > 0 && matches.every(({ code }) => selected.has(code));
  selectAll.indeterminate = matches.some(({ code }) => selected.has(code)) && !selectAll.checked;
  clearEntities.disabled = selected.size === 0;
  if (selected.size === 0) {
    entitySummary.textContent = "Nenhuma selecionada";
  } else if (selected.size === 1) {
    entitySummary.textContent = entityNames.get(filters.entities[0]);
  } else {
    entitySummary.textContent = selected.size + " seguradoras selecionadas";
  }
}

function localReference() {
  if (filters.entities.length === 1) return entityNames.get(filters.entities[0]);
  if (filters.entities.length > 1) return filters.entities.length + " seguradoras selecionadas";
  const group = catalog.groups.find(({ code }) => code === filters.group);
  return group ? "Grupo: " + group.name : "Nenhuma referência selecionada";
}

function renderPage() {
  const route = window.location.hash.slice(1);
  const tab = tabs.find((item) => item.dataset.page === route) || tabs[0];
  if (selectedPage !== tab.dataset.page) {
    selection = null;
    ufSelection = null;
    simulation.clearSelection();
    ma.clearSelection();
  }
  selectedPage = tab.dataset.page;
  for (const item of tabs) {
    if (item === tab) item.setAttribute("aria-current", "page");
    else item.removeAttribute("aria-current");
  }
  entitySelect.open = false;
  byId("page-inicio").hidden = !catalog || selectedPage !== "inicio";
  byId("page-raio-x").hidden = !catalog || selectedPage !== "raio-x";
  byId("page-visao-uf").hidden = !catalog || selectedPage !== "visao-uf";
  byId("page-simulacoes").hidden = !catalog || selectedPage !== "simulacoes";
  byId("page-fusao-aquisicao").hidden = !catalog || selectedPage !== "fusao-aquisicao";
  byId("page-guia").hidden = !catalog || selectedPage !== "guia";
  document.title = selectedPage === "inicio" ? "SUSEP | Market Share Intelligence" : "SUSEP | " + tab.textContent;
  if (selectedPage === "raio-x" && catalog) {
    loadAnalysis();
  } else if (selectedPage === "visao-uf" && catalog) {
    loadUfAnalysis();
  } else if (selectedPage === "simulacoes" && catalog) {
    loadSimulation();
  } else if (selectedPage === "fusao-aquisicao" && catalog) {
    loadMa();
  } else {
    activeRequest?.abort();
    if (selectedPage === "guia" && catalog) loadGuide();
  }
  if (tab.offsetLeft < tab.parentElement.scrollLeft) tab.parentElement.scrollLeft = tab.offsetLeft;
  if (tab.offsetLeft + tab.offsetWidth > tab.parentElement.scrollLeft + tab.parentElement.clientWidth) {
    tab.parentElement.scrollLeft = tab.offsetLeft + tab.offsetWidth - tab.parentElement.clientWidth;
  }
}

function loadGuide() {
  if (guideLoad) return;
  const status = byId("guide-status");
  const content = byId("guide-content");
  content.setAttribute("aria-busy", "true");
  renderStatus(status, "Carregando o Guia…");
  guideLoad = Promise.all([import("./guide.js"), requestJson("./guide-data.json")])
    .then(([{ mountGuide }, data]) => {
      mountGuide(content, data);
      renderStatus(status, "");
    })
    .catch((error) => {
      console.error(error);
      guideLoad = null;
      renderStatus(status, "Não foi possível carregar o Guia de Indicadores.", loadGuide);
    })
    .finally(() => content.setAttribute("aria-busy", "false"));
}

async function initCatalog() {
  renderStatus(catalogStatus, "Carregando dados da SUSEP…");
  try {
    catalog = await requestJson("./api/catalog");
    if (catalog.pbixUrl) {
      const download = byId("pbix-download");
      download.href = catalog.pbixUrl;
      download.hidden = false;
    }
    filters = { ...catalog.defaults, entities: [...catalog.defaults.entities] };
    entityNames = new Map(catalog.entities.map(({ code, name }) => [code, name]));
    groupSelect.replaceChildren(new Option("Nenhum grupo selecionado", ""));
    groupSelect.append(...catalog.groups.map(({ code, name }) => new Option(name, code)));
    groupSelect.value = filters.group;
    renderEntitySelection();

    for (const [control, defaultKey] of [[maCompanyA, "companyA"], [maCompanyB, "companyB"]]) {
      control.replaceChildren(...catalog.entities.map(({ code, name }) => new Option(name, code)));
      control.value = catalog.defaults.ma?.[defaultKey] ?? "";
    }
    for (const [control, key] of periodControls) {
      control.replaceChildren(...catalog.months.map(({ code, label }) => new Option(label, code)));
      control.value = filters[key];
    }
    for (const input of document.querySelectorAll("input[name=metric]")) {
      input.checked = input.value === filters.metric;
    }
    const latest = catalog.months.at(-1)?.code;
    const date = latest ? new Date(Date.UTC(Number(latest.slice(0, 4)), Number(latest.slice(4)) - 1, 1)) : null;
    for (const node of document.querySelectorAll("[data-coverage]")) {
      node.textContent = date ? "Dados contabilizados até " + coverageDate.format(date) : "Dados não disponíveis";
    }
    renderStatus(catalogStatus, "");
    renderPage();
  } catch (error) {
    console.error(error);
    renderStatus(catalogStatus, "Não foi possível carregar os dados da SUSEP.", initCatalog);
  }
}

async function loadAnalysis({ preserve = false, focus = null } = {}) {
  activeRequest?.abort();
  const request = new AbortController();
  activeRequest = request;
  analysis.setAttribute("aria-busy", "true");
  byId("reference-name").textContent = localReference();
  const invalidDates = filters.start > filters.end;
  renderStatus(analysisStatus, invalidDates ? "O período inicial é posterior ao período final." : "Consultando dados da SUSEP…");
  if (!preserve || invalidDates) renderAnalysis(null);
  if (invalidDates) {
    analysis.setAttribute("aria-busy", "false");
    return;
  }
  const params = referenceParams();
  params.set("metric", filters.metric);
  if (selection) params.set(selection.param, selection.code);
  try {
    const result = await requestJson("./api/raio-x?" + params, { signal: request.signal });
    if (request.signal.aborted || activeRequest !== request) return;
    const restoreFocus = focus?.contains(document.activeElement);
    renderAnalysis(result);
    if (restoreFocus) {
      const name = focus.dataset.insurer ? "insurer" : "branch";
      const code = CSS.escape(focus.dataset[name]);
      analysis.querySelector(`[data-${name}="${code}"]`)?.focus();
    }
    const empty = missing(result.cards.premium) && result.ranking.length === 0;
    renderStatus(analysisStatus, empty ? "Sem dados para a seleção e o período informados." : "");
  } catch (error) {
    if (request.signal.aborted) return;
    console.error(error);
    renderStatus(analysisStatus, "Não foi possível calcular o Raio-X Competitivo.", loadAnalysis);
  } finally {
    if (activeRequest === request) analysis.setAttribute("aria-busy", "false");
  }
}

function referenceParams() {
  const params = new URLSearchParams({ start: filters.start, end: filters.end });
  if (filters.group) params.set("group", filters.group);
  for (const code of filters.entities) params.append("entity", code);
  return params;
}

const simulation = mountSimulation(byId("simulation"), { onChange: loadSimulation });

async function loadSimulation() {
  activeRequest?.abort();
  const request = new AbortController();
  activeRequest = request;
  byId("simulation-reference").textContent = localReference();
  if (filters.start > filters.end) {
    simulation.error("O período inicial é posterior ao período final.");
    return;
  }
  const { referenceGrowth, competitorGrowth, goal, selectedInsurer } = simulation.getScenario();
  const params = referenceParams();
  params.set("reference_growth", referenceGrowth);
  params.set("competitor_growth", competitorGrowth);
  params.set("goal", goal);
  if (selectedInsurer) params.set("selected_insurer", selectedInsurer);
  simulation.loading();
  try {
    const result = await requestJson("./api/simulacoes?" + params, { signal: request.signal });
    if (request.signal.aborted || activeRequest !== request) return;
    byId("simulation-reference").textContent = result.reference;
    simulation.render(result);
  } catch (error) {
    if (request.signal.aborted) return;
    console.error(error);
    simulation.error(error.status === 404
      ? "Reinicie o servidor local com o server.py atualizado e recarregue a página."
      : "Não foi possível calcular as Simulações Estratégicas.");
  }
}

function selectUfVisual(value) {
  ufSelection = value;
  loadUfAnalysis({ preserve: true });
}

const ma = mountMa(maAnalysis, loadMa);

for (const control of [maCompanyA, maCompanyB]) {
  control.addEventListener("change", () => loadMa());
}

async function loadMa() {
  activeRequest?.abort();
  const request = new AbortController();
  activeRequest = request;
  maReference.textContent = localReference();
  if (filters.start > filters.end) {
    ma.render(null);
    maAnalysis.setAttribute("aria-busy", "false");
    renderStatus(maStatus, "O período inicial é posterior ao período final.");
    return;
  }

  maAnalysis.setAttribute("aria-busy", "true");
  renderStatus(maStatus, "Calculando a operação…");
  const params = referenceParams();
  params.set("company_a", maCompanyA.value);
  params.set("company_b", maCompanyB.value);
  const selection = ma.getSelection();
  if (selection) params.set(selection.param, selection.code);

  try {
    const result = await requestJson("./api/fusao-aquisicao?" + params, { signal: request.signal });
    if (request.signal.aborted || activeRequest !== request) return;
    if (selection && !result[selection.table].rows.some(({ code }) => code === selection.code)) {
      ma.clearSelection();
      return loadMa();
    }
    maReference.textContent = result.reference;
    ma.render(result);
    renderStatus(maStatus, "");
  } catch (error) {
    if (request.signal.aborted) return;
    console.error(error);
    ma.render(null);
    renderStatus(maStatus, error.status === 404
      ? "Reinicie o servidor local com o server.py atualizado e recarregue a página."
      : "Não foi possível calcular a operação.", loadMa);
  } finally {
    if (activeRequest === request) maAnalysis.setAttribute("aria-busy", "false");
  }
}

byId("uf-analyze-insurer").addEventListener("click", () => {
  const code = ufSelection?.insurer;
  if (!code || !entityNames.has(code)) return;
  filters.entities = [code];
  renderEntitySelection();
  ufSelection = null;
  loadUfAnalysis({ revealReference: true });
});

async function loadUfAnalysis({ preserve = false, revealReference = false } = {}) {
  activeRequest?.abort();
  const request = new AbortController();
  activeRequest = request;
  ufAnalysis.setAttribute("aria-busy", "true");
  byId("uf-reference").textContent = localReference();
  const candidate = entityNames.get(ufSelection?.insurer);
  byId("uf-rank-candidate").textContent = candidate || "";
  byId("uf-rank-action").hidden = !candidate;
  if (filters.start > filters.end) {
    emptyUf("Sem dados para o período selecionado.");
    renderStatus(ufStatus, "O período inicial é posterior ao período final.");
    ufAnalysis.setAttribute("aria-busy", "false");
    return;
  }
  if (!preserve) emptyUf("");
  renderStatus(ufStatus, "Consultando dados da SUSEP…");
  const params = referenceParams();
  if (ufSelection?.uf) params.set("uf", ufSelection.uf);
  if (ufSelection?.insurer) params.set("selected_insurer", ufSelection.insurer);
  try {
    const result = await requestJson("./api/visao-uf?" + params, { signal: request.signal });
    if (request.signal.aborted || activeRequest !== request) return;
    byId("uf-reference").textContent = result.reference;
    await renderUf(result, ufSelection, selectUfVisual);
    if (!request.signal.aborted) {
      renderStatus(ufStatus, "");
      if (revealReference) {
        const ranking = byId("uf-ranking");
        const row = ranking.querySelector("[data-reference]");
        if (row) {
          ranking.scrollTop += row.getBoundingClientRect().top - ranking.getBoundingClientRect().top;
          row.focus({ preventScroll: true });
        }
      }
    }
  } catch (error) {
    if (request.signal.aborted) return;
    console.error(error);
    emptyUf("Não foi possível exibir os dados.");
    const message = error.status === 404
      ? "Este servidor local não oferece a rota da Visão por UF. Reinicie o servidor com o server.py atualizado e recarregue a página."
      : "Não foi possível calcular a Visão por UF.";
    renderStatus(ufStatus, message, loadUfAnalysis);
  } finally {
    if (activeRequest === request) ufAnalysis.setAttribute("aria-busy", "false");
  }
}

function selectVisualValue(param, code, focus) {
  selection = selection?.param === param && selection.code === code ? null : { param, code };
  loadAnalysis({ preserve: true, focus });
}

function renderAnalysis(result) {
  data = result;
  const metric = metrics[filters.metric];
  const cards = result?.cards || {};
  if (result?.reference) byId("reference-name").textContent = result.reference;
  byId("ranking-title").textContent = metric.ranking;
  byId("ranking-subtitle").textContent = metric.subtitle;
  byId("evolution-title").textContent = metric.evolution;
  byId("diagnosis-title").textContent = "Diagnóstico da Carteira | " + metric.diagnosis;
  byId("kpi-position").textContent = format(cards.position, (n) => n + "º");
  byId("kpi-competitors").textContent = missing(cards.position) || missing(cards.competitor_count) ? "" : "entre " + cards.competitor_count + " seguradoras";
  byId("next-label").textContent = cards.next_label || "Distância para a posição acima";
  for (const [id, value] of [
    ["kpi-next", cards.next_distance],
    ["kpi-leader", cards.leader_distance],
    ["kpi-premium", cards.premium],
  ]) {
    byId(id).textContent = compactCurrency(value);
    byId(id).title = missing(value) ? "" : asCurrency(value);
  }
  byId("kpi-share").textContent = asPercent(cards.share);
  byId("kpi-variation").textContent = withPoints(cards.share_change_pp);
  renderRanking(result?.ranking || [], metric);
  renderEvolution();
  renderTableHeader();
  renderTableBody();
}

function renderRanking(rows, metric) {
  ranking.replaceChildren();
  const values = rows.filter(({ value }) => !missing(value));
  if (!values.length) {
    if (data) ranking.append(create("p", "status", "Sem dados para a seleção."));
    return;
  }
  const withHighlight = selection?.param === "selected_branch_group";
  const magnitudes = values.flatMap((row) => {
    if (withHighlight && !missing(row.highlight_value)) return [Number(row.value), Number(row.highlight_value)];
    return [Number(row.value)];
  });
  const minimum = Math.min(0, ...magnitudes);
  const maximum = Math.max(0, ...magnitudes);
  const axis = maximum - minimum || 1;
  const zero = (-minimum / axis) * 100;
  ranking.toggleAttribute("data-has-negative", minimum < 0);
  const list = create("ul", "ranking-list");
  for (const row of values) {
    const number = Number(row.value);
    const x = ((number - minimum) / axis) * 100;
    const item = create("li");
    const entry = create("button", "rank-row");
    entry.type = "button";
    entry.dataset.insurer = row.id;
    const selected = selection?.param === "selected_insurer" && selection.code === row.id;
    entry.setAttribute("aria-pressed", String(selected));
    entry.toggleAttribute("data-reference", Boolean(row.selected));
    entry.toggleAttribute("data-negative", number < 0);
    entry.title = row.name + " — " + metric.rankingFormat(number);
    const name = create("span", "rank-company", row.name);
    const track = create("span", "rank-plot");
    const bar = create("span", "rank-bar");
    bar.style.left = Math.min(zero, x) + "%";
    bar.style.width = Math.abs(zero - x) + "%";
    const value = create("span", "rank-value", metric.rankingFormat(number));
    value.style.left = x + "%";
    track.append(bar, value);
    if (withHighlight) {
      bar.classList.add("rank-dimmed");
      if (!missing(row.highlight_value)) {
        const result = Number(row.highlight_value);
        const highlight = create("span", "rank-bar rank-highlight");
        const highlightedPoint = ((result - minimum) / axis) * 100;
        highlight.style.left = Math.min(zero, highlightedPoint) + "%";
        highlight.style.width = Math.abs(zero - highlightedPoint) + "%";
        track.insertBefore(highlight, value);
        entry.title += " | Grupo de ramos selecionado · " + metric.rankingFormat(result);
      }
    }
    entry.append(name, track);
    entry.addEventListener("click", () => selectVisualValue("selected_insurer", row.id, entry));
    item.append(entry);
    list.append(item);
  }
  ranking.append(list);
}

function renderEvolution() {
  points.replaceChildren();
  legend.replaceChildren();
  const observations = data?.evolution || [];
  const present = observations.filter(({ value }) => !missing(value));
  const continuous = observations.some(({ axis }) => axis);
  const seriesKey = (row) => row.series ?? row.year;
  const axisKey = (row) => row.axis ?? row.month;
  const series = [...new Set(present.map(seriesKey))];
  if (!continuous) series.sort((a, b) => a - b);
  const months = [...new Set(observations.map(axisKey))].sort((a, b) => a - b);
  const width = plot.clientWidth;
  const height = plot.clientHeight;
  lastPlotWidth = width;
  const dpr = window.devicePixelRatio || 1;
  canvas.width = width * dpr;
  canvas.height = height * dpr;
  const context = canvas.getContext("2d");
  context.scale(dpr, dpr);
  evolutionEmpty.hidden = !data || series.length > 0;
  plot.classList.toggle("evolution-empty", Boolean(data && !series.length));
  if (!series.length || width === 0) return;

  const values = present.map(({ value }) => Number(value));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min;
  const x = (month) => months.length < 2 ? width / 2 : 26 + ((width - 52) * months.indexOf(month)) / (months.length - 1);
  const y = (value) => span ? height - 28 - ((height - 54) * (Number(value) - min)) / span : (height - 5) / 2;
  const latest = continuous ? "current" : series.at(-1);
  const labelsFit = width / months.length > 36;
  const step = continuous ? Math.ceil(months.length / Math.max(2, Math.floor(width / 56))) : 1;

  for (const [index, month] of months.entries()) {
    const last = index === months.length - 1;
    if (!last && (index % step || (index && months.length - 1 - index < step))) continue;
    const labelText = continuous
      ? monthNames[Number(month.slice(4)) - 1] + "/" + month.slice(2, 4)
      : monthNames[month - 1];
    const label = create("span", "month-label", labelText);
    label.style.left = x(month) + "px";
    points.append(label);
  }
  for (const key of series) {
    const olderYear = continuous ? key === "previous" : key < Number(filters.end.slice(0, 4));
    const color = olderYear ? "#b3c3d1" : "#79b8e8";
    const mark = create("span", "legend-mark");
    mark.toggleAttribute("data-previous", olderYear);
    mark.append(create("i"), continuous ? (olderYear ? "12 meses antes" : "Período selecionado") : String(key));
    legend.append(mark);

    const byMonth = new Map(observations.filter((row) => seriesKey(row) === key).map((row) => [axisKey(row), row]));
    context.beginPath();
    context.lineWidth = 2.5;
    context.lineJoin = "round";
    context.strokeStyle = color;
    let connected = false;
    for (const month of months) {
      const value = byMonth.get(month)?.value;
      if (missing(value)) {
        connected = false;
        continue;
      }
      if (connected) context.lineTo(x(month), y(value));
      else context.moveTo(x(month), y(value));
      connected = true;
    }
    context.stroke();
    for (const month of months) {
      const row = byMonth.get(month);
      const value = row?.value;
      if (missing(value)) continue;
      const cx = x(month);
      const cy = y(value);
      context.beginPath();
      context.arc(cx, cy, 2.5, 0, Math.PI * 2);
      context.fillStyle = color;
      context.fill();

      const valueText = percent.format(Number(value) / 100);
      const description = monthNames[row.month - 1] + "/" + row.year + " — " + valueText;
      if (labelsFit && key === latest) {
        const label = create("span", "point-value", valueText);
        label.style.left = cx + "px";
        label.style.top = cy + "px";
        points.append(label);
      }
      const point = create("span", "plot-point");
      point.tabIndex = 0;
      point.style.left = cx + "px";
      point.style.top = cy + "px";
      point.title = description;
      point.setAttribute("aria-label", description);
      point.dataset.tip = description;
      points.append(point);
    }
  }
}

function tableColumns() {
  return [...baseColumns, ...metrics[filters.metric].columns];
}

function renderTableHeader() {
  const row = create("tr");
  for (const { key, label } of tableColumns()) {
    const cell = create("th");
    cell.scope = "col";
    cell.dataset.column = key;
    const button = create("button", "", label);
    button.type = "button";
    button.addEventListener("click", () => {
      tableSort = { key, descending: key === tableSort.key ? !tableSort.descending : key !== "label" };
      renderTableBody();
    });
    cell.append(button);
    row.append(cell);
  }
  table.tHead.replaceChildren(row);
}

function renderTableBody() {
  const columns = tableColumns();
  const diagnosis = data?.diagnosis;
  const rows = [...(diagnosis?.rows || [])];
  for (const header of table.tHead.querySelectorAll("th")) {
    if (header.dataset.column === tableSort.key) header.setAttribute("aria-sort", tableSort.descending ? "descending" : "ascending");
    else header.removeAttribute("aria-sort");
  }
  const key = tableSort.key;
  const direction = tableSort.descending ? -1 : 1;
  rows.sort((a, b) => {
    if (key === "label") return direction * a.label.localeCompare(b.label, "pt-BR");
    if (missing(a[key])) return missing(b[key]) ? 0 : 1;
    if (missing(b[key])) return -1;
    return direction * (Number(a[key]) - Number(b[key]));
  });
  const body = table.tBodies[0];
  body.replaceChildren(...rows.map((row) => diagnosisRow(row, columns, false)));
  if (data && !rows.length) {
    const row = create("tr");
    const cell = create("td", "empty-cell", "Sem dados para a seleção.");
    cell.colSpan = columns.length;
    row.append(cell);
    body.append(row);
  }
  table.tFoot.replaceChildren();
  if (diagnosis?.total) table.tFoot.append(diagnosisRow(diagnosis.total, columns, true));
}

function diagnosisRow(row, columns, total) {
  const element = create("tr");
  let control;
  for (const { key, formatter } of columns) {
    const value = row[key];
    const cell = create(total && key === "label" ? "th" : "td", "", total && key === "label" ? "Total" : (formatter || asPoints)(value));
    if (cell.tagName === "TH") cell.scope = "row";
    if (key === "label" && !total) {
      control = create("button", "branch-button", cell.textContent);
      control.type = "button";
      control.dataset.branch = row.code;
      const selected = selection?.param === "selected_branch_group" && selection.code === row.code;
      control.setAttribute("aria-pressed", String(selected));
      element.toggleAttribute("data-selected", selected);
      cell.replaceChildren(control);
    }
    if (!missing(value) && key === "premiumDeltaPct" && Number(value) !== 0) {
      cell.classList.add(Number(value) > 0 ? "positive" : "negative");
    }
    if (!missing(value) && key === "deviationPp" && Math.abs(Number(value)) >= 0.005) {
      const favorable = filters.metric === "sinistralidade" ? Number(value) < 0 : Number(value) > 0;
      cell.classList.add(favorable ? "positive" : "negative");
    }
    element.append(cell);
  }
  if (control) element.addEventListener("click", () => selectVisualValue("selected_branch_group", row.code, control));
  return element;
}

groupSelect.addEventListener("change", () => {
  filters.group = groupSelect.value;
  const available = new Set(matchedEntities().map(({ code }) => code));
  filters.entities = filters.entities.filter((code) => available.has(code));
  renderEntitySelection();
});
entityOptions.addEventListener("change", (event) => {
  filters.entities = [...entityOptions.querySelectorAll("input:checked")].map((control) => control.value);
  if (!event.target.checked && !matchedEntities().some(({ code }) => code === event.target.value)) {
    renderEntitySelection();
    entitySummary.focus();
  } else {
    syncEntitySelection();
  }
});
selectAll.addEventListener("change", () => {
  filters.entities = selectAll.checked ? matchedEntities().map(({ code }) => code) : [];
  renderEntitySelection();
});
clearEntities.addEventListener("click", () => {
  filters.entities = [];
  renderEntitySelection();
});
document.addEventListener("pointerdown", (event) => {
  if (entitySelect.open && !entitySelect.contains(event.target)) entitySelect.open = false;
});
entitySelect.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && entitySelect.open) {
    entitySelect.open = false;
    entitySummary.focus();
  }
});
const periodControls = [
  [startSelect, "start"], [endSelect, "end"],
  [ufStartSelect, "start"], [ufEndSelect, "end"],
  [byId("simulation-start-select"), "start"], [byId("simulation-end-select"), "end"],
  [byId("ma-start-select"), "start"], [byId("ma-end-select"), "end"],
];
for (const [control, key] of periodControls) {
  control.addEventListener("change", () => {
    filters[key] = control.value;
    for (const [linked, field] of periodControls) {
      if (field === key) linked.value = control.value;
    }
    selection = null;
    ufSelection = null;
    simulation.clearSelection();
    ma.clearSelection();
    if (selectedPage === "visao-uf") loadUfAnalysis();
    else if (selectedPage === "simulacoes") loadSimulation();
    else if (selectedPage === "fusao-aquisicao") loadMa();
    else loadAnalysis();
  });
}
document.querySelector(".metric-control").addEventListener("change", (event) => {
  filters.metric = event.target.value;
  tableSort = { key: "premium", descending: true };
  selection = null;
  loadAnalysis();
});
window.addEventListener("hashchange", renderPage);
new ResizeObserver(() => {
  if (selectedPage === "raio-x" && plot.clientWidth !== lastPlotWidth) renderEvolution();
}).observe(plot);

renderPage();
initCatalog();
