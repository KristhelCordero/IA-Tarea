import sys
import os
from dataclasses import dataclass, replace
import random
import time
import statistics

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from game import createBoard, action, isInputFileValid

RAIZ = os.path.join(os.path.dirname(__file__), '..', '..')

n = 5
cromo_prueba = [5, 0, 4, 3, 1]
fichas = [(1,2), (4,2), (1,4), (6,9), (3,2)]

@dataclass
class Individuo:
    cromosoma: list[int]
    aptitud: int

@dataclass
class Resultado:
    colocaciones: list[tuple[int, int]]  # (fila, col) por ficha, en orden
    colocadas: int                       # == len(colocaciones)
    ocupadas: int
    mayor: int

@dataclass
class Params:
    tam_poblacion: int = 100
    tam_elite: int = 2
    tam_torneo: int = 3          # controla la presion selectiva (ojo: NO es el K de la instancia)
    prob_cruce: float = 0.8
    tasa: float = None           # None -> 1/M, una mutacion por cromosoma en promedio
    max_generaciones: int = 300
    max_sin_mejora: int = 60     # por encima del mayor intervalo entre mejoras medido (46)
    limite_seg: float = 10.0

@dataclass
class Metricas:
    evaluaciones: int            # medida de esfuerzo del algoritmo
    generaciones: int
    tiempo: float                # segundos
    motivo_paro: str             # "generaciones" | "tiempo" | "estancamiento"
    curva: list[int]             # mejor aptitud al cierre de cada generacion

def celdas_vacias(tablero):
    """Celdas libres del tablero, en orden row-major (por fila, luego por columna).

    El orden es canónico y determinista: la decodificación indexa sobre esta
    lista, así que si el orden variara entre ejecuciones el agente dejaría de
    ser reproducible con la misma semilla.
    """
    return [(i, j)
            for i, fila in enumerate(tablero)
            for j, celda in enumerate(fila)
            if celda[0] == 0]

def decodificar(cromosoma, n, fichas):
    tablero = createBoard(n)
    colocaciones = []
    for i, ficha in enumerate(fichas):
        vacias = celdas_vacias(tablero)
        # Verificar si vacias esta vacia, si es asi, entonces perdimos
        if (len(vacias) == 0): break
        elegida = vacias[cromosoma[i] % len(vacias)]
        tablero = action(ficha, elegida, tablero)
        colocaciones.append(elegida)
    
    ocupadas = sum(1 for row in tablero for cell in row if cell[0] != 0)
    mayor = max(cell[1] for row in tablero for cell in row)

    return Resultado(colocaciones = colocaciones, colocadas = len(colocaciones), ocupadas = ocupadas, mayor = mayor)

def aptitud(resultado, n):
    return resultado.colocadas * (n*n + 1) - resultado.ocupadas

def crear_cromosoma(rng, m, n):
    cromosoma = []
    for _ in range(m):
        cromosoma.append(rng.randint(0, n*n - 1))
    return cromosoma

def busqueda_aleatoria(n, fichas, rng, num_muestras):
    if (num_muestras <= 0): return None
    individuos = []
    for _ in range(num_muestras):
        cromosoma = crear_cromosoma(rng, len(fichas), n)
        apt = aptitud(decodificar(cromosoma, n, fichas), n)
        individuos.append(Individuo(cromosoma = cromosoma, aptitud = apt))
    return max(individuos, key=lambda i: i.aptitud)

def crear_poblacion_inicial(rng, tam_poblacion, n, fichas):
    if (tam_poblacion <= 0): return None
    poblacion = []
    for _ in range(tam_poblacion):
        cromosoma = crear_cromosoma(rng, len(fichas), n)
        apt = aptitud(decodificar(cromosoma, n, fichas), n)
        poblacion.append(Individuo(cromosoma = cromosoma, aptitud = apt))
    return poblacion

def seleccion_torneo(poblacion, k, rng):
    # Seleccion con reemplazo de la poblacion
    indices = []
    seleccionados = []
    for _ in range(k):
        indices.append(rng.randint(0, len(poblacion) - 1))
    for i in indices:
        seleccionados.append(poblacion[i])
    return max(seleccionados, key=lambda i: i.aptitud)

