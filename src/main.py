import argparse
import random
from pathlib import Path

from agente_evolutivo.agent import resolver
from game import isInputFileValid
from searchAgent.searchAgent import resolver as resolver_busqueda
from validator import validateFiles


ROOT = Path(__file__).resolve().parent.parent


def main(argv=None):
    parser = argparse.ArgumentParser(description="Ejecuta un agente de TileUp")
    # Agrega los argumentos de línea de comandos
    # --instancia: ruta del archivo de entrada
    parser.add_argument(
        "--instancia",
        type=Path,
        default=ROOT / "entradas" / "instancia_01.txt",
        help="ruta de la instancia (por defecto: entradas/instancia_01.txt)",
    )

    # --salida: ruta del archivo de salida
    parser.add_argument(
        "--salida",
        type=Path,
        default=ROOT / "salidas" / "solution.txt",
        help="ruta del archivo de solución (por defecto: salidas/solution.txt)",
    )

    # --semilla: semilla aleatoria
    parser.add_argument("--semilla", type=int, default=42, help="semilla aleatoria (por defecto: 42)")

    # --limite-segundos: tiempo máximo de ejecución del agente evolutivo
    parser.add_argument(
        "--limite-segundos",
        type=float,
        default=10.0,
        help="límite de tiempo del agente en segundos (por defecto: 10)",
    )
    parser.add_argument(
        "--agente",
        choices=("evolutivo", "busqueda"),
        default="evolutivo",
        help="agente a ejecutar (por defecto: evolutivo)",
    )
    args = parser.parse_args(argv)

    if args.limite_segundos <= 0:
        parser.error("--limite-segundos debe ser mayor que cero")

    instancia = isInputFileValid(str(args.instancia))
    if instancia is False or not instancia[0]:
        parser.error("La instancia no existe o no tiene un formato válido")

    _, (n, k), _, fichas = instancia

    if args.agente == "evolutivo":
        resolver(n, k, fichas, random.Random(args.semilla), args.limite_segundos, path_salida=str(args.salida))
    else:
        resolver_busqueda(n, k, fichas, random.Random(args.semilla), args.limite_segundos, path_salida=str(args.salida))
    
    try:
        colocadas, total_fichas = validateFiles(args.instancia, args.salida)
    except (OSError, ValueError, IndexError) as error:
        parser.error(f"La solución generada no es válida: {error}")
    
    estado = "válida" if colocadas == total_fichas else "válida pero incompleta"
        
    print(
        f"Validación automática: solución {estado} "
        f"({colocadas}/{total_fichas} fichas)."
    )


if __name__ == "__main__":
    main()