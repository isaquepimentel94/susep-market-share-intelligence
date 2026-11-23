const MINIMUM = -30;
const MAXIMUM = 100;
const DEFAULTS = { referenceGrowth: 18, competitorGrowth: 0, goal: -3 };
const emptyValue = "—";
const percent = new Intl.NumberFormat("pt-BR", {
  style: "percent", minimumFractionDigits: 2, maximumFractionDigits: 2,
});
const points = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 2, maximumFractionDigits: 2, signDisplay: "exceptZero",
});
const integer = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });
const currency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const compactAmount = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 1, maximumFractionDigits: 1,
});

const fields = {
  currentShare: (value) => percent.format(value),
  simulatedShare: (value) => percent.format(value),
  impactPp: (value) => points.format(value) + " p.p.",
  currentPosition: (value) => integer.format(value) + "º",
  simulatedPosition: (value) => integer.format(value),
  positionChange: (value) => integer.format(value),
  additionalGrowth: (value) => percent.format(value),
  safetyMargin: (value) => Math.abs(value) >= 1e6
    ? "R$ " + pointsWithoutSign(value / 1e6) + " Mi"
    : currency.format(value),
};
const decimal = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 2, maximumFractionDigits: 2,
});

function pointsWithoutSign(value) {
  return decimal.format(value);
}

const goals = [
  [0, "Sem meta"], [1, "Subir 1 posição"], [2, "Subir 2 posições"],
  [3, "Subir 3 posições"], [4, "Subir 4 posições"], [5, "Subir 5 posições"],
  [-1, "Cair 1 posição"], [-2, "Cair 2 posições"], [-3, "Cair 3 posições"],
  [-4, "Cair 4 posições"], [-5, "Cair 5 posições"],
];

