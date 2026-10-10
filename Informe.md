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

## Comparación experimental

Los agentes se ejecutaron sobre 6 configuraciones distintas con 3 semillas distintas. Las instancias se encuentran en la carpeta `/entradas`. Se utilizaron las instancias de la 2 a la 7 y todos los resultados se encuentran en la carpeta `/salidas`

Las semillas utilizadas fueron:
- S1 = 58
- S2 = 24
- S3 = 99

Las medidas de esfuerzo elegidas, propias de cada agente son:
- Evolutivo: Evaluaciones de aptitud 
- Búsqueda: Nodos expandidos

### 1ra configuración

#### Comandos

```powershell
#Semilla 1
python src/main.py --agente evolutivo --instancia entradas/instancia_02.txt --salida salidas/instancia_02_AE_S1.txt --semilla 58 --limite-segundos 10
python src/main.py --agente busqueda --instancia entradas/instancia_02.txt --salida salidas/instancia_02_AB_S1.txt --semilla 58 --limite-segundos 10

#Semilla 2
python src/main.py --agente evolutivo --instancia entradas/instancia_02.txt --salida salidas/instancia_02_AE_S2.txt --semilla 24 --limite-segundos 10
python src/main.py --agente busqueda --instancia entradas/instancia_02.txt --salida salidas/instancia_02_AB_S2.txt --semilla 24 --limite-segundos 10


#Semilla 3
python src/main.py --agente evolutivo --instancia entradas/instancia_02.txt --salida salidas/instancia_02_AE_S3.txt --semilla 99 --limite-segundos 10
python src/main.py --agente busqueda --instancia entradas/instancia_02.txt --salida salidas/instancia_02_AB_S3.txt  --semilla 99 --limite-segundos 10
```

#### Inputs 

`entradas/instancia_02`

#### Outputs

```text
salidas/instancia_02_AE_S1.txt 
salidas/instancia_02_AE_S2.txt 
salidas/instancia_02_AE_S3.txt 

salidas/instancia_02_AB_S1.txt 
salidas/instancia_02_AB_S2.txt 
salidas/instancia_02_AB_S3.txt 
```

### 2da configuración

#### Comandos

```powershell
#Semilla 1
python src/main.py --agente evolutivo --instancia entradas/instancia_03.txt --salida salidas/instancia_03_AE_S1.txt --semilla 58 --limite-segundos 10
python src/main.py --agente busqueda --instancia entradas/instancia_03.txt --salida salidas/instancia_03_AB_S1.txt --semilla 58 --limite-segundos 10

#Semilla 2
python src/main.py --agente evolutivo --instancia entradas/instancia_03.txt --salida salidas/instancia_03_AE_S2.txt --semilla 24 --limite-segundos 10
python src/main.py --agente busqueda --instancia entradas/instancia_03.txt --salida salidas/instancia_03_AB_S2.txt --semilla 24 --limite-segundos 10

#Semilla 3
python src/main.py --agente evolutivo --instancia entradas/instancia_03.txt --salida salidas/instancia_03_AE_S3.txt --semilla 99 --limite-segundos 10
python src/main.py --agente busqueda --instancia entradas/instancia_03.txt --salida salidas/instancia_03_AB_S3.txt  --semilla 99 --limite-segundos 10
```

#### Inputs 

`entradas/instancia_03`

#### Outputs

```text
salidas/instancia_03_AE_S1.txt 
salidas/instancia_03_AE_S2.txt 
salidas/instancia_03_AE_S3.txt 

salidas/instancia_03_AB_S1.txt 
salidas/instancia_03_AB_S2.txt 
salidas/instancia_03_AB_S3.txt 
```

### 3ra configuración

#### Comandos

```powershell
#Semilla 1
python src/main.py --agente evolutivo --instancia entradas/instancia_04.txt --salida salidas/instancia_04_AE_S1.txt --semilla 58 --limite-segundos 10
python src/main.py --agente busqueda --instancia entradas/instancia_04.txt --salida salidas/instancia_04_AB_S1.txt --semilla 58 --limite-segundos 10

#Semilla 2
python src/main.py --agente evolutivo --instancia entradas/instancia_04.txt --salida salidas/instancia_04_AE_S2.txt --semilla 24 --limite-segundos 10
python src/main.py --agente busqueda --instancia entradas/instancia_04.txt --salida salidas/instancia_04_AB_S2.txt --semilla 24 --limite-segundos 10


#Semilla 3
python src/main.py --agente evolutivo --instancia entradas/instancia_04.txt --salida salidas/instancia_04_AE_S3.txt --semilla 99 --limite-segundos 10
python src/main.py --agente busqueda --instancia entradas/instancia_04.txt --salida salidas/instancia_04_AB_S3.txt  --semilla 99 --limite-segundos 10
```

