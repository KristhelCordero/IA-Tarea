# Tarea Corta - Agentes de búsqueda y evolutivos para TileUp

## Integrantes

2024154899 - Djedrielle Alexander Vargas

2023135405 - Kristhel Cordero Leiva

2000000000 - Jose Pablo Sequeira

## Descripción

Este proyecto implementa dos agentes inteligentes para resolver instancias del juego TileUp: un agente basado en búsqueda y un agente evolutivo. Ambos agentes reciben una instancia del juego y generan una secuencia de posiciones en las que colocar las fichas, buscando completar la secuencia antes de que el tablero quede lleno.

### El juego: TileUp

El juego se lleva a cabo en un tablero cuadrado con `NxN` celdas vacías, en el cual se va colocando una secuencia fija de fichas, cada una compuesta de dos variables: valor y color. Una ficha colocada se combina con las fichas del mismo color que sean ortogonalmente adyacentes a ella. La combinación suma los valores de todas las fichas involucradas y coloca el resultado en la celda donde se colocó la nueva ficha. Las demás celdas ocupadas por las fichas combinadas quedan vacías.

El juego continúa hasta que la secuencia de fichas termina, o que el tablero esté completamente lleno y no se pueda colocar ninguna ficha más. La partida termina con victoria cuando se colocan todas las fichas de la secuencia. Termina con derrota cuando queda al menos una ficha pendiente y el tablero no tiene ninguna celda vacía

#### Implementación

El juego está determinado por un archivo de texto plano. Las líneas en blanco y las que comienzan con `#` se ignoran. El resto se lee en este orden: una línea con `N` (tamaño del tablero) y `K` (cantidad de colores) separados por espacio, una línea con `M` (cantidad de fichas en la secuencia), y a continuación `M` líneas, cada una con el color y el valor de una ficha, en el orden en que deben colocarse.

El motor lee este archivo e inicializa el tablero y la secuencia de fichas.

### Agentes

A continuación se describen los agentes, de búsqueda y evolutivo, implementados. Para más detalles sobre las decisiones de implementación refierase al [Informe](./Informe.md)

### Agente de Búsqueda

**TODO:** describir el agente de búsqueda

### Agente Evolutivo

El agente evolutivo es un **algoritmo genético generacional con elitismo**. A diferencia del agente de búsqueda, que explora estados parciales del tablero, este trabaja sobre **soluciones completas**: cada individuo codifica una partida entera, desde la primera ficha hasta la última.

Esa elección tiene una consecuencia práctica relevante para el requisito de límite de tiempo: el algoritmo es *anytime*, es decir, en cualquier momento de la ejecución existe un mejor individuo listo para entregarse. Al vencer el plazo, el agente devuelve esa solución sin necesidad de completar ninguna etapa.

#### Representación del individuo

El cromosoma es una lista de `M` enteros en el rango `[0, N²-1]`, uno por cada ficha de la secuencia.

La decodificación es **indirecta**: el gen no indica una celda `(fila, columna)` sino una posición dentro de la lista de celdas actualmente libres.

```text
celda_elegida = celdas_vacías[ gen_i mod len(celdas_vacías) ]
```

La lista de celdas vacías se recorre siempre en orden *row-major* (por fila y luego por columna), lo cual es indispensable para la reproducibilidad: la decodificación indexa sobre esa lista, de modo que un orden variable rompería el determinismo por semilla.

**Justificación.** Una representación directa produce individuos ilegales con altísima frecuencia, porque una colocación solo es válida si la celda está vacía *en ese instante*, y la ocupación cambia dinámicamente con cada fusión. Las alternativas habituales son penalizar los individuos ilegales o repararlos; ambas se descartaron. La penalización desperdicia la mayor parte de la población en aprender a ser legal en vez de a jugar bien, y la reparación traslada buena parte de las decisiones a una heurística ajena al algoritmo evolutivo.

