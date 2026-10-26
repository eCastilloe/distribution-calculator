"""Calculadora: lee los datos de cada problema, hace el cálculo y arma la respuesta."""

import math

from distributions import NORMAL, student_t, chi_square, fisher_f


# ---------- Lectura y validación de los datos ----------

MAX_SCORE = 1000
MAX_WHOLE = 10**9
MAX_DF = 1000
MAX_DATA = 1000
SUBSCRIPTS = {"": "", "1": "₁", "2": "₂"}


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


def read_optional_number(data, name, label):
    """Como read_number, pero si el campo está vacío devuelve None."""
    if str(data.get(name, "")).strip() == "":
        return None
    return read_number(data, name, label)


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


def read_data_list(data, name, label):
    """Convierte un texto como "1.3%, 1.4%, 1.2%" en la lista [1.3, 1.4, 1.2]."""
    text = str(data.get(name, ""))
    # Las comas y los punto y coma separan datos; %, $, corchetes y paréntesis se ignoran
    for symbol in (",", ";", "%", "$", "[", "]", "(", ")"):
        text = text.replace(symbol, " ")
    values = []
    for piece in text.split():
        try:
            value = float(piece)
        except ValueError:
            raise ValueError(f"{label}: «{piece}» no es un número (usa punto decimal).")
        if not math.isfinite(value):
            raise ValueError(f"{label}: «{piece}» no es un número válido.")
        values.append(value)
    if len(values) < 2:
        raise ValueError(f"{label}: escribe al menos 2 datos.")
    if len(values) > MAX_DATA:
        raise ValueError(f"{label}: escribe como máximo {MAX_DATA} datos.")
    return values


def sample_stats(values, label):
    """Media y desviación estándar muestral (se divide entre n − 1) de una lista de datos."""
    n = len(values)
    mean = sum(values) / n
    squares = 0
    for value in values:
        squares += (value - mean) ** 2
    std_dev = math.sqrt(squares / (n - 1))
    if std_dev == 0:
        raise ValueError(f"{label}: todos los datos son iguales, la desviación estándar es 0.")
    return mean, std_dev, n


def read_sample(data, number, std_symbol, min_n=2):
    """Media, desviación estándar y tamaño de una muestra.
    Se leen del resumen que escribió el usuario o se calculan con su lista de datos."""
    which = f" {number}" if number else ""
    sub = SUBSCRIPTS[number]
    if data.get("input_mode") == "data":
        values = read_data_list(data, "values" + number, f"Datos{which}")
        return sample_stats(values, f"Datos{which}")
    mean = read_number(data, "mean" + number, f"Media{which} (x̄{sub})")
    std_label = f"Desviación estándar{which} ({std_symbol}{sub})"
    std_dev = read_number(data, "std_dev" + number, std_label, positive=True)
    n = read_sample_size(data, "n" + number, f"Tamaño de muestra{which} (n{sub})", minimum=min_n)
    return mean, std_dev, n


def read_variance(data, number=""):
    """Varianza muestral s² y tamaño de muestra, a partir de s², de s o de la lista de datos."""
    which = f" {number}" if number else ""
    sub = SUBSCRIPTS[number]
    modes = ("variance", "std_dev", "data")
    mode = read_choice(data, "input_mode", "¿Cómo tienes los datos?", modes)
    if mode == "data":
        values = read_data_list(data, "values" + number, f"Datos{which}")
        if len(values) > MAX_DF + 1:
            raise ValueError(f"Datos{which}: escribe como máximo {MAX_DF + 1} datos.")
        mean, std_dev, n = sample_stats(values, f"Datos{which}")
        return std_dev ** 2, n
    n_label = f"Tamaño de muestra{which} (n{sub})"
    n = read_sample_size(data, "n" + number, n_label, maximum=MAX_DF + 1)
    if mode == "std_dev":
        std_dev = read_number(data, "std_dev" + number, f"Desviación estándar{which} (s{sub})",
                              positive=True)
        return std_dev ** 2, n
    variance = read_number(data, "variance" + number, f"Varianza muestral{which} (s{sub}²)",
                           positive=True)
    return variance, n


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


# ---------- Formato de la respuesta: tabla, interpretación y conclusiones (H₀ y H₁) ----------

PARAMETER_NAMES = {
    "μ": "la media poblacional μ",
    "μ_D": "la diferencia media μ_D (dato 1 − dato 2)",
    "μ₁ − μ₂": "la diferencia de medias μ₁ − μ₂",
    "π": "la proporción poblacional π",
    "π₁ − π₂": "la diferencia de proporciones π₁ − π₂",
    "σ²": "la varianza poblacional σ²",
    "σ₁² / σ₂²": "el cociente de varianzas σ₁² / σ₂²",
}


