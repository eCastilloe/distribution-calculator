# Calculadora de distribuciones Z y t

Programa con interfaz web y backend en Python. No usa librerías externas: solo la biblioteca estándar.

## Cómo ejecutarlo

    python server.py

Después abre http://localhost:8000 en el navegador. Requiere Python 3.8 o superior.

## Qué calcula

| Distribución | Problemas |
|---|---|
| Z (normal) | Intervalo para una media (σ conocida), una proporción y dos proporciones; probabilidades; valor crítico |
| t de Student | Intervalo para una media (σ desconocida); probabilidades; valor crítico |

Cada resultado incluye la respuesta, la gráfica de la curva con el área correspondiente y una tabla con los valores del cálculo.

## Estructura

    server.py            Servidor y API (POST /api/calculate)
    problems.py          Validación de datos y cálculo de cada tipo de problema
    distributions.py     Curvas Z y t, área bajo la curva, probabilidad y valor crítico
    frontend/            Interfaz (index.html, style.css, app.js)

## Método

- La probabilidad es el área bajo la curva de la distribución, calculada con la regla de Simpson.
- El valor crítico se obtiene por bisección sobre esa probabilidad.
- Se usa `math.lgamma` de la biblioteca estándar para la constante de la curva t.
