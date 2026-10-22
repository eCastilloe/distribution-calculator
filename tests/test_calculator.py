"""Pruebas del cálculo. Ejecutar desde la carpeta del proyecto con:  python -m unittest discover tests"""
import math
import statistics
import unittest

from distributions import NORMAL, student_t, chi_square, fisher_f
from problems import solve


def answer(**data):
    return solve(data)["answer"]


def limits(**data):
    """Los dos límites del intervalo, leídos del texto de la respuesta "… (a , b)"."""
    text = answer(**data)
    lower, upper = text[text.index("(") + 1:text.index(")")].split(" , ")
    return float(lower), float(upper)


class CriticalValuesTest(unittest.TestCase):
    # Valores de tablas o de fórmulas exactas, a 4 decimales

    def test_normal(self):
        self.assertAlmostEqual(NORMAL.quantile(0.975), 1.9600, places=4)
        self.assertAlmostEqual(NORMAL.below(1.96), 0.9750, places=4)

    def test_t(self):
        self.assertAlmostEqual(student_t(10).quantile(0.975), 2.2281, places=4)
        # Con 1 gl la t es la distribución de Cauchy: P(T < x) = 1/2 + arctan(x)/π
        self.assertAlmostEqual(student_t(1).quantile(0.99995), math.tan(math.pi * 0.49995), places=2)

    def test_chi_square(self):
        self.assertAlmostEqual(chi_square(10).quantile(0.975), 20.4832, places=4)
        self.assertAlmostEqual(chi_square(10).quantile(0.025), 3.2470, places=4)
        self.assertAlmostEqual(chi_square(30).quantile(0.975), 46.9792, places=4)
        # Con 2 gl: P(χ² < x) = 1 − e^(−x/2).  Con 1 gl: χ² = Z²
        self.assertAlmostEqual(chi_square(2).quantile(0.95), -2 * math.log(0.05), places=6)
        self.assertAlmostEqual(chi_square(1).quantile(0.95), NORMAL.quantile(0.975) ** 2, places=6)

    def test_f(self):
        self.assertAlmostEqual(fisher_f(5, 10).quantile(0.975), 4.2361, places=4)
        self.assertAlmostEqual(fisher_f(9, 14).quantile(0.975), 3.2093, places=4)
        # Con (2, 2) gl: P(F < x) = x / (1 + x).  Con (1, ν) gl: F = t²
        self.assertAlmostEqual(fisher_f(2, 2).quantile(0.95), 19, places=6)
        self.assertAlmostEqual(fisher_f(1, 10).quantile(0.95), student_t(10).quantile(0.975) ** 2, places=6)


class IntervalsTest(unittest.TestCase):

    def test_one_mean(self):
        self.assertIn("(48.0400 , 51.9600)", answer(distribution="z", problem="mean_interval",
                                                     mean=50, std_dev=8, n=64, confidence=95))
        self.assertIn("(44.2771 , 55.7229)", answer(distribution="t", problem="mean_interval",
                                                     mean=50, std_dev=8, n=10, confidence=95))

    def test_paired(self):
        # 2.5 ± t(0.025, 11) · 3 / √12 = 2.5 ± 2.2010 · 0.8660
        self.assertIn("(0.5939 , 4.4061)", answer(distribution="t", problem="paired",
                                                   mean=2.5, std_dev=3, n=12, confidence=95))

    def test_proportions(self):
        self.assertIn("(0.3525 , 0.5475)", answer(distribution="z", problem="one_proportion",
                                                   n=100, successes=45, confidence=95))
        self.assertIn("(-0.0211 , 0.2545)", answer(distribution="z", problem="two_proportions", n1=100,
                                                    successes1=45, n2=90, successes2=30, confidence=95))

    def test_two_means(self):
        samples = dict(mean1=20, std_dev1=4, n1=10, mean2=17, std_dev2=5, n2=12, confidence=95)
        # Z: 5 ± 1.96 · √(100/50 + 144/60)
        self.assertIn("(0.8887 , 9.1113)", answer(distribution="z", problem="two_means", mean1=80,
                                                   std_dev1=10, n1=50, mean2=75, std_dev2=12, n2=60,
                                                   confidence=95))
        # Iguales: Sp = 4.5771, gl = 20.  Diferentes: gl de Welch = 19.98
        self.assertIn("(-1.0881 , 7.0881)", answer(distribution="t", problem="two_means",
                                                    variances="equal", **samples))
        self.assertIn("(-1.0036 , 7.0036)", answer(distribution="t", problem="two_means",
                                                    variances="different", **samples))

    def test_one_variance(self):
        # (9 · 4 / 19.0228 , 9 · 4 / 2.7004)
        self.assertIn("(1.8925 , 13.3314)", answer(distribution="chi2", problem="variance_interval",
                                                    input_mode="variance", n=10, variance=4, confidence=95))

    def test_variance_ratio(self):
        # (2.25 / F(5, 10) , 2.25 · F(10, 5)) = (2.25 / 4.2361 , 2.25 · 6.6192)
        self.assertIn("(0.5312 , 14.8931)", answer(distribution="f", problem="variance_ratio", input_mode="variance",
                                                    n1=6, variance1=9, n2=11, variance2=4, confidence=95))

    def test_sample_size(self):
        # (1.96 · 15 / 3)² = 96.04  y  1.96² · 0.25 / 0.05² = 384.16: se redondea hacia arriba
        self.assertIn("n = 97", answer(distribution="z", problem="sample_size", target="mean",
                                       std_dev=15, error=3, confidence=95))
        self.assertIn("n = 385", answer(distribution="z", problem="sample_size", target="proportion",
                                        p=0.5, error=0.05, confidence=95))


