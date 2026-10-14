import math

from distributions import (
    normal_curve, t_curve, probability_below, probability_above, critical_value,
)

CHART_POINTS = 200
COMMON_CONFIDENCES = [90, 95, 98, 99]
MAX_SCORE = 1000
MAX_WHOLE = 10**9


def fmt(value):
    if isinstance(value, (int, str)):
        return str(value)
    return f"{value:.4f}"


def read_number(data, name, label, minimum=None, maximum=None, whole=False, positive=False):
    try:
        value = float(str(data.get(name, "")).replace(",", "."))
    except ValueError:
        raise ValueError(f"{label}: escribe un número.")
    if not math.isfinite(value):
        raise ValueError(f"{label}: escribe un número válido.")
    if whole:
        if value != int(value):
            raise ValueError(f"{label}: debe ser un número entero.")
        value = int(value)
        if maximum is None:
            maximum = MAX_WHOLE
    if positive and value <= 0:
        raise ValueError(f"{label}: debe ser mayor que 0.")
    if minimum is not None and value < minimum:
        raise ValueError(f"{label}: debe ser al menos {minimum}.")
    if maximum is not None and value > maximum:
        raise ValueError(f"{label}: debe ser como máximo {maximum}.")
    return value


def read_choice(data, name, label, options):
    value = data.get(name)
    if value not in options:
        raise ValueError(f"{label}: elige una opción.")
    return value


def read_confidence(data):
    return read_number(data, "confidence", "Nivel de confianza (%)", minimum=50, maximum=99.99) / 100


def read_df(data):
    return read_number(data, "df", "Grados de libertad (gl)", minimum=1, maximum=1000, whole=True)


def standardize(value, mean, std_dev):
    score = (value - mean) / std_dev
    if abs(score) > MAX_SCORE:
        raise ValueError("El valor está demasiado lejos de la media.")
    return score


def values_table(rows):
    return {
        "title": "Valores del cálculo",
        "headers": ["Concepto", "Valor"],
        "rows": [[label, fmt(value)] for label, value in rows],
    }


def make_chart(curve, axis, shaded, marks):
    # El eje va de -limit a limit: lo justo para ver las marcas, entre 4 y 8
    farthest = max(abs(mark) for mark in marks)
    limit = min(max(4, math.ceil(farthest + 1)), 8)
    grid = [-limit + 2 * limit * i / CHART_POINTS for i in range(CHART_POINTS + 1)]
    # Las marcas se agregan como puntos para que el área sombreada empiece justo en ellas
    visible_marks = [mark for mark in marks if abs(mark) <= limit]
    xs = sorted(set(grid + visible_marks))
    return {
        "axis": axis,
        "limit": limit,
        "points": [[x, curve(x)] for x in xs],
        "shaded": shaded,
        "marks": marks,
    }


def two_sided_critical(curve, confidence):
    return critical_value(curve, 1 - (1 - confidence) / 2)


def proportion_notes(samples):
    for successes, n in samples:
        if successes < 5 or n - successes < 5:
            return ["Hay menos de 5 éxitos o fracasos: la aproximación normal puede no ser confiable."]
    return []


def interval_result(symbol, estimate, standard_error, critical, confidence, curve, axis, inputs,
                    notes=()):
    margin = critical * standard_error
    lower = estimate - margin
    upper = estimate + margin
    rows = inputs + [
        ("Error estándar", standard_error),
        (f"Valor crítico {axis}", critical),
        ("Margen de error", margin),
        ("Límite inferior", lower),
        ("Límite superior", upper),
    ]
    return {
        "answer": f"Intervalo de confianza al {confidence * 100:g}% para {symbol}: "
                  f"({fmt(lower)} , {fmt(upper)})",
        "tables": [values_table(rows)],
        "chart": make_chart(curve, axis, [[-critical, critical]], [-critical, critical]),
        "notes": list(notes),
    }


