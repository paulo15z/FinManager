from django.shortcuts import render
from django.db.models import Sum
from django.db.models.functions import TruncWeek
from datetime import timedelta
from django.views.generic import TemplateView
from django.db import models

from home.models import Lancamento
from home.forms import RelatorioPeriodoForm

# Create your views here.
# --- Views de Relatórios ---
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
    


""" DRE = 
(+) RECEITA TOTAL

Venda à vista                       [entradas]
Venda a prazo                       [entradas]
(-) CUSTOS VARIÁVEIS

CMV / CMA                           [pagamento de fornecedor]
Simples Nacional                    [DAS]
Taxa de administração de cartões
(=) MARGEM DE CONTRIBUIÇÃO (1-2)    [entradas - 2]

(-) CUSTOS FIXOS

Salários 
Encargos sociais sobre salários
Pró-labore                          [prolabore]
Contador
Energia/Água
Aluguel                             [aluguel]
Juros de antecipação de CR e DB
Manutenção de máquinas e prédio
Segurança
Telefone e internet
Vale transporte
(=) RESULTADO OPERACIONAL LÍQUIDO (3-4)

(-) Investimentos e Amortizações

(=) RESULTADO FINAL (5-6-7)
"""

