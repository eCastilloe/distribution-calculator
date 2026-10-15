import math

from distributions import NORMAL, student_t, chi_square, fisher_f

CHART_POINTS = 200
COMMON_CONFIDENCES = [90, 95, 98, 99]
MAX_SCORE = 1000
MAX_WHOLE = 10**9
MAX_DF = 1000
TAIL_OPTIONS = ("below", "above", "between")


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
    percent = read_number(data, "confidence", "Nivel de confianza (%)", minimum=50, maximum=99.99)
    return percent / 100


def read_df(data, name="df", label="Grados de libertad (gl)"):
    return read_number(data, name, label, minimum=1, maximum=MAX_DF, whole=True)


def read_sample_size(data, name, label, minimum=2, maximum=None):
    return read_number(data, name, label, minimum=minimum, maximum=maximum, whole=True)


def read_distribution(data):
    """Distribución elegida y las filas de la tabla que describen sus grados de libertad."""
    name = data.get("distribution")
    if name == "z":
        return NORMAL, []
    if name == "t":
        df = read_df(data)
        return student_t(df), [("Grados de libertad (gl)", df)]
    if name == "chi2":
        df = read_df(data)
        return chi_square(df), [("Grados de libertad (gl)", df)]
    df1 = read_df(data, "df1", "Grados de libertad del numerador (ν₁)")
    df2 = read_df(data, "df2", "Grados de libertad del denominador (ν₂)")
    return fisher_f(df1, df2), [("ν₁ (numerador)", df1), ("ν₂ (denominador)", df2)]


def values_table(rows):
    return {
        "title": "Valores del cálculo",
        "headers": ["Concepto", "Valor"],
        "rows": [[label, fmt(value)] for label, value in rows],
    }


def chart_ticks(start, end):
    # Paso "redondo" (1, 2 o 5 por una potencia de 10) para tener 10 marcas en el eje
    raw_step = (end - start) / 10
    power = 10 ** math.floor(math.log10(raw_step))
    step = next(m * power for m in (1, 2, 5, 10) if m * power >= raw_step)
    first = math.ceil(start / step)
    last = math.floor(end / step)
    return [round(i * step, 10) for i in range(first, last + 1)]


def make_chart(dist, shaded, marks):
    if dist.symmetric:
        # El eje va de -limit a limit
        farthest = max(abs(mark) for mark in marks)
        limit = min(max(4, math.ceil(farthest + 1)), 8)
        start, end = -limit, limit
    else:
        # χ² y F empiezan en 0. Se muestra hasta un poco después de las marcas,
        # pero sin pasar del punto que deja el 99.9% del área a la izquierda
        start = 0
        end = max(dist.quantile(0.99), max(marks) * 1.15)
        end = min(end, dist.quantile(0.999))
    grid = [start + (end - start) * i / CHART_POINTS for i in range(CHART_POINTS + 1)]
    # Las marcas se agregan como puntos para que el área sombreada empiece en ellas
    visible_marks = [mark for mark in marks if start <= mark <= end]
    xs = sorted(set(grid + visible_marks))
    return {
        "axis": dist.axis,
        "start": start,
        "end": end,
        "ticks": chart_ticks(start, end),
        "points": [[x, dist.curve(x)] for x in xs],
        "shaded": shaded,
        "marks": marks,
    }


def two_sided_critical(dist, confidence):
    return dist.quantile(1 - (1 - confidence) / 2)


def difference_criterion(lower, upper, first, second):
    if lower > 0:
        return f"Criterio de decisión: ambos límites son positivos, así que {first} > {second}."
    if upper < 0:
        return f"Criterio de decisión: ambos límites son negativos, así que {first} < {second}."
    return f"Criterio de decisión: el intervalo incluye el 0, así que {first} = {second}."


def ratio_criterion(lower, upper):
    if lower > 1:
        return "Criterio de decisión: ambos límites son mayores que 1, así que σ₁² > σ₂²."
    if upper < 1:
        return "Criterio de decisión: ambos límites son menores que 1, así que σ₁² < σ₂²."
    return "Criterio de decisión: el intervalo incluye el 1, así que σ₁² = σ₂²."