class ProbabilityTest(unittest.TestCase):

    def test_probabilities(self):
        self.assertIn("0.9750", answer(distribution="z", problem="probability", mean=0, std_dev=1,
                                       tail="below", x=1.96))
        self.assertIn("0.0500", answer(distribution="chi2", problem="probability", df=2,
                                       tail="above", x=-2 * math.log(0.05)))
        # Con (2, 2) gl: 19/20 − 1/2
        self.assertIn("0.4500", answer(distribution="f", problem="probability", df1=2, df2=2,
                                       tail="between", x=1, x2=19))


class ExamProblemsTest(unittest.TestCase):
    # Ejercicios del documento "2do Parcial". La media y la varianza esperadas se calculan
    # con el módulo statistics (solo en las pruebas) y los valores críticos vienen de tablas.

    def test_claimed_mean(self):
        # Ejercicio 1: 320 ± 1.96 · 40 / 8; la afirmación μ = 300 queda fuera
        result = solve(dict(distribution="z", problem="mean_interval", mean=320, std_dev=40, n=64,
                            confidence=95, claimed=300))
        self.assertIn("(310.2002 , 329.7998)", result["answer"])
        self.assertIn("se rechaza H₀", result["interpretation"])
        result = solve(dict(distribution="z", problem="one_proportion", n=500, successes=390,
                            confidence=95, claimed=0.8))
        self.assertIn("no se rechaza H₀", result["interpretation"])

    def test_variance_from_data(self):
        # Intervalos de varianzas, ejercicio 1: (9 s² / 19.0228 , 9 s² / 2.7004)
        sales = [12.4, 13.0, 11.8, 14.2, 12.1, 12.5, 13.1, 11.9, 12.8, 14.1]
        variance = statistics.variance(sales)
        lower, upper = limits(distribution="chi2", problem="variance_interval", input_mode="data",
                              values="12.4, 13.0, 11.8, 14.2, 12.1, 12.5, 13.1, 11.9, 12.8, 14.1",
                              confidence=95)
        self.assertAlmostEqual(lower, 9 * variance / 19.0228, places=3)
        self.assertAlmostEqual(upper, 9 * variance / 2.7004, places=3)

    def test_variance_from_std_dev(self):
        # Repaso 8: s = 2.8, n = 25, 80%: (24 · 7.84 / 33.1963 , 24 · 7.84 / 15.6587)
        lower, upper = limits(distribution="chi2", problem="variance_interval", input_mode="std_dev",
                              std_dev=2.8, n=25, confidence=80)
        self.assertAlmostEqual(lower, 24 * 7.84 / 33.1963, places=3)
        self.assertAlmostEqual(upper, 24 * 7.84 / 15.6587, places=3)

    def test_mean_from_data(self):
        # Repaso 2 (pH): x̄ ± t(0.05, 9) · s / √10, con t = 1.8331
        ph = [6.2, 6.5, 6.1, 6.4, 6.3, 6.0, 6.2, 6.5, 6.3, 6.1]
        margin = 1.8331 * statistics.stdev(ph) / math.sqrt(10)
        lower, upper = limits(distribution="t", problem="mean_interval", input_mode="data",
                              values="6.2 6.5 6.1 6.4 6.3 6.0 6.2 6.5 6.3 6.1", confidence=90)
        self.assertAlmostEqual(lower, statistics.mean(ph) - margin, places=3)
        self.assertAlmostEqual(upper, statistics.mean(ph) + margin, places=3)

    def test_paired_columns(self):
        # Pareadas, problema 2: d = antes − después; d̄ ± t(0.005, 9) · s_d / √10, con t = 3.2498
        before = [50, 45, 60, 55, 50, 48, 52, 57, 53, 49]
        after = [65, 55, 75, 70, 60, 58, 67, 72, 68, 59]
        differences = [b - a for b, a in zip(before, after)]
        margin = 3.2498 * statistics.stdev(differences) / math.sqrt(10)
        lower, upper = limits(distribution="t", problem="paired", input_mode="pairs",
                              values1="50 45 60 55 50 48 52 57 53 49",
                              values2="65 55 75 70 60 58 67 72 68 59", confidence=99)
        self.assertAlmostEqual(lower, statistics.mean(differences) - margin, places=3)
        self.assertAlmostEqual(upper, statistics.mean(differences) + margin, places=3)

    def test_percent_lists(self):
        # Intervalos de 2 varianzas, ejercicio 2: listas entre corchetes y con %
        p1 = [1.3, 1.4, 1.2, 1.3, 1.5, 1.3, 1.2, 1.4, 1.5]
        p2 = [1.1, 1.0, 1.2, 1.1, 1.2, 1.0, 1.2]
        ratio = statistics.variance(p1) / statistics.variance(p2)
        result = solve(dict(distribution="f", problem="variance_ratio", input_mode="data",
                            values1="[1.3%, 1.4%, 1.2%, 1.3%, 1.5%, 1.3%, 1.2%, 1.4%, 1.5%]",
                            values2="[1.1%, 1.0%, 1.2%, 1.1%, 1.2%, 1.0%, 1.2%]", confidence=95))
        # (cociente / F(8, 6) , cociente · F(6, 8)) = (cociente / 5.5996 , cociente · 4.6517)
        self.assertIn(f"({ratio / 5.5996:.4f} , ", result["answer"])
        self.assertIn("no son significativamente diferentes", result["interpretation"])


