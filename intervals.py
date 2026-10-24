"""Intervalos de confianza del formulario y tamaño de muestra."""

import math

from distributions import NORMAL, student_t, chi_square, fisher_f
from inputs import (
    MAX_WHOLE, read_number, read_optional_number, read_choice, read_confidence,
    read_sample_size, read_data_list, sample_stats, read_sample, read_variance,
)
from results import (
    fmt, values_table, interval_result, claim_conclusion, difference_conclusion,
    ratio_conclusion,
)
from charts import make_chart


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
    chart = make_chart(dist, [[-critical, critical]], [-critical, critical])
    return estimate - margin, estimate + margin, chart


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
    lower, upper, chart = plus_minus_limits(mean, std_dev / math.sqrt(n), dist, confidence, rows)
    conclusion = ""
    if claimed is not None:
        conclusion = claim_conclusion("μ", claimed, lower, upper)
    return interval_result("μ", confidence, lower, upper, rows, chart, conclusion, notes)


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
    lower, upper, chart = plus_minus_limits(mean, std_dev / math.sqrt(n), student_t(n - 1),
                                            confidence, rows)
    conclusion = difference_conclusion(lower, upper, "μ₁", "μ₂")
    return interval_result("μ_D", confidence, lower, upper, rows, chart, conclusion)


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

    lower, upper, chart = plus_minus_limits(mean1 - mean2, standard_error, dist, confidence, rows)
    conclusion = difference_conclusion(lower, upper, "μ₁", "μ₂")
    return interval_result("μ₁ − μ₂", confidence, lower, upper, rows, chart, conclusion)


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
    lower, upper, chart = plus_minus_limits(p, math.sqrt(p * (1 - p) / n), NORMAL, confidence, rows)
    conclusion = ""
    if claimed is not None:
        conclusion = claim_conclusion("π", claimed, lower, upper)
    return interval_result("π", confidence, lower, upper, rows, chart, conclusion,
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
    lower, upper, chart = plus_minus_limits(p1 - p2, standard_error, NORMAL, confidence, rows)
    conclusion = difference_conclusion(lower, upper, "π₁", "π₂")
    return interval_result("π₁ − π₂", confidence, lower, upper, rows, chart, conclusion,
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
    chart = make_chart(dist, [[left, right]], [left, right])
    return interval_result("σ²", confidence, lower, upper, rows, chart, conclusion)


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
    # En la curva F(ν₁, ν₂) el valor crítico izquierdo es 1 / F a/2 (ν₂, ν₁)
    chart = make_chart(fisher_f(df1, df2), [[1 / f_21, f_12]], [1 / f_21, f_12])
    return interval_result("σ₁² / σ₂²", confidence, lower, upper, rows, chart,
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
        "chart": make_chart(NORMAL, [[-z, z]], [-z, z]),
        "notes": [],
    }