El decodificador evita ambos problemas: **todo cromosoma produce una partida legal por construcción**, sin reparación ni descartes, y el espacio es completo, ya que cualquier partida legal es alcanzable por algún cromosoma.

**Costo de la decisión.** La representación tiene **baja localidad**: el significado del gen *i* depende de todos los genes anteriores, porque el estado del tablero es histórico. Un cambio pequeño en el genotipo puede producir un fenotipo muy distinto. Esta propiedad condiciona la elección del operador de cruce (ver más abajo). El mapeo además es *muchos a uno*: cuando hay menos celdas libres que `N²`, varios alelos distintos decodifican a la misma celda.

#### Función de aptitud

```text
aptitud = colocadas × (N² + 1) − ocupadas
```

La aptitud replica exactamente el orden de evaluación definido en el enunciado: primero la mayor cantidad de fichas colocadas y, ante igualdad, la menor cantidad de celdas ocupadas.

El multiplicador `N² + 1` no es arbitrario. Dado que `ocupadas ≤ N²`, la diferencia producida por una sola ficha adicional siempre supera cualquier diferencia posible en celdas ocupadas, por lo que el orden lexicográfico queda garantizado en un único escalar. Esto simplifica la selección por torneo, que solo necesita comparar números.

**Qué se excluyó deliberadamente.** La suma total de valores del tablero **no** se usa como señal: la fusión conserva la suma, de modo que es invariante y no depende de las decisiones del agente. El valor de la ficha mayor tampoco entra en la aptitud, ya que no es criterio de ordenamiento; se calcula únicamente porque el enunciado exige reportarlo.

#### Mecanismo de selección

**Torneo con reemplazo.** Se eligen `tam_torneo` individuos al azar de la población y se retorna el de mayor aptitud; el procedimiento se repite para cada progenitor requerido.

Se eligió sobre la selección proporcional a la aptitud (ruleta) porque esta última es sensible a la escala de los valores: con aptitudes del orden de 4500, dos individuos que difieren en una celda ocupada resultarían prácticamente equiprobables, anulando la presión selectiva. El torneo es invariante a la escala y expone la presión selectiva como un único parámetro entero, directamente medible.

#### Operadores de variación

**Cruce de un punto.** Se corta en una posición aleatoria del rango `[1, M-1]`, excluyendo los extremos, que producirían copias exactas, y se generan **dos** descendientes complementarios: prefijo del primer progenitor con sufijo del segundo, y viceversa. Se aprovechan ambos para no desperdiciar evaluaciones.

Se descartó el cruce uniforme precisamente por la baja localidad del decodificador. Como el significado de cada gen depende del historial completo, intercambiar genes salteados destruiría el contexto y el descendiente no se parecería a ninguno de sus progenitores, degenerando en una mutación masiva. El cruce de un punto, en cambio, preserva íntegro el **prefijo** de un progenitor, que sí constituye una unidad con significado: "juega las primeras *c* fichas como A y el resto como B".

**Mutación por gen.** Cada gen se reemplaza por un alelo nuevo del rango con probabilidad `tasa`. Es el único operador capaz de introducir material genético ausente en la población, y por lo tanto el único que puede recuperar diversidad perdida.

Ambos operadores devuelven estructuras nuevas y **nunca modifican sus argumentos**. Esto no es un detalle de estilo: los individuos de la élite se preservan por referencia, de modo que una mutación en el sitio corrompería el mejor individuo conocido sin generar ningún error visible.

#### Política de reemplazo

**Generacional con elitismo.** En cada generación se ordena la población por aptitud, se preservan intactos los `tam_elite` mejores y el resto se completa con los descendientes producidos.

El elitismo garantiza que la mejor aptitud **nunca decrezca** entre generaciones, lo cual se verifica inspeccionando la curva de convergencia que el agente reporta. Los individuos de la élite conservan su aptitud ya calculada y no se vuelven a evaluar, evitando gasto inútil en la medida de esfuerzo.

#### Criterio de paro

