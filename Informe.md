# Informe: búsqueda y algoritmo evolutivo para TileUp

## Objetivo y criterio de comparación

Se comparan un agente de búsqueda por haz y un algoritmo evolutivo para decidir dónde colocar una secuencia fija de fichas en TileUp. En cada corrida, el criterio del problema es lexicográfico: maximizar las fichas colocadas y, entre resultados con igual cantidad, minimizar las celdas ocupadas al final. El valor mayor del tablero se registra como dato descriptivo, no como criterio de selección.

## Motor y arquitectura compartida

El motor de [game.py](src/game.py) representa cada celda como `(color, valor)` y una celda vacía como `(0, 0)`. Ambos agentes usan `createBoard` y `action`, de modo que simulan las mismas reglas. Una acción coloca la siguiente ficha en una celda libre y fusiona los vecinos inmediatos de igual color que comparten un lado con ella; suma sus valores en la celda elegida y vacía las otras celdas. Esta implementación no recorre componentes conectadas a través de vecinos indirectos. El caso de fusión de tres o más de las pruebas corresponde a varias fichas adyacentes directamente a la colocación.

La secuencia se consume en orden. Colocar todas las fichas es victoria; tener el tablero lleno con fichas pendientes es derrota. `action` presupone una celda legal: los agentes solo eligen celdas libres y el validador comprueba las coordenadas y la ocupación antes de aplicar cada acción.

El punto de entrada [main.py](src/main.py) separa la selección del agente, la lectura de la instancia y la validación de la solución. La búsqueda reutiliza `Resultado`, `celdas_vacias` y `escribir_solucion` del módulo evolutivo para compartir el orden de las celdas y el formato de salida, sin duplicarlos. Esto introduce una dependencia entre módulos, pero no ejecuta el algoritmo evolutivo al seleccionar búsqueda.

## Formulación de los agentes

### Agente de búsqueda

Un estado es el tablero después de colocar un prefijo de la secuencia. El nivel del nodo determina cuál es la siguiente ficha, así que los sucesores se obtienen colocando esa ficha en cada celda vacía y aplicando la regla de fusión. Los tableros iguales dentro de un mismo nivel se deduplican. Se expande un haz de ancho acotado y se conservan los estados con menos celdas ocupadas; los empates se resuelven por orden de generación, determinista.

La búsqueda es de ancho creciente: empieza con ancho 1 y multiplica el ancho por 4; 8192 es el umbral configurado para detener nuevas pasadas (por el factor de crecimiento, el último ancho intentable puede ser 16384). La mejor solución
encontrada se conserva entre pasadas. Puede detenerse al alcanzar el límite de tiempo, al probar exhaustivamente una pasada, al llegar al piso teórico de ocupación (un estado final necesita al menos una celda por color presente), o
al alcanzar el ancho máximo. El método es anytime, pero el podado del haz significa que no garantiza encontrar una solución óptima. Su esfuerzo se mide en nodos expandidos: estados a los que se les generaron sucesores.

El orden por ocupación se justifica porque, en un mismo nivel, todos los nodos ya colocaron la misma cantidad de fichas; entonces el segundo criterio del objetivo distingue sus prefijos. No estima la calidad futura, por lo que no se presenta como una heurística informada ni admisible. Si una jugada fusiona `|G|` fichas, incluida la recién colocada, la ocupación cambia en `2 − |G|`. Con los vecinos inmediatos del motor, `1 ≤ |G| ≤ 5`; el costo no negativo `5 − |G|` suma, para un camino de profundidad `d`, `ocupadas + 3d`. Por ello ordenar por ocupación equivale a ordenar por ese costo acumulado en un mismo nivel, pero no entre profundidades diferentes. Entre pasadas se compara explícitamente primero la profundidad y luego la menor ocupación.

Se usa un haz para limitar cuántos estados se conservan entre niveles frente al crecimiento del árbol de colocaciones. Ampliar el ancho permite reconsiderar alternativas descartadas en pasadas anteriores, a costa de más trabajo. La implementación genera y ordena los candidatos de un nivel antes de recortar el haz, así que su memoria no está limitada estrictamente al ancho. Deduplicar tableros en el mismo nivel es válido porque comparten el mismo sufijo de fichas y, por tanto, las mismas continuaciones posibles. Los punteros al padre permiten reconstruir la solución sin copiar todo el camino en cada sucesor.