def probability_result(curve, axis, variable, tail, values, scores, rows):
    if tail == "below":
        probability = probability_below(curve, scores[0])
        text = f"P({variable} < {values[0]:g})"
        shaded = [[None, scores[0]]]
    elif tail == "above":
        probability = probability_above(curve, scores[0])
        text = f"P({variable} > {values[0]:g})"
        shaded = [[scores[0], None]]
    else:
        if scores[0] >= scores[1]:
            raise ValueError("El primer valor debe ser menor que el segundo.")
        probability = probability_below(curve, scores[1]) - probability_below(curve, scores[0])
        text = f"P({values[0]:g} < {variable} < {values[1]:g})"
        shaded = [[scores[0], scores[1]]]
    rows = rows + [("Probabilidad", probability), ("Probabilidad complementaria", 1 - probability)]
    return {
        "answer": f"{text} = {probability:.4f}  ({probability * 100:.2f}%)",
        "tables": [values_table(rows)],
        "chart": make_chart(curve, axis, shaded, list(scores)),
        "notes": [],
    }


def critical_value_result(curve, axis, data, rows):
    confidence = read_confidence(data)
    tails = read_choice(data, "tails", "Tipo de prueba", ("two", "one"))
    alpha = 1 - confidence
    if tails == "two":
        critical = critical_value(curve, 1 - alpha / 2)
        answer = f"Valor crítico {axis}α/2 = ±{fmt(critical)}"
        shaded = [[None, -critical], [critical, None]]
        marks = [-critical, critical]
    else:
        critical = critical_value(curve, 1 - alpha)
        answer = f"Valor crítico {axis}α = {fmt(critical)}"
        shaded = [[critical, None]]
        marks = [critical]
    rows = rows + [
        ("Nivel de confianza", f"{confidence * 100:g}%"),
        ("Nivel de significancia (α)", alpha),
        ("Colas", "Dos colas" if tails == "two" else "Una cola"),
        ("Valor crítico", critical),
    ]
    common_rows = []
    for level in COMMON_CONFIDENCES:
        common_rows.append([f"{level}%", fmt(two_sided_critical(curve, level / 100)),
                            fmt(critical_value(curve, level / 100))])
    return {
        "answer": answer,
        "tables": [
            values_table(rows),
            {
                "title": "Valores críticos más usados",
                "headers": ["Confianza", f"{axis} (dos colas)", f"{axis} (una cola)"],
                "rows": common_rows,
            },
        ],
        "chart": make_chart(curve, axis, shaded, marks),
        "notes": [],
    }


def z_mean_interval(data):
    mean = read_number(data, "sample_mean", "Media muestral")
    sigma = read_number(data, "sigma", "Desviación estándar poblacional (σ)", positive=True)
    n = read_number(data, "n", "Tamaño de muestra (n)", minimum=1, whole=True)
    confidence = read_confidence(data)
    critical = two_sided_critical(normal_curve, confidence)
    inputs = [("Media muestral (x̄)", mean), ("Desviación poblacional (σ)", sigma),
              ("Tamaño de muestra (n)", n)]
    return interval_result("μ", mean, sigma / math.sqrt(n), critical, confidence,
                           normal_curve, "Z", inputs)


def z_one_proportion(data):
    n = read_number(data, "n", "Tamaño de muestra (n)", minimum=1, whole=True)
    successes = read_number(data, "successes", "Éxitos (x)", minimum=0, maximum=n, whole=True)
    confidence = read_confidence(data)
    p = successes / n
    critical = two_sided_critical(normal_curve, confidence)
    inputs = [("Tamaño de muestra (n)", n), ("Éxitos (x)", successes), ("Proporción muestral (p̂)", p)]
    notes = proportion_notes([(successes, n)])
    return interval_result("p", p, math.sqrt(p * (1 - p) / n), critical, confidence,
                           normal_curve, "Z", inputs, notes)