Se detiene al cumplirse **cualquiera** de tres condiciones, evaluadas por separado para poder informar cuál fue la que cortó:

| Criterio | Cubre |
|---|---|
| `generaciones >= max_generaciones` | Fija un presupuesto de evaluaciones, necesario para que las corridas sean comparables entre máquinas |
| `tiempo >= limite_seg` | Requisito de la especificación; se mide con `time.monotonic()`, inmune a ajustes del reloj del sistema |
| `sin_mejora >= max_sin_mejora` | Detiene la ejecución una vez convergida. Dado que el tercer criterio de desempate del concurso es el menor tiempo de cómputo, continuar tras la convergencia solo representa una desventaja |

El motivo de paro se reporta junto con las métricas, dato indispensable para interpretar los experimentos: un resultado deficiente por agotamiento del tiempo y uno por convergencia prematura exigen correcciones opuestas.

#### Parámetros y procedimiento por el cual se fijaron
*Sujeto a cambios.*

Los valores no se eligieron por intuición. Se fijaron mediante **barridos de un parámetro a la vez**, dejando el resto constante, sobre `instancia_06.txt` (N=8, K=6, M=70) con **5 semillas por configuración**. Se eligió esa instancia porque es la que mejor discrimina: en instancias pequeñas como `instancia_01.txt` la búsqueda aleatoria alcanza resultados casi óptimos y ninguna configuración se distingue de otra.

| Parámetro | Valor | Procedimiento |
|---|---|---|
| `tam_poblacion` | 100 | Efecto monótono y dominante (ver tabla). El valor conviene elevarlo tanto como el límite de tiempo permita |
| `tam_elite` | 2 | 2 % de la población: suficiente para garantizar monotonía sin reducir la renovación |
| `tam_torneo` | 3 | Sin efecto significativo en el rango 2–8 |
| `prob_cruce` | 0.8 | Ver tabla; la medición favorece valores altos |
| `tasa` | `1/M` | Óptimo confirmado experimentalmente |
| `max_generaciones` | 300 | Rara vez es el criterio que corta; actúa como tope de seguridad |
| `max_sin_mejora` | 60 | Más allá de 60 la mejora cae dentro de la dispersión |
| `limite_seg` | 10 (CLI) | Parámetro de ejecución, no de diseño |

**Tamaño de población.** Es el parámetro de mayor impacto, con efecto monótono:

| `tam_poblacion` | Aptitud media | Desv. | Evaluaciones | Tiempo |
|---|---|---|---|---|
| 50 | 4516.8 | 2.39 | 6 808 | 2.9 s |
| 100 | 4517.0 | 2.35 | 14 173 | 4.0 s |
| 200 | 4519.2 | 3.42 | 26 296 | 7.7 s |
| 400 | **4524.6** | 2.70 | 75 383 | 22.1 s |

El resultado es coherente con el diagnóstico de que el factor limitante es la **diversidad** y no la cantidad de iteraciones: prolongar una corrida con población reducida solo profundiza en una región ya explorada, mientras que ampliar la población explora más regiones simultáneamente. El valor por defecto es 100 para respetar el límite de 10 segundos; con un presupuesto mayor debe elevarse.

**Tasa de mutación.** Confirma la regla habitual de `1/M`, equivalente a mutar un gen por cromosoma en promedio:

| `tasa` | Aptitud media | Desv. |
|---|---|---|
| 0.5/M | 4517.6 | 1.52 |
| **1/M** | **4519.6** | 1.95 |
| 2/M | 4519.2 | 2.28 |
| 4/M | 4515.8 | 2.28 |

La caída en 4/M es el comportamiento esperado: una mutación excesiva destruye la herencia y degrada el algoritmo a una búsqueda aleatoria.

**Probabilidad de cruce.** La tendencia favorece valores altos:

