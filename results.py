"""Formato de la respuesta: tabla de valores, interpretación y conclusiones (H₀ y H₁)."""


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


def interval_result(symbol, confidence, lower, upper, rows, chart, conclusion="", notes=()):
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
        "chart": chart,
        "notes": list(notes),
    }
