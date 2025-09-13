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



from django.db.models import Sum
from home.models import Lancamento
from decimal import Decimal
from dateutil.relativedelta import relativedelta

def calcular_total_entradas(inicio: date, fim: date) -> Decimal:
    """Total de entradas no período: Útil para KPIs de receita em cantina (ex: vendas diárias)."""
    return Lancamento.objects.filter(
        tipo='entrada', data__gte=inicio, data__lte=fim
    ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

def calcular_total_saidas(inicio: date, fim: date) -> Decimal:
    """Total de saídas no período (excluindo cartões): Reflete despesas reais de caixa."""
    return Lancamento.objects.filter(
        tipo='saida', data__gte=inicio, data__lte=fim
    ).exclude(metodo_pagamento='cartao_credito').aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

def calcular_saldo_periodo(inicio: date, fim: date) -> Decimal:
    """Saldo líquido do período: Entradas - Saídas. Para análises isoladas mensais."""
    return calcular_total_entradas(inicio, fim) - calcular_total_saidas(inicio, fim)

def calcular_saldo_acumulado(ate_data: date) -> Decimal:
    """Saldo histórico até a data: Garante continuidade de caixa entre meses."""
    entradas = Lancamento.objects.filter(tipo='entrada', data__lte=ate_data).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
    saidas = Lancamento.objects.filter(tipo='saida', data__lte=ate_data).exclude(metodo_pagamento='cartao_credito').aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
    return entradas - saidas

def calcular_saldo_total_com_inicial(inicio: date, fim: date) -> Decimal:
    """Saldo total: Inicial + Período. Ideal para dashboard de home.html."""
    dia_anterior = inicio - relativedelta(days=1)
    return calcular_saldo_acumulado(dia_anterior) + calcular_saldo_periodo(inicio, fim)