| `prob_cruce` | Aptitud media | Desv. |
|---|---|---|
| 0.0 (sin cruce) | 4518.4 | 2.61 |
| 0.5 | 4520.6 | 1.95 |
| 0.8 | 4519.2 | 3.42 |
| 1.0 | **4523.2** | 3.77 |

La configuración `0.0` constituye una ablación deliberada: con mutación únicamente, el algoritmo todavía alcanza 4518.4, de modo que el cruce aporta pero no es el operador dominante. Esto es consistente con la baja localidad de la representación.

**Criterio de estancamiento y tamaño de torneo.** Ninguno de los dos muestra un efecto que supere la dispersión entre semillas:

| `max_sin_mejora` | Media | Desv. | Evaluaciones |
|---|---|---|---|
| 30 | 4517.6 | 2.88 | 13 664 |
| 60 | 4519.2 | 3.42 | 26 296 |
| 150 | 4519.4 | 3.36 | 46 888 |
| 400 | 4519.4 | 3.36 | 59 600 |

| `tam_torneo` | Media | Desv. |
|---|---|---|
| 2 | 4517.4 | 1.14 |
| 3 | 4519.2 | 3.42 |
| 5 | 4519.2 | 3.03 |
| 8 | 4518.2 | 1.64 |

Pasar de 60 a 150 generaciones de paciencia mejora la media en 0.2 puntos —muy por debajo de la desviación— a cambio de un 78 % más de evaluaciones, por lo que 60 se mantiene. Que `tam_torneo` resulte indiferente entre 2 y 8 es un resultado reportable: en este problema la presión selectiva no es un parámetro crítico.

#### Validación frente a una búsqueda aleatoria

Como control experimental se implementó una búsqueda aleatoria —generar cromosomas al azar y conservar el mejor— que se compara con el agente evolutivo bajo **idéntico presupuesto de evaluaciones**:

| Instancia | Búsqueda aleatoria | Agente evolutivo | Ventaja |
|---|---|---|---|
| `instancia_01.txt` (N=4, M=24) | 401.3 | 401.0 | ~0 |
| `instancia_04.txt` (N=6, M=28) | 1023.0 | 1027.0 | +4.0 |
| `instancia_06.txt` (N=8, M=70) | 4506.3 | 4513.3 | +7.0 |

La ventaja crece con el tamaño del espacio de búsqueda, que es el comportamiento esperado: en espacios reducidos el muestreo ciego cubre una fracción suficiente del dominio, mientras que en espacios grandes la búsqueda dirigida resulta indispensable. En `instancia_06.txt` la búsqueda aleatoria se estanca en 4506 con desviación 0.58 incluso al multiplicar su presupuesto, evidenciando un techo que el agente evolutivo supera.

#### Métricas reportadas

Al finalizar, el agente informa por salida estándar en formato `clave=valor`: `colocadas`, `ocupadas`, `mayor`, `tiempo`, `evaluaciones`, `generaciones` y `motivo_paro`.

La **medida de esfuerzo** del algoritmo es la cantidad de **evaluaciones de aptitud**, contabilizadas explícitamente durante la ejecución. Es la magnitud comparable con los nodos expandidos del agente de búsqueda, y permite contrastar ambos agentes con independencia del hardware.

### Estructura del proyecto

El siguiente árbol describe la organización del repositorio:

```text
.
├── src/
│   ├── game.py
│   ├── validator.py
│   ├── generador/
│   │   └── generador_instancias.py
|   ├── agente_evolutivo/
│   │   └── agent.py
│   └── searchAgent/
│       └── searchAgent.py
├── entradas/
├── salidas/
└── A_Tests/
```

La tabla describe cada componente:

|Archivo/Directorio                         | Descripción                                 |
|-------------------------------------------|---------------------------------------------|
| `src/game.py`                             | Implementación del motor de TileUp          |
| `src/generador/generador_instancias.py`   | Genera instancias reproducibles             |
| `src/validator.py`                        | Verifica si una solución generada es válida |
| `src/agente_evolutivo/agent.py`           | Implementación del agente evolutivo         |
| `src/searchAgent/searchAgent.py`          | Implementación del agente de búsqueda       |
| `entradas/`                               | Instancias de entrada                       |
| `salidas/`                                | Soluciones generadas                        |
| `A_Tests/`                                | Pruebas del proyecto                        |

