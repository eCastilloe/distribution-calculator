"""Probabilidad: área bajo la curva a la izquierda, a la derecha o entre dos valores."""

from distributions import NORMAL
from inputs import MAX_SCORE, MAX_WHOLE, read_number, read_choice, read_distribution
from results import values_table
from charts import make_chart


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
        shaded = [[None, scores[0]]]
    elif tail == "above":
        result = dist.above(scores[0])
        text = f"P({variable} > {values[0]:g})"
        meaning = f"sea mayor que {values[0]:g}"
        shaded = [[scores[0], None]]
    else:
        result = dist.below(scores[1]) - dist.below(scores[0])
        text = f"P({values[0]:g} < {variable} < {values[1]:g})"
        meaning = f"esté entre {values[0]:g} y {values[1]:g}"
        shaded = [[scores[0], scores[1]]]
    rows += [("Probabilidad", result), ("Probabilidad complementaria", 1 - result)]
    return {
        "answer": f"{text} = {result:.4f}  ({result * 100:.2f}%)",
        "interpretation": f"La probabilidad de que {variable} {meaning} es {result * 100:.2f}%.",
        "tables": [values_table(rows)],
        "chart": make_chart(dist, shaded, scores),
        "notes": [],
    }
