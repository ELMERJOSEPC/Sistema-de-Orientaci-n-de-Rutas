# Sistema de Orientación de Rutas para la Optimización del Transporte Público en Puno

Proyecto en Python creado según el informe **"Sistema de Orientación de Rutas para la Optimización del Transporte Público en Puno"**.

El sistema aplica programación funcional con datos inmutables (`NamedTuple`), funciones puras, cálculo de entropía de Shannon, recomendación de línea directa, recálculo por incidencias y búsqueda BFS con transbordos. Ahora incluye una **interfaz gráfica profesional y funcional en Tkinter**.

## Novedad: interfaz gráfica profesional

La interfaz permite trabajar con tres módulos:

1. **Pasajero**
   - Selección de origen y destino.
   - Recomendación automática de la línea más directa.
   - Cálculo de la entropía de Shannon.
   - Visualización de recorrido sugerido.
   - Tabla de alternativas.
   - Alertas por incidencias activas.
   - Botón para abrir el recorrido en Google Maps.

2. **Conductor**
   - Login de conductor.
   - Registro de turno.
   - Clasificación automática: `en tiempo`, `retrasado` o `crítico`.
   - Tabla de turnos registrados.

3. **Administrador**
   - Login de administrador.
   - Dashboard con conteos del sistema.
   - Crear y resolver incidencias.
   - Agregar y eliminar líneas.
   - Guardado automático en archivos JSON.

## Estructura del proyecto

```text
sistema_rutas_puno/
│
├── run.py              # Abre la interfaz gráfica
├── run_gui.py          # También abre la interfaz gráfica
├── run_cli.py          # Abre la versión de consola
├── requirements.txt
├── README.md
├── data/
│   ├── lineas.json
│   ├── incidencias.json
│   ├── usuarios.json
│   └── turnos.json
├── docs/
│   └── pipeline.mmd
├── rutas_puno/
│   ├── __init__.py
│   ├── cli.py
│   ├── data.py
│   ├── domain.py
│   ├── gui.py          # Interfaz profesional Tkinter
│   ├── logging_config.py
│   ├── maps.py
│   ├── models.py
│   ├── security.py
│   └── storage.py
└── tests/
    ├── test_domain.py
    ├── test_security.py
    └── test_storage.py
```

## Cómo ejecutar la interfaz gráfica

Abre una terminal dentro de la carpeta del proyecto y ejecuta:

```bash
python run.py
```

También puedes usar:

```bash
python run_gui.py
```

No requiere librerías externas. Usa `tkinter`, que viene incluido con la mayoría de instalaciones de Python en Windows.

## Cómo ejecutar la versión de consola

```bash
python run_cli.py
```

## Cómo probar el ejemplo principal del informe

En la pestaña **Pasajero**, selecciona:

```text
Origen: EsSalud Salcedo
Destino: Universidad
```

Luego presiona **Recomendar ruta**.

Resultado esperado sin incidencias activas:

```text
Línea recomendada: L50
Entropía de Shannon: H = 2.0 bits
```

La entropía es 2 bits porque el sistema encuentra 4 alternativas directas y usa:

```text
H = log2(4) = 2
```

## Cómo probar una incidencia

1. Ve a la pestaña **Administrador**.
2. Inicia sesión con las credenciales de administrador.
3. Crea una incidencia en:

```text
Paradero: Terminal Terrestre
Motivo: Alta congestión en hora punta
```

4. Regresa a **Pasajero** y vuelve a recomendar:

```text
EsSalud Salcedo -> Universidad
```

El sistema debe evitar el paradero bloqueado y recomendar una alternativa que no pase por la congestión.

## Credenciales de prueba

Administrador:

```text
Usuario: admin
Contraseña: admin123
```

Conductor:

```text
Usuario: chofer1
Contraseña: clave123
```

## Ejecutar pruebas unitarias

```bash
python -m unittest discover -s tests -v
```

El proyecto incluye 28 pruebas unitarias que validan el núcleo funcional: entropía, recomendación de rutas, incidencias, BFS, turnos, sanciones, login y persistencia JSON.

## Archivos principales

### `rutas_puno/models.py`
Define los tipos inmutables:

- `Linea`
- `Vehiculo`
- `Segmento`
- `Ruta`
- `Recomendacion`
- `Turno`
- `Incidencia`
- `Cuenta`
- `Reporte`

### `rutas_puno/domain.py`
Contiene el núcleo funcional puro:

- `entropia_shannon()`
- `recomendar_linea()`
- `buscar_mejor_ruta()`
- `crear_incidencia()`
- `resolver_incidencia()`
- `marcar_turno()`
- `resumen_dashboard()`

### `rutas_puno/gui.py`
Contiene la interfaz gráfica profesional:

- Pestaña pasajero.
- Pestaña conductor.
- Pestaña administrador.
- Tablas, formularios, dashboard y botones funcionales.

### `data/*.json`
Contiene datos editables de líneas, usuarios, incidencias y turnos.

## Flujo del algoritmo

1. Recibe origen, destino, líneas e incidencias activas.
2. Obtiene paraderos bloqueados.
3. Filtra líneas directas que evitan congestión.
4. Calcula entropía de Shannon.
5. Elige la línea con menor número de tramos y menor costo.
6. Si no hay línea directa, busca una ruta con transbordos mediante BFS.
7. Muestra recomendación, alternativas, costo, alerta y URL de Google Maps.

## Diagrama Mermaid

El diagrama está en:

```text
docs/pipeline.mmd
```

Puedes pegarlo en <https://mermaid.live> para visualizarlo.