## Replicación

A continuación se describen los pasos para replicar la ejecución de los agentes sobre una instancia del juego de TileUp

### Requisitos

- Python 3.9 o posterior.
- No se requieren paquetes externos.
- Git es necesario para clonar el repositorio.

### Procedimiento

``` text
Requisitos
↓
Clonar
↓
Generar instancia (OPCIONAL)
↓
Ejecutar agente
↓
Validar resultado
↓
Ejecutar pruebas
```

### 1. Clonación del repositorio

Haciendo uso de github desktop o del siguiente comando de github se puede clonar el repositorio:

```powershell
git clone https://github.com/KristhelCordero/IA-Tarea.git
Set-Location IA-Tarea
```

Los comandos siguientes se ejecutan desde la raíz del proyecto, salvo cuando se indique lo contrario

### 2. Generar una instancia (OPCIONAL)

Este componente genera una instancia de juego. Es decir, coloca el tamaño del tablero, cantidad de colores, cantidad de fichas y la secuencia de fichas; en un archivo de texto que se puede utilizar para probar los agentes.

El generador recibe los siguientes parámetros:

- Tamaño del tablero: `N`
- Cantidad de colores: `K`
- Cantidad de fichas: `M`
- Semilla: `X`
- Ruta: `PATH`

Si no se indica una ruta, se crea el archivo dentro de `entradas/`

```powershell
python src/generador_instancias.py <N> <K> <M> <X> <PATH>
```

Se puede omitir este paso si se desea utilizar una instancia que ya existe o una propia

#### Formato de las instancias

Una instancia tiene el siguiente formato:

```text
N K
M
color valor
color valor
...
```

#### Ejemplos

```powershell
python src/generador_instancias.py 4 3 8 42
```

Para especificar una ruta de salida:

```powershell
python src/generador_instancias.py 4 3 8 42 entradas/mi_instancia.txt
```

## 3. Ejecutar agente

Desde la raíz del proyecto, el siguiente comando ejecuta el AE con la instancia predeterminada y guarda el resultado en `salidas/solution.txt`:

```powershell
python src/main.py
```

Se pueden indicar `--instancia`, `--salida`, `--semilla` y `--limite-segundos` para personalizar la ejecución. El sistema utiliza únicamente la biblioteca estándar de Python, por lo que no requiere instalar dependencias externas ni editar archivos.

Ejemplo:

## 4. Validar Resultado

Una solución consiste en una secuencia de posiciones del tablero, donde cada posición indica la celda en la que el agente coloca la siguiente ficha de la secuencia.

### Formato de las soluciones

Una solución tiene el siguiente formato:

```text
índice_ficha fila columna
índice_ficha fila columna
índice_ficha fila columna
...
# colocadas = 24 ocupadas = 8 mayor = 14 
```

En este paso se determina si la solución del agente es válida o no

## 5. Ejecutar las pruebas automatizadas

Desde la raíz del proyecto, ejecutar las pruebas unitarias y las de integración con:

```powershell
python -m unittest discover -s A_Tests -p "*Test.py" -v
```

Las pruebas unitarias cubren fusión de dos fichas, fusión de tres o más, colocación sin fusión y detección de derrota. La prueba de integración está preparada pero omitida hasta conectar un agente con el validador.

## TODO

- Integrar el agente de búsqueda con el motor de TileUp.
- Implementar la prueba de integración de resolución de una instancia pequeña y validación de la solución.
- Completar la declaración de uso de IA de acuerdo con el trabajo realizado.

## Declaración del Uso de IA

TODO: describir las herramientas de IA utilizadas y el alcance de su uso.