El piso teórico sirve como certificado solo cuando se colocaron todas las fichas: la fusión no elimina un color, por lo que debe quedar al menos una celda por color de la secuencia. Alcanzar ese piso con una solución completa demuestra que no se puede mejorar ninguno de los dos criterios. No significa que el haz siempre alcance ese resultado. Tampoco se garantiza completar una secuencia arbitraria con ancho 1 o un límite de tiempo pequeño; se conserva el mejor prefijo encontrado.

### Agente evolutivo

Cada individuo es un cromosoma de `M` enteros en `[0, N²−1]`. El gen de cada ficha selecciona, por módulo, una celda de la lista de celdas vacías en orden por fila y columna. La decodificación simula la partida en el motor del juego; por ello, cada individuo produce una secuencia de acciones legales hasta colocar todas las fichas o llenar el tablero.

La aptitud es `colocadas × (N² + 1) − ocupadas`. La población inicial es aleatoria; se usa selección por torneo con reemplazo, cruce de un punto y mutación por gen. En cada generación se conserva elitistamente a los mejores individuos. Los parámetros por defecto son población 100, élite 2, torneo 3, probabilidad de cruce 0.8, tasa de mutación `1/M`, máximo 300 generaciones y 60 generaciones sin mejora. Es anytime y su esfuerzo se mide por evaluaciones de aptitud. La implementación y sus detalles adicionales están en `src/agente_evolutivo/agent.py`; la del agente de búsqueda está en `src/searchAgent/searchAgent.py`.

La representación indirecta evita generar coordenadas ocupadas: cada gen indexa únicamente la lista de celdas libres del  tablero actual. No necesita reparar movimientos ilegales, aunque el módulo puede sesgar la frecuencia con que se eligen celdas y un cambio temprano puede alterar la interpretación de los genes posteriores. El orden por fila y columna mantiene determinista la decodificación.

La escala de aptitud preserva el objetivo porque `0 ≤ ocupadas ≤ N²`. Una ficha colocada adicional aporta `N² + 1`, más que cualquier diferencia posible de ocupación; si las cantidades colocadas son iguales, gana la menor ocupación. El torneo introduce presión selectiva sin requerir probabilidades proporcionales a la aptitud. El cruce intercambia segmentos de decisiones, la mutación reemplaza genes por valores del mismo dominio y el elitismo evita perder la mejor aptitud entre generaciones. Con tasa `1/M`, el número esperado de intentos de mutación por cromosoma es uno, aunque un reemplazo puede repetir el valor previo.

### Parámetros: justificación y evidencia disponible

| Parámetro | Función y razonamiento de diseño | Alcance de la evidencia |
| --- | --- | --- |
| Búsqueda: ancho inicial 1 y factor 4 | Empezar con una pasada barata y ampliar progresivamente las alternativas exploradas. | Se documenta su funcionamiento; no se aporta un barrido que pruebe que el factor 4 es el mejor. |
| Búsqueda: umbral 8192 | Evitar ampliar indefinidamente el haz. El chequeo se hace después de cada pasada; con crecimiento por 4 puede intentarse ancho 16384. | Es un límite configurado, no una garantía estricta de memoria ni un valor calibrado en este informe. |
| Evolutivo: población 100 y élite 2 | Mantener alternativas y conservar los dos mejores individuos durante el reemplazo. | La batería usa estos valores fijos; no demuestra que sean óptimos. |
| Evolutivo: torneo 3 y cruce 0.8 | Favorecer individuos de mayor aptitud y recombinar padres en la mayoría de los cruces. | Se justifican sus funciones, no la superioridad experimental de estos valores. |
| Evolutivo: mutación `1/M` | Mantener un intento de mutación esperado por cromosoma al cambiar la longitud de la instancia. | La expectativa se deriva de la tasa; no demuestra que produzca la mejor calidad. |
| Evolutivo: 300 generaciones y 60 sin mejora | Limitar el esfuerzo y detenerse tras una sucesión de generaciones sin mejora de la mejor aptitud. | No se adjuntan curvas ni barridos que certifiquen estos umbrales. |
| Ambos: límite nominal de 10 segundos | Comparar bajo el mismo presupuesto temporal configurado y conservar el mejor resultado disponible. | Los tiempos y motivos de parada están en el CSV; el límite no equivale a igual trabajo ni es un corte exacto. |

