# Tarea Corta - Agentes de búsqueda y evolutivos para TileUp

## Integrantes

2000000000 - Djedrielle Alexander Vargas

2023135405 - Kristhel Cordero Leiva

2000000000 - Jose Pablo Sequeira

## Descripción

Proyecto académico de TileUp para trabajar con un motor de juego y agentes que proponen secuencias de colocaciones.

### El juego: TileUp

El juego se lleva a cabo en un tablero cuadrado con `NxN` celdas vacías, en el cual se va colocando una secuencia fija de fichas, cada una compuesta de dos variables: valor y color. Cuando una ficha es colocada y a su lado hay 1 o más fichas, estas se combinan.

Combinar se refiere a sumar sus valores y colocar el resultado en el lugar donde se puso la última ficha, dejando las celdas de las otras fichas del mismo color, colindantes, vacías.

El juego continúa hasta que la secuencia de fichas termina, o que el tablero esté completamente lleno y no se pueda colocar ninguna ficha más. La partida termina con victoria cuando se colocan todas las fichas de la secuencia. Termina con derrota cuando queda al menos una ficha pendiente y el tablero no tiene ninguna celda vacía

#### Implementación



### Agentes

#### Agente de Búsqueda

**TODO:** describir el agente de búsqueda

#### Agente Evolutivo

**TODO:** describir el agente evolutivo

### Componentes

- `src/game.py`: motor del juego.
- `src/generador_instancias.py`: generador reproducible de instancias mediante una semilla.
- `src/validator.py`: validador que determina si la solución de los agentes es válida o no.
- `src/agente_evolutivo/agent.py`: agente evolutivo.
- `src/searchAgent/searchAgent.py`: agente de búsqueda.
- `entradas/`: instancias de ejemplo.
- `salidas/`: soluciones generadas.
- `A_Tests/`: pruebas unitarias del motor y pruebas de integración de los agentes con el juego.

## Replicación

A continuación se describen los pasos para replicar la ejecución de los agentes sobre una instancia del juego de TileUp

### Requisitos

- Python 3.9 o posterior.
- No se requieren paquetes externos.
- Git es necesario para clonar el repositorio.

### Clonación del repositorio

Haciendo uso de github desktop o del siguiente comando de github se puede clonar el repositorio:

```powershell
git clone https://github.com/KristhelCordero/IA-Tarea.git
Set-Location Prueba
```

Los comandos siguientes se ejecutan desde la raíz del proyecto, salvo cuando se indique lo contrario

## Uso

### Generar una instancia

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

#### Ejemplos

```powershell
python src/generador_instancias.py 4 3 8 42
```

Para especificar una ruta de salida:

```powershell
python src/generador_instancias.py 4 3 8 42 entradas/mi_instancia.txt
```

### Ejecutar el motor aleatorio de ejemplo

El ejemplo usa `entradas/instancia_01.txt` y escribe la solución en
`salidas/solution.txt`.

```powershell
cd ./src
python game.py
```

## Ejecutar las pruebas automatizadas

Desde la raíz del proyecto, ejecutar las pruebas unitarias y descubrir las de integración con:

```powershell
python -m unittest discover -s unitTests -p "*Test.py" -v
```

Las pruebas unitarias cubren fusión de dos fichas, fusión de tres o más, colocación sin fusión y detección de derrota. La prueba de integración está preparada pero omitida hasta conectar un agente con el validador.

## TODO

- Corregir y documentar cómo ejecutar el agente evolutivo y el agente de búsqueda sobre instancias de TileUp.
- Implementar la prueba de integración de resolución de una instancia pequeña y validación de la solución.
- Añadir la URL del repositorio remoto.
- Completar la declaración de uso de IA de acuerdo con el trabajo realizado.

## Declaración del Uso de IA

TODO: describir las herramientas de IA utilizadas y el alcance de su uso.
