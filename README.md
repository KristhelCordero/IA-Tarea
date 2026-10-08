# Tarea Corta - Agentes de búsqueda y evolutivos para TileUp

## Integrantes

2000000000 - Djedrielle Alexander Vargas

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

**TODO:** describir el agente evolutivo

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
