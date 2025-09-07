from django.shortcuts import render
from django.db.models import Sum, Q
from django.db.models.functions import TruncWeek
from datetime import timedelta
from django.views.generic import TemplateView
from django.db import models
from home.models import Lancamento, Categoria
from home.forms import RelatorioPeriodoForm

from django.utils import timezone
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal

from gerente.utils import get_periodo_contabil_atual


# Create your views here.
# --- Views de Relatórios ---

class RelatoriosDashboardView(TemplateView):
    template_name = 'relatorios/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

#-----------------------------------------------------------------#
        data_inicio, data_fim = get_periodo_contabil_atual()
        context['periodo_inicio'] = data_inicio
        context['data_fim'] = data_fim

#-----------------------------------------------------------------#

        lancamentos_periodo = Lancamento.objects.filter(data__gte=data_inicio, data__lte=data_fim)

        categorias_dre = Categoria.objects.exclude(nome='TRANSFERENCIAS')

        receitas = lancamentos_periodo.filter(
            tipo='entrada',
            categoria__categoria_pai__in=categorias_dre
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

        despesas = lancamentos_periodo.filter(
            tipo='saida',
            categoria__categoria_pai__in=categorias_dre
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

        resultado_liquido = receitas - despesas
        
        context['kpi_resultado_liquido'] = resultado_liquido
        
        return context

class RelatorioEntradasSaidasView(TemplateView):
    template_name = 'relatorios/entradas_saidas.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = RelatorioPeriodoForm(self.request.GET or None)
        context['form'] = form
        if form.is_valid():
            data_inicio = form.cleaned_data.get('data_inicio')
            data_fim = form.cleaned_data.get('data_fim')
            metodo_pagamento = form.cleaned_data.get('metodo_pagamento')
            lancamentos_filtrados = Lancamento.objects.all()
            if data_inicio:
                lancamentos_filtrados = lancamentos_filtrados.filter(data__gte=data_inicio)
            if data_fim:
                lancamentos_filtrados = lancamentos_filtrados.filter(data__lte=data_fim)
            if metodo_pagamento:
                lancamentos_filtrados = lancamentos_filtrados.filter(metodo_pagamento=metodo_pagamento)

            total_entradas = lancamentos_filtrados.filter(tipo='entrada').aggregate(Sum('valor'))['valor__sum'] or 0
            total_saidas = lancamentos_filtrados.filter(tipo='saida').aggregate(Sum('valor'))['valor__sum'] or 0
            saldo_periodo = total_entradas - total_saidas

            # Cálculo: Total de saídas por fornecedor
            gastos_por_fornecedor = lancamentos_filtrados.filter(
                tipo='saida', fornecedor__isnull=False
            ).values('fornecedor__nome').annotate(
                total_gasto=Sum('valor')
            ).order_by('-total_gasto')

            # Cálculo: Resumo semanal
            resumo_semanal = []
            if data_inicio and data_fim:
                lancamentos_semanais = lancamentos_filtrados.annotate(
                    semana=TruncWeek('data')
                ).values('semana').annotate(
                    total_entradas=Sum('valor', filter=models.Q(tipo='entrada')),
                    total_saidas=Sum('valor', filter=models.Q(tipo='saida'))
                ).order_by('semana')

                for semana in lancamentos_semanais:
                    data_inicio_semana = semana['semana']
                    data_fim_semana = data_inicio_semana + timedelta(days=6)
                    saldo_semana = (semana['total_entradas'] or 0) - (semana['total_saidas'] or 0)
                    resumo_semanal.append({
                        'semana': f'Semana de {data_inicio_semana.strftime("%d/%m")} a {data_fim_semana.strftime("%d/%m")}',
                        'total_entradas': semana['total_entradas'] or 0,
                        'total_saidas': semana['total_saidas'] or 0,
                        'saldo_semana': saldo_semana
                    })

            context.update({
                'lancamentos_filtrados': lancamentos_filtrados.order_by('-data'),
                'total_entradas': total_entradas,
                'total_saidas': total_saidas,
                'saldo_periodo': saldo_periodo,
                'gastos_por_fornecedor': gastos_por_fornecedor,
                'resumo_semanal': resumo_semanal
            })
        else:
            context.update({
                'lancamentos_filtrados': [],
                'total_entradas': 0,
                'total_saidas': 0,
                'saldo_periodo': 0,
                'gastos_por_fornecedor': [],
                'resumo_semanal': []
            })
        return context
    
class RelatorioDREView(TemplateView):

    template_name = 'relatorios/dre.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        data_inicio, data_fim = get_periodo_contabil_atual()    # utils 
        context['data_inicio'] = data_inicio
        context['data_fim'] = data_fim
        
        lancamentos_periodo = Lancamento.objects.filter(data__gte=data_inicio, data__lte=data_fim)

        categorias_receitas = Categoria.objects.filter(nome = 'RECEITAS')
        categorias_custos = Categoria.objects.filter(nome='CUSTOS DE PRODUTOS/SERVIÇOS')
        categorias_desp_op = Categoria.objects.filter(nome='DESPESAS OPERACIONAIS')
        categorias_desp_adm = Categoria.objects.filter(nome='DESPESAS ADMINISTRATIVAS')
        categorias_desp_fin = Categoria.objects.filter(nome='DESPESAS FINANCEIRAS')

        def calcular_total_categoria_pai(queryset, categorias_pai):
            if not categorias_pai.exists():
                return Decimal('0.00')
            total = queryset.filter(categoria__categoria_pai__in = categorias_pai).aggregate(soma=Sum('valor'))['soma']
            return total or Decimal('0.00')
        
        # calculo das linhas do DRE

        receita_bruta = calcular_total_categoria_pai(lancamentos_periodo.filter(tipo='entrada'), categorias_receitas)

        custos = calcular_total_categoria_pai(lancamentos_periodo.filter(tipo='saida'), categorias_custos)

        lucro_bruto = receita_bruta - custos

        despesas_operacionais = calcular_total_categoria_pai(lancamentos_periodo.filter(tipo='saida'), categorias_desp_op)

        despesas_administrativas = calcular_total_categoria_pai(lancamentos_periodo.filter(tipo='saida'), categorias_desp_adm)

        ebitda = lucro_bruto - despesas_operacionais - despesas_administrativas #earning before interest, taxes, cepreciation and amortization

        despesas_financeiras = calcular_total_categoria_pai(lancamentos_periodo.filter(tipo='saida'), categorias_desp_fin)

        resultado_liquido = ebitda - despesas_financeiras


        context['dre'] = {      # enviar pro template
            'receita_bruta': receita_bruta,
            'custos': custos,
            'lucro_bruto': lucro_bruto,
            'despesas_operacionais': despesas_operacionais,
            'despesas_administrativas': despesas_administrativas,
            'ebitda': ebitda,
            'despesas_financeiras': despesas_financeiras,
            'resultado_liquido': resultado_liquido,
        }

        return context
    
