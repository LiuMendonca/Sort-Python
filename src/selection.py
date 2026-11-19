from metricas import Metricas


def selection_sort(arr):
    """Ordena a própria lista e retorna as métricas, como merge_sort."""
    metricas = Metricas()

    for i in range(len(arr) - 1):
        menor = i

        # Procura o menor valor na parte que ainda não foi ordenada.
        for j in range(i + 1, len(arr)):
            metricas.comparacoes += 1
            if arr[j] < arr[menor]:
                menor = j

        # Coloca o menor na posição i; evita trocar um valor com ele mesmo.
        if menor != i:
            arr[i], arr[menor] = arr[menor], arr[i]
            metricas.movimentacoes += 2

    return metricas
