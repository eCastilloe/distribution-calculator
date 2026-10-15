# Calculadora de distribuciones Z, t, χ² y F

Programa con interfaz web y backend en Python. No usa librerías externas: solo la biblioteca estándar.

## Cómo ejecutarlo en tu computadora

    python server.py

Después abre http://localhost:8000 en el navegador. Requiere Python 3.8 o superior.

## Crear un ejecutable (doble clic, sin instalar Python)

El ejecutable se debe generar en el mismo sistema operativo donde se va a usar. Necesita Python solo para crearlo.

- **Windows:** haz doble clic en `build_exe.bat`. Al terminar, el programa queda en `dist\CalculadoraDistribuciones.exe`.
- **Mac o Linux:** ejecuta `sh build_exe.sh`. El programa queda en `dist/CalculadoraDistribuciones`.

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

Las cuatro distribuciones también calculan probabilidades (menor, mayor o entre dos valores) y valores críticos (una o dos colas, con tabla de los niveles más usados).

Cada resultado incluye la respuesta, la gráfica de la curva con el área correspondiente, una tabla con los valores del cálculo y, en las comparaciones de dos poblaciones, el criterio de decisión.

## Estructura

    server.py            Servidor y API (POST /api/calculate, GET /health)
    desktop.py           Arranque local: abre el navegador solo (se usa para el ejecutable)
    build_exe.bat / .sh  Generan el ejecutable con PyInstaller
    problems.py          Validación de datos y cálculo de cada tipo de problema
    distributions.py     Curvas Z, t, χ² y F; área bajo la curva, probabilidad y valor crítico
    frontend/            Interfaz (index.html, style.css, app.js)
    tests/               Pruebas automáticas (python -m unittest discover tests)
    render.yaml          Configuración para publicar en Render

## Método

- La probabilidad es el área bajo la curva de la distribución, calculada con la regla de Simpson.
- Para poder sumar el área desde 0 aunque la curva sea infinita ahí (χ² con 1 gl, F con ν₁ = 1), se usa el cambio de variable x = u⁴; lejos del centro, x = 10·eˢ.
- El valor crítico se obtiene por búsqueda binaria sobre esa probabilidad.
- Se usa `math.lgamma` de la biblioteca estándar para las constantes de las curvas t, χ² y F.
- Los grados de libertad de dos medias con varianzas diferentes (fórmula de Welch) no se redondean.

## Publicar en Render con un dominio propio

1. Sube esta carpeta a un repositorio de GitHub (`git init`, `git add .`, `git commit`, `git push`).
2. En Render: **New > Web Service**, elige el repositorio y usa:
   - Runtime: Python
   - Build command: `pip install -r requirements.txt`
   - Start command: `python server.py`
   - Instance type: Free
   
   También puedes usar **New > Blueprint**: Render lee `render.yaml` y llena todo solo.
3. Cuando termine el despliegue, la página ya abre en `https://<tu-servicio>.onrender.com`.
4. Dominio propio: en el servicio, **Settings > Custom Domains > Add Custom Domain**. Render muestra qué registros DNS crear (normalmente un CNAME hacia `<tu-servicio>.onrender.com`). Créalos en el panel donde compraste el dominio .tech, borra cualquier registro AAAA que choque y presiona **Verify**. El certificado HTTPS se genera solo.

## Que la página esté siempre disponible

El plan gratuito de Render apaga el servicio tras 15 minutos sin visitas, y despertarlo tarda cerca de un minuto. Opciones:

- **Plan Starter de Render (7 USD al mes):** el servicio no se apaga.
- **Monitor gratuito:** un servicio como UptimeRobot que visite `https://tu-dominio.tech/health` cada 5 minutos mantiene el servicio despierto. Un servicio encendido todo el mes (744 horas) cabe en las 750 horas gratuitas de Render, siempre que no tengas otros servicios gratuitos en el mismo espacio de trabajo.
