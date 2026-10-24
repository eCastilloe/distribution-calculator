// Página: muestra los campos del problema elegido, envía los datos al servidor y muestra el resultado.
// Usa DISTRIBUTIONS (forms.js) y drawChart (chart.js), que se cargan antes en index.html.

const problemSelect = document.getElementById("problem");
const fieldsBox = document.getElementById("fields");
const form = document.getElementById("form");
const submitButton = document.getElementById("submit");
const resultBox = document.getElementById("result");
const distributionHint = document.getElementById("distribution-hint");
const problemHint = document.getElementById("problem-hint");

function currentDistribution() {
  return document.querySelector("input[name=distribution]:checked").value;
}

function currentProblem() {
  return DISTRIBUTIONS[currentDistribution()].problems[problemSelect.value];
}

function showProblems() {
  const distribution = DISTRIBUTIONS[currentDistribution()];
  distributionHint.textContent = distribution.hint;
  problemSelect.innerHTML = "";
  for (const key in distribution.problems) {
    problemSelect.add(new Option(distribution.problems[key].label, key));
  }
  showFields();
}

function showFields() {
  const problem = currentProblem();
  problemHint.textContent = problem.hint || "";
  problemHint.hidden = !problem.hint;
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
  let input;
  if (field.type === "textarea") {
    input = document.createElement("textarea");
    input.rows = 3;
  } else {
    input = document.createElement("input");
    input.type = "text";
    input.inputMode = "decimal";
  }
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
  for (const field of currentProblem().fields) {
    if (!field.showWhen) continue;
    const [otherName, allowedValues] = field.showWhen;
    const other = fieldsBox.querySelector(`[name=${otherName}]`);
    const box = fieldsBox.querySelector(`[data-name=${field.name}]`);
    box.hidden = !allowedValues.includes(other.value);
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
  const interpretation = createElement("div", "interpretation", "");
  interpretation.append(createElement("strong", "", "Interpretación: "), result.interpretation);
  resultBox.append(interpretation);
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

for (const radio of document.querySelectorAll("input[name=distribution]")) {
  radio.addEventListener("change", showProblems);
}
problemSelect.addEventListener("change", showFields);
form.addEventListener("submit", calculate);
showProblems();
