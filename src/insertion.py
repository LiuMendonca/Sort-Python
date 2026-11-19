from metricas import Metricas


def insertion_sort(arr):
    """Ordena a própria lista e retorna as métricas, como merge_sort."""
    metricas = Metricas()

    # A parte à esquerda de i já está ordenada.
    for i in range(1, len(arr)):
        atual = arr[i]
        j = i - 1

        while j >= 0:
            # Conta a comparação de valores, inclusive a que encerra o laço.
            metricas.comparacoes += 1
            if arr[j] <= atual:
                break

            # Abre espaço para inserir o valor atual.
            arr[j + 1] = arr[j]
            metricas.movimentacoes += 1
            j -= 1

        arr[j + 1] = atual
        metricas.movimentacoes += 1

    return metricas
