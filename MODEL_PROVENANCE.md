# Procedencia científica del gemelo de Azul

Motor original: [PREDWEEM/LOLIUM_AZUL2026](https://github.com/PREDWEEM/LOLIUM_AZUL2026/tree/f60de7d5c5c82f2e202eea9f5b1d409b98742ff9),
revisión `f60de7d5c5c82f2e202eea9f5b1d409b98742ff9`. El repositorio fuente no se modificó.

La interfaz, persistencia, asimilación y calibración externa se adaptaron del
[gemelo Tres Arroyos](https://github.com/PREDWEEM/TREASA_digitaltween/tree/a71235301b2f746f244a5fca5f873d67d8e37949).
La normalización con referencia compartida utiliza la implementación del
[gemelo Lartigau](https://github.com/PREDWEEM/larti_digitaltween/tree/b14687448c63c538d28ca17fe58f58ecaf01573b).
Los activos neuronales, parámetros fisiológicos y meteorología proceden de
Azul. El perfil de calibración se ajustó con el archivo aportado para Azul.

## Activos originales

| Archivo | SHA-256 |
|---|---|
| `models/IW.npy` | `8614f90cd5f1337ae746690e474587b6fb22cf81652e694573cbfe4573f406d5` |
| `models/LW.npy` | `13cb012d7f4fe8e9e8399b31226e160ed60690cd4fb225a2de40375d250eb97b` |
| `models/bias_IW.npy` | `69423ba136a4caad97bed6b3aae2e7a387d87851a32eb5b2ab8de74dbcae3788` |
| `models/bias_out.npy` | `53451c25cc92da6bff25404a1e47815e38dfe58f7d83bb87c2d471298ec8a12d` |
| `models/modelo_clusters_k3.pkl` | `29f0508543bdda4b2520038c678a9df80ff9be555e0c15d5fa1f4da16a499d30` |

## Correspondencia del motor

Se conservaron las funciones de `app_emergenciacombinado_core.py`, incorporando
el parche activo `modelo_decaimiento_15abril.py`. Las pruebas comparan las
trayectorias con una extracción independiente de esas funciones en
`tests/fixtures/azul_original.py`, con distintas coberturas, Wmax y Kr.

- ANN original de cuatro entradas: día juliano, TMAX, TMIN y precipitación.
- Cobertura inicial 10 %; Wmax 18,81 mm; exponente Kr=0.
- Coordenadas −36,87, −59,89; ET0 Hargreaves con esa latitud.
- Latencia hasta JD 25 y primer pico estrictamente mayor que 0,20.
- Choque hídrico: 45 mm en tres días, hasta JD 110, piso 0,75 antes de filtros.
- Termoinhibición: media móvil de cinco días mayor o igual que 24 °C.
- Factor hídrico sigmoide, corte de humedad relativa menor que 0,20 y recarga
  habilitada por una lluvia diaria mayor o igual que Wmax.
- Desde el 15/04: techo inicial del 50 % del máximo previo, multiplicado por
  `(1 − I) + I × exp(−(días/τ)^β)`, con τ=60 días, β=1 e I=0,75.
  Sin emergencia positiva previa al 15/04, el original no impone un techo.
- Reloj térmico triangular 2–20–30 °C; ventana de manejo 600–800 °Cd.

La cobertura diaria, la normalización parcial, la asimilación y la calibración
externa son extensiones del gemelo. La cobertura afecta el balance hídrico
y el diagnóstico de suelo, no las entradas neuronales. La calibración no
modifica el reloj térmico ni los pesos.

## Referencia estacional

Se utilizan nueve campañas del clasificador original, excluyendo 2010, 2015,
Balcarce y San Pedro.
No contiene una campaña histórica identificada como Azul. Es una referencia
compartida, no una validación histórica local. El clasificador no se modifica;
los nombres de las campañas utilizadas quedan registrados en el perfil JSON.

## Meteorología y calibración

`actualizar_clima.py`, su prueba de recuperación y `meteo_daily.csv` proceden
de la misma revisión fuente. El workflow conserva horarios y validaciones,
con ejecución manual y programada. Se conserva el cierre inclusivo del
01/10/2026 y la secuencia ERA5-Land → respaldo ERA5 → histórico ECMWF IFS →
pronóstico ECMWF IFS HRES. Los metadatos FUENTE, TIPO y FECHA_EMISION conservan
su significado original; la última fecha histórica no implica observación
instrumental local. FECHA_EMISION no se etiqueta como UTC: es hora local.

El ajuste utiliza 244 días fijos del 01/01 al 01/09/2026, todos ERA5 con tipo
REANALISIS_FALLBACK. Se incluyen el Excel original y su CSV de 11 muestreos.
La hoja contiene FECHA y PLM2, sin repeticiones ni cobertura; la localidad
se asigna por la instrucción del usuario.

El origen, revisión, coordenadas y hashes están en
`data/calibration/azul_2026_source.json` y en el perfil JSON.
Los resultados de ajuste se separan de la evaluación temporal sobre cuatro
intervalos posteriores. Esta evaluación empeora respecto de la base y se
informa explícitamente en la interfaz. Se usa reanálisis realizado; no se
presenta como validación independiente de pronósticos emitidos ni de otra campaña.

## Exclusión de Balcarce y San Pedro

Se excluyen `emererel2025 balcarce.xlsx` y `emrel sp 2025 san pedro.xlsx`
antes de calcular P10, mediana y P90. El filtro ignora mayúsculas y espacios
repetidos y exige un nombre por curva. Quedan ocho archivos identificados
sólo por año (2008, 2009, 2011–2014, 2023 y 2024) y Tres Arroyos 2025.
La localidad de los ocho archivos no se infiere de sus nombres.

Se regeneran el perfil 2026 y los diagnósticos con los mismos datos y cortes;
el fingerprint incluye el código de selección. El perfil registra filtros,
cantidad y nombres incluidos/excluidos. La interfaz recarga la referencia
en cada ejecución para evitar datos obsoletos de Streamlit. Se conserva el
mecanismo de anclaje estacional, así como la ANN y la fisiología del sitio.