#### Inputs 

`entradas/instancia_04`

#### Outputs

```text
salidas/instancia_04_AE_S1.txt 
salidas/instancia_04_AE_S2.txt 
salidas/instancia_04_AE_S3.txt 

salidas/instancia_04_AB_S1.txt 
salidas/instancia_04_AB_S2.txt 
salidas/instancia_04_AB_S3.txt 
```

### 4ta configuración

#### Comandos

```powershell
#Semilla 1
python src/main.py --agente evolutivo --instancia entradas/instancia_05.txt --salida salidas/instancia_05_AE_S1.txt --semilla 58 --limite-segundos 10
python src/main.py --agente busqueda --instancia entradas/instancia_05.txt --salida salidas/instancia_05_AB_S1.txt --semilla 58 --limite-segundos 10

#Semilla 2
python src/main.py --agente evolutivo --instancia entradas/instancia_05.txt --salida salidas/instancia_05_AE_S2.txt --semilla 24 --limite-segundos 10
python src/main.py --agente busqueda --instancia entradas/instancia_05.txt --salida salidas/instancia_05_AB_S2.txt --semilla 24 --limite-segundos 10


#Semilla 3
python src/main.py --agente evolutivo --instancia entradas/instancia_05.txt --salida salidas/instancia_05_AE_S3.txt --semilla 99 --limite-segundos 10
python src/main.py --agente busqueda --instancia entradas/instancia_05.txt --salida salidas/instancia_05_AB_S3.txt  --semilla 99 --limite-segundos 10
```

#### Inputs 

`entradas/instancia_05`

#### Outputs

```text
salidas/instancia_05_AE_S1.txt 
salidas/instancia_05_AE_S2.txt 
salidas/instancia_05_AE_S3.txt 

salidas/instancia_05_AB_S1.txt 
salidas/instancia_05_AB_S2.txt 
salidas/instancia_05_AB_S3.txt 
```

### 5ta configuración

#### Comandos

```powershell
#Semilla 1
python src/main.py --agente evolutivo --instancia entradas/instancia_06.txt --salida salidas/instancia_06_AE_S1.txt --semilla 58 --limite-segundos 10
python src/main.py --agente busqueda --instancia entradas/instancia_06.txt --salida salidas/instancia_06_AB_S1.txt --semilla 58 --limite-segundos 10

#Semilla 2
python src/main.py --agente evolutivo --instancia entradas/instancia_06.txt --salida salidas/instancia_06_AE_S2.txt --semilla 24 --limite-segundos 10
python src/main.py --agente busqueda --instancia entradas/instancia_06.txt --salida salidas/instancia_06_AB_S2.txt --semilla 24 --limite-segundos 10


#Semilla 3
python src/main.py --agente evolutivo --instancia entradas/instancia_06.txt --salida salidas/instancia_06_AE_S3.txt --semilla 99 --limite-segundos 10
python src/main.py --agente busqueda --instancia entradas/instancia_06.txt --salida salidas/instancia_06_AB_S3.txt  --semilla 99 --limite-segundos 10
```

#### Inputs 

`entradas/instancia_06`

#### Outputs

```text
salidas/instancia_06_AE_S1.txt 
salidas/instancia_06_AE_S2.txt 
salidas/instancia_06_AE_S3.txt 

salidas/instancia_06_AB_S1.txt 
salidas/instancia_06_AB_S2.txt 
salidas/instancia_06_AB_S3.txt 
```

### 6ta configuración

#### Comandos

