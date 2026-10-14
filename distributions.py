import math

STEPS = 2000
SPLIT = 10


def normal_curve(x):
    return math.exp(-x * x / 2) / math.sqrt(2 * math.pi)


def t_curve(df):
    constant = math.exp(math.lgamma((df + 1) / 2) - math.lgamma(df / 2))
    constant /= math.sqrt(df * math.pi)

    def curve(x):
        return constant * (1 + x * x / df) ** (-(df + 1) / 2)
    return curve


def area_under(curve, start, end):
    # Regla de Simpson: STEPS tiras (debe ser par) que se suman con pesos 1, 4, 2, 4, ..., 1
    width = (end - start) / STEPS
    total = curve(start) + curve(end)
    for i in range(1, STEPS):
        weight = 4 if i % 2 == 1 else 2
        total += weight * curve(start + i * width)
    return total * width / 3


def probability_below(curve, x):
    # Las curvas son simétricas: la mitad izquierda vale 0.5 y se suma o resta el área entre 0 y x
    distance = abs(x)
    area = area_under(curve, 0, min(distance, SPLIT))
    if distance > SPLIT:
        # Más allá de SPLIT la curva es casi plana: se integra con el cambio x = SPLIT * e^s
        # para que la cantidad de cálculos no dependa de qué tan lejos esté x
        def stretched(s):
            x = SPLIT * math.exp(s)
            return curve(x) * x
        area += area_under(stretched, 0, math.log(distance / SPLIT))
    return 0.5 + area if x >= 0 else 0.5 - area


def probability_above(curve, x):
    return probability_below(curve, -x)


def critical_value(curve, probability):
    # Bisección: se prueba el punto medio y se descarta la mitad donde no está la respuesta
    low = 0.0
    high = 1.0
    while probability_below(curve, high) < probability:
        high *= 2
    while high - low > 1e-9:
        middle = (low + high) / 2
        if probability_below(curve, middle) < probability:
            low = middle
        else:
            high = middle
    return (low + high) / 2
