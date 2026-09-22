# PREDWEEM Digital Twin · Azul

Gemelo digital de *Lolium multiflorum* basado en
[PREDWEEM/LOLIUM_AZUL2026](https://github.com/PREDWEEM/LOLIUM_AZUL2026).
Integra meteorología, observaciones por lote y calibración local 2026 externa
a la red neuronal. Conserva los pesos y la configuración científica de Azul.

**PREDWEEM by Guillermo R. Chantre.** Copyright © 2026 Guillermo R. Chantre /
PREDWEEM. Todos los derechos reservados. Consulte [COPYRIGHT.md](COPYRIGHT.md).

## Ejecutar

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

En Streamlit Community Cloud, seleccione `PREDWEEM/AZUL_digitaltween`,
rama `main` y archivo principal `app.py`.

## Visitas periódicas para reducir la hibernación

El workflow [mantener_activo.yml](.github/workflows/mantener_activo.yml) abre
[la aplicación de Azul](https://srlztzpuwzpfcfcnt7yd7m.streamlit.app/)
con Chromium cada cuatro horas: 00:23, 04:23, 08:23, 12:23, 16:23 y 20:23 UTC
(01:23, 05:23, 09:23, 13:23, 17:23 y 21:23 de Argentina).
También permite ejecución manual desde
**Actions → Mantener activo el gemelo Azul → Run workflow** y se ejecuta
al modificar el workflow o su script.

Cuando aparece **Yes, get this app back up!**, la tarea hace clic en el botón
y espera la apertura, con un límite total de cinco minutos. Comprueba el
encabezado de Azul, el indicador de emergencia, el panel principal y su
gráfico, incluso si están dentro de un iframe. Una respuesta HTTP 200 por sí
sola no cuenta como éxito. Si la app muestra una excepción o no termina de
cargar, la ejecución queda fallida; los avisos dependen de las preferencias
de notificaciones de GitHub Actions.

La tarea no requiere secretos ni modifica observaciones o parámetros del modelo.
Playwright se instala solamente en el ejecutor de Actions. Esto reduce el riesgo
de hibernación, pero **no garantiza disponibilidad continua**:
[Streamlit suspende las apps sin visitas durante 12 horas](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app#app-hibernation)
y [GitHub puede demorar tareas o desactivarlas tras 60 días sin actividad en un repositorio público](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).
Si ocurre lo último, vuelva a habilitar el workflow desde Actions.

## Funcionamiento

- **Estado del lote:** dos gráficos paralelos, flujo y acumulado, con referencia
  local tenue, curva base, curva calibrada y estado actualizado. El flujo inicia
  en vista semanal y permite pasar a diario. Ambos flujos se expresan en % del
  total por semana o día; el eje calendario termina el 1 de octubre.
- **Configuración:** desplegable en el cuerpo principal, sin menú lateral.
- **Indicadores:** intensidad a siete días relativa al máximo semanal histórico
  y semáforo de tiempo térmico desde el primer pico, con banda 600–800 °Cd.
- **Calibración local 2026:** activada por defecto, con interruptor sobre el
  gráfico principal. La selección se conserva durante la sesión y actualiza
  el gráfico, estado, escenarios y exportación.
- **Observaciones:** carga CSV/XLS/XLSX de flujos en plantas/m² o emergencia
  acumulada. Admite repeticiones cuando están disponibles y permite borrar
  los registros seleccionados del lote.
- **Cobertura:** constante o serie FECHA + COBERTURA_PCT (0–100 %), incluso en
  el archivo de emergencia. Interpola entre mediciones, conserva el último valor
  y utiliza el respaldo antes de la primera medición.
- **Escenarios:** cambios exploratorios de lluvia y temperatura.
- **Trazabilidad:** procedencia, parámetros, asimilación y descarga CSV de la
  trayectoria diaria auditable.

Observaciones y cobertura se guardan por lote en `data/twin_state.db`, que no
se versiona. En alojamientos con disco efímero, conserve los archivos originales
para recuperar los registros después de un reinicio o redespliegue.

## Motor de Azul

La configuración inicial conserva cobertura 10 %, Wmax 18,81 mm, exponente Kr=0,
latencia JD 25, termoinhibición de cinco días a 24 °C y primer pico mayor que 0,20.
El choque hídrico usa 45 mm en tres días, hasta JD 110, con piso de emergencia
0,75 antes de aplicar los filtros hídricos. La ANN utiliza temperatura del aire;
la cobertura modifica Ke y el balance hídrico.

Desde el 15/04 aplica un techo del 50 % del máximo previo, con decaimiento
τ=60 días, β=1 e intensidad 0,75. Se conserva el reloj térmico triangular
2–20–30 °C y la banda de manejo 600–800 °Cd. Modelo y meteorología utilizan
las coordenadas −36,87, −59,89.

Consulte [MODEL_PROVENANCE.md](MODEL_PROVENANCE.md) para la revisión de origen,
los hashes y la correspondencia científica.

## Pool histórico exclusivo de Azul 2026

La única fuente es `data/calibration/azul_2026_counts.csv`: **11 fechas, del
01/03 al 01/09/2026**, con **8.224 plantas/m²** registradas. El clasificador
compartido no se lee para construir la referencia, ni siquiera su eje de días.
Quedan excluidas todas sus curvas: 2008, 2009, 2010, 2011, 2012, 2013, 2014,
2015, 2023, 2024, Balcarce, San Pedro y Tres Arroyos 2025.

El acumulado observado se divide por el total registrado y se interpola
linealmente entre visitas. El flujo diario se obtiene por diferencias de ese
acumulado; la vista semanal lo suma de lunes a domingo, igual que el flujo del
gemelo. Las barras parciales se rayan e indican los días incluidos. La
interpolación suaviza los picos y no equivale a un muestreo diario.

El gráfico presenta **Pool histórico · orientativo** con colores tenues sólo
entre el 1 de marzo y el 1 de septiembre, trasladando mes y día al calendario
consultado. Fuera de esa ventana no hay referencia observada y no se dibujan
ceros. En Trazabilidad se puede consultar y descargar la curva utilizada,
las campañas excluidas y el número de campañas. **P10, mediana y P90 coinciden
porque sólo hay una campaña; no son intervalos de confianza.**

Para evitar información futura, el total 2026 sólo se habilita desde el
**01/09/2026**. Si se consulta un corte anterior no existe historia local
previa: la app lo informa y no calcula porcentajes, remanente ni intensidad.
Al habilitar la campaña meteorológica 2027 se usará Azul 2026; antes del inicio de su ventana o
sin señal suficiente tampoco se fuerza un porcentaje usando el último día
del pronóstico como 100 %. Se conserva el motor fisiológico y la meteorología
propios de Azul; la actualización meteorológica mantiene su cierre 2026.

Después del 1 de septiembre se mantiene el total registrado como **supuesto
de normalización** para el gemelo. No se presenta como una cola histórica
observada ni como evidencia de ausencia de nuevos nacimientos. El 100 % es
el total de la ventana, no el agotamiento del banco de semillas. Las consultas
de 2026 con ese total conocido son retrospectivas.

## Intensidad de emergencia y tiempo térmico

La intensidad compara la suma del flujo previsto desde mañana hasta siete
días después con el máximo de semanas históricas completas de lunes a domingo,
en la misma escala que las barras y dentro del eje enero–1 de octubre:

- 🔴 **Alta:** >75 % del máximo histórico.
- 🟠 **Media:** 25–75 %, incluidos ambos límites.
- 🟡 **Baja:** >0 y <25 % del máximo histórico.
- 🟢 **Nula:** flujo semanal exactamente cero con siete días válidos.

Si faltan días de pronóstico, se indica ausencia o insuficiencia en gris; no
se convierte un horizonte incompleto en flujo nulo. Un flujo positivo sin
máximo histórico se indica sin referencia. Es intensidad relativa, no una
probabilidad. El indicador utiliza la misma curva histórica del gráfico.

El semáforo térmico clasifica el TT de la fecha consultada sin redondear:

- 🔴 **FUERA DE CONTROL:** >800 °Cd.
- 🟠 **ULTIMO PLAZO:** >700 y ≤800 °Cd.
- 🟡 **CONTROL A TIEMPO:** ≥600 y ≤700 °Cd.
- 🟢 **AUN NO CONTROLAR:** <600 °Cd.

Estos indicadores acompañan el monitoreo y el criterio profesional. No
modifican la ANN, el decaimiento desde el 15 de abril ni el cálculo térmico.

## Meteorología y actualización

La fuente predeterminada conserva la jerarquía del repositorio original:

1. **ERA5-Land:** reanálisis histórico hasta el último día completo disponible.
2. **ERA5:** respaldo explícito si ERA5-Land no entrega una ventana reciente válida.
3. **ECMWF IFS histórico:** puente para los días recientes sin reanálisis.
4. **ECMWF IFS HRES:** pronóstico desde hoy hasta siete días posteriores.

`meteo_daily.csv` conserva `FUENTE`, `TIPO` y `FECHA_EMISION` con hora local.
La interfaz reconoce estos metadatos y distingue historia de pronóstico.
Esta serie no corresponde a observaciones de una estación meteorológica local.
La copia inicial contiene 255 días ERA5 (01/01–12/09), seis días de histórico
ECMWF (13–18/09) y ocho días de pronóstico HRES (19–26/09).
El gemelo utiliza el estado histórico más siete días disponibles; inicialmente
el estado llega al 18/09 y el horizonte visible termina el 25/09.
Al consultar un corte pasado se utiliza la meteorología actualmente archivada,
no el pronóstico emitido en aquel corte.

El workflow `actualizar_clima.yml` actualiza a las 07:30 y 15:30 de Argentina y
admite ejecución manual. El pronóstico se recorta al **01/10/2026 inclusive**.
Después del cierre sólo se completan los datos históricos hasta esa fecha.
El actualizador recupera huecos, valida la continuidad y reemplaza el CSV de
forma atómica. La precipitación faltante no se inventa ni se arrastra.
Open-Meteo y un archivo aportado son opciones adicionales en la interfaz.

## Calibración local 2026

Se incorporó `VALIDA (1).xlsx`, hoja `Hoja1`, columnas FECHA y PLM2.
La localidad se asigna según la instrucción del usuario; no está en la hoja.

| Dato | Valor |
|---|---|
| Muestreos | 11, del 01/03 al 01/09/2026 |
| Intervalos de ajuste | 10, de 11 a 29 días |
| Total registrado | 8.224 plantas/m² |
| Repeticiones y cobertura | No informadas |
| Meteorología fija | 244 días, 01/01–01/09/2026 |
| Procedencia meteorológica | ERA5, tipo REANALISIS_FALLBACK |

El cero inicial delimita el primer intervalo de 25 días, hasta el 26/03,
con 2.713 plantas/m². No se infiere ausencia de emergencia antes del 01/03.
Cada conteo se compara con la suma simulada sobre su intervalo real, incluidos
los 29 días entre el 17/06 y el 16/07; no se convierten en semanas artificiales.

La transformación externa `G(F) = logistic(offset + slope × logit(F))`
ajusta dos parámetros: **offset -0,300; slope 0,675**. Conserva 0 y 1, mantiene
la monotonía y no crea flujos en días bloqueados por el motor. No modifica los
pesos ANN, el decaimiento ni el tiempo térmico. Cobertura y Wmax son supuestos
operativos originales: el adjunto no los informa. Sin repeticiones se utiliza
un piso común de ponderación, no un error de muestreo medido.

| Evaluación | RMSE base | RMSE calibrado |
|---|---:|---:|
| Ajuste retrospectivo, 10 intervalos | 548.77 | 378.43 |

RMSE en plantas/m² por intervalo. El perfil fue regenerado el 22/09/2026 con
la referencia exclusiva. La curva histórica y la calibración utilizan los
mismos conteos: **este ajuste no demuestra mejora predictiva independiente**.

Los cuatro cortes temporales anteriores al 01/09/2026 no son evaluables con
este pool porque no existía otra campaña histórica local. Se conserva su
listado y motivo de exclusión en el perfil JSON; el CSV de evaluación temporal
queda con encabezados y sin filas. Las métricas anteriores con nueve curvas
compartidas no se presentan como resultados de esta versión. Es necesario
evaluar una campaña posterior con datos y emisiones meteorológicas fechadas.
El perfil sigue siendo experimental y no reduce automáticamente la
incertidumbre del gemelo.

La capa se aplica al seleccionar Azul, desde el 01/09/2026 y con el mismo motor
y referencia utilizados al ajustar. Las fechas anteriores no usan un perfil
que incluye observaciones posteriores. Si se asimilan conteos de 2026, se usa
la base para evitar reutilizar esa evidencia como calibración y asimilación.
El motivo aparece junto al interruptor.

El pool histórico y la calibración son capas distintas: desactivar la
calibración conserva la referencia Azul 2026. Los adjuntos se conservan; no se cargan
automáticamente en SQLite. Para asimilarlos en un lote, descargue el CSV desde
**Calibración por sitio** y cárguelo en **Observaciones**.

`data/calibration/` incluye el Excel original, conteos CSV, meteorología fija,
perfil JSON, resultados de ajuste y evaluación temporal, y procedencia con
hashes. La actualización meteorológica diaria no modifica esa copia fija.

Para reproducir el ajuste sin acceso a la red:

```bash
python scripts/calibrate_site.py
```

## Verificación

```bash
python -m pytest -q
python -m compileall -q app.py predweem_twin scripts actualizar_clima.py
```

Las pruebas comparan el motor con una extracción independiente del original y
verifican datos adjuntos, perfil reproducible, disponibilidad temporal y exclusividad del pool, semáforos, gráficos, calibración,
asimilación, cobertura, almacenamiento, fuentes y cierre meteorológico.
Se ejecutan automáticamente en GitHub Actions.