```powershell
#Semilla 1
python src/main.py --agente evolutivo --instancia entradas/instancia_07.txt --salida salidas/instancia_07_AE_S1.txt --semilla 58 --limite-segundos 10
python src/main.py --agente busqueda --instancia entradas/instancia_07.txt --salida salidas/instancia_07_AB_S1.txt --semilla 58 --limite-segundos 10

#Semilla 2
python src/main.py --agente evolutivo --instancia entradas/instancia_07.txt --salida salidas/instancia_07_AE_S2.txt --semilla 24 --limite-segundos 10
python src/main.py --agente busqueda --instancia entradas/instancia_07.txt --salida salidas/instancia_07_AB_S2.txt --semilla 24 --limite-segundos 10


#Semilla 3
python src/main.py --agente evolutivo --instancia entradas/instancia_07.txt --salida salidas/instancia_07_AE_S3.txt --semilla 99 --limite-segundos 10
python src/main.py --agente busqueda --instancia entradas/instancia_07.txt --salida salidas/instancia_07_AB_S3.txt  --semilla 99 --limite-segundos 10
```

#### Inputs 

`entradas/instancia_07`

#### Outputs

```text
salidas/instancia_07_AE_S1.txt 
salidas/instancia_07_AE_S2.txt 
salidas/instancia_07_AE_S3.txt 

salidas/instancia_07_AB_S1.txt 
salidas/instancia_07_AB_S2.txt 
salidas/instancia_07_AB_S3.txt 
```

### Matriz de Resultados

| Configuración | Agente | Semilla | Instancia | Cantidad de fichas colocadas | Celdas ocupadas | Tiempo de cómputo | Medida de Esfuerzo | Esfuerzo |
|---|-----------|----|--------------|----|---|--------|-------------------------|-|
| 1 | evolutivo | 58 | instancia_02 | 22 | 7 | 1.193s | Evaluaciones de aptitud | 8822 |
| 1 | búsqueda  | 58 | instancia_02 | 22 | 4 | 0.004s | Nodos expandidos | 22 |
| 1 | evolutivo | 24 | instancia_02 | 22 | 7 | 0.821s | Evaluaciones de aptitud | 7646 |
| 1 | búsqueda  | 24 | instancia_02 | 22 | 4 | 0.002s | Nodos expandidos | 22 |
| 1 | evolutivo | 99 | instancia_02 | 22 | 7 | 0.746s | Evaluaciones de aptitud | 8136 |
| 1 | búsqueda  | 99 | instancia_02 | 22 | 4 | 0.002s | Nodos expandidos | 22 |
| 2 | evolutivo | 58 | instancia_03 | 25 | 2 | 0.613s | Evaluaciones de aptitud | 6372 |
| 2 | búsqueda  | 58 | instancia_03 | 25 | 2 | 0.001s | Nodos expandidos | 25 |
| 2 | evolutivo | 24 | instancia_03 | 25 | 2 | 0.343s | Evaluaciones de aptitud | 5980 |
| 2 | búsqueda  | 24 | instancia_03 | 25 | 2 | 0.001s | Nodos expandidos | 25 |
| 2 | evolutivo | 99 | instancia_03 | 25 | 2 | 0.527s | Evaluaciones de aptitud | 6274 |
| 2 | búsqueda  | 99 | instancia_03 | 25 | 2 | 0.001s | Nodos expandidos | 25 |
| 3 | evolutivo | 58 | instancia_04 | 28 | 8 | 2.747s | Evaluaciones de aptitud | 15290 |
| 3 | búsqueda  | 58 | instancia_04 | 28 | 3 | 0.005s | Nodos expandidos | 28 |
| 3 | evolutivo | 24 | instancia_04 | 28 | 10 | 1.251s | Evaluaciones de aptitud | 7842 |
| 3 | búsqueda  | 24 | instancia_04 | 28 | 3 | 0.006s | Nodos expandidos | 28 |
| 3 | evolutivo | 99 | instancia_04 | 28 | 7 | 1.280s | Evaluaciones de aptitud | 8430 |
| 3 | búsqueda  | 99 | instancia_04 | 28 | 3 | 0.005s | Nodos expandidos | 28 |
| 4 | evolutivo | 58 | instancia_05 | 26 | 3 | 1.098s | Evaluaciones de aptitud | 7058 |
| 4 | búsqueda  | 58 | instancia_05 | 26 | 2 | 0.001s | Nodos expandidos | 26 |
| 4 | evolutivo | 24 | instancia_05 | 26 | 3 | 1.012s | Evaluaciones de aptitud | 6764 |
| 4 | búsqueda  | 24 | instancia_05 | 26 | 2 | 0.001s | Nodos expandidos | 26 |
| 4 | evolutivo | 99 | instancia_05 | 26 | 2 | 1.006s | Evaluaciones de aptitud | 10684 |
| 4 | búsqueda  | 99 | instancia_05 | 26 | 2 | 0.001s | Nodos expandidos | 26 |
| 5 | evolutivo | 58 | instancia_06 | 70 | 30 | 8.915s | Evaluaciones de aptitud | 18916 |
| 5 | búsqueda  | 58 | instancia_06 | 70 | 6 | 0.170s | Nodos expandidos | 347 |
| 5 | evolutivo | 24 | instancia_06 | 70 | 31 | 6.110s | Evaluaciones de aptitud | 13918 |
| 5 | búsqueda  | 24 | instancia_06 | 70 | 6 | 0.170s | Nodos expandidos | 347 |
| 5 | evolutivo | 99 | instancia_06 | 70 | 31 | 5.885s | Evaluaciones de aptitud | 11860 |
| 5 | búsqueda  | 99 | instancia_06 | 70 | 6 | 0.223s | Nodos expandidos | 347 |
| 6 | evolutivo | 58 | instancia_07 | 110 | 56 | 10.050s | Evaluaciones de aptitud | 9802 |
| 6 | búsqueda  | 58 | instancia_07 | 110 | 6 | 0.600s | Nodos expandidos | 547 |
| 6 | evolutivo | 24 | instancia_07 | 110 | 55 | 10.001s | Evaluaciones de aptitud | 10488 |
| 6 | búsqueda  | 24 | instancia_07 | 110 | 6 | 0.590s | Nodos expandidos | 547 |
| 6 | evolutivo | 99 | instancia_07 | 110 | 61 | 10.003s | Evaluaciones de aptitud | 10586 |
| 6 | búsqueda  | 99 | instancia_07 | 110 | 6 | 0.597s | Nodos expandidos | 547 |

