"""Lectura y validación de los datos que escribe el usuario."""

import math

from distributions import NORMAL, student_t, chi_square, fisher_f


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
