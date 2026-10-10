# Agentes de búsqueda y evolutivo para TileUp

Proyecto de Inteligencia Artificial que compara dos agentes para jugar TileUp: un agente de búsqueda por haz (beam search) y un algoritmo evolutivo. Ambos reciben la misma secuencia de fichas y deben decidir dónde colocar cada ficha antes de que el tablero se llene.

## Integrantes

2024154899 - Djedrielle Alexander Vargas

2023135405 - Kristhel Cordero Leiva

## Declaración de uso de inteligencia artificial

Se utilizó un asistente de IA mediante Copilot SDK en VS Code como apoyo para diagnosticar y corregir bugs en el código una vez se ha estado intentando por un periodo considerable de tiempo, con el fin de ahorrar tiempo y evitar atrasos, se usó para preparar una base de la documentación, mas no en la justificación de las decisiones técnicas de los agentes. La base de documentación generada fue alterada posteriormente y adaptada al proyecto. La asistencia incluyó propuestas, arreglo de bugs y edición de documentación.

## TileUp

La instancia define un tablero cuadrado `N × N`, `K` colores y una secuencia de `M` fichas. Cada ficha tiene un color y un valor. Al colocarla en una celda vacía, se combina con las fichas del mismo color que comparten un lado con la celda elegida: sus valores se suman y el resultado queda en la celda elegida. Las demás celdas de la combinación quedan vacías.

La partida termina cuando se colocan las `M` fichas o cuando el tablero se llena antes de colocar toda la secuencia. El objetivo de los agentes es maximizar las fichas colocadas y, a igualdad de cantidad, minimizar las celdas ocupadas al terminar.

El formato de una instancia es texto plano: la primera línea contiene `N K`, la segunda `M` y las siguientes `M` líneas contienen `color valor`. Se ignoran las líneas en blanco y las que empiezan por `#`.

```text
4 3
5
1 2
3 4
1 1
2 3
3 2
```

## Agentes e informe

- **Búsqueda:** búsqueda por haz con ancho creciente.
- **Evolutivo:** algoritmo genético con población de soluciones completas.

La formulación, las decisiones de arquitectura, los parámetros, el diseño del estudio, los resultados y su análisis están documentados en el [informe](Informe.md). La comparación usa instancias comunes a ambos agentes; los resultados por corrida están disponibles en [`comparacion.csv`](src/modulo_adicional/resultados/comparacion.csv).

## Requisitos

- Python 3.9 o posterior.
- No se requieren paquetes externos; se usa la biblioteca estándar de Python.

Clona o descarga este repositorio. En PowerShell, se puede clonar con:

```powershell
git clone https://github.com/KristhelCordero/IA-Tarea.git
cd ./IA-Tarea
```

Los comandos siguientes se ejecutan desde la raíz del repositorio.

## Ejecutar un agente en una instancia

El punto de entrada `src/main.py` resuelve una sola instancia por ejecución. Por defecto ejecuta el agente evolutivo; `--agente busqueda` selecciona el agente de búsqueda:

```powershell
python src/main.py --agente evolutivo --instancia src/modulo_adicional/instancias/N04_K2_s1.txt --salida salidas/solution.txt --semilla 1 --limite-segundos 10
python src/main.py --agente busqueda --instancia src/modulo_adicional/instancias/N04_K2_s1.txt --salida salidas/solution.txt --semilla 1 --limite-segundos 10
```

La solución contiene una línea `índice_ficha fila columna` por cada colocación y un resumen final con las fichas colocadas, las celdas ocupadas y el valor mayor del tablero. Al terminar, `main.py` valida automáticamente el archivo
que acaba de generar contra la instancia indicada y reporta si la solución es válida y si colocó toda la secuencia.

## Validar una solución

También se puede validar cualquier archivo de solución directamente, indicando la instancia con la que se produjo y la ruta de la solución:

```powershell
python src/validator.py --instancia entradas/instancia_01.txt --solucion salidas/solution.txt
```

El validador reproduce las acciones usando la secuencia de la instancia y comprueba los índices, las coordenadas, que cada celda esté libre y que el resumen de la solución coincida con el tablero final. Acepta soluciones válidas incompletas, por ejemplo si el agente agotó su tiempo, e informa cuántas fichas colocó.