def cruce_un_punto(cromosoma_padre1, cromosoma_padre2, rng):
    punto_corte = rng.randint(1, len(cromosoma_padre1) - 1)
    return (cromosoma_padre1[:punto_corte]+cromosoma_padre2[punto_corte:], cromosoma_padre2[:punto_corte]+cromosoma_padre1[punto_corte:])

def mutacion(cromosoma, tasa, n, rng):
    copia_cromosoma = list(cromosoma)
    for i, gen in enumerate(copia_cromosoma):
        if (rng.random() < tasa):
            copia_cromosoma[i] = rng.randint(0, n*n - 1)
    return copia_cromosoma

def reemplazo(poblacion, hijos, tam_elite):
    poblacion.sort(key=lambda i: i.aptitud, reverse=True)
    reemplazo = poblacion[:tam_elite] + hijos
    if (len(reemplazo) > len(poblacion)): reemplazo = reemplazo[:len(poblacion)]
    return reemplazo

def evolucionar(n, fichas, rng, params):
    inicio = time.monotonic()
    vencimiento = inicio + params.limite_seg
    tasa = params.tasa if params.tasa is not None else 1 / len(fichas)

    poblacion = crear_poblacion_inicial(rng, params.tam_poblacion, n, fichas)
    evaluaciones = params.tam_poblacion
    mejor = max(poblacion, key=lambda i: i.aptitud)
    curva = [mejor.aptitud]
    sin_mejora = 0
    generaciones = 0

    while True:
        # Los tres criterios van por separado para poder informar cual fue el que corto
        if (generaciones >= params.max_generaciones):
            motivo_paro = "generaciones"
            break
        if (time.monotonic() >= vencimiento):
            motivo_paro = "tiempo"
            break
        if (sin_mejora >= params.max_sin_mejora):
            motivo_paro = "estancamiento"
            break

        hijos = []
        while (len(hijos) < len(poblacion) - params.tam_elite):
            padre1 = seleccion_torneo(poblacion, params.tam_torneo, rng)
            padre2 = seleccion_torneo(poblacion, params.tam_torneo, rng)
            if (rng.random() < params.prob_cruce):
                cromo1, cromo2 = cruce_un_punto(padre1.cromosoma, padre2.cromosoma, rng)
            else:
                cromo1 = padre1.cromosoma
                cromo2 = padre2.cromosoma
            cromo1 = mutacion(cromo1, tasa, n, rng)
            cromo2 = mutacion(cromo2, tasa, n, rng)
            # Obtener la aptitud
            hijos.append(Individuo(cromosoma = cromo1, aptitud = aptitud(decodificar(cromo1, n, fichas), n)))
            hijos.append(Individuo(cromosoma = cromo2, aptitud = aptitud(decodificar(cromo2, n, fichas), n)))
            evaluaciones += 2

        poblacion = reemplazo(poblacion, hijos, params.tam_elite)
        generaciones += 1

        nuevo_mejor = max(poblacion, key=lambda i: i.aptitud)
        if (nuevo_mejor.aptitud > mejor.aptitud):
            mejor = nuevo_mejor
            sin_mejora = 0
        else:
            sin_mejora += 1
        curva.append(mejor.aptitud)

    metricas = Metricas(evaluaciones = evaluaciones, generaciones = generaciones, tiempo = time.monotonic() - inicio, motivo_paro = motivo_paro, curva = curva)
    return mejor, metricas

def escribir_solucion(path, resultado):
    """Escribe la solucion en el formato del enunciado: una linea por colocacion
    con 'indice fila columna', y una linea final de resumen que empieza con #.

    Se escribe igual en derrota, con las colocaciones que alcanzo a realizar
    (requisito 3 del enunciado).
    """
    carpeta = os.path.dirname(path)
    if (carpeta): os.makedirs(carpeta, exist_ok = True)
    with open(path, 'w') as archivo:
        for indice, (fila, columna) in enumerate(resultado.colocaciones):
            archivo.write(f"{indice} {fila} {columna}\n")
        archivo.write(f"# colocadas={resultado.colocadas} ocupadas={resultado.ocupadas} mayor={resultado.mayor}\n")

