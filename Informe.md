# Informe: búsqueda y algoritmo evolutivo para TileUp

## Objetivo y criterio de comparación

Se comparan un agente de búsqueda por haz y un algoritmo evolutivo para decidir dónde colocar una secuencia fija de fichas en TileUp. En cada corrida, el criterio del problema es lexicográfico: maximizar las fichas colocadas y, entre resultados con igual cantidad, minimizar las celdas ocupadas al final. El valor mayor del tablero se registra como dato descriptivo, no como criterio de selección.

## Formulación de los agentes

### Agente de búsqueda

Un estado es el tablero después de colocar un prefijo de la secuencia. El nivel del nodo determina cuál es la siguiente ficha, así que los sucesores se obtienen colocando esa ficha en cada celda vacía y aplicando la regla de fusión. Los tableros iguales dentro de un mismo nivel se deduplican. Se expande un haz de ancho acotado y se conservan los estados con menos celdas ocupadas; los empates se resuelven por orden de generación, determinista.

La búsqueda es de ancho creciente: empieza con ancho 1 y multiplica el ancho por 4; 8192 es el umbral configurado para detener nuevas pasadas (por el factor de crecimiento, el último ancho intentable puede ser 16384). La mejor solución
encontrada se conserva entre pasadas. Puede detenerse al alcanzar el límite de tiempo, al probar exhaustivamente una pasada, al llegar al piso teórico de ocupación (un estado final necesita al menos una celda por color presente), o
al alcanzar el ancho máximo. El método es anytime, pero el podado del haz significa que no garantiza encontrar una solución óptima. Su esfuerzo se mide en nodos expandidos: estados a los que se les generaron sucesores.

### Agente evolutivo

Cada individuo es un cromosoma de `M` enteros en `[0, N²−1]`. El gen de cada ficha selecciona, por módulo, una celda de la lista de celdas vacías en orden por fila y columna. La decodificación simula la partida en el motor del juego; por ello, cada individuo produce una secuencia de acciones legales hasta colocar todas las fichas o llenar el tablero.

La aptitud es `colocadas × (N² + 1) − ocupadas`, escalarización que conserva exactamente el orden lexicográfico del objetivo. La población inicial es aleatoria; se usa selección por torneo con reemplazo, cruce de un punto y
mutación por gen. En cada generación se conserva elitistamente a los mejores individuos. Los parámetros por defecto son población 100, élite 2, torneo 3, probabilidad de cruce 0.8, tasa de mutación `1/M`, máximo 300 generaciones y
60 generaciones sin mejora. Es anytime y su esfuerzo se mide por evaluaciones de aptitud. La implementación y sus detalles adicionales están en `src/agente_evolutivo/agent.py`; la del agente de búsqueda está en `src/searchAgent/searchAgent.py`.

## Ejecución y validación de soluciones

`src/main.py` ejecuta el agente seleccionado sobre una instancia y, después de guardar la solución, la valida automáticamente contra esa misma instancia. También se puede validar cualquier pareja de archivos de forma independiente:

```powershell
python src/validator.py --instancia entradas/instancia_01.txt --solucion salidas/solution.txt
```

El comando reutiliza las funciones existentes `processSolution`, `validateSolution` y `compareSummary`; verifica las acciones y el resumen reportado por la solución. Una solución incompleta puede ser válida si el agente se detuvo antes de terminar la secuencia. Los casos y la función `test(files)` se conservan para depuración, pero no se ejecutan al importar ni al ejecutar el validador.

## Diseño experimental y reproducción

Se usó una rejilla factorial de 12 configuraciones `N × K`, con cuatro tamaños de tablero (`N ∈ {4, 6, 8, 10}`), tres cantidades de colores (`K ∈ {2, 4, 6}`) y tres semillas (`1, 2, 3`) por configuración: 36 instancias y 72 corridas de agente. La cantidad de fichas se fija en `M = round(1.1 × N²)` para mantener aproximadamente constante la densidad:
`M = 18, 40, 70, 110`, respectivamente. Cada semilla genera una secuencia determinista de fichas con valores entre 1 y 4 y colores entre 1 y `K`. Ambos agentes reciben exactamente el mismo archivo en cada corrida.