class ValidationTest(unittest.TestCase):

    def test_errors(self):
        with self.assertRaisesRegex(ValueError, "al menos 2"):
            solve(dict(distribution="t", problem="mean_interval", mean=5, std_dev=1, n=1,
                       confidence=95))
        with self.assertRaisesRegex(ValueError, "escribe un número"):
            solve(dict(distribution="chi2", problem="variance_interval", input_mode="variance", n=10,
                       variance="abc",
                       confidence=95))
        with self.assertRaisesRegex(ValueError, "Elige una distribución"):
            solve(dict(distribution="chi2", problem="two_means"))
        with self.assertRaisesRegex(ValueError, "Elige una distribución"):
            solve(dict(distribution="z", problem="critical_value"))

    def test_data_errors(self):
        with self.assertRaisesRegex(ValueError, "misma cantidad"):
            solve(dict(distribution="t", problem="paired", input_mode="pairs", values1="1 2 3",
                       values2="1 2", confidence=95))
        with self.assertRaisesRegex(ValueError, "no es un número"):
            solve(dict(distribution="t", problem="mean_interval", input_mode="data",
                       values="5 abc 7", confidence=95))
        with self.assertRaisesRegex(ValueError, "todos los datos son iguales"):
            solve(dict(distribution="t", problem="mean_interval", input_mode="data",
                       values="5, 5, 5", confidence=95))


if __name__ == "__main__":
    unittest.main()