def interval_result(symbol, confidence, lower, upper, rows, chart, notes=()):
    rows = rows + [("Límite inferior", lower), ("Límite superior", upper)]
    return {
        "answer": f"Intervalo de confianza al {confidence * 100:g}% para {symbol}: "
                  f"({fmt(lower)} , {fmt(upper)})",
        "tables": [values_table(rows)],
        "chart": chart,
        "notes": list(notes),
    }


def estimate_plus_minus(symbol, estimate, standard_error, dist, confidence, rows,
                        compare=None, notes=()):
    """Intervalo de la forma estimación ± valor crítico · error estándar (Z y t)."""
    critical = two_sided_critical(dist, confidence)
    margin = critical * standard_error
    lower = estimate - margin
    upper = estimate + margin
    rows = rows + [
        ("Error estándar", standard_error),
        (f"Valor crítico {dist.axis}", critical),
        ("Margen de error (e)", margin),
    ]
    notes = list(notes)
    if compare:
        notes.append(difference_criterion(lower, upper, *compare))
    chart = make_chart(dist, [[-critical, critical]], [-critical, critical])
    return interval_result(symbol, confidence, lower, upper, rows, chart, notes)


def one_mean(data, symbol="μ", mean_label="Media muestral (x̄)", std_label=None):
    known_sigma = data.get("distribution") == "z"
    if std_label is None:
        std_label = "Desviación estándar (σ)" if known_sigma else "Desviación estándar muestral (s)"
    mean = read_number(data, "sample_mean", mean_label)
    std_dev = read_number(data, "std_dev", std_label, positive=True)
    n = read_sample_size(data, "n", "Tamaño de muestra (n)", minimum=1 if known_sigma else 2)
    confidence = read_confidence(data)
    rows = [(mean_label, mean), (std_label, std_dev), ("Tamaño de muestra (n)", n)]
    if known_sigma:
        dist = NORMAL
    else:
        dist = student_t(n - 1)
        rows.append(("Grados de libertad (n − 1)", n - 1))
    return estimate_plus_minus(symbol, mean, std_dev / math.sqrt(n), dist, confidence, rows)


def paired_samples(data):
    # Es el intervalo de una media con t, aplicado a las diferencias de cada par
    return one_mean(data, "μ_D", "Media de las diferencias (d̄)",
                    "Desviación estándar de las diferencias (s_d)")


def two_means(data):
    known_sigma = data.get("distribution") == "z"
    std_symbol = "σ" if known_sigma else "s"
    mean1 = read_number(data, "mean1", "Media de la muestra 1 (x̄₁)")
    std1 = read_number(data, "std_dev1", f"Desviación estándar 1 ({std_symbol}₁)", positive=True)
    n1 = read_sample_size(data, "n1", "Tamaño de muestra 1 (n₁)")
    mean2 = read_number(data, "mean2", "Media de la muestra 2 (x̄₂)")
    std2 = read_number(data, "std_dev2", f"Desviación estándar 2 ({std_symbol}₂)", positive=True)
    n2 = read_sample_size(data, "n2", "Tamaño de muestra 2 (n₂)")
    confidence = read_confidence(data)
    rows = [("Diferencia de medias (x̄₁ − x̄₂)", mean1 - mean2)]
    part1 = std1 ** 2 / n1
    part2 = std2 ** 2 / n2

    if known_sigma:
        dist = NORMAL
        standard_error = math.sqrt(part1 + part2)
    elif read_choice(data, "variances", "Varianzas", ("equal", "different")) == "equal":
        df = n1 + n2 - 2
        pooled = math.sqrt(((n1 - 1) * std1 ** 2 + (n2 - 1) * std2 ** 2) / df)
        dist = student_t(df)
        standard_error = pooled * math.sqrt(1 / n1 + 1 / n2)
        rows += [("Desviación combinada (Sp)", pooled), ("Grados de libertad (n₁ + n₂ − 2)", df)]
    else:
        # Grados de libertad de Welch (fórmula del formulario); no se redondean
        df = (part1 + part2) ** 2 / (part1 ** 2 / (n1 - 1) + part2 ** 2 / (n2 - 1))
        dist = student_t(df)
        standard_error = math.sqrt(part1 + part2)
        rows.append(("Grados de libertad (ν)", df))

    return estimate_plus_minus("μ₁ − μ₂", mean1 - mean2, standard_error, dist, confidence, rows,
                               compare=("μ₁", "μ₂"))