function create(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function present(value) {
  return value !== null && value !== undefined && Number.isFinite(Number(value));
}

function format(value, render) {
  return present(value) ? render(Number(value)) : emptyValue;
}

function compact(value) {
  const unit = [[1e9, "Bi"], [1e6, "Mi"], [1e3, "mil"]].find(([base]) => Math.abs(value) >= base);
  return unit ? compactAmount.format(value / unit[0]) + " " + unit[1] : currency.format(value);
}

const template = `
  <div class="sim-sliders" aria-label="Cenário de crescimento"></div>
  <p class="status sim-status" role="status" aria-live="polite" hidden></p>
  <div class="sim-result" aria-busy="true">
    <dl class="cards sim-cards" aria-label="Indicadores da simulação">
      <div class="card"><dt>Participação atual</dt><dd data-sim-card="currentShare">—</dd></div>
      <div class="card"><dt>Participação simulada</dt><dd data-sim-card="simulatedShare">—</dd></div>
      <div class="card"><dt>Variação da participação (p.p.)</dt><dd data-sim-card="impactPp">—</dd></div>
      <div class="card"><dt>Posição atual</dt><dd data-sim-card="currentPosition">—</dd></div>
      <div class="card"><dt>Posição simulada</dt><dd data-sim-card="simulatedPosition">—</dd></div>
      <div class="card"><dt>Variação de posições</dt><dd data-sim-card="positionChange">—</dd></div>
    </dl>
    <div class="sim-layout">
      <section class="chart-panel sim-chart" aria-labelledby="sim-chart-title">
        <h2 id="sim-chart-title">Prêmios diretos — atual × simulado</h2>
        <p class="chart-subtitle">Prêmios concorrente na carteira e prêmios concorrente simulado por seguradora.</p>
        <div class="sim-bars"></div>
        <div class="sim-legend" aria-label="Séries do gráfico">
          <span><i aria-hidden="true"></i>Prêmios concorrente na carteira</span>
          <span><i aria-hidden="true"></i>Prêmios concorrente simulado</span>
        </div>
      </section>
      <section class="chart-panel sim-movement" aria-labelledby="sim-movement-title">
        <h2 id="sim-movement-title">Movimentação no ranking competitivo</h2>
        <div class="table-scroll" role="region" aria-label="Tabela de movimentação" tabindex="0">
          <table>
            <thead><tr>
              <th scope="col"><button type="button" data-sort="name">Seguradora</button></th>
              <th scope="col" aria-sort="ascending"><button type="button" data-sort="currentPosition">Posição atual</button></th>
              <th scope="col"><button type="button" data-sort="simulatedPosition">Posição simulada</button></th>
              <th scope="col"><button type="button" data-sort="positionChange">Δ Posição</button></th>
            </tr></thead>
            <tbody></tbody>
          </table>
        </div>
      </section>
      <section class="chart-panel sim-goal" aria-labelledby="sim-goal-title">
        <h2 id="sim-goal-title">Meta competitiva</h2>
        <p id="sim-goal-basis" class="chart-subtitle">Os indicadores de meta usam o cenário atual, com crescimento de 0% para a referência e para os concorrentes.</p>
        <div class="sim-goal-layout">
          <fieldset class="sim-goal-options">
            <legend>Objetivo</legend>
          </fieldset>
          <dl class="sim-goal-cards" aria-describedby="sim-goal-basis">
            <div class="card"><dt>Margem de Segurança Meta R$</dt><dd data-sim-card="safetyMargin">—</dd></div>
            <div class="card"><dt>Crescimento Adicional Meta %</dt><dd data-sim-card="additionalGrowth">—</dd></div>
          </dl>
        </div>
      </section>
    </div>
  </div>
`;

function slider(key, label, initial, setValue) {
  const wrap = create("div", "sim-slider");
  const heading = create("label", null, label);
  heading.htmlFor = `sim-${key}`;
  const range = create("input");
  range.id = heading.htmlFor;
  range.type = "range";
  range.min = MINIMUM;
  range.max = MAXIMUM;
  range.step = 1;
  range.value = initial;
  range.setAttribute("aria-valuetext", `${initial}%`);
  const number = create("input");
  number.type = "number";
  number.min = MINIMUM;
  number.max = MAXIMUM;
  number.step = 1;
  number.value = initial;
  number.setAttribute("aria-label", label + " — valor");
  const numberWrap = create("span", "sim-slider-number");
  numberWrap.append(number, create("span", null, "%"));
  const sync = (value, immediate) => {
    const adjusted = Math.max(MINIMUM, Math.min(MAXIMUM, Math.round(value)));
    range.value = String(adjusted);
    range.setAttribute("aria-valuetext", `${adjusted}%`);
    setValue(key, adjusted, immediate);
  };
  const syncFromRange = (immediate) => {
    number.value = range.value;
    sync(range.valueAsNumber, immediate);
  };
  const commitNumber = () => {
    sync(Number.isFinite(number.valueAsNumber) ? number.valueAsNumber : range.valueAsNumber, true);
    number.value = range.value;
  };
  range.addEventListener("input", () => syncFromRange(false));
  range.addEventListener("change", () => syncFromRange(true));
  number.addEventListener("input", () => {
    if (number.validity.valid && Number.isFinite(number.valueAsNumber)) sync(number.valueAsNumber, false);
  });
  number.addEventListener("change", commitNumber);
  number.addEventListener("keydown", (event) => {
    if (event.key === "Enter") commitNumber();
  });
  wrap.append(heading, numberWrap, range);
  return wrap;
}

function renderChart(container, rows, active, select) {
  if (!rows.length) {
    container.replaceChildren(create("p", "status", "Não há prêmios para os filtros selecionados."));
    return;
  }
  const focused = container.contains(document.activeElement) ? document.activeElement.dataset.simCompany : null;
  const list = create("ul", "sim-bar-list");
  const values = rows.flatMap(({ currentPremium, simulatedPremium }) => [currentPremium, simulatedPremium])
    .filter(present).map(Number);
  const minimum = Math.min(0, ...values);
  const maximum = Math.max(0, ...values);
  const extent = maximum - minimum || 1;
  const position = (value) => (value - minimum) / extent * 100;
  for (const row of rows) {
    const item = create("li");
    const button = create("button", "sim-company-bar");
    button.type = "button";
    button.dataset.simCompany = row.id;
    button.setAttribute("aria-pressed", String(row.id === active));
    button.title = `${row.name} · Atual: ${format(row.currentPremium, currency.format)} · Simulado: ${format(row.simulatedPremium, currency.format)}`;
    button.setAttribute("aria-label", button.title);
    button.addEventListener("click", () => select(row.id, "chart"));
    const company = create("span", "sim-company-name", row.name);
    const track = create("span", "sim-track");
    track.setAttribute("aria-hidden", "true");
    for (const [kind, premium] of [["current", row.currentPremium], ["simulated", row.simulatedPremium]]) {
      const line = create("span", `sim-track-line sim-${kind}`);
      if (present(premium)) {
        const endpoint = position(Number(premium));
        const zero = position(0);
        const bar = create("i");
        bar.style.left = Math.min(zero, endpoint) + "%";
        bar.style.width = Math.abs(endpoint - zero) + "%";
        line.append(bar);
        if (kind === "current") {
          const amount = create("span", "sim-bar-amount", compact(Number(premium)));
          amount.style.left = endpoint + "%";
          amount.toggleAttribute("data-negative", Number(premium) < 0);
          line.append(amount);
        }
      }
      track.append(line);
    }
    button.append(company, track);
    item.append(button);
    list.append(item);
  }
  list.toggleAttribute("data-negative", minimum < 0);
  container.replaceChildren(list);
  if (focused) [...list.querySelectorAll("button")].find((node) => node.dataset.simCompany === focused)?.focus({ preventScroll: true });
}

function renderRanking(body, rows, active, sort, select) {
  const focused = body.contains(document.activeElement)
    ? document.activeElement.closest("[data-sim-company]")?.dataset.simCompany : null;
  const fragment = document.createDocumentFragment();
  const ordered = [...rows].sort((left, right) => {
    if (sort.key === "name") return left.name.localeCompare(right.name, "pt-BR") * sort.direction;
    const a = left[sort.key];
    const b = right[sort.key];
    if (!present(a) || !present(b)) return Number(present(b)) - Number(present(a));
    return (Number(a) - Number(b)) * sort.direction;
  });
  for (const row of ordered) {
    const tr = create("tr");
    tr.dataset.simCompany = row.id;
    tr.toggleAttribute("data-selected", row.id === active);
    const name = create("button", "branch-button", row.name);
    name.type = "button";
    name.setAttribute("aria-pressed", String(row.id === active));
    name.addEventListener("click", () => select(row.id, "table"));
    const label = create("td");
    label.append(name);
    tr.append(label);
    for (const key of ["currentPosition", "simulatedPosition", "positionChange"]) {
      tr.append(create("td", null, format(row[key], integer.format)));
    }
    fragment.append(tr);
  }
  if (!ordered.length) {
    const row = create("tr");
    const cell = create("td", "empty-cell", "Não há posições para os filtros selecionados.");
    cell.colSpan = 4;
    row.append(cell);
    fragment.append(row);
  }
  body.replaceChildren(fragment);
  if (focused) [...body.rows].find((node) => node.dataset.simCompany === focused)
    ?.querySelector("button")?.focus({ preventScroll: true });
}

export function mountSimulation(host, { onChange }) {
  host.innerHTML = template;
  const scenario = { ...DEFAULTS };
  const status = host.querySelector(".sim-status");
  const sliders = host.querySelector(".sim-sliders");
  const results = host.querySelector(".sim-result");
  const options = host.querySelector(".sim-goal-options");
  const bars = host.querySelector(".sim-bars");
  const body = host.querySelector("tbody");
  let response;
  let selected = null;
  let source = null;
  const getScenario = () => ({ ...scenario, selectedInsurer: selected, source });
  let lastNotified = getScenario();
  let sort = { key: "currentPosition", direction: 1 };
  let timer;

  const notify = () => {
    clearTimeout(timer);
    const next = getScenario();
    if (Object.keys(next).every((key) => next[key] === lastNotified[key])) return;
    lastNotified = next;
    onChange(lastNotified);
  };
  const setValue = (key, value, immediate) => {
    scenario[key] = value;
    clearTimeout(timer);
    if (immediate) notify();
    else timer = setTimeout(notify, 120);
  };
  sliders.append(
    slider("referenceGrowth", "Variação dos prêmios da referência (%)", scenario.referenceGrowth, setValue),
    slider("competitorGrowth", "Variação dos prêmios dos concorrentes (%)", scenario.competitorGrowth, setValue),
  );
  for (const [movement, text] of goals) {
    const label = create("label", "sim-goal-option");
    const radio = create("input");
    radio.type = "radio";
    radio.name = "simulation-goal";
    radio.value = movement;
    radio.checked = movement === scenario.goal;
    radio.addEventListener("change", () => setValue("goal", movement, true));
    label.append(radio, text);
    options.append(label);
  }

  function visibleRanking(data) {
    const ranking = data?.ranking ?? [];
    return source === "chart" ? ranking.filter((row) => row.id === selected) : ranking;
  }

  function select(company, origin) {
    selected = selected === company ? null : company;
    source = selected === null ? null : origin;
    for (const node of bars.querySelectorAll("[data-sim-company]")) {
      const active = source === "chart" && node.dataset.simCompany === selected;
      node.setAttribute("aria-pressed", String(active));
    }
    bars.toggleAttribute("data-selection", source === "chart");
    renderRanking(body, visibleRanking(response), selected, sort, select);
    notify();
  }

  for (const button of host.querySelectorAll("[data-sort]")) {
    button.addEventListener("click", () => {
      const key = button.dataset.sort;
      sort = { key, direction: sort.key === key ? -sort.direction : 1 };
      for (const header of host.querySelectorAll("th[aria-sort]")) header.removeAttribute("aria-sort");
      button.parentElement.setAttribute("aria-sort", sort.direction === 1 ? "ascending" : "descending");
      renderRanking(body, visibleRanking(response), selected, sort, select);
    });
  }

  function flagStatus(message, failed = false) {
    status.textContent = message;
    status.hidden = !message;
    status.toggleAttribute("data-error", failed);
  }

  function show(data) {
    response = data;
    const chart = data?.chart ?? [];
    const ranking = data?.ranking ?? [];
    if (!chart.some((row) => row.id === selected) && !ranking.some((row) => row.id === selected)) {
      selected = source = null;
      lastNotified = getScenario();
    }
    bars.toggleAttribute("data-selection", source === "chart");
    for (const node of host.querySelectorAll("[data-sim-card]")) {
      const key = node.dataset.simCard;
      const value = data?.cards?.[key];
      node.textContent = format(value, fields[key]);
      if (key === "safetyMargin" && present(value)) node.title = currency.format(Number(value));
      else node.removeAttribute("title");
    }
    renderChart(bars, chart, source === "chart" ? selected : null, select);
    renderRanking(body, visibleRanking(data), selected, sort, select);
    results.setAttribute("aria-busy", "false");
  }

  return {
    getScenario,
    clearSelection() {
      clearTimeout(timer);
      selected = source = null;
      lastNotified = getScenario();
    },
    loading() {
      results.setAttribute("aria-busy", "true");
      flagStatus("Calculando simulação…");
    },
    render(data) {
      flagStatus("");
      show(data);
    },
    error(message) {
      show(null);
      flagStatus(message, true);
    },
  };
}