def informar_metricas(resultado, metricas):
    """Informa por salida estandar lo que pide el requisito 6 del enunciado.

    Formato clave=valor, una por linea, para que la bateria de experimentos de
    la fase E pueda parsearlo sin trabajo extra.
    """
    print(f"colocadas={resultado.colocadas}")
    print(f"ocupadas={resultado.ocupadas}")
    print(f"mayor={resultado.mayor}")
    print(f"tiempo={metricas.tiempo:.3f}")
    print(f"evaluaciones={metricas.evaluaciones}")
    print(f"generaciones={metricas.generaciones}")
    print(f"motivo_paro={metricas.motivo_paro}")

def resolver(n, k, fichas, rng, limite_seg, path_salida = None, params = None):
    """Punto de entrada del agente evolutivo.

    'k' es la cantidad de colores de la instancia. El AE no la usa (el
    decodificador no necesita conocerla); esta en la firma para que coincida
    con la del agente de busqueda y el CLI pueda intercambiarlos.
    """
    if (params is None): params = Params()
    params = replace(params, limite_seg = limite_seg)

    mejor, metricas = evolucionar(n, fichas, rng, params)
    resultado = decodificar(mejor.cromosoma, n, fichas)

    if (path_salida is None):
        path_salida = os.path.join(RAIZ, 'salidas', 'solution.txt')
    escribir_solucion(path_salida, resultado)
    informar_metricas(resultado, metricas)
    return resultado, metricas

# ---------------------------------------------------------------------------
# Banco de pruebas: correr el agente, medir y calibrar parametros.
# Nada de esto forma parte del agente; es la herramienta de la fase experimental.
# ---------------------------------------------------------------------------

@dataclass
class Corrida:
    semilla: int
    aptitud: int
    colocadas: int
    total_fichas: int
    ocupadas: int
    mayor: int
    evaluaciones: int
    generaciones: int
    tiempo: float
    motivo_paro: str

def cargar_instancia(path):
    """Lee una instancia y devuelve (n, k, fichas)."""
    valido, nk, cant, fichas = isInputFileValid(path)
    if (not valido): raise ValueError(f"instancia mal formada: {path}")
    return nk[0], nk[1], fichas

def correr(n, fichas, semilla, params):
    """Una corrida del AE con una semilla. No escribe archivos, para poder
    repetirla miles de veces sin tocar salidas/."""
    mejor, metricas = evolucionar(n, fichas, random.Random(semilla), params)
    resultado = decodificar(mejor.cromosoma, n, fichas)
    return Corrida(semilla = semilla,
                   aptitud = mejor.aptitud,
                   colocadas = resultado.colocadas,
                   total_fichas = len(fichas),
                   ocupadas = resultado.ocupadas,
                   mayor = resultado.mayor,
                   evaluaciones = metricas.evaluaciones,
                   generaciones = metricas.generaciones,
                   tiempo = metricas.tiempo,
                   motivo_paro = metricas.motivo_paro)

def resumir(corridas, campo = "aptitud"):
    """(media, desviacion, minimo, maximo) de un campo a lo largo de las semillas."""
    valores = [getattr(c, campo) for c in corridas]
    desv = statistics.stdev(valores) if len(valores) > 1 else 0.0
    return statistics.mean(valores), desv, min(valores), max(valores)