El agente evolutivo usa la semilla de la instancia como semilla del generador aleatorio; la búsqueda es determinista y no depende de ella. Se concedió a cada corrida un límite nominal de 10 segundos. El CSV registra también el motivo de parada para distinguir las corridas que terminan por tiempo de las que llegan a otro criterio. El tiempo medido es dependiente del hardware; las comparaciones de esfuerzo (nodos expandidos frente a evaluaciones de aptitud) son específicas de cada algoritmo y no representan operaciones equivalentes.

Desde la raíz del repositorio, la batería completa se puede regenerar con:

```powershell
python src/modulo_adicional/bateria.py generar
python src/modulo_adicional/bateria.py correr --agentes busqueda evolutivo --limite 10 --salida src/modulo_adicional/resultados/comparacion.csv
```

Las instancias quedan en `src/modulo_adicional/instancias/`. Los resultados individuales por agente, configuración y semilla están en [`comparacion.csv`](src/modulo_adicional/resultados/comparacion.csv). La ejecución de referencia se hizo en Windows con Python 3.12.10.

## Resultados

Cada fila resume la configuración a través de sus tres semillas; las columnas muestran media ± desviación estándar muestral (`n = 3`). El tiempo está en segundos. El esfuerzo es el número de nodos expandidos en búsqueda y de evaluaciones de aptitud en el evolutivo.

| `N` | `K` | `M` | Agente | Fichas colocadas | Celdas ocupadas | Tiempo (s) | Esfuerzo |
| ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 4 | 2 | 18 | Búsqueda | 18.00 ± 0.00 | 2.00 ± 0.00 | 0.000 ± 0.000 | 18.00 ± 0.00 |
| 4 | 2 | 18 | Evolutivo | 18.00 ± 0.00 | 2.00 ± 0.00 | 0.505 ± 0.078 | 9704.00 ± 965.19 |
| 4 | 4 | 18 | Búsqueda | 18.00 ± 0.00 | 4.00 ± 0.00 | 0.000 ± 0.000 | 41.00 ± 39.84 |
| 4 | 4 | 18 | Evolutivo | 18.00 ± 0.00 | 4.33 ± 0.58 | 0.458 ± 0.040 | 9083.33 ± 688.33 |
| 4 | 6 | 18 | Búsqueda | 18.00 ± 0.00 | 5.67 ± 0.58 | 0.005 ± 0.009 | 178.00 ± 157.62 |
| 4 | 6 | 18 | Evolutivo | 18.00 ± 0.00 | 7.00 ± 1.00 | 0.385 ± 0.094 | 7809.33 ± 1519.26 |
| 6 | 2 | 40 | Búsqueda | 40.00 ± 0.00 | 2.00 ± 0.00 | 0.016 ± 0.000 | 40.00 ± 0.00 |
| 6 | 2 | 40 | Evolutivo | 40.00 ± 0.00 | 5.33 ± 2.31 | 2.135 ± 0.800 | 12252.00 ± 5104.47 |
| 6 | 4 | 40 | Búsqueda | 40.00 ± 0.00 | 4.00 ± 0.00 | 0.068 ± 0.079 | 353.00 ± 413.68 |
| 6 | 4 | 40 | Evolutivo | 40.00 ± 0.00 | 11.00 ± 0.00 | 1.599 ± 0.033 | 9606.00 ± 196.00 |
| 6 | 6 | 40 | Búsqueda | 40.00 ± 0.00 | 6.00 ± 0.00 | 0.287 ± 0.354 | 1436.67 ± 1636.02 |
| 6 | 6 | 40 | Evolutivo | 40.00 ± 0.00 | 15.33 ± 0.58 | 1.583 ± 0.250 | 10096.00 ± 1671.75 |
| 8 | 2 | 70 | Búsqueda | 70.00 ± 0.00 | 2.00 ± 0.00 | 0.031 ± 0.000 | 70.00 ± 0.00 |
| 8 | 2 | 70 | Evolutivo | 70.00 ± 0.00 | 12.00 ± 2.00 | 5.891 ± 1.747 | 14800.00 ± 4365.13 |
| 8 | 4 | 70 | Búsqueda | 70.00 ± 0.00 | 4.00 ± 0.00 | 0.083 ± 0.079 | 162.33 ± 159.93 |
| 8 | 4 | 70 | Evolutivo | 70.00 ± 0.00 | 23.67 ± 3.51 | 5.797 ± 2.750 | 14506.00 ± 7301.49 |
| 8 | 6 | 70 | Búsqueda | 70.00 ± 0.00 | 6.00 ± 0.00 | 2.781 ± 2.252 | 4028.33 ± 3188.13 |
| 8 | 6 | 70 | Evolutivo | 70.00 ± 0.00 | 32.67 ± 1.53 | 3.891 ± 0.654 | 9671.33 ± 1556.73 |
| 10 | 2 | 110 | Búsqueda | 110.00 ± 0.00 | 2.00 ± 0.00 | 0.141 ± 0.016 | 110.00 ± 0.00 |
| 10 | 2 | 110 | Evolutivo | 110.00 ± 0.00 | 24.33 ± 1.15 | 10.047 ± 0.047 | 9867.33 ± 1209.55 |
| 10 | 4 | 110 | Búsqueda | 110.00 ± 0.00 | 4.00 ± 0.00 | 0.333 ± 0.324 | 255.67 ± 252.30 |
| 10 | 4 | 110 | Evolutivo | 110.00 ± 0.00 | 44.33 ± 1.53 | 10.057 ± 0.009 | 9998.00 ± 294.00 |
| 10 | 6 | 110 | Búsqueda | 110.00 ± 0.00 | 6.33 ± 0.58 | 3.933 ± 5.308 | 2387.67 ± 3188.13 |
| 10 | 6 | 110 | Evolutivo | 110.00 ± 0.00 | 55.33 ± 0.58 | 10.057 ± 0.023 | 10128.67 ± 204.00 |