El módulo evolutivo incluye herramientas de barrido y comparación con búsqueda aleatoria, pero su presencia en el código no prueba que se ejecutaran ni respalda una conclusión sin resultados registrados. La comparación presentada evalúa configuraciones fijas, no constituye una calibración de hiperparámetros. No se consideran demostradas las afirmaciones de comentarios del código sobre calibraciones o heurísticas descartadas si no están acompañadas de evidencia en este informe.

## Ejecución y validación de soluciones

`src/main.py` ejecuta el agente seleccionado sobre una instancia y, después de guardar la solución, la valida automáticamente contra esa misma instancia. También se puede validar cualquier pareja de archivos de forma independiente:

```powershell
python src/validator.py --instancia entradas/instancia_01.txt --solucion salidas/solution.txt
```

El comando reutiliza las funciones existentes `processSolution`, `validateSolution` y `compareSummary`; verifica las acciones y el resumen reportado por la solución. Los índices comienzan en cero y deben seguir el orden de la secuencia; las coordenadas deben estar dentro del tablero y la celda debe estar vacía. El resumen registra las fichas colocadas, las celdas ocupadas y el mayor valor final. Una solución incompleta puede ser válida si el agente se detuvo antes de terminar la secuencia: legalidad y completitud son propiedades distintas. Los casos antiguos y la función `test(files)` permanecen comentados y no forman parte de las pruebas automatizadas.

### Pruebas y alcance de la validación

Las pruebas unitarias de [test_engine.py](A_Tests/test_engine.py) ejercitan únicamente el motor, sin ejecutar agentes ni leer soluciones:

- Dos fichas del mismo color suman sus valores y liberan la celda de la ficha previa.
- Tres vecinas del mismo color y la ficha nueva se fusionan en una ficha de valor 14.
- Una colocación junto a otro color no fusiona ni modifica las otras celdas.
- Un tablero lleno con fichas pendientes cumple `isBoardFull` y no cumple `isWin`, la condición de derrota del motor.

Las pruebas de integración de [test_integration.py](A_Tests/test_integration.py) crean una instancia temporal de tablero 3 × 3, dos colores y cinco fichas. Ejecutan ambos agentes mediante `main.main`, con semilla 7 y límite de 2 segundos; leen la solución con `validateFiles`, exigen que se hayan colocado las cinco fichas y verifican el comando del validador con código de salida cero. Una segunda prueba comprueba el rechazo de una solución que reutiliza una celda ocupada. Los archivos temporales se eliminan al terminar.

Desde la raíz, el comando también documentado en el [README](README.md) es:

```powershell
python -m unittest discover -v
```

Son cuatro pruebas unitarias y dos de integración; una de estas últimas incluye un subcaso por agente. La integración invoca el punto de entrada en el mismo proceso, no lanza un proceso de consola separado. El validador reproduce las acciones con el mismo motor que los agentes: verifica consistencia y legalidad respecto a esa implementación, pero no es una implementación independiente de las reglas ni demuestra que no haya errores compartidos. Estas pruebas no certifican optimalidad, calibración, todos los casos de archivos malformados o fusiones indirectas.

## Diseño experimental y reproducción

Se usó una rejilla factorial de 12 configuraciones `N × K`, con cuatro tamaños de tablero (`N ∈ {4, 6, 8, 10}`), tres cantidades de colores (`K ∈ {2, 4, 6}`) y tres semillas (`1, 2, 3`) por configuración: 36 instancias y 72 corridas de agente. La cantidad de fichas se fija en `M = round(1.1 × N²)` para mantener aproximadamente constante la densidad:
`M = 18, 40, 70, 110`, respectivamente. Cada semilla genera una secuencia determinista de fichas con valores entre 1 y 4 y colores entre 1 y `K`. Ambos agentes reciben exactamente el mismo archivo en cada corrida.

El agente evolutivo usa la semilla de la instancia como semilla del generador aleatorio; la búsqueda es determinista y no depende de ella. Se concedió a cada corrida un límite nominal de 10 segundos. El CSV registra también el motivo de parada para distinguir las corridas que terminan por tiempo de las que llegan a otro criterio. El tiempo medido es dependiente del hardware; las comparaciones de esfuerzo (nodos expandidos frente a evaluaciones de aptitud) son específicas de cada algoritmo y no representan operaciones equivalentes.

Variar `N` observa el crecimiento del tablero y variar `K` cambia las oportunidades de encontrar vecinos del mismo color. Mantener `M` aproximadamente proporcional a `N²` evita reducir la densidad de fichas al aumentar el tablero; el factor 1.1 estudia secuencias algo más largas que la cantidad de celdas. No es una demostración de dificultad uniforme entre configuraciones. El generador muestrea colores y valores con `randint`; no garantiza que todos los colores aparezcan en cada instancia.