## Ejecutar pruebas

```powershell
python -m unittest discover -v
```

Las pruebas unitarias cubren fusiones y reglas básicas del motor. Las pruebas de integración ejecutan ambos agentes desde `main.py` y verifican su validación automática, además de probar el comando independiente del validador. Los archivos siguen el patrón `test*.py` de `unittest` para que también se descubran automáticamente desde VS Code.

## Replicar la comparación experimental

Para comparar el rendimiento de ambos agentes se elaboró una comparación experimental sobre 6 instancias con diferentes valores de `N`, `K` y `M`. Además, por cada instancia se ejecutaron 3 semillas distintas. Los comandos utilizados para realizar la comparación se encuentran en [Informe.md](/Informe.md). Para replicar estas comparaciones se pueden utilizar esos mismos comandos, teniendo en cuenta que se sobreescribiran los archivos originales documentados en el informe. 

## Módulo adicional

El módulo se implementó aunque no era necesario, debido a una situación con el grupo. Se mantiene la implementación como evidencia, pero no se realiza el informe ni el experimento. 

La batería ejecuta **72 corridas** sobre 36 instancias reproducibles: cuatro tamaños de tablero, tres cantidades de colores y tres semillas por cada combinación de `N` y `K`. La cantidad de fichas mantiene una densidad aproximada de `1.1` fichas por celda (`M = round(1.1 × N²)`). Los valores concretos son:

| `N` | `K` | `M` | Semillas |
| ---: | --- | ---: | --- |
| 4 | 2, 4, 6 | 18 | 1, 2, 3 |
| 6 | 2, 4, 6 | 40 | 1, 2, 3 |
| 8 | 2, 4, 6 | 70 | 1, 2, 3 |
| 10 | 2, 4, 6 | 110 | 1, 2, 3 |

Cada semilla define una secuencia de fichas determinista y, por tanto, el mismo archivo de instancia para ambos agentes. Para regenerar las entradas y ejecutar ambos agentes con un límite de 10 segundos por corrida:

```powershell
python src/modulo_adicional/bateria.py generar
python src/modulo_adicional/bateria.py correr --agentes busqueda evolutivo --limite 10 --salida src/modulo_adicional/resultados/comparacion.csv
```

El generador crea los archivos `N{N}_K{K}_s{semilla}.txt` en `src/modulo_adicional/instancias/`. El corredor lee esas mismas entradas para los dos agentes y escribe una fila por agente, instancia y semilla en el CSV. Ese archivo conserva los valores individuales (incluidos tiempo, esfuerzo y motivo de parada) que sustentan los estadísticos del informe. Si se cambia la rejilla, el límite, los parámetros del agente o el equipo de ejecución, se debe volver a generar el CSV y actualizar el informe; el tiempo depende del hardware.

Para ejecutar solo uno de los agentes en todas las instancias, sustituya la lista de agentes, por ejemplo:

```powershell
python src/modulo_adicional/bateria.py correr --agentes busqueda --limite 10 --salida src/modulo_adicional/resultados/busqueda.csv
```

La batería es un estudio independiente del programa principal. Se conserva como material adicional; no se ejecuta al iniciar `main.py`.

## Organización

| Ruta | Contenido |
| --- | --- |
| `src/game.py` | Motor y reglas del juego |
| `src/searchAgent/searchAgent.py` | Agente de búsqueda |
| `src/agente_evolutivo/agent.py` | Agente evolutivo |
| `src/modulo_adicional/generador_instancias.py` | Generador de instancias deterministas |
| `src/modulo_adicional/bateria.py` | Generación de la batería y ejecución comparativa |
| `src/modulo_adicional/instancias/` | Entradas de las 36 corridas experimentales |
| `src/modulo_adicional/resultados/comparacion.csv` | Resultados individuales de la comparación |
| `src/validator.py` | Validador de soluciones |
| `A_Tests/` | Pruebas automatizadas |
| `Informe.md` | Formulación de agentes y estudio experimental |
