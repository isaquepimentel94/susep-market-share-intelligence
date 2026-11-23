import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { guideCards } from "../dist/guide.js";

const data = JSON.parse(readFileSync(new URL("../dist/guide-data.json", import.meta.url), "utf8"));
const { category, indicator } = data.defaults;

test("a seleção salva reproduz os quatro cartões da margem técnica parcial", () => {
  assert.deepEqual(guideCards(data, category, indicator), {
    definition: "Resultado técnico parcial após sinistros ocorridos e despesas comerciais.",
    formula: "(Prêmios ganhos - Sinistros ocorridos - Despesas comerciais) / Prêmios ganhos x 100",
    interpretation: "Valores maiores geralmente indicam desempenho técnico parcial mais favorável.",
    source: "fato_premios_nacional",
  });
});

test("categoria e indicador incompatíveis acionam o texto original nos quatro cartões", () => {
  const result = guideCards(data, "Concentração de Mercado", indicator);
  assert.deepEqual(Object.values(result), Array(4).fill(data.fallback));
});

test("sem indicador, cada cartão avalia seus próprios valores distintos", () => {
  assert.deepEqual(guideCards(data, "Concentração de Mercado", ""), {
    definition: data.fallback,
    formula: data.fallback,
    interpretation: data.fallback,
    source: "Prêmios SUSEP e mercado comparável",
  });
});