def proportion_notes(samples):
    for successes, n in samples:
        if successes < 5 or n - successes < 5:
            return ["Hay menos de 5 éxitos o fracasos: "
                    "la aproximación normal puede no ser confiable."]
    return []


def one_proportion(data):
    n = read_sample_size(data, "n", "Tamaño de muestra (n)", minimum=1)
    successes = read_number(data, "successes", "Éxitos (x)", minimum=0, maximum=n, whole=True)
    confidence = read_confidence(data)
    p = successes / n
    rows = [("Tamaño de muestra (n)", n), ("Éxitos (x)", successes), ("Proporción muestral (p)", p),
            ("q = 1 − p", 1 - p)]
    return estimate_plus_minus("π", p, math.sqrt(p * (1 - p) / n), NORMAL, confidence, rows,
                               notes=proportion_notes([(successes, n)]))


def two_proportions(data):
    n1 = read_sample_size(data, "n1", "Tamaño de muestra 1 (n₁)", minimum=1)
    successes1 = read_number(data, "successes1", "Éxitos de la muestra 1 (x₁)",
                             minimum=0, maximum=n1, whole=True)
    n2 = read_sample_size(data, "n2", "Tamaño de muestra 2 (n₂)", minimum=1)
    successes2 = read_number(data, "successes2", "Éxitos de la muestra 2 (x₂)",
                             minimum=0, maximum=n2, whole=True)
    confidence = read_confidence(data)
    p1 = successes1 / n1
    p2 = successes2 / n2
    standard_error = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    rows = [("Proporción muestra 1 (p₁)", p1), ("Proporción muestra 2 (p₂)", p2),
            ("Diferencia (p₁ − p₂)", p1 - p2)]
    notes = proportion_notes([(successes1, n1), (successes2, n2)])
    return estimate_plus_minus("π₁ − π₂", p1 - p2, standard_error, NORMAL, confidence, rows,
                               compare=("π₁", "π₂"), notes=notes)


def sample_size(data):
    target = read_choice(data, "target", "Tamaño de muestra para", ("mean", "proportion"))
    error = read_number(data, "error", "Error máximo (e)", positive=True)
    confidence = read_confidence(data)
    z = two_sided_critical(NORMAL, confidence)
    if target == "mean":
        sigma = read_number(data, "std_dev", "Desviación estándar (σ)", positive=True)
        exact = (z * sigma / error) ** 2
        rows = [("Desviación estándar (σ)", sigma)]
    else:
        p = read_number(data, "p", "Proporción estimada (p)", positive=True, maximum=0.9999)
        exact = z ** 2 * p * (1 - p) / error ** 2
        rows = [("Proporción estimada (p)", p), ("q = 1 − p", 1 - p)]
    if exact > MAX_WHOLE:
        raise ValueError("El tamaño de muestra sale demasiado grande: revisa el error máximo (e).")
    # Se redondea hacia arriba: con menos datos el error pasaría del máximo pedido.
    # round(…, 9) evita que un 385.0000000001 de la aritmética se vuelva 386
    n = max(1, math.ceil(round(exact, 9)))
    rows += [("Error máximo (e)", error), ("Valor crítico Z", z), ("n sin redondear", exact),
             ("n (redondeado hacia arriba)", n)]
    return {
        "answer": f"Tamaño de muestra necesario: n = {n}",
        "tables": [values_table(rows)],
        "chart": make_chart(NORMAL, [[-z, z]], [-z, z]),
        "notes": [],
    }