Las 72 corridas colocaron todas las fichas de su secuencia. En 35 de las 36 corridas, búsqueda alcanzó el piso teórico de ocupación y se detuvo por optimalidad; la restante agotó el tiempo. El evolutivo terminó por estancamiento en 27 corridas y por tiempo en 9 (las nueve instancias de `N = 10`). Alcanzar el límite de tiempo no impidió completar las fichas en estas corridas. El límite es nominal: el evolutivo comprueba el tiempo entre generaciones, por lo que puede excederlo ligeramente.

En esta rejilla ambos agentes completaron las secuencias, pero la búsqueda obtuvo sistemáticamente menos celdas ocupadas y menos tiempo promedio en las 12 configuraciones. El tiempo y esfuerzo de búsqueda varían entre configuraciones y semillas; en `N = 10`, `K = 6`, por ejemplo, una corrida agotó el tiempo mientras las otras dos terminaron antes. El evolutivo usó alrededor de diez mil evaluaciones por corrida y su dispersión entre semillas también muestra sensibilidad a las instancias. Estos resultados son observaciones de esta batería y no prueban que un agente domine en otras rejillas o con otros presupuestos.

## Alcance y limitaciones

Los resultados describen esta rejilla y estos parámetros, no garantizan generalización a otras distribuciones de instancias. Las semillas cambian la secuencia de fichas; la dispersión refleja tanto esa variación de instancia como, para el agente evolutivo, su aleatoriedad de búsqueda. El agente de búsqueda no recibe ventaja por repetir semillas: es determinista para una misma instancia. Un límite de tiempo igual tampoco implica igual cantidad de trabajo, ya que ambos algoritmos tienen costos por operación diferentes.