def fmt(value):
    if isinstance(value, (int, str)):
        return str(value)
    return f"{value:.4f}"


def values_table(rows):
    table_rows = []
    for label, value in rows:
        table_rows.append([label, fmt(value)])
    return {"title": "Valores del cálculo", "headers": ["Concepto", "Valor"], "rows": table_rows}


def claim_conclusion(symbol, claimed, lower, upper):
    """H₀ se rechaza si el valor afirmado queda fuera del intervalo."""
    text = f"H₀: {symbol} = {claimed:g} y H₁: {symbol} ≠ {claimed:g}. "
    if lower <= claimed <= upper:
        return text + f"El valor {claimed:g} está dentro del intervalo: no se rechaza H₀."
    return text + f"El valor {claimed:g} está fuera del intervalo: se rechaza H₀."


def difference_conclusion(lower, upper, first, second):
    text = f"H₀: {first} = {second} y H₁: {first} ≠ {second}. "
    if lower > 0:
        return text + ("Ambos límites son positivos: se rechaza H₀ y se concluye que "
                       f"{first} > {second}.")
    if upper < 0:
        return text + ("Ambos límites son negativos: se rechaza H₀ y se concluye que "
                       f"{first} < {second}.")
    return text + f"El intervalo incluye el 0: no se rechaza H₀, así que {first} = {second}."


def ratio_conclusion(lower, upper):
    text = "H₀: σ₁² = σ₂² y H₁: σ₁² ≠ σ₂². "
    if lower > 1:
        return text + ("Ambos límites son mayores que 1: se rechaza H₀; las varianzas son "
                       "significativamente diferentes (σ₁² > σ₂²).")
    if upper < 1:
        return text + ("Ambos límites son menores que 1: se rechaza H₀; las varianzas son "
                       "significativamente diferentes (σ₁² < σ₂²).")
    return text + ("El intervalo incluye el 1: no se rechaza H₀; las varianzas no son "
                   "significativamente diferentes.")


def interval_result(symbol, confidence, lower, upper, rows, conclusion="", notes=()):
    rows = rows + [("Límite inferior", lower), ("Límite superior", upper)]
    interpretation = (f"Con {confidence * 100:g}% de confianza, {PARAMETER_NAMES[symbol]} "
                      f"está entre {fmt(lower)} y {fmt(upper)}.")
    if conclusion:
        interpretation += " " + conclusion
    return {
        "answer": f"Intervalo de confianza al {confidence * 100:g}% para {symbol}: "
                  f"({fmt(lower)} , {fmt(upper)})",
        "interpretation": interpretation,
        "tables": [values_table(rows)],
        "notes": list(notes),
    }


# ---------- Intervalos de confianza y tamaño de muestra ----------

def plus_minus_limits(estimate, standard_error, dist, confidence, rows):
    """Límites de estimación ± valor crítico · error estándar (Z y t).
    También agrega sus filas a la tabla."""
    critical = dist.quantile(1 - (1 - confidence) / 2)
    margin = critical * standard_error
    rows += [
        ("Error estándar", standard_error),
        (f"Valor crítico {dist.axis}", critical),
        ("Margen de error (e)", margin),
    ]
    return estimate - margin, estimate + margin


def one_mean(data):
    known_sigma = data.get("distribution") == "z"
    if known_sigma:
        std_label = "Desviación estándar (σ)"
        mean, std_dev, n = read_sample(data, "", "σ", min_n=1)
    else:
        std_label = "Desviación estándar muestral (s)"
        mean, std_dev, n = read_sample(data, "", "s")
    claimed = read_optional_number(data, "claimed", "Valor afirmado (μ₀)")
    confidence = read_confidence(data)
    rows = [("Media muestral (x̄)", mean), (std_label, std_dev), ("Tamaño de muestra (n)", n)]
    notes = []
    if known_sigma:
        dist = NORMAL
    else:
        dist = student_t(n - 1)
        rows.append(("Grados de libertad (n − 1)", n - 1))
        if n >= 30:
            notes.append("Con n ≥ 30 el formulario indica usar Z (una media n ≥ 30).")
    lower, upper = plus_minus_limits(mean, std_dev / math.sqrt(n), dist, confidence, rows)
    conclusion = ""
    if claimed is not None:
        conclusion = claim_conclusion("μ", claimed, lower, upper)
    return interval_result("μ", confidence, lower, upper, rows, conclusion, notes)