def one_variance(data):
    n = read_sample_size(data, "n", "Tamaño de muestra (n)", maximum=MAX_DF + 1)
    variance = read_number(data, "variance", "Varianza muestral (s²)", positive=True)
    confidence = read_confidence(data)
    df = n - 1
    dist = chi_square(df)
    alpha = 1 - confidence
    # χ² no es simétrica: se necesita un valor crítico de cada lado
    left = dist.quantile(alpha / 2)
    right = dist.quantile(1 - alpha / 2)
    lower = df * variance / right
    upper = df * variance / left
    rows = [("Tamaño de muestra (n)", n), ("Varianza muestral (s²)", variance),
            ("Grados de libertad (n − 1)", df), ("χ² α/2 (cola derecha)", right),
            ("χ² 1−α/2 (cola izquierda)", left)]
    notes = [f"Para la desviación estándar σ: ({fmt(math.sqrt(lower))} , {fmt(math.sqrt(upper))})"]
    chart = make_chart(dist, [[left, right]], [left, right])
    return interval_result("σ²", confidence, lower, upper, rows, chart, notes)


def variance_ratio(data):
    n1 = read_sample_size(data, "n1", "Tamaño de muestra 1 (n₁)", maximum=MAX_DF + 1)
    variance1 = read_number(data, "variance1", "Varianza muestral 1 (s₁²)", positive=True)
    n2 = read_sample_size(data, "n2", "Tamaño de muestra 2 (n₂)", maximum=MAX_DF + 1)
    variance2 = read_number(data, "variance2", "Varianza muestral 2 (s₂²)", positive=True)
    confidence = read_confidence(data)
    df1 = n1 - 1
    df2 = n2 - 1
    alpha = 1 - confidence
    ratio = variance1 / variance2
    f_12 = fisher_f(df1, df2).quantile(1 - alpha / 2)
    f_21 = fisher_f(df2, df1).quantile(1 - alpha / 2)
    lower = ratio / f_12
    upper = ratio * f_21
    rows = [("Cociente s₁² / s₂²", ratio), ("ν₁ = n₁ − 1", df1), ("ν₂ = n₂ − 1", df2),
            ("F α/2 (ν₁, ν₂)", f_12), ("F α/2 (ν₂, ν₁)", f_21)]
    # En la curva F(ν₁, ν₂) el valor crítico izquierdo es 1 / F a/2 (ν₂, ν₁)
    chart = make_chart(fisher_f(df1, df2), [[1 / f_21, f_12]], [1 / f_21, f_12])
    return interval_result("σ₁² / σ₂²", confidence, lower, upper, rows, chart,
                           [ratio_criterion(lower, upper)])


def read_values(data, tail, minimum, maximum):
    first = read_number(data, "x", "Valor", minimum=minimum, maximum=maximum)
    if tail != "between":
        return [first]
    second = read_number(data, "x2", "Segundo valor", minimum=minimum, maximum=maximum)
    if first >= second:
        raise ValueError("El primer valor debe ser menor que el segundo.")
    return [first, second]


def read_z_values(data, tail):
    """Lee μ, σ y los valores de X, y los estandariza: Z = (x − μ) / σ."""
    mean = read_number(data, "mean", "Media (μ)")
    std_dev = read_number(data, "std_dev", "Desviación estándar (σ)", positive=True)
    values = read_values(data, tail, None, None)
    scores = [(value - mean) / std_dev for value in values]
    if any(abs(score) > MAX_SCORE for score in scores):
        raise ValueError("El valor está demasiado lejos de la media.")
    rows = [("Media (μ)", mean), ("Desviación estándar (σ)", std_dev)]
    rows += [(f"Valor Z {i + 1}", score) for i, score in enumerate(scores)]
    return values, scores, rows


