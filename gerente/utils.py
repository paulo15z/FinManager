from django.utils import timezone
from datetime import date, timedelta

def get_periodo_contabil_atual(dia_de_corte=11):
    """
    Calcula as datas de início e fim do período contábil atual
    com base em um dia de corte.

    Retorna uma tupla (data_inicio, data_fim).
    """
    hoje = timezone.localtime(timezone.now()).date()

    if hoje.day >= dia_de_corte:
        ano_inicio = hoje.year
        mes_inicio = hoje.month
    else:
        data_mes_anterior = hoje.replace(day=1) - timedelta(days=1)
        ano_inicio = data_mes_anterior.year
        mes_inicio = data_mes_anterior.month

    data_inicio = date(ano_inicio, mes_inicio, dia_de_corte)

    if mes_inicio == 12:
        proximo_ano = ano_inicio + 1
        proximo_mes = 1
    else:
        proximo_ano = ano_inicio
        proximo_mes = mes_inicio + 1

    inicio_ciclo_seguinte = date(proximo_ano, proximo_mes, dia_de_corte)
    data_fim = inicio_ciclo_seguinte - timedelta(days=1)

    return data_inicio, data_fim
