import argparse
import random
from pathlib import Path

from agente_evolutivo.agent import resolver
from game import isInputFileValid


ROOT = Path(__file__).resolve().parent.parent


def main(argv=None):
    parser = argparse.ArgumentParser(description="Ejecuta el agente evolutivo de TileUp")
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
        help="tiempo máximo del AE en segundos (por defecto: 10)",
    )
    args = parser.parse_args(argv)

    if args.limite_segundos <= 0:
        parser.error("--limite-segundos debe ser mayor que cero")

    instancia = isInputFileValid(str(args.instancia))
    if instancia is False or not instancia[0]:
        parser.error("La instancia no existe o no tiene un formato válido")

    _, (n, k), _, fichas = instancia
    resolver(n, k, fichas, random.Random(args.semilla), args.limite_segundos, path_salida=str(args.salida))

    # TODO: Validar la solución generada y mostrar un mensaje de éxito o error


if __name__ == "__main__":
    main()