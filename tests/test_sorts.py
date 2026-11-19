import contextlib
import csv
import io
import itertools
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crime import Crime
from insertion import insertion_sort
import main
from merge import merge_sort
from metricas import Metricas
from selection import selection_sort


ALGORITMOS = (merge_sort, insertion_sort, selection_sort)


class OrdenacaoTests(unittest.TestCase):
    def test_listas_pequenas_com_repetidos_e_negativos(self):
        for tamanho in range(6):
            for valores in itertools.product((-1, 0, 1), repeat=tamanho):
                for ordenar in ALGORITMOS:
                    with self.subTest(algoritmo=ordenar.__name__, valores=valores):
                        dados = list(valores)
                        metricas = ordenar(dados)
                        self.assertEqual(dados, sorted(valores))
                        self.assertIsInstance(metricas, Metricas)

    def test_registros_crime_e_preservacao_dos_objetos(self):
        crimes = [Crime(chave, "", "", "", 0, str(i))
                  for i, chave in enumerate([3, 1, 3, 0, 1])]
        for ordenar in ALGORITMOS:
            with self.subTest(algoritmo=ordenar.__name__):
                dados = crimes.copy()
                ordenar(dados)
                self.assertEqual([c.dr_no for c in dados], [0, 1, 1, 3, 3])
                self.assertCountEqual([id(c) for c in dados], [id(c) for c in crimes])

    def test_insertion_preserva_ordem_de_chaves_iguais(self):
        dados = [Crime(chave, "", "", "", 0, str(i))
                 for i, chave in enumerate([2, 1, 2, 1])]
        esperado = sorted(dados)
        insertion_sort(dados)
        self.assertEqual([id(c) for c in dados], [id(c) for c in esperado])

    def test_contadores_conhecidos(self):
        casos = [
            ([], (0, 0), (0, 0)),
            ([7], (0, 0), (0, 0)),
            ([1, 2, 3], (2, 2), (3, 0)),
            ([3, 2, 1], (3, 5), (3, 2)),
            ([3, 1, 2], (3, 4), (3, 4)),
            ([2, 2, 2], (2, 2), (3, 0)),
        ]
        for dados, insertion_esperado, selection_esperado in casos:
            for ordenar, esperado in [
                (insertion_sort, insertion_esperado),
                (selection_sort, selection_esperado),
            ]:
                with self.subTest(algoritmo=ordenar.__name__, dados=dados):
                    metricas = ordenar(dados.copy())
                    self.assertEqual(
                        (metricas.comparacoes, metricas.movimentacoes), esperado
                    )

    def test_metricas_nao_acumulam_entre_chamadas(self):
        for ordenar in ALGORITMOS:
            primeira = ordenar([3, 2, 1])
            segunda = ordenar([])
            self.assertIsNot(primeira, segunda)
            self.assertEqual(segunda, Metricas())


class BenchmarkTests(unittest.TestCase):
    def test_cenarios_compartilham_amostra_sem_alterar_entrada(self):
        crimes = [Crime(i, "", "", "", 0, "") for i in range(7)]
        chamadas = []
        executar_original = main.executar_benchmark

        def observar(nome, cenario, ordenar, dados):
            antes = [id(c) for c in dados]
            resultado = executar_original(nome, cenario, ordenar, dados)
            self.assertEqual([id(c) for c in dados], antes)
            chamadas.append((nome, cenario, [c.dr_no for c in dados]))
            return resultado

        with patch.object(sys, "argv", ["main.py", "--limite", "5"]), \
                patch.object(main, "carregar_crimes", return_value=crimes), \
                patch.object(main, "salvar_metricas") as salvar, \
                patch.object(main, "executar_benchmark", side_effect=observar), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main.main(), 0)

        self.assertEqual(len(chamadas), 9)
        self.assertEqual(len(salvar.call_args.args[0]), 9)
        amostra = random.Random(42).sample(list(range(7)), 5)
        for cenario, esperado in [
            ("Aleatório", amostra),
            ("Ordenado", sorted(amostra)),
            ("Reverso", sorted(amostra, reverse=True)),
        ]:
            entradas = [dados for _, c, dados in chamadas if c == cenario]
            self.assertEqual(entradas, [esperado] * 3)
        self.assertEqual([c.dr_no for c in crimes], list(range(7)))

    def test_cli_le_csv_e_escreve_nove_resultados(self):
        with tempfile.TemporaryDirectory() as pasta:
            entrada = Path(pasta) / "crimes.csv"
            with entrada.open("w", newline="", encoding="utf-8") as arquivo:
                writer = csv.writer(arquivo)
                writer.writerow(["DR_NO"])
                writer.writerows((i,) for i in range(1003, 0, -1))

            for opcoes, tamanho in [([], 1000), (["--limite", "3"], 3),
                                    (["--limite", "0"], 1003)]:
                with self.subTest(opcoes=opcoes):
                    resultado = subprocess.run(
                        [sys.executable, "-B", str(ROOT / "src/main.py"),
                         "--csv", str(entrada), "--saida", "metricas.csv", *opcoes],
                        cwd=pasta, capture_output=True, text=True, check=True,
                        timeout=30,
                    )
                    self.assertIn("Métricas salvas com sucesso", resultado.stdout)
                    with (Path(pasta) / "metricas.csv").open(
                        newline="", encoding="utf-8"
                    ) as arquivo:
                        linhas = list(csv.DictReader(arquivo))
                    self.assertEqual(len(linhas), 9)
                    self.assertEqual({int(r["tamanho"]) for r in linhas}, {tamanho})
                    self.assertEqual(
                        {(r["algoritmo"], r["cenario"]) for r in linhas},
                        set(itertools.product(
                            ["Merge Sort", "Insertion Sort", "Selection Sort"],
                            ["Aleatório", "Ordenado", "Reverso"],
                        )),
                    )
                    for linha in linhas:
                        self.assertGreaterEqual(float(linha["tempo_segundos"]), 0)
                        if linha["algoritmo"] == "Selection Sort":
                            self.assertEqual(
                                int(linha["comparacoes"]), tamanho * (tamanho - 1) // 2
                            )

    def test_cli_rejeita_limite_negativo(self):
        resultado = subprocess.run(
            [sys.executable, "-B", str(ROOT / "src/main.py"), "--limite", "-1"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(resultado.returncode, 2)
        self.assertIn("--limite deve ser maior ou igual a zero", resultado.stderr)


if __name__ == "__main__":
    unittest.main()