def paired_samples(data):
    # Es el intervalo de una media con t, aplicado a las diferencias de cada par
    rows = []
    if data.get("input_mode") == "pairs":
        first = read_data_list(data, "values1", "Datos 1 (antes)")
        second = read_data_list(data, "values2", "Datos 2 (después)")
        if len(first) != len(second):
            raise ValueError("Las dos columnas deben tener la misma cantidad de datos.")
        differences = []
        for i in range(len(first)):
            differences.append(first[i] - second[i])
        mean, std_dev, n = sample_stats(differences, "Diferencias")
        texts = []
        for difference in differences:
            texts.append(f"{difference:g}")
        rows.append(("Diferencias d = dato 1 − dato 2", ", ".join(texts)))
    else:
        mean = read_number(data, "mean", "Media de las diferencias (d̄)")
        std_dev = read_number(data, "std_dev", "Desviación estándar de las diferencias (s_d)",
                              positive=True)
        n = read_sample_size(data, "n", "Número de pares (n)")
    confidence = read_confidence(data)
    rows += [("Media de las diferencias (d̄)", mean),
             ("Desviación estándar de las diferencias (s_d)", std_dev),
             ("Número de pares (n)", n), ("Grados de libertad (n − 1)", n - 1)]
    lower, upper = plus_minus_limits(mean, std_dev / math.sqrt(n), student_t(n - 1),
                                            confidence, rows)
    conclusion = difference_conclusion(lower, upper, "μ₁", "μ₂")
    return interval_result("μ_D", confidence, lower, upper, rows, conclusion)


def two_means(data):
    known_sigma = data.get("distribution") == "z"
    std_symbol = "σ" if known_sigma else "s"
    mean1, std1, n1 = read_sample(data, "1", std_symbol)
    mean2, std2, n2 = read_sample(data, "2", std_symbol)
    confidence = read_confidence(data)
    rows = [("Media 1 (x̄₁)", mean1), (f"Desviación estándar 1 ({std_symbol}₁)", std1),
            ("Tamaño de muestra 1 (n₁)", n1), ("Media 2 (x̄₂)", mean2),
            (f"Desviación estándar 2 ({std_symbol}₂)", std2), ("Tamaño de muestra 2 (n₂)", n2),
            ("Diferencia de medias (x̄₁ − x̄₂)", mean1 - mean2)]
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

    lower, upper = plus_minus_limits(mean1 - mean2, standard_error, dist, confidence, rows)
    conclusion = difference_conclusion(lower, upper, "μ₁", "μ₂")
    return interval_result("μ₁ − μ₂", confidence, lower, upper, rows, conclusion)


def proportion_notes(samples):
    for successes, n in samples:
        if successes < 5 or n - successes < 5:
            return ["Hay menos de 5 éxitos o fracasos: "
                    "la aproximación normal puede no ser confiable."]
    return []


def one_proportion(data):
    n = read_sample_size(data, "n", "Tamaño de muestra (n)", minimum=1)
    successes = read_number(data, "successes", "Éxitos (x)", minimum=0, maximum=n, whole=True)
    claimed = read_optional_number(data, "claimed", "Valor afirmado (π₀)")
    confidence = read_confidence(data)
    p = successes / n
    rows = [("Tamaño de muestra (n)", n), ("Éxitos (x)", successes), ("Proporción muestral (p)", p),
            ("q = 1 − p", 1 - p)]
    lower, upper = plus_minus_limits(p, math.sqrt(p * (1 - p) / n), NORMAL, confidence, rows)
    conclusion = ""
    if claimed is not None:
        conclusion = claim_conclusion("π", claimed, lower, upper)
    return interval_result("π", confidence, lower, upper, rows, conclusion,
                           proportion_notes([(successes, n)]))


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
    lower, upper = plus_minus_limits(p1 - p2, standard_error, NORMAL, confidence, rows)
    conclusion = difference_conclusion(lower, upper, "π₁", "π₂")
    return interval_result("π₁ − π₂", confidence, lower, upper, rows, conclusion,
                           proportion_notes([(successes1, n1), (successes2, n2)]))


def one_variance(data):
    variance, n = read_variance(data)
    claimed = read_optional_number(data, "claimed", "Valor afirmado (σ₀²)")
    confidence = read_confidence(data)
    df = n - 1
    dist = chi_square(df)
    alpha = 1 - confidence
    left = dist.quantile(alpha / 2)
    right = dist.quantile(1 - alpha / 2)
    lower = df * variance / right
    upper = df * variance / left
    rows = [("Tamaño de muestra (n)", n), ("Varianza muestral (s²)", variance),
            ("Grados de libertad (n − 1)", df), ("χ² α/2 (cola derecha)", right),
            ("χ² 1−α/2 (cola izquierda)", left)]
    conclusion = (f"Para la desviación estándar, σ está entre {fmt(math.sqrt(lower))} "
                  f"y {fmt(math.sqrt(upper))}.")
    if claimed is not None:
        conclusion += " " + claim_conclusion("σ²", claimed, lower, upper)
    return interval_result("σ²", confidence, lower, upper, rows, conclusion)