## Conclusiones

### Resultado principal

En las 18 corridas (6 configuraciones × 3 semillas) **ambos agentes colocaron siempre la secuencia completa**. El primer criterio del objetivo, maximizar las fichas colocadas, nunca llegó a discriminar: ninguna instancia del conjunto produjo una derrota. Toda la comparación quedó decidida por el segundo criterio, la ocupación final.

Bajo ese criterio, **el agente de búsqueda alcanzó el piso teórico en las seis configuraciones**. Como una solución completa no puede ocupar menos de una celda por color presente en la secuencia, y en cada configuración la ocupación obtenida coincide exactamente con el número de colores, esos resultados no son solo los mejores observados: son demostrablemente óptimos para ambos criterios del objetivo. El agente evolutivo igualó ese piso únicamente en la configuración 2 y en una de las tres semillas de la configuración 4.

| Config. | Instancia | N | K | M | Piso | Evolutivo (3 semillas) | Desv. | Búsqueda | Brecha |
|---|---|---|---|---|---|---|---|---|---|
| 2 | instancia_03 | 3 | 2 | 25 | 2 | 2, 2, 2 | 0.00 | **2** | 0.0 |
| 4 | instancia_05 | 4 | 2 | 26 | 2 | 3, 3, 2 | 0.58 | **2** | 0.7 |
| 1 | instancia_02 | 5 | 4 | 22 | 4 | 7, 7, 7 | 0.00 | **4** | 3.0 |
| 3 | instancia_04 | 6 | 3 | 28 | 3 | 8, 10, 7 | 1.53 | **3** | 5.3 |
| 5 | instancia_06 | 8 | 6 | 70 | 6 | 30, 31, 31 | 0.58 | **6** | 24.7 |
| 6 | instancia_07 | 10 | 6 | 110 | 6 | 56, 55, 61 | 3.21 | **6** | 51.3 |

### Cómo escala la diferencia

Ordenadas por tamaño de tablero, las configuraciones muestran que **la brecha entre ambos agentes crece de forma monótona con N**: es nula en el tablero de 3×3, llega a 5.3 celdas en el de 6×6 y a 51.3 en el de 10×10. El agente de búsqueda mantiene la calidad óptima en todo el rango, de modo que la degradación observada es enteramente atribuible al agente evolutivo.

La dispersión entre semillas sigue el mismo patron. El agente de búsqueda es determinista y la semilla no altera su salida, por lo que su desviación es cero en todas las configuraciones. La del evolutivo pasa de 0.00 en las instancias pequeñas a 3.21 en la mayor: al crecer el espacio, no solo empeora su resultado medio sino que se vuelve menos predecible.

