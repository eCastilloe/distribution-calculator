// Formularios: qué campos pide cada problema de cada distribución.
// Cada problema define sus campos. "showWhen" muestra un campo solo cuando otro campo
// tiene uno de los valores indicados (por ejemplo, la lista de datos solo en el modo "Lista de datos").

const CONFIDENCE = { name: "confidence", label: "Nivel de confianza (%)", value: "95" };
const DF = { name: "df", label: "Grados de libertad (gl)", placeholder: "ej. 10" };
const F_DFS = [
  { name: "df1", label: "Grados de libertad del numerador (ν₁)", placeholder: "ej. 5" },
  { name: "df2", label: "Grados de libertad del denominador (ν₂)", placeholder: "ej. 10" },
];
const DATA_HINT = "En «Lista de datos» pega los valores separados por comas o espacios " +
  "(usa punto decimal; el símbolo % se ignora).";
const CLAIM_HINT = "Si el problema hace una afirmación (por ejemplo, «el promedio es 300»), " +
  "escríbela en «Valor afirmado» para obtener H₀, H₁ y la decisión. Si no, déjalo vacío.";
const DIFFERENCE_HINT = "Si ambos límites son positivos, el primero es mayor; si ambos son negativos, " +
  "es menor; si el intervalo incluye el 0, se consideran iguales.";

const MEAN_MODE = {
  name: "input_mode",
  label: "¿Cómo tienes los datos?",
  options: [["summary", "Media, desviación estándar y n"], ["data", "Lista de datos"]],
};
const VARIANCE_MODE = {
  name: "input_mode",
  label: "¿Cómo tienes los datos?",
  options: [["variance", "Varianza (s²) y n"], ["std_dev", "Desviación estándar (s) y n"], ["data", "Lista de datos"]],
};
const SUMMARY = ["input_mode", ["summary"]];
const DATA = ["input_mode", ["data"]];
const NOT_DATA = ["input_mode", ["variance", "std_dev"]];

function probabilityFields(valueLabel) {
  return [
    {
      name: "tail",
      label: "Tipo de probabilidad",
      options: [
        ["below", "Menor que un valor"],
        ["above", "Mayor que un valor"],
        ["between", "Entre dos valores"],
      ],
    },
    { name: "x", label: valueLabel, placeholder: "ej. 1.5" },
    { name: "x2", label: "Segundo valor", placeholder: "ej. 2.5", showWhen: ["tail", ["between"]] },
  ];
}

function oneMeanFields(stdLabel) {
  return [
    MEAN_MODE,
    { name: "mean", label: "Media muestral (x̄)", placeholder: "ej. 320", showWhen: SUMMARY },
    { name: "std_dev", label: stdLabel, placeholder: "ej. 40", showWhen: SUMMARY },
    { name: "n", label: "Tamaño de muestra (n)", placeholder: "ej. 64", showWhen: SUMMARY },
    { name: "values", label: "Datos", type: "textarea", placeholder: "ej. 6.2, 6.5, 6.1, 6.4", showWhen: DATA },
    CONFIDENCE,
    { name: "claimed", label: "Valor afirmado μ₀ (opcional)", placeholder: "ej. 300" },
  ];
}

function twoMeansFields(stdSymbol) {
  return [
    MEAN_MODE,
    { name: "n1", label: "Tamaño de muestra 1 (n₁)", placeholder: "ej. 15", showWhen: SUMMARY },
    { name: "mean1", label: "Media de la muestra 1 (x̄₁)", placeholder: "ej. 82", showWhen: SUMMARY },
    { name: "std_dev1", label: "Desviación estándar 1 (" + stdSymbol + "₁)", placeholder: "ej. 5", showWhen: SUMMARY },
    { name: "n2", label: "Tamaño de muestra 2 (n₂)", placeholder: "ej. 12", showWhen: SUMMARY },
    { name: "mean2", label: "Media de la muestra 2 (x̄₂)", placeholder: "ej. 76", showWhen: SUMMARY },
    { name: "std_dev2", label: "Desviación estándar 2 (" + stdSymbol + "₂)", placeholder: "ej. 6", showWhen: SUMMARY },
    { name: "values1", label: "Datos de la muestra 1", type: "textarea", placeholder: "ej. 82, 79, 88", showWhen: DATA },
    { name: "values2", label: "Datos de la muestra 2", type: "textarea", placeholder: "ej. 76, 70, 81", showWhen: DATA },
    CONFIDENCE,
  ];
}