def variance_ratio(data):
    variance1, n1 = read_variance(data, "1")
    variance2, n2 = read_variance(data, "2")
    confidence = read_confidence(data)
    df1 = n1 - 1
    df2 = n2 - 1
    alpha = 1 - confidence
    ratio = variance1 / variance2
    f_12 = fisher_f(df1, df2).quantile(1 - alpha / 2)
    f_21 = fisher_f(df2, df1).quantile(1 - alpha / 2)
    lower = ratio / f_12
    upper = ratio * f_21
    rows = [("Varianza 1 (s₁²)", variance1), ("Tamaño de muestra 1 (n₁)", n1),
            ("Varianza 2 (s₂²)", variance2), ("Tamaño de muestra 2 (n₂)", n2),
            ("Cociente s₁² / s₂²", ratio), ("ν₁ = n₁ − 1", df1), ("ν₂ = n₂ − 1", df2),
            ("F α/2 (ν₁, ν₂)", f_12), ("F α/2 (ν₂, ν₁)", f_21)]
    return interval_result("σ₁² / σ₂²", confidence, lower, upper, rows,
                           ratio_conclusion(lower, upper))


def sample_size(data):
    target = read_choice(data, "target", "Tamaño de muestra para", ("mean", "proportion"))
    error = read_number(data, "error", "Error máximo (e)", positive=True)
    confidence = read_confidence(data)
    z = NORMAL.quantile(1 - (1 - confidence) / 2)
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
    n = max(1, math.ceil(round(exact, 9)))
    rows += [("Error máximo (e)", error), ("Valor crítico Z", z), ("n sin redondear", exact),
             ("n (redondeado hacia arriba)", n)]
    return {
        "answer": f"Tamaño de muestra necesario: n = {n}",
        "interpretation": f"Se necesitan al menos {n} datos para que el error de estimación "
                          f"no pase de {error:g}, con {confidence * 100:g}% de confianza.",
        "tables": [values_table(rows)],
        "notes": [],
    }


# ---------- Probabilidad ----------

TAIL_OPTIONS = ("below", "above", "between")


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
    rows = [("Media (μ)", mean), ("Desviación estándar (σ)", std_dev)]
    scores = []
    for value in values:
        score = (value - mean) / std_dev
        if abs(score) > MAX_SCORE:
            raise ValueError("El valor está demasiado lejos de la media.")
        scores.append(score)
        rows.append((f"Valor Z {len(scores)}", score))
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
        meaning = f"sea menor que {values[0]:g}"
    elif tail == "above":
        result = dist.above(scores[0])
        text = f"P({variable} > {values[0]:g})"
        meaning = f"sea mayor que {values[0]:g}"
    else:
        result = dist.below(scores[1]) - dist.below(scores[0])
        text = f"P({values[0]:g} < {variable} < {values[1]:g})"
        meaning = f"esté entre {values[0]:g} y {values[1]:g}"
    rows += [("Probabilidad", result), ("Probabilidad complementaria", 1 - result)]
    return {
        "answer": f"{text} = {result:.4f}  ({result * 100:.2f}%)",
        "interpretation": f"La probabilidad de que {variable} {meaning} es {result * 100:.2f}%.",
        "tables": [values_table(rows)],
        "notes": [],
    }


# ---------- Índice: qué función resuelve cada problema ----------

PROBLEMS = {
    ("z", "mean_interval"): one_mean,
    ("z", "two_means"): two_means,
    ("z", "one_proportion"): one_proportion,
    ("z", "two_proportions"): two_proportions,
    ("z", "sample_size"): sample_size,
    ("z", "probability"): probability,
    ("t", "mean_interval"): one_mean,
    ("t", "two_means"): two_means,
    ("t", "paired"): paired_samples,
    ("t", "probability"): probability,
    ("chi2", "variance_interval"): one_variance,
    ("chi2", "probability"): probability,
    ("f", "variance_ratio"): variance_ratio,
    ("f", "probability"): probability,
}


def solve(data):
    problem = PROBLEMS.get((data.get("distribution"), data.get("problem")))
    if problem is None:
        raise ValueError("Elige una distribución y un tipo de problema.")
    return problem(data)