La batería llama directamente a `buscar` y `evolucionar` y registra métricas; no produce ni valida un archivo de solución por cada una de las 72 corridas. La ruta de escritura y validación de archivos se comprueba por separado en `main.py` y en las pruebas de integración. En el CSV, `termino` significa que el motivo de parada fue distinto de `tiempo`, no que se colocaron todas las fichas; la completitud se determina comparando `colocadas` con `total_fichas`. El tiempo de cada agente mide su búsqueda interna, no la escritura ni la validación posterior.

Desde la raíz del repositorio, la batería completa se puede regenerar con:

```powershell
python src/modulo_adicional/bateria.py generar
python src/modulo_adicional/bateria.py correr --agentes busqueda evolutivo --limite 10 --salida src/modulo_adicional/resultados/comparacion.csv
```

Las instancias quedan en `src/modulo_adicional/instancias/`. Los resultados individuales por agente, configuración y semilla están en [`comparacion.csv`](src/modulo_adicional/resultados/comparacion.csv). La ejecución de referencia se hizo en Windows con Python 3.12.10.

No es obligatorio ejecutar la reproducción dentro de un entorno virtual porque no se requieren dependencias externas. El [README](README.md#entorno-virtual-opcional-powershell) documenta su creación opcional y el uso directo de su intérprete si PowerShell no permite activarlo. Para preservar el CSV de referencia puede usarse `comparacion_reproduccion.csv` como salida. La sección [Comprobar que la réplica terminó](README.md#comprobar-que-la-réplica-terminó) verifica el código de salida, las 72 filas y la correspondencia exacta con la rejilla. Esas comprobaciones acreditan que la batería terminó, no igualdad de tiempos o calidad con la referencia ni validación independiente de cada solución.

## Resultados

Cada fila resume la configuración a través de sus tres semillas; las columnas muestran media ± desviación estándar muestral (`n = 3`). Para cada métrica `x`, se calcula la media como `sum(x) / 3` y la desviación como `sqrt(sum((x − media)²) / 2)`. Los estadísticos se calculan a partir de los valores almacenados en el CSV, cuyo tiempo está redondeado a tres decimales. El tiempo está en segundos; `0.000` indica el redondeo disponible, no un costo nulo. El esfuerzo es el número de nodos expandidos en búsqueda y de evaluaciones de aptitud en el evolutivo.

| `N` | `K` | `M` | Agente | Fichas colocadas | Celdas ocupadas | Tiempo (s) | Esfuerzo |
| ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 4 | 2 | 18 | Búsqueda | 18.00 ± 0.00 | 2.00 ± 0.00 | 0.000 ± 0.000 | 18.00 ± 0.00 |
| 4 | 2 | 18 | Evolutivo | 18.00 ± 0.00 | 2.00 ± 0.00 | 0.505 ± 0.079 | 9704.00 ± 965.19 |
| 4 | 4 | 18 | Búsqueda | 18.00 ± 0.00 | 4.00 ± 0.00 | 0.000 ± 0.000 | 41.00 ± 39.84 |
| 4 | 4 | 18 | Evolutivo | 18.00 ± 0.00 | 4.33 ± 0.58 | 0.458 ± 0.040 | 9083.33 ± 688.33 |
| 4 | 6 | 18 | Búsqueda | 18.00 ± 0.00 | 5.67 ± 0.58 | 0.005 ± 0.009 | 178.00 ± 157.62 |
| 4 | 6 | 18 | Evolutivo | 18.00 ± 0.00 | 7.00 ± 1.00 | 0.385 ± 0.094 | 7809.33 ± 1519.26 |
| 6 | 2 | 40 | Búsqueda | 40.00 ± 0.00 | 2.00 ± 0.00 | 0.016 ± 0.000 | 40.00 ± 0.00 |
| 6 | 2 | 40 | Evolutivo | 40.00 ± 0.00 | 5.33 ± 2.31 | 2.135 ± 0.798 | 12252.00 ± 5104.47 |
| 6 | 4 | 40 | Búsqueda | 40.00 ± 0.00 | 4.00 ± 0.00 | 0.068 ± 0.077 | 353.00 ± 413.68 |
| 6 | 4 | 40 | Evolutivo | 40.00 ± 0.00 | 11.00 ± 0.00 | 1.599 ± 0.033 | 9606.00 ± 196.00 |
| 6 | 6 | 40 | Búsqueda | 40.00 ± 0.00 | 6.00 ± 0.00 | 0.287 ± 0.352 | 1436.67 ± 1636.02 |
| 6 | 6 | 40 | Evolutivo | 40.00 ± 0.00 | 15.33 ± 0.58 | 1.583 ± 0.250 | 10096.00 ± 1671.75 |
| 8 | 2 | 70 | Búsqueda | 70.00 ± 0.00 | 2.00 ± 0.00 | 0.031 ± 0.000 | 70.00 ± 0.00 |
| 8 | 2 | 70 | Evolutivo | 70.00 ± 0.00 | 12.00 ± 2.00 | 5.891 ± 1.752 | 14800.00 ± 4365.13 |
| 8 | 4 | 70 | Búsqueda | 70.00 ± 0.00 | 4.00 ± 0.00 | 0.083 ± 0.077 | 162.33 ± 159.93 |
| 8 | 4 | 70 | Evolutivo | 70.00 ± 0.00 | 23.67 ± 3.51 | 5.797 ± 2.747 | 14506.00 ± 7301.49 |
| 8 | 6 | 70 | Búsqueda | 70.00 ± 0.00 | 6.00 ± 0.00 | 2.781 ± 2.248 | 4028.33 ± 3188.13 |
| 8 | 6 | 70 | Evolutivo | 70.00 ± 0.00 | 32.67 ± 1.53 | 3.891 ± 0.654 | 9671.33 ± 1556.73 |
| 10 | 2 | 110 | Búsqueda | 110.00 ± 0.00 | 2.00 ± 0.00 | 0.141 ± 0.016 | 110.00 ± 0.00 |
| 10 | 2 | 110 | Evolutivo | 110.00 ± 0.00 | 24.33 ± 1.15 | 10.047 ± 0.047 | 9867.33 ± 1209.55 |
| 10 | 4 | 110 | Búsqueda | 110.00 ± 0.00 | 4.00 ± 0.00 | 0.333 ± 0.320 | 255.67 ± 252.30 |
| 10 | 4 | 110 | Evolutivo | 110.00 ± 0.00 | 44.33 ± 1.53 | 10.057 ± 0.009 | 9998.00 ± 294.00 |
| 10 | 6 | 110 | Búsqueda | 110.00 ± 0.00 | 6.33 ± 0.58 | 3.933 ± 5.311 | 2387.67 ± 3188.13 |
| 10 | 6 | 110 | Evolutivo | 110.00 ± 0.00 | 55.33 ± 0.58 | 10.057 ± 0.024 | 10128.67 ± 204.00 |

Las 72 corridas colocaron todas las fichas de su secuencia. En 35 de las 36 corridas, búsqueda alcanzó el piso teórico de ocupación y se detuvo por optimalidad; la restante agotó el tiempo. El evolutivo terminó por estancamiento en 27 corridas y por tiempo en 9 (las nueve instancias de `N = 10`). Alcanzar el límite de tiempo no impidió completar las fichas en estas corridas. El límite es nominal: el evolutivo comprueba el tiempo entre generaciones, por lo que puede excederlo ligeramente.

En esta rejilla ambos agentes completaron las secuencias, pero la búsqueda obtuvo sistemáticamente menos celdas ocupadas y menos tiempo promedio en las 12 configuraciones. El tiempo y esfuerzo de búsqueda varían entre configuraciones y semillas; en `N = 10`, `K = 6`, por ejemplo, una corrida agotó el tiempo mientras las otras dos terminaron antes. El evolutivo usó alrededor de diez mil evaluaciones por corrida y su dispersión entre semillas también muestra sensibilidad a las instancias. Estos resultados son observaciones de esta batería y no prueban que un agente domine en otras rejillas o con otros presupuestos.

## Alcance y limitaciones

Los resultados describen esta rejilla y estos parámetros, no garantizan generalización a otras distribuciones de instancias. Las semillas cambian la secuencia de fichas; la dispersión refleja tanto esa variación de instancia como, para el agente evolutivo, su aleatoriedad de búsqueda. El agente de búsqueda no recibe ventaja por repetir semillas: es determinista para una misma instancia. Un límite de tiempo igual tampoco implica igual cantidad de trabajo, ya que ambos algoritmos tienen costos por operación diferentes.
