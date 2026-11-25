# Sort-Python

Comparação de Merge Sort, Insertion Sort e Selection Sort com registros de crimes,
ordenados pelo número do registro policial (`DR_NO`). Cada função ordena a lista
recebida **no próprio lugar** e retorna um objeto `Metricas` com os contadores.

## Database
- **Obtenção e Configuração do Dataset**
Este projeto utiliza a base de dados pública de Crimes da Cidade de Los Angeles (2020 a 2024), mantida pelo LAPD (*Los Angeles Police Department).
- **Passo a Passo para Download:**
  1. Baixar o arquivo CSV: Acesse o dataset no portal oficial [Data.gov - LA Crime Data](https://catalog.data.gov/dataset/crime-data-from-2020-to-present) ou faça o download direto via [Portal Data.lacity.org](https://data.lacity.org/api/v3/views/2nrs-mtv8/export.csv?accessType=DOWNLOAD).
  2. Renomear e Organizar o Arquivo: Renomeie o arquivo baixado (que vem como `export.csv`) para `crime_data.csv`, coloque o arquivo em `data/`.
- ou utilize o `crime_data_reduzido.csv`.


## Executar

Coloque o dataset em `data/crime_data.csv` (ele não está incluído no repositório)
e execute os comandos a partir da raiz do projeto:

```bash
python3 src/main.py
```

Por padrão, o benchmark usa uma amostra de até **1.000 registros**, com semente 42.
Os três algoritmos recebem cópias da mesma amostra, nos cenários aleatório,
ordenado e reverso. A seleção da amostra e a preparação dos cenários ficam fora
do tempo medido. O CSV de entrada inteiro ainda é carregado na memória.

Para escolher o tamanho e os caminhos:

```bash
python3 src/main.py --limite 5000
python3 src/main.py --csv data/crime_data.csv --limite 1000 --saida data/metricas_1000.csv
```

`--limite 0` usa todos os registros. Insertion e Selection têm custo quadrático
no pior caso; no dataset de mais de 1 milhão de registros, a execução completa
pode demorar muito. Selection realiza `n * (n - 1) / 2` comparações em qualquer
ordem de entrada.

A execução padrão substitui `data/metricas.csv` com nove resultados (três
algoritmos × três cenários). Os resultados e gráficos já versionados são do
benchmark anterior, somente com Merge Sort. Para gerar novos gráficos:

```bash
python3 -m pip install pandas matplotlib
python3 scripts/gerar_graficos.py
```

O script de gráficos lê `data/metricas.csv`; gere os resultados nesse caminho
para atualizar os gráficos. Os algoritmos e os testes usam apenas a biblioteca
padrão do Python.

## Como funcionam

- **Insertion** (`src/insertion.py`): pega o próximo elemento, desloca os maiores
  para a direita e o insere na posição correta. Preserva a ordem relativa de
  registros com a mesma chave (estável).
- **Selection** (`src/selection.py`): procura o menor elemento da parte restante
  e troca com o elemento da posição atual. Essa versão não é estável.

O arquivo vazio `src/insetrion.py` foi substituído por `src/insertion.py`, com
a grafia correta.

| Algoritmo | Melhor caso | Caso médio | Pior caso |
| --- | --- | --- | --- |
| Merge Sort | O(n log n) | O(n log n) | O(n log n) |
| Insertion Sort | O(n) | O(n²) | O(n²) |
| Selection Sort | O(n²) | O(n²) | O(n²) |

## Contagem das métricas

- **Comparações:** somente comparações entre valores, sem contar verificações
  de índices ou condições dos laços. No Insertion, inclui a comparação que
  interrompe os deslocamentos.
- **Movimentações:** escritas em posições de listas, seguindo a convenção já
  usada pelo Merge. No Insertion, cada deslocamento e a colocação final contam
  uma escrita (mesmo se o valor ficar na posição original). No Selection, uma
  troca conta duas escritas; não há troca quando o menor já está na posição.
  Atribuições a variáveis locais não entram na contagem. No Merge, a cópia
  inicial para o buffer continua fora do contador, como na implementação original.

## Testes

```bash
python3 -B -m unittest discover -s tests -v
```
