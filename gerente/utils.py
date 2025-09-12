from django.utils import timezone
from datetime import date, timedelta
# dateutil.relativedelta não é necessário para esta função
# from dateutil.relativedelta import relativedelta

def get_periodo_contabil_atual(dia_de_corte=11):
    """
    Calcula as datas de início e fim do período contábil atual
    com base em um dia de corte.
    """
    hoje = timezone.localtime(timezone.now()).date()

    # Se o dia atual for igual ou maior que o dia de corte, o período
    # contábil começou neste mês.
    if hoje.day >= dia_de_corte:
        ano_inicio = hoje.year
        mes_inicio = hoje.month

    # Se o dia atual for menor que o dia de corte, o período contábil
    # começou no mês anterior.
    else:
        data_mes_anterior = hoje.replace(day=1) - timedelta(days=1)
        ano_inicio = data_mes_anterior.year
        mes_inicio = data_mes_anterior.month

    # Com ano_inicio e mes_inicio definidos, o resto da lógica funciona perfeitamente.
    data_inicio = date(ano_inicio, mes_inicio, dia_de_corte)

    # Calcula o início do próximo ciclo para encontrar a data de fim do ciclo atual.
    # Esta lógica lida corretamente com a virada de ano.
    if mes_inicio == 12:
        proximo_ano = ano_inicio + 1
        proximo_mes = 1
    else:
        proximo_ano = ano_inicio
        proximo_mes = mes_inicio + 1

    inicio_ciclo_seguinte = date(proximo_ano, proximo_mes, dia_de_corte)
    data_fim = inicio_ciclo_seguinte - timedelta(days=1)

    return data_inicio, data_fim

