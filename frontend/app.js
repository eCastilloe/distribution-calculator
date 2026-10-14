const CONFIDENCE = { name: "confidence", label: "Nivel de confianza (%)", value: "95" };
const TAILS = {
  name: "tails",
  label: "Tipo de valor crítico",
  options: [["two", "Dos colas (intervalos de confianza)"], ["one", "Una cola"]],
};

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
    { name: "x2", label: "Segundo valor", placeholder: "ej. 2.5", showWhen: ["tail", "between"] },
  ];
}

const DISTRIBUTIONS = {
  z: {
    hint: "Úsala cuando la desviación estándar poblacional (σ) es conocida, o con proporciones.",
    problems: {
      mean_interval: {
        label: "Intervalo para una media",
        fields: [
          { name: "sample_mean", label: "Media muestral (x̄)", placeholder: "ej. 50" },
          { name: "sigma", label: "Desviación estándar poblacional (σ)", placeholder: "ej. 8" },
          { name: "n", label: "Tamaño de muestra (n)", placeholder: "ej. 64" },
          CONFIDENCE,
        ],
      },
      one_proportion: {
        label: "Intervalo para una proporción",
        fields: [
          { name: "n", label: "Tamaño de muestra (n)", placeholder: "ej. 100" },
          { name: "successes", label: "Éxitos (x)", placeholder: "ej. 45" },
          CONFIDENCE,
        ],
      },
      two_proportions: {
        label: "Intervalo para dos proporciones",
        fields: [
          { name: "n1", label: "Tamaño de muestra 1 (n₁)", placeholder: "ej. 100" },
          { name: "successes1", label: "Éxitos de la muestra 1 (x₁)", placeholder: "ej. 45" },
          { name: "n2", label: "Tamaño de muestra 2 (n₂)", placeholder: "ej. 90" },
          { name: "successes2", label: "Éxitos de la muestra 2 (x₂)", placeholder: "ej. 30" },
          CONFIDENCE,
        ],
      },
      probability: {
        label: "Probabilidad",
        fields: [
          { name: "mean", label: "Media (μ)", value: "0" },
          { name: "std_dev", label: "Desviación estándar (σ)", value: "1" },
          ...probabilityFields("Valor x"),
        ],
      },
      critical_value: {
        label: "Valor crítico",
        fields: [CONFIDENCE, TAILS],
      },
    },
  },
  t: {
    hint: "Úsala cuando σ es desconocida y se trabaja con la desviación muestral (s), sobre todo con muestras chicas.",
    problems: {
      mean_interval: {
        label: "Intervalo para una media",
        fields: [
          { name: "sample_mean", label: "Media muestral (x̄)", placeholder: "ej. 50" },
          { name: "s", label: "Desviación estándar muestral (s)", placeholder: "ej. 8" },
          { name: "n", label: "Tamaño de muestra (n)", placeholder: "ej. 10" },
          CONFIDENCE,
        ],
      },
      probability: {
        label: "Probabilidad",
        fields: [
          { name: "df", label: "Grados de libertad (gl)", placeholder: "ej. 10" },
          ...probabilityFields("Valor de t"),
        ],
      },
      critical_value: {
        label: "Valor crítico",
        fields: [{ name: "df", label: "Grados de libertad (gl)", placeholder: "ej. 10" }, CONFIDENCE, TAILS],
      },
    },
  },
};

const problemSelect = document.getElementById("problem");
const fieldsBox = document.getElementById("fields");
const form = document.getElementById("form");
const submitButton = document.getElementById("submit");
const resultBox = document.getElementById("result");
const hintBox = document.getElementById("distribution-hint");

function currentDistribution() {
  return document.querySelector("input[name=distribution]:checked").value;
}

function showProblems() {
  const distribution = DISTRIBUTIONS[currentDistribution()];
  hintBox.textContent = distribution.hint;
  problemSelect.innerHTML = "";
  for (const [key, problem] of Object.entries(distribution.problems)) {
    problemSelect.add(new Option(problem.label, key));
  }
  showFields();
}

function showFields() {
  const problem = DISTRIBUTIONS[currentDistribution()].problems[problemSelect.value];
  fieldsBox.innerHTML = "";
  for (const field of problem.fields) {
    const label = document.createElement("label");
    label.className = "field";
    label.dataset.name = field.name;
    const title = document.createElement("span");
    title.textContent = field.label;
    label.append(title, field.options ? buildSelect(field) : buildInput(field));
    fieldsBox.append(label);
  }
  updateVisibleFields();
}

function buildInput(field) {
  const input = document.createElement("input");
  input.type = "text";
  input.inputMode = "decimal";
  input.name = field.name;
  input.value = field.value || "";
  input.placeholder = field.placeholder || "";
  return input;
}

function buildSelect(field) {
  const select = document.createElement("select");
  select.name = field.name;
  for (const [value, text] of field.options) {
    select.add(new Option(text, value));
  }
  select.addEventListener("change", updateVisibleFields);
  return select;
}