def probability(data):
    tail = read_choice(data, "tail", "Tipo de probabilidad", TAIL_OPTIONS)
    # values son los datos como los escribió el usuario; scores, su posición en la curva
    if data.get("distribution") == "z":
        dist, variable = NORMAL, "X"
        values, scores, rows = read_z_values(data, tail)
    else:
        dist, rows = read_distribution(data)
        variable = dist.axis
        if dist.symmetric:
            values = read_values(data, tail, -MAX_SCORE, MAX_SCORE)
        else:
            values = read_values(data, tail, 0, MAX_WHOLE)
        scores = values

    if tail == "below":
        result = dist.below(scores[0])
        text = f"P({variable} < {values[0]:g})"
        shaded = [[None, scores[0]]]
    elif tail == "above":
        result = dist.above(scores[0])
        text = f"P({variable} > {values[0]:g})"
        shaded = [[scores[0], None]]
    else:
        result = dist.below(scores[1]) - dist.below(scores[0])
        text = f"P({values[0]:g} < {variable} < {values[1]:g})"
        shaded = [[scores[0], scores[1]]]
    rows += [("Probabilidad", result), ("Probabilidad complementaria", 1 - result)]
    return {
        "answer": f"{text} = {result:.4f}  ({result * 100:.2f}%)",
        "tables": [values_table(rows)],
        "chart": make_chart(dist, shaded, scores),
        "notes": [],
    }


def critical_values(dist, confidence):
    """(izquierdo, derecho) de dos colas y el de una cola (derecha)."""
    alpha = 1 - confidence
    right = dist.quantile(1 - alpha / 2)
    left = -right if dist.symmetric else dist.quantile(alpha / 2)
    return left, right, dist.quantile(1 - alpha)


def two_tail_text(dist, left, right):
    if dist.symmetric:
        return f"±{fmt(right)}"
    return f"{fmt(left)} y {fmt(right)}"


def critical_value(data):
    dist, rows = read_distribution(data)
    confidence = read_confidence(data)
    tails = read_choice(data, "tails", "Tipo de prueba", ("two", "one"))
    axis = dist.axis
    left, right, one_tail = critical_values(dist, confidence)
    if tails == "two":
        value = two_tail_text(dist, left, right)
        if dist.symmetric:
            answer = f"Valor crítico {axis}α/2 = {value}"
        else:
            answer = f"Valores críticos: {axis}1−α/2 = {fmt(left)} y {axis}α/2 = {fmt(right)}"
        shaded = [[None, left], [right, None]]
        marks = [left, right]
    else:
        value = fmt(one_tail)
        answer = f"Valor crítico {axis}α = {value}"
        shaded = [[one_tail, None]]
        marks = [one_tail]
    rows += [
        ("Nivel de confianza", f"{confidence * 100:g}%"),
        ("Nivel de significancia (α)", 1 - confidence),
        ("Colas", "Dos colas" if tails == "two" else "Una cola (derecha)"),
        ("Valor crítico", value),
    ]

    common_rows = []
    for level in COMMON_CONFIDENCES:
        left, right, one_tail = critical_values(dist, level / 100)
        common_rows.append([f"{level}%", two_tail_text(dist, left, right), fmt(one_tail)])
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
        "chart": make_chart(dist, shaded, marks),
        "notes": [],
    }


PROBLEMS = {
    ("z", "mean_interval"): one_mean,
    ("z", "two_means"): two_means,
    ("z", "one_proportion"): one_proportion,
    ("z", "two_proportions"): two_proportions,
    ("z", "sample_size"): sample_size,
    ("z", "probability"): probability,
    ("z", "critical_value"): critical_value,
    ("t", "mean_interval"): one_mean,
    ("t", "two_means"): two_means,
    ("t", "paired"): paired_samples,
    ("t", "probability"): probability,
    ("t", "critical_value"): critical_value,
    ("chi2", "variance_interval"): one_variance,
    ("chi2", "probability"): probability,
    ("chi2", "critical_value"): critical_value,
    ("f", "variance_ratio"): variance_ratio,
    ("f", "probability"): probability,
    ("f", "critical_value"): critical_value,
}


def solve(data):
    problem = PROBLEMS.get((data.get("distribution"), data.get("problem")))
    if problem is None:
        raise ValueError("Elige una distribución y un tipo de problema.")
    return problem(data)