const DISTRIBUTIONS = {
  z: {
    hint: "Úsala cuando la desviación estándar poblacional (σ) es conocida o n ≥ 30, y con proporciones.",
    problems: {
      mean_interval: {
        label: "Intervalo para una media",
        hint: "Si no conoces σ pero n ≥ 30, usa la desviación muestral s. " + CLAIM_HINT + " " + DATA_HINT,
        fields: oneMeanFields("Desviación estándar (σ)"),
      },
      two_means: {
        label: "Intervalo para dos medias",
        hint: "Para σ conocidas o muestras grandes (n ≥ 30). " + DIFFERENCE_HINT,
        fields: twoMeansFields("σ"),
      },
      one_proportion: {
        label: "Intervalo para una proporción",
        hint: "x es la cantidad de éxitos en la muestra; la proporción es p = x / n. " + CLAIM_HINT,
        fields: [
          { name: "n", label: "Tamaño de muestra (n)", placeholder: "ej. 500" },
          { name: "successes", label: "Éxitos (x)", placeholder: "ej. 390" },
          CONFIDENCE,
          { name: "claimed", label: "Valor afirmado π₀ (opcional)", placeholder: "ej. 0.8" },
        ],
      },
      two_proportions: {
        label: "Intervalo para dos proporciones",
        hint: DIFFERENCE_HINT,
        fields: [
          { name: "n1", label: "Tamaño de muestra 1 (n₁)", placeholder: "ej. 250" },
          { name: "successes1", label: "Éxitos de la muestra 1 (x₁)", placeholder: "ej. 180" },
          { name: "n2", label: "Tamaño de muestra 2 (n₂)", placeholder: "ej. 240" },
          { name: "successes2", label: "Éxitos de la muestra 2 (x₂)", placeholder: "ej. 150" },
          CONFIDENCE,
        ],
      },
      sample_size: {
        label: "Tamaño de muestra",
        hint: "Cuántos datos hacen falta para no pasar del error máximo e. " +
          "Si no conoces la proporción, usa p = 0.5 (el caso que pide más datos).",
        fields: [
          {
            name: "target",
            label: "¿Para qué parámetro?",
            options: [["mean", "Una media"], ["proportion", "Una proporción"]],
          },
          { name: "std_dev", label: "Desviación estándar (σ)", placeholder: "ej. 15", showWhen: ["target", ["mean"]] },
          { name: "p", label: "Proporción estimada (p)", value: "0.5", showWhen: ["target", ["proportion"]] },
          { name: "error", label: "Error máximo (e)", placeholder: "ej. 3 (media) o 0.05 (proporción)" },
          CONFIDENCE,
        ],
      },
      probability: {
        label: "Probabilidad",
        fields: [
          { name: "mean", label: "Media (μ)", value: "0" },
          { name: "std_dev", label: "Desviación estándar (σ)", value: "1" },
        ].concat(probabilityFields("Valor x")),
      },
    },
  },
  t: {
    hint: "Úsala cuando σ es desconocida y se trabaja con la desviación muestral (s), sobre todo con n < 30.",
    problems: {
      mean_interval: {
        label: "Intervalo para una media",
        hint: CLAIM_HINT + " " + DATA_HINT,
        fields: oneMeanFields("Desviación estándar muestral (s)"),
      },
      two_means: {
        label: "Intervalo para dos medias",
        hint: "Elige si el problema dice que las varianzas de las poblaciones son iguales o diferentes. " +
          DIFFERENCE_HINT,
        fields: [
          {
            name: "variances",
            label: "Varianzas de las poblaciones",
            options: [["equal", "Suponiéndolas iguales"], ["different", "Suponiéndolas diferentes"]],
          },
        ].concat(twoMeansFields("s")),
      },
      paired: {
        label: "Muestras pareadas",
        hint: "Pega las dos columnas de la tabla (por ejemplo, antes y después) en el mismo orden: " +
          "el programa resta cada par (d = dato 1 − dato 2). " + DIFFERENCE_HINT,
        fields: [
          {
            name: "input_mode",
            label: "¿Cómo tienes los datos?",
            options: [["pairs", "Dos columnas de datos"], ["summary", "Media y desviación de las diferencias"]],
          },
          { name: "values1", label: "Datos 1 (por ejemplo, antes)", type: "textarea", placeholder: "ej. 50, 45, 60, 55", showWhen: ["input_mode", ["pairs"]] },
          { name: "values2", label: "Datos 2 (por ejemplo, después)", type: "textarea", placeholder: "ej. 65, 55, 75, 70", showWhen: ["input_mode", ["pairs"]] },
          { name: "mean", label: "Media de las diferencias (d̄)", placeholder: "ej. 18.5", showWhen: SUMMARY },
          { name: "std_dev", label: "Desviación estándar de las diferencias (s_d)", placeholder: "ej. 6.2", showWhen: SUMMARY },
          { name: "n", label: "Número de pares (n)", placeholder: "ej. 16", showWhen: SUMMARY },
          CONFIDENCE,
        ],
      },
      probability: {
        label: "Probabilidad",
        fields: [DF].concat(probabilityFields("Valor de t")),
      },
    },
  },
  chi2: {
    hint: "Úsala para estimar la varianza (σ²) o la desviación estándar (σ) de una población.",
    problems: {
      variance_interval: {
        label: "Intervalo para una varianza",
        hint: "El resultado también incluye el intervalo para σ. " + CLAIM_HINT + " " + DATA_HINT,
        fields: [
          VARIANCE_MODE,
          { name: "n", label: "Tamaño de muestra (n)", placeholder: "ej. 25", showWhen: NOT_DATA },
          { name: "variance", label: "Varianza muestral (s²)", placeholder: "ej. 0.0152", showWhen: ["input_mode", ["variance"]] },
          { name: "std_dev", label: "Desviación estándar muestral (s)", placeholder: "ej. 2.8", showWhen: ["input_mode", ["std_dev"]] },
          { name: "values", label: "Datos", type: "textarea", placeholder: "ej. 12.4, 13.0, 11.8, 14.2", showWhen: DATA },
          CONFIDENCE,
          { name: "claimed", label: "Valor afirmado σ₀² (opcional)", placeholder: "ej. 4" },
        ],
      },
      probability: {
        label: "Probabilidad",
        fields: [DF].concat(probabilityFields("Valor de χ²")),
      },
    },
  },
  f: {
    hint: "Úsala para comparar dos varianzas: estima el cociente σ₁² / σ₂².",
    problems: {
      variance_ratio: {
        label: "Intervalo para el cociente de varianzas",
        hint: "Dice si las varianzas son significativamente diferentes: si el intervalo incluye el 1, " +
          "no lo son. " + DATA_HINT,
        fields: [
          VARIANCE_MODE,
          { name: "n1", label: "Tamaño de muestra 1 (n₁)", placeholder: "ej. 10", showWhen: NOT_DATA },
          { name: "variance1", label: "Varianza muestral 1 (s₁²)", placeholder: "ej. 0.005", showWhen: ["input_mode", ["variance"]] },
          { name: "std_dev1", label: "Desviación estándar 1 (s₁)", placeholder: "ej. 0.07", showWhen: ["input_mode", ["std_dev"]] },
          { name: "n2", label: "Tamaño de muestra 2 (n₂)", placeholder: "ej. 12", showWhen: NOT_DATA },
          { name: "variance2", label: "Varianza muestral 2 (s₂²)", placeholder: "ej. 0.002", showWhen: ["input_mode", ["variance"]] },
          { name: "std_dev2", label: "Desviación estándar 2 (s₂)", placeholder: "ej. 0.04", showWhen: ["input_mode", ["std_dev"]] },
          { name: "values1", label: "Datos de la muestra 1", type: "textarea", placeholder: "ej. 1.3%, 1.4%, 1.2%", showWhen: DATA },
          { name: "values2", label: "Datos de la muestra 2", type: "textarea", placeholder: "ej. 1.1%, 1.0%, 1.2%", showWhen: DATA },
          CONFIDENCE,
        ],
      },
      probability: {
        label: "Probabilidad",
        fields: F_DFS.concat(probabilityFields("Valor de F")),
      },
    },
  },
};
