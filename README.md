# Calculadora de distribuciones Z, t, χ² y F

Programa con interfaz web y backend en Python. No usa librerías externas: solo la biblioteca estándar.

## Cómo ejecutarlo en tu computadora

    python backend/server.py

Desde la carpeta del proyecto. Después abre http://localhost:8000 en el navegador. Requiere Python 3.8 o superior.

## Crear un ejecutable (doble clic, sin instalar Python)

El ejecutable se debe generar en el mismo sistema operativo donde se va a usar. Necesita Python solo para crearlo.

- **Windows:** haz doble clic en `ejecutable\build_exe.bat`. Al terminar, el programa queda en `ejecutable\dist\CalculadoraDistribuciones.exe`.
- **Mac o Linux:** ejecuta `sh ejecutable/build_exe.sh`. El programa queda en `ejecutable/dist/CalculadoraDistribuciones`.

Al abrirlo se muestra una ventana de texto y se abre el navegador con la calculadora. Para cerrar el programa, cierra esa ventana. Usa un puerto libre automáticamente, así que se puede abrir aunque otro programa ocupe el 8000.

Windows puede mostrar una advertencia de "aplicación no reconocida" porque el ejecutable no está firmado. Se puede abrir con "Más información > Ejecutar de todas formas".

## Qué calcula

Todos los intervalos del formulario del parcial:

| Distribución | Problemas |
|---|---|
| Z (normal) | Intervalo para una media (σ conocida o n ≥ 30), dos medias, una proporción y dos proporciones; tamaño de muestra (media o proporción) |
| t de Student | Intervalo para una media (σ desconocida), dos medias (varianzas iguales o diferentes) y muestras pareadas |
| χ² (chi cuadrada) | Intervalo para una varianza (y para σ) |
| F de Fisher | Intervalo para el cociente de dos varianzas |

Las cuatro distribuciones también calculan probabilidades (menor, mayor o entre dos valores).

Cómo se capturan los datos:

- **Resumen o lista de datos.** En medias, varianzas y cocientes de varianzas se puede escribir el resumen (x̄, s, n o s²) o pegar la lista de datos tal como viene en el problema. Los valores se separan con comas o espacios, se usa punto decimal, y el símbolo %, el $ y los corchetes se ignoran. El programa calcula la media, la desviación estándar (dividiendo entre n − 1) y n.
- **Muestras pareadas.** Se pegan las dos columnas (por ejemplo, antes y después) y el programa resta cada par.
- **Afirmaciones.** Si el problema afirma un valor ("el promedio es 300 ms"), se escribe en «Valor afirmado» y el resultado plantea H₀ y H₁ y dice si se rechaza H₀.

Cada resultado incluye:
- la respuesta;
- una interpretación corta en palabras;
- una tabla con los valores del cálculo.

En las comparaciones de dos poblaciones se agrega el criterio de decisión del formulario (por ejemplo, si las varianzas son significativamente diferentes).

## Estructura

    backend/
      server.py          Servidor y API (POST /api/calculate, GET /health)
      calculator.py      Lectura de datos, intervalos, probabilidad, interpretación e índice de problemas
      distributions.py   Curvas Z, t, χ² y F; área bajo la curva y valores críticos
      desktop.py         Arranque local: abre el navegador solo (se usa para el ejecutable)
    frontend/
      index.html         Página completa: diseño (<style>), campos de cada problema y lógica (<script>)
    ejecutable/
      build_exe.bat/.sh  Generan el ejecutable con PyInstaller (queda en ejecutable/dist)
    render.yaml          Configuración para publicar en Render (start: python backend/server.py)

## Método

- La probabilidad es el área bajo la curva de la distribución, calculada con la regla de Simpson.
- Para poder sumar el área desde 0 aunque la curva sea infinita ahí (χ² con 1 gl, F con ν₁ = 1), se usa el cambio de variable x = u⁴; lejos del centro, x = 10·eˢ.
- Los valores críticos de cada intervalo se obtienen por búsqueda binaria sobre esa probabilidad.
- Se usa `math.lgamma` de la biblioteca estándar para las constantes de las curvas t, χ² y F.
- Los grados de libertad de dos medias con varianzas diferentes (fórmula de Welch) no se redondean.
