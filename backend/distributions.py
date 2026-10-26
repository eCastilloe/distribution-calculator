import math

STEPS = 2000
SPLIT = 10


def normal_curve(x):
    return math.exp(-x * x / 2) / math.sqrt(2 * math.pi)


def t_curve(df):
    constant = math.exp(math.lgamma((df + 1) / 2) - math.lgamma(df / 2)) / math.sqrt(df * math.pi)

    def curve(x):
        return constant * (1 + x * x / df) ** (-(df + 1) / 2)
    return curve


# χ² y F se calculan con logaritmos: con muchos grados de libertad, x^(gl/2) se desbordaría
def chi_square_curve(df):
    log_constant = -(df / 2) * math.log(2) - math.lgamma(df / 2)

    def curve(x):
        if x <= 0:
            return 0.0
        return math.exp(log_constant + (df / 2 - 1) * math.log(x) - x / 2)
    return curve


def f_curve(df1, df2):
    log_constant = (math.lgamma((df1 + df2) / 2) - math.lgamma(df1 / 2) - math.lgamma(df2 / 2)
                    + (df1 / 2) * math.log(df1 / df2))

    def curve(x):
        if x <= 0:
            return 0.0
        return math.exp(log_constant + (df1 / 2 - 1) * math.log(x)
                        - (df1 + df2) / 2 * math.log(1 + df1 * x / df2))
    return curve


def area_under(curve, start, end):
    width = (end - start) / STEPS
    total = curve(start) + curve(end)
    for i in range(1, STEPS):
        weight = 4 if i % 2 == 1 else 2
        total += weight * curve(start + i * width)
    return total * width / 3


def area_from_zero(curve, x):
    # Con el cambio x = u⁴ se integra una curva suave que vale 0 en u = 0,
    # aunque la original sea infinita en 0 (χ² con 1 gl, F con ν₁ = 1)
    def smooth(u):
        return curve(u ** 4) * 4 * u ** 3
    area = area_under(smooth, 0, min(x, SPLIT) ** 0.25)
    if x > SPLIT:
        # Más allá de SPLIT la curva es casi plana: se integra con el cambio x = SPLIT * e^s
        # para que la cantidad de cálculos no dependa de qué tan lejos esté x
        def stretched(s):
            x = SPLIT * math.exp(s)
            return curve(x) * x
        area += area_under(stretched, 0, math.log(x / SPLIT))
    return area


class Distribution:
    def __init__(self, axis, curve, symmetric):
        self.axis = axis
        self.curve = curve
        self.symmetric = symmetric

    def below(self, x):
        if self.symmetric:
            # La mitad izquierda vale 0.5: se suma o se resta el área entre 0 y x
            area = area_from_zero(self.curve, abs(x))
            return 0.5 + area if x >= 0 else 0.5 - area
        return area_from_zero(self.curve, x) if x > 0 else 0.0

    def above(self, x):
        return 1 - self.below(x)

    def quantile(self, probability):
        """Valor x que deja `probability` de área a su izquierda."""
        if self.symmetric and probability < 0.5:
            return -self.quantile(1 - probability)
        # Búsqueda binaria: se prueba el punto medio y se descarta la mitad sin la respuesta
        low = 0.0
        high = 1.0
        while self.below(high) < probability:
            high *= 2
        while high - low > 1e-9 * high:
            middle = (low + high) / 2
            if self.below(middle) < probability:
                low = middle
            else:
                high = middle
        return (low + high) / 2


NORMAL = Distribution("Z", normal_curve, symmetric=True)


def student_t(df):
    return Distribution("t", t_curve(df), symmetric=True)


def chi_square(df):
    return Distribution("χ²", chi_square_curve(df), symmetric=False)


def fisher_f(df1, df2):
    return Distribution("F", f_curve(df1, df2), symmetric=False)