def experimento(path_instancia, params = None, semillas = (1, 2, 3), verboso = True):
    """Corre el AE sobre una instancia con varias semillas.

    El enunciado exige reportar los resultados con su dispersion entre semillas,
    no como un numero unico; por eso el minimo son tres semillas.
    """
    if (params is None): params = Params()
    n, k, fichas = cargar_instancia(path_instancia)
    corridas = [correr(n, fichas, s, params) for s in semillas]

    if (verboso):
        print(f"{os.path.basename(path_instancia)}  N={n} K={k} M={len(fichas)}  "
              f"| poblacion={params.tam_poblacion} elite={params.tam_elite} "
              f"torneo={params.tam_torneo} cruce={params.prob_cruce} "
              f"max_gen={params.max_generaciones} max_sin_mejora={params.max_sin_mejora}")
        print("-" * 86)
        print(f"{'semilla':>8} {'aptitud':>8} {'colocadas':>11} {'ocupadas':>9} "
              f"{'mayor':>6} {'evals':>8} {'gen':>5} {'tiempo':>8}  motivo_paro")
        for c in corridas:
            print(f"{c.semilla:>8} {c.aptitud:>8} {str(c.colocadas)+'/'+str(c.total_fichas):>11} "
                  f"{c.ocupadas:>9} {c.mayor:>6} {c.evaluaciones:>8} {c.generaciones:>5} "
                  f"{c.tiempo:>7.2f}s  {c.motivo_paro}")
        print("-" * 86)
        media, desv, mn, mx = resumir(corridas)
        print(f"  aptitud: media={media:.1f}  desv={desv:.2f}  min={mn}  max={mx}")
        media_o, desv_o, mn_o, mx_o = resumir(corridas, "ocupadas")
        print(f"  ocupadas: media={media_o:.1f}  desv={desv_o:.2f}  min={mn_o}  max={mx_o}")
    return corridas

def barrido(path_instancia, parametro, valores, semillas = (1, 2, 3), params = None):
    """Varia UN parametro dejando los demas fijos y reporta media y dispersion.

    Este es el 'procedimiento explicito' con el que se justifican los parametros
    en el informe: no se eligen por intuicion, se eligen midiendo.
    """
    if (params is None): params = Params()
    n, k, fichas = cargar_instancia(path_instancia)
    print(f"Barrido de '{parametro}' sobre {os.path.basename(path_instancia)} "
          f"(N={n} K={k} M={len(fichas)}), {len(semillas)} semillas")
    print("-" * 74)
    print(f"{parametro:>16} | {'media':>7} {'desv':>6} {'min':>5} {'max':>5} | "
          f"{'evals':>9} {'tiempo':>8}")
    tabla = []
    for v in valores:
        p = replace(params, **{parametro: v})
        corridas = [correr(n, fichas, s, p) for s in semillas]
        media, desv, mn, mx = resumir(corridas)
        ev = statistics.mean([c.evaluaciones for c in corridas])
        tt = statistics.mean([c.tiempo for c in corridas])
        print(f"{str(v):>16} | {media:>7.1f} {desv:>6.2f} {mn:>5} {mx:>5} | "
              f"{ev:>9.0f} {tt:>7.2f}s")
        tabla.append((v, media, desv, mn, mx, ev, tt))
    return tabla

def comparar_con_aleatoria(path_instancia, params = None, semillas = (1, 2, 3)):
    """Compara el AE contra busqueda aleatoria con el MISMO presupuesto de
    evaluaciones. Es el control experimental: si el AE no gana, hay un bug."""
    if (params is None): params = Params()
    n, k, fichas = cargar_instancia(path_instancia)
    corridas = [correr(n, fichas, s, params) for s in semillas]
    presupuesto = int(statistics.mean([c.evaluaciones for c in corridas]))
    aleatorias = [aptitud(decodificar(busqueda_aleatoria(n, fichas, random.Random(s), presupuesto).cromosoma, n, fichas), n)
                  for s in semillas]
    m_ae, d_ae, _, _ = resumir(corridas)
    d_al = statistics.stdev(aleatorias) if len(aleatorias) > 1 else 0.0
    print(f"{os.path.basename(path_instancia)}: presupuesto de {presupuesto} evaluaciones, "
          f"{len(semillas)} semillas")
    print(f"  aleatoria : media={statistics.mean(aleatorias):.1f}  desv={d_al:.2f}  {aleatorias}")
    print(f"  evolutivo : media={m_ae:.1f}  desv={d_ae:.2f}  {[c.aptitud for c in corridas]}")
    return corridas, aleatorias

if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, "entradas", "instancia_01.txt")
    params = Params(
        tam_poblacion = 100,
        tam_elite = 2,
        tam_torneo = 3,
        prob_cruce = 0.8,
        tasa = None,
        # Condiciones de parada
        max_generaciones = 300,
        max_sin_mejora = 60,
        limite_seg = 10.0
    )
    experimento(ruta, params, semillas = (1, 2, 3, 4, 5))
    print()
    comparar_con_aleatoria(ruta)