function updateVisibleFields() {
  const problem = DISTRIBUTIONS[currentDistribution()].problems[problemSelect.value];
  for (const field of problem.fields) {
    if (!field.showWhen) continue;
    const [otherName, otherValue] = field.showWhen;
    const other = fieldsBox.querySelector(`[name=${otherName}]`);
    fieldsBox.querySelector(`[data-name=${field.name}]`).hidden = other.value !== otherValue;
  }
}

async function calculate(event) {
  event.preventDefault();
  const payload = { distribution: currentDistribution(), problem: problemSelect.value };
  for (const input of fieldsBox.querySelectorAll("[name]")) {
    payload[input.name] = input.value;
  }
  submitButton.disabled = true;
  submitButton.textContent = "Calculando...";
  try {
    const response = await fetch("/api/calculate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    showResult(await response.json());
  } catch (error) {
    showResult({ error: "No se pudo conectar con el programa. ¿Sigue corriendo el servidor?" });
  }
  submitButton.disabled = false;
  submitButton.textContent = "Calcular";
}

function showResult(result) {
  resultBox.innerHTML = "";
  if (result.error) {
    resultBox.append(createElement("div", "error", result.error));
    return;
  }
  resultBox.append(createElement("div", "answer", result.answer));
  for (const note of result.notes) {
    resultBox.append(createElement("div", "note", note));
  }
  const canvas = document.createElement("canvas");
  resultBox.append(canvas);
  drawChart(canvas, result.chart);
  for (const table of result.tables) {
    resultBox.append(createElement("h3", "table-title", table.title), buildTable(table));
  }
}

function createElement(tag, className, text) {
  const element = document.createElement(tag);
  element.className = className;
  element.textContent = text;
  return element;
}

function buildTable(table) {
  const element = document.createElement("table");
  const head = element.createTHead().insertRow();
  for (const header of table.headers) {
    head.append(createElement("th", "", header));
  }
  const body = element.createTBody();
  for (const row of table.rows) {
    const tableRow = body.insertRow();
    for (const value of row) {
      tableRow.insertCell().textContent = value;
    }
  }
  return element;
}

function drawChart(canvas, chart) {
  const style = getComputedStyle(document.documentElement);
  const accent = style.getPropertyValue("--accent");
  const accentSoft = style.getPropertyValue("--accent-soft");
  const textColor = style.getPropertyValue("--text");
  const mutedColor = style.getPropertyValue("--muted");

  const ratio = window.devicePixelRatio || 1;
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  canvas.width = width * ratio;
  canvas.height = height * ratio;
  const context = canvas.getContext("2d");
  context.scale(ratio, ratio);

  const left = 12;
  const top = 22;
  const plotWidth = width - 2 * left;
  const plotHeight = height - top - 28;
  const maxY = Math.max(...chart.points.map((point) => point[1])) * 1.1;
  const toX = (x) => left + ((x + chart.limit) / (2 * chart.limit)) * plotWidth;
  const toY = (y) => top + plotHeight - (y / maxY) * plotHeight;

  context.fillStyle = accentSoft;
  for (const [start, end] of chart.shaded) {
    const from = start === null ? -chart.limit : Math.max(start, -chart.limit);
    const to = end === null ? chart.limit : Math.min(end, chart.limit);
    if (from >= to) continue;
    context.beginPath();
    context.moveTo(toX(from), toY(0));
    for (const [x, y] of chart.points) {
      if (x >= from && x <= to) context.lineTo(toX(x), toY(y));
    }
    context.lineTo(toX(to), toY(0));
    context.closePath();
    context.fill();
  }

  const [firstX, firstY] = chart.points[0];
  context.beginPath();
  context.moveTo(toX(firstX), toY(firstY));
  for (const [x, y] of chart.points) {
    context.lineTo(toX(x), toY(y));
  }
  context.strokeStyle = accent;
  context.lineWidth = 2;
  context.stroke();

  context.strokeStyle = mutedColor;
  context.lineWidth = 1;
  context.beginPath();
  context.moveTo(left, toY(0));
  context.lineTo(left + plotWidth, toY(0));
  context.stroke();

  context.fillStyle = mutedColor;
  context.font = "11px system-ui, sans-serif";
  context.textAlign = "center";
  for (let tick = -chart.limit; tick <= chart.limit; tick++) {
    context.fillText(tick, toX(tick), toY(0) + 14);
  }
  context.fillText(chart.axis, left + plotWidth / 2, height - 3);

  context.fillStyle = textColor;
  context.strokeStyle = textColor;
  context.setLineDash([4, 3]);
  for (const mark of chart.marks) {
    if (Math.abs(mark) > chart.limit) continue;
    context.beginPath();
    context.moveTo(toX(mark), top - 4);
    context.lineTo(toX(mark), toY(0));
    context.stroke();
    context.fillText(mark.toFixed(2), toX(mark), top - 8);
  }
  context.setLineDash([]);
}

document.querySelectorAll("input[name=distribution]").forEach((radio) => {
  radio.addEventListener("change", showProblems);
});
problemSelect.addEventListener("change", showFields);
form.addEventListener("submit", calculate);
showProblems();
