import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import main
from validator import commandLine, validateFiles


class GameIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.instance_path = self.root / "instance.txt"
        self.instance_path.write_text(
            "3 2\n"
            "5\n"
            "1 2\n"
            "1 3\n"
            "2 1\n"
            "1 4\n"
            "2 2\n",
            encoding="utf-8",
        )

    def test_each_agent_writes_a_solution_accepted_by_validator(self):
        for agent in ("evolutivo", "busqueda"):
            with self.subTest(agent=agent):
                solution_path = self.root / f"{agent}-solution.txt"
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    main.main(
                        [
                            "--agente",
                            agent,
                            "--instancia",
                            str(self.instance_path),
                            "--salida",
                            str(solution_path),
                            "--semilla",
                            "7",
                            "--limite-segundos",
                            "2",
                        ]
                    )

                with contextlib.redirect_stdout(io.StringIO()):
                    colocadas, total_fichas = validateFiles(self.instance_path, solution_path)
                self.assertEqual(colocadas, 5)
                self.assertEqual(total_fichas, 5)
                self.assertIn("Validación automática: solución válida", output.getvalue())

                with contextlib.redirect_stdout(io.StringIO()):
                    exit_code = commandLine(
                        ["--instancia", str(self.instance_path), "--solucion", str(solution_path)]
                    )
                self.assertEqual(exit_code, 0)

    def test_validator_rejects_a_solution_with_reused_cell(self):
        solution_path = self.root / "invalid-solution.txt"
        solution_path.write_text(
            "0 0 0\n"
            "1 0 0\n"
            "# colocadas=2 ocupadas=1 mayor=3\n",
            encoding="utf-8",
        )

        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, "Solution not valid"):
                validateFiles(self.instance_path, solution_path)


if __name__ == "__main__":
    unittest.main()
