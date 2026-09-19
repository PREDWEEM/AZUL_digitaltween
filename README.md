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

## Funcionamiento

- **Estado del lote:** emergencia acumulada, barras azules de flujo diario,
  curva base, curva calibrada, estado actualizado y banda amarilla 600–800 °Cd.
  El eje horizontal muestra fechas calendario.
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

Para series parciales se utiliza una referencia **compartida de 11 campañas**
del clasificador original, excluyendo 2010 y 2015. No contiene una campaña
histórica identificada como Azul: no constituye una validación histórica local.
El total observado parcial no se supone igual al potencial estacional completo.

Consulte [MODEL_PROVENANCE.md](MODEL_PROVENANCE.md) para la revisión de origen,
los hashes y la correspondencia científica.

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
ajusta dos parámetros: **offset −0,30; slope 0,675**. Conserva 0 y 1, mantiene
la monotonía y no crea flujos en días bloqueados por el motor. No modifica los
pesos ANN, el decaimiento ni el tiempo térmico. Cobertura y Wmax son supuestos
operativos originales: el adjunto no los informa. Sin repeticiones se utiliza
un piso común de ponderación, no un error de muestreo medido.

| Evaluación | RMSE base | RMSE calibrado |
|---|---:|---:|
| Ajuste retrospectivo, 10 intervalos | 548,77 | 373,72 |
| Evaluación temporal, 4 intervalos posteriores | 203,06 | 367,21 |

RMSE en plantas/m² por intervalo. El ajuste retrospectivo mejora un 31,9 %, pero
**la evaluación temporal empeora un 80,8 %**; mejora sólo uno de cuatro intervalos.
La interfaz muestra esta limitación junto al gráfico principal y en el detalle
de calibración. Los cuatro cortes se ajustan sólo con datos disponibles hasta
cada corte y se evalúa el intervalo siguiente con reanálisis realizado. No son
pronósticos archivados. El perfil es **experimental** y no demuestra mejora
predictiva ni transferencia a otros años. Tampoco reduce automáticamente
la incertidumbre del gemelo.

La capa se aplica al seleccionar Azul, desde el 01/09/2026 y con el mismo motor
y referencia utilizados al ajustar. Las fechas anteriores no usan un perfil
que incluye observaciones posteriores. Si se asimilan conteos de 2026, se usa
la base para evitar reutilizar esa evidencia como calibración y asimilación.
El motivo aparece junto al interruptor.

Los adjuntos se conservan como referencia de calibración; no se cargan
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
verifican datos adjuntos, perfil reproducible, cortes temporales, calibración,
asimilación, cobertura, almacenamiento, fuentes y cierre meteorológico.
Se ejecutan automáticamente en GitHub Actions.
