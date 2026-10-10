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

TODO