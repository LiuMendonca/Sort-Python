"""Prepara um CSV menor para o benchmark, sem dependências externas.

Na raiz de Sort-Python:
    python3 scripts/reduzir_csv.py export.csv --linhas 10000
    python3 src/main.py --limite 1000

Se data/crime_data.csv já existir, escolha outro arquivo:
    python3 scripts/reduzir_csv.py export.csv --saida data/crime_data_reduzido.csv
    python3 src/main.py --csv data/crime_data_reduzido.csv --limite 1000

Use --linhas 0 para manter todos os registros e remover apenas colunas extras.
O original é preservado. O script recusa substituir arquivos existentes.
"""

import argparse
import csv
from pathlib import Path
import random
import sys


# São exatamente os campos utilizados pela classe Crime.
COLUNAS = ["DR_NO", "DATE OCC", "AREA NAME", "Crm Cd Desc", "Vict Age", "LOCATION"]


def reduzir_csv(entrada, saida, linhas=10000, semente=42, separador=","):
    """Lê uma vez, guarda até 'linhas' registros e retorna (lidos, gravados).

Usa amostragem por reservatório: cada registro tem a mesma chance de entrar
na amostra, mesmo quando a quantidade total de registros ainda é desconhecida.
Com linhas=0, escreve todos os registros à medida que os lê.
"""
    entrada, saida = Path(entrada), Path(saida)
    if linhas < 0:
        raise ValueError("--linhas deve ser maior ou igual a zero.")
    if len(separador) != 1:
        raise ValueError("--separador deve ter exatamente um caractere.")
    if entrada.resolve() == saida.resolve():
        raise ValueError("Entrada e saída devem ser arquivos diferentes.")
    if saida.exists():
        raise FileExistsError(
            f"A saída já existe: {saida}. Use --saida com outro nome, "
            "por exemplo data/crime_data_reduzido.csv."
        )

    gerador = random.Random(semente)
    amostra = []
    total = 0
    # utf-8-sig também aceita CSV UTF-8 com BOM; newline trata campos multilinha.
    with entrada.open("r", encoding="utf-8-sig", newline="") as original:
        leitor = csv.DictReader(original, delimiter=separador, strict=True)
        faltantes = [c for c in COLUNAS if c not in (leitor.fieldnames or [])]
        if faltantes:
            raise ValueError(
                "Colunas ausentes: " + ", ".join(faltantes)
                + ". Confira o arquivo e o --separador."
            )

        saida.parent.mkdir(parents=True, exist_ok=True)
        # Modo x: cria somente se o arquivo ainda não existir.
        with saida.open("x", encoding="utf-8", newline="") as reduzido:
            try:
                escritor = csv.DictWriter(reduzido, fieldnames=COLUNAS)
                escritor.writeheader()
                for total, registro in enumerate(leitor, start=1):
                    if None in registro or any(registro[c] is None for c in COLUNAS):
                        raise ValueError(
                            f"Registro {total} com quantidade incorreta de campos."
                        )

                    if linhas == 0:
                        escritor.writerow({c: registro[c] for c in COLUNAS})
                    elif total <= linhas:
                        amostra.append({c: registro[c] for c in COLUNAS})
                    else:
                        # Novos registros podem substituir os que já foram guardados.
                        posicao = gerador.randrange(total)
                        if posicao < linhas:
                            amostra[posicao] = {c: registro[c] for c in COLUNAS}

                if linhas:
                    gerador.shuffle(amostra)
                    escritor.writerows(amostra)
            except BaseException:
                # Remove somente a saída recém-criada se a operação for interrompida.
                reduzido.close()
                saida.unlink(missing_ok=True)
                raise

    return total, total if linhas == 0 else len(amostra)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("entrada", nargs="?", default="export.csv",
                        help="CSV original (padrão: export.csv).")
    parser.add_argument("--saida", default="data/crime_data.csv",
                        help="Arquivo novo (padrão: data/crime_data.csv).")
    parser.add_argument("--linhas", type=int, default=10000,
                        help="Tamanho máximo da amostra (padrão: 10000; 0 mantém todas).")
    parser.add_argument("--semente", type=int, default=42,
                        help="Semente para repetir a amostra (padrão: 42).")
    parser.add_argument("--separador", default=",",
                        help="Separador do CSV original (padrão: vírgula).")
    args = parser.parse_args()

    print(f"Lendo {args.entrada} em uma única passagem...")
    try:
        total, gravados = reduzir_csv(
            args.entrada, args.saida, args.linhas, args.semente, args.separador
        )
        tamanho_entrada = Path(args.entrada).stat().st_size
        tamanho_saida = Path(args.saida).stat().st_size
    except (OSError, ValueError, csv.Error) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1

    print(f"Registros lidos: {total:,} | Registros gravados: {gravados:,}")
    print(f"Colunas mantidas: {len(COLUNAS)} | Semente: {args.semente}")
    print(f"Entrada: {tamanho_entrada / 1024**2:.2f} MiB")
    print(f"Saída: {tamanho_saida / 1024**2:.3f} MiB ({tamanho_saida:,} bytes)")
    print(f"Arquivo pronto: {args.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