Conviene señalar que en la configuración 6 el evolutivo se detuvo por límite de tiempo (10.05 s, 10.00 s y 10.00 s contra un tope de 10 s), no por convergencia. En las cinco configuraciones restantes se detuvo por estancamiento. Su resultado en la instancia mayor es, por lo tanto, el mejor alcanzado dentro del presupuesto, no el valor al que habría convergido.

### Interpretación

La explicación más consistente con los datos es que el problema tiene una **estructura secuencial fuerte** que la búsqueda constructiva aprovecha de forma directa y la representación del evolutivo no conserva.

El agente de búsqueda decide una ficha a la vez con el tablero real a la vista: cada sucesor refleja el efecto exacto de una colocación, incluida la fusión, y el orden por ocupación selecciona inmediatamente las jugadas que fusionan. La deduplicación por nivel y el piso teórico como certificado completan el mecanismo.

El evolutivo, en cambio, opera sobre un genotipo cuya interpretación depende del historial completo: el gen de la ficha *i* indexa la lista de celdas libres **en ese instante**, de modo que alterar un gen temprano cambia el significado de todos los posteriores. Esa baja localidad hace que el cruce y la mutacion produzcan descendientes cuyo fenotipo guarda poca relacion con el de sus progenitores, y la recombinación pierde buena parte de su capacidad de combinar material útil. La representación garantiza legalidad sin reparación --su ventaja de diseño-- pero lo hace a costa de la propiedad que un algoritmo genético necesita para explotar soluciones parciales buenas.

### Costo computacional

Las medidas de esfuerzo de ambos agentes no son directamente comparables: una evaluación de aptitud simula una partida completa de M colocaciones, mientras que una expansión de nodo genera a lo sumo N² sucesores de una sola colocación cada uno. Normalizando ambas a colocaciones simuladas, el evolutivo realiza entre **21 y 690 veces más trabajo** que la búsqueda, según la configuración.

Esa relacion es consistente con los tiempos medidos, de 17× a 1039× a favor de la búsqueda. El factor se comprime en las instancias grandes por dos motivos: el costo por nivel del haz crece con N², y el tiempo del evolutivo queda artificialmente acotado por el límite de 10 segundos.

### Una inversión respecto de lo esperado

El planteo de la tarea anticipa que el agente de búsqueda deje de terminar dentro del límite de tiempo al crecer el problema. En este estudio ocurrió lo contrario: la búsqueda resolvió la instancia mayor en 0.6 segundos, mientras que el evolutivo agotó el presupuesto completo.

Esto es consecuencia directa de la elección de algoritmo. Una búsqueda exhaustiva o con garantía de optimalidad --BFS, costo uniforme o A*-- si habría explotado: el árbol tiene del orden de 10¹²⁶ hojas en la instancia de 8×8. La búsqueda por haz renuncia a esa garantía a cambio de un costo acotado por `ancho × celdas × M`, que es polinómico. El resultado es un agente que no solo termina siempre, sino que además alcanzó el óptimo en todos los casos probados; el precio es que no puede certificar optimalidad salvo cuando llega al piso teórico, como ocurrió aquí.

### Limitaciones del estudio

Tres advertencias acotan el alcance de estas conclusiones.

El motor fusiona únicamente los vecinos inmediatos de igual color, no la componente conexa completa descrita en la especificación. Ambos agentes comparten esa misma implementacion, de modo que la comparación entre ellos es válida, pero las ocupaciones absolutas corresponden a esa variante de las reglas.

Ninguna de las instancias produjo una derrota, por lo que el criterio dominante del objetivo quedó sin ejercitar. Determinar cuál agente degrada mejor cuando el tablero se llena requeriría instancias con secuencias construidas de forma adversarial, alternando colores para impedir la formacion de adyacencias; la sola densidad de fichas no basta, porque una celda absorbe sin límite fichas del mismo color.

Por último, los parámetros del evolutivo se fijaron mediante barridos documentados, mientras que la programación de anchos del agente de búsqueda se adoptó sin un barrido equivalente. Dado que la búsqueda ya alcanza el óptimo demostrable en todo el conjunto, afinarla no cambiaría los resultados, pero si podria reducir aún más sus tiempos.
