// Gráfica: dibuja la curva, el área sombreada, el eje y las marcas en un <canvas>.

function drawChart(canvas, chart) {
  const style = getComputedStyle(document.documentElement);
  const accent = style.getPropertyValue("--accent");
  const accentSoft = style.getPropertyValue("--accent-soft");
  const textColor = style.getPropertyValue("--text");
  const mutedColor = style.getPropertyValue("--muted");

  // El canvas se dibuja al doble de resolución en pantallas de alta densidad para que no se vea borroso
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
  let maxY = 0;
  for (const [x, y] of chart.points) {
    if (y > maxY) maxY = y;
  }
  maxY = maxY * 1.1;

  // Convierten un valor de la gráfica en una posición en pixeles
  function toX(x) {
    return left + ((x - chart.start) / (chart.end - chart.start)) * plotWidth;
  }
  function toY(y) {
    return top + plotHeight - (y / maxY) * plotHeight;
  }

  context.fillStyle = accentSoft;
  for (const [start, end] of chart.shaded) {
    const from = start === null ? chart.start : Math.max(start, chart.start);
    const to = end === null ? chart.end : Math.min(end, chart.end);
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
  for (const tick of chart.ticks) {
    context.fillText(tick, toX(tick), toY(0) + 14);
  }
  context.fillText(chart.axis, left + plotWidth / 2, height - 3);

  context.fillStyle = textColor;
  context.strokeStyle = textColor;
  context.setLineDash([4, 3]);
  for (const mark of chart.marks) {
    if (mark < chart.start || mark > chart.end) continue;
    context.beginPath();
    context.moveTo(toX(mark), top - 4);
    context.lineTo(toX(mark), toY(0));
    context.stroke();
    context.fillText(mark.toFixed(2), toX(mark), top - 8);
  }
  context.setLineDash([]);
}