def z_two_proportions(data):
    n1 = read_number(data, "n1", "Tamaño de muestra 1 (n₁)", minimum=1, whole=True)
    successes1 = read_number(data, "successes1", "Éxitos de la muestra 1 (x₁)",
                             minimum=0, maximum=n1, whole=True)
    n2 = read_number(data, "n2", "Tamaño de muestra 2 (n₂)", minimum=1, whole=True)
    successes2 = read_number(data, "successes2", "Éxitos de la muestra 2 (x₂)",
                             minimum=0, maximum=n2, whole=True)
    confidence = read_confidence(data)
    p1 = successes1 / n1
    p2 = successes2 / n2
    critical = two_sided_critical(normal_curve, confidence)
    standard_error = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    inputs = [("Proporción muestra 1 (p̂₁)", p1), ("Proporción muestra 2 (p̂₂)", p2),
              ("Diferencia (p̂₁ − p̂₂)", p1 - p2)]
    notes = proportion_notes([(successes1, n1), (successes2, n2)])
    return interval_result("p₁ − p₂", p1 - p2, standard_error, critical, confidence,
                           normal_curve, "Z", inputs, notes)


def z_probability(data):
    mean = read_number(data, "mean", "Media (μ)")
    std_dev = read_number(data, "std_dev", "Desviación estándar (σ)", positive=True)
    tail = read_choice(data, "tail", "Tipo de probabilidad", ("below", "above", "between"))
    x1 = read_number(data, "x", "Valor x")
    x2 = read_number(data, "x2", "Segundo valor") if tail == "between" else None
    values = [x1] if x2 is None else [x1, x2]
    scores = [standardize(value, mean, std_dev) for value in values]
    rows = [("Media (μ)", mean), ("Desviación estándar (σ)", std_dev)]
    rows += [(f"Valor Z {i + 1}", score) for i, score in enumerate(scores)]
    return probability_result(normal_curve, "Z", "X", tail, values, scores, rows)


def z_critical_value(data):
    return critical_value_result(normal_curve, "Z", data, [])


def t_mean_interval(data):
    mean = read_number(data, "sample_mean", "Media muestral")
    s = read_number(data, "s", "Desviación estándar muestral (s)", positive=True)
    n = read_number(data, "n", "Tamaño de muestra (n)", minimum=2, whole=True)
    confidence = read_confidence(data)
    df = n - 1
    curve = t_curve(df)
    critical = two_sided_critical(curve, confidence)
    inputs = [("Media muestral (x̄)", mean), ("Desviación muestral (s)", s),
              ("Tamaño de muestra (n)", n), ("Grados de libertad (n − 1)", df)]
    return interval_result("μ", mean, s / math.sqrt(n), critical, confidence, curve, "t", inputs)


def t_probability(data):
    df = read_df(data)
    tail = read_choice(data, "tail", "Tipo de probabilidad", ("below", "above", "between"))
    t1 = read_number(data, "x", "Valor de t", minimum=-MAX_SCORE, maximum=MAX_SCORE)
    t2 = None
    if tail == "between":
        t2 = read_number(data, "x2", "Segundo valor de t", minimum=-MAX_SCORE, maximum=MAX_SCORE)
    values = [t1] if t2 is None else [t1, t2]
    rows = [("Grados de libertad (gl)", df)]
    return probability_result(t_curve(df), "t", "T", tail, values, values, rows)


def t_critical_value(data):
    df = read_df(data)
    return critical_value_result(t_curve(df), "t", data, [("Grados de libertad (gl)", df)])


PROBLEMS = {
    ("z", "mean_interval"): z_mean_interval,
    ("z", "one_proportion"): z_one_proportion,
    ("z", "two_proportions"): z_two_proportions,
    ("z", "probability"): z_probability,
    ("z", "critical_value"): z_critical_value,
    ("t", "mean_interval"): t_mean_interval,
    ("t", "probability"): t_probability,
    ("t", "critical_value"): t_critical_value,
}


def solve(data):
    problem = PROBLEMS.get((data.get("distribution"), data.get("problem")))
    if problem is None:
        raise ValueError("Elige una distribución y un tipo de problema.")
    return problem(data)
