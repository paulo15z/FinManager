from django.utils import timezone
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

def get_periodo_contabil_atual(dia_de_corte=11):
    hoje = timezone.localtime(timezone.now()).date()


    if hoje.day >= dia_de_corte:
        ano_atual = hoje.year
        mes_atual = hoje.month

    # O resto da lógica, que já estava correta, permanece igual.
    else :
        primeiro_dia_mes_atual = hoje.replace(day=1)
        data_mes_anterior = primeiro_dia_mes_atual - timedelta(days=1)
        ano_inicio = data_mes_anterior.year
        mes_inicio = data_mes_anterior.month
    
    data_inicio = date(ano_inicio, mes_inicio, dia_de_corte)
            
    proximo_mes = mes_inicio + 1
    proximo_ano = ano_inicio
    if proximo_mes > 12:
        proximo_mes = 1
        proximo_ano += 1
    
    inicio_ciclo_seguinte = date(proximo_ano, proximo_mes, dia_de_corte)
    data_fim = inicio_ciclo_seguinte - timedelta(days=1)

    return data_inicio, data_fim