from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.db.models import Sum
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, FormView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Lancamento, Cofrinho, Fornecedor, Categoria, CartaoCredito
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncWeek
from django.db.models import F
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from .forms import LancamentoForm, CofrinhoForm, FornecedorForm, CategoriaForm, RelatorioPeriodoForm, TransferirParaCofrinhoForm, CartaoCreditoForm
from datetime import date

# --- Views de Lançamentos ---
class LancamentoListView(ListView):
    model = Lancamento
    template_name = 'lancamentos/lista.html'
    context_object_name = 'lancamentos'
    ordering = ['-data']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Usar o queryset completo para os cálculos
        todos_lancamentos = self.get_queryset()

        # LÓGICA CORRIGIDA:
        # 1. Total de Entradas: Soma TODAS as entradas, independentemente do método de pagamento.
        total_entradas = todos_lancamentos.filter(tipo='entrada').aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

        # 2. Total de Saídas para o Saldo: Soma apenas as saídas que NÃO são no cartão de crédito.
        total_saidas_saldo = todos_lancamentos.filter(
            tipo='saida'
        ).exclude(
            metodo_pagamento='cartao_credito'
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

        # 3. Calcula o saldo com base nas regras corretas.
        saldo_total = total_entradas - total_saidas_saldo

        context['total_entradas'] = total_entradas
        context['total_saidas'] = total_saidas_saldo # Mostra apenas as saídas que afetam o saldo
        context['saldo_total'] = saldo_total
        
        # Adicionar informações sobre cartões de crédito (isso permanece igual)
        context['cartoes_credito'] = CartaoCredito.objects.filter(ativo=True)
        
        return context

class LancamentoCreateView(CreateView):
    model = Lancamento
    form_class = LancamentoForm
    template_name = 'lancamentos/adicionar.html'
    success_url = reverse_lazy('lista_lancamentos')

    def form_valid(self, form):
        lancamento = form.save(commit=False)
        
        # A LÓGICA AGORA VIVE AQUI!
        # Só executa a lógica de limite se for uma SAÍDA com cartão de crédito.
        if lancamento.tipo == 'saida' and lancamento.metodo_pagamento == 'cartao_credito':
            try:
                cartao = lancamento.cartao_credito
                valor = lancamento.valor
                
                # Verifica o limite antes de tentar salvar
                if not cartao.tem_limite_disponivel(valor):
                    messages.error(self.request, f"Limite insuficiente no cartão {cartao.nome}.")
                    return self.form_invalid(form)

                # Garante que ambas as operações (salvar e usar limite) funcionem
                with transaction.atomic():
                    cartao.usar_limite(valor)
                    lancamento.save()
                
                messages.success(self.request, 'Lançamento de saída no cartão adicionado com sucesso!')
                return redirect(self.success_url)

            except ValidationError as e:
                messages.error(self.request, str(e))
                return self.form_invalid(form)
        
        # Para todos os outros casos (entradas, outras formas de pagamento),
        # apenas salva o lançamento normalmente.
        lancamento.save()
        messages.success(self.request, 'Lançamento adicionado com sucesso!')
        return redirect(self.success_url)

class LancamentoUpdateView(UpdateView):
    model = Lancamento
    form_class = LancamentoForm
    template_name = 'lancamentos/editar.html'
    success_url = reverse_lazy('lista_lancamentos')

    def form_valid(self, form):
        novo_lancamento = form.save(commit=False)
        antigo_lancamento = Lancamento.objects.get(pk=self.object.pk)

        try:
            with transaction.atomic():
                # 1. Reverte o efeito do lançamento antigo, SE ele era uma saída no cartão.
                if antigo_lancamento.tipo == 'saida' and antigo_lancamento.metodo_pagamento == 'cartao_credito':
                    antigo_lancamento.cartao_credito.liberar_limite(antigo_lancamento.valor)

                # 2. Aplica o efeito do novo lançamento, SE ele é uma saída no cartão.
                if novo_lancamento.tipo == 'saida' and novo_lancamento.metodo_pagamento == 'cartao_credito':
                    novo_lancamento.cartao_credito.usar_limite(novo_lancamento.valor)
                
                # Salva o objeto no banco de dados
                novo_lancamento.save()

            messages.success(self.request, 'Lançamento atualizado com sucesso!')
            return redirect(self.success_url)
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

class LancamentoDeleteView(DeleteView):
    model = Lancamento
    template_name = 'lancamentos/deletar.html'
    success_url = reverse_lazy('lista_lancamentos')

    def form_valid(self, form):
        lancamento = self.get_object()

        # Libera o limite APENAS se for uma SAÍDA de cartão de crédito
        if lancamento.tipo == 'saida' and lancamento.metodo_pagamento == 'cartao_credito':
            try:
                with transaction.atomic():
                    lancamento.cartao_credito.liberar_limite(lancamento.valor)
                    # A exclusão ocorre depois da liberação do limite
                    response = super().form_valid(form)
                messages.success(self.request, 'Lançamento excluído e limite do cartão restaurado!')
                return response
            except Exception as e:
                messages.error(self.request, f"Erro ao excluir: {e}")
                return redirect(self.success_url)

        # Para todos os outros casos, apenas deleta
        response = super().form_valid(form)
        messages.success(self.request, 'Lançamento excluído com sucesso!')
        return response

# --- Views de Cartões de Crédito ---
class CartaoCreditoListView(ListView):
    model = CartaoCredito
    template_name = 'cartoes/lista.html'
    context_object_name = 'cartoes'
    ordering = ['nome']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cartoes = context['cartoes']
        
        # Adicionar informações extras para cada cartão
        for cartao in cartoes:
            cartao.limite_usado_valor = cartao.limite_usado()
            cartao.percentual_usado_valor = cartao.percentual_usado()
            
            # Últimos lançamentos do cartão
            cartao.ultimos_lancamentos = Lancamento.objects.filter(
                cartao_credito=cartao
            ).order_by('-data')[:5]
            
            # Total gasto no mês atual
            hoje = timezone.now().date()
            primeiro_dia_mes = hoje.replace(day=1)
            cartao.gasto_mes_atual = Lancamento.objects.filter(
                cartao_credito=cartao,
                data__gte=primeiro_dia_mes,
                tipo='saida'
            ).aggregate(Sum('valor'))['valor__sum'] or 0
        
        return context

class CartaoCreditoCreateView(CreateView):
    model = CartaoCredito
    form_class = CartaoCreditoForm
    template_name = 'cartoes/adicionar.html'
    success_url = reverse_lazy('lista_cartoes')

    def form_valid(self, form):
        # Garantir que o limite disponível seja igual ao limite total para cartões novos
        cartao = form.save(commit=False)
        cartao.limite_disponivel = cartao.limite_total
        cartao.save()
        
        messages.success(self.request, 'Cartão de crédito adicionado com sucesso!')
        return redirect(self.success_url)

class CartaoCreditoUpdateView(UpdateView):
    model = CartaoCredito
    form_class = CartaoCreditoForm
    template_name = 'cartoes/editar.html'
    success_url = reverse_lazy('lista_cartoes')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Cartão de crédito atualizado com sucesso!')
        return response

class CartaoCreditoDeleteView(DeleteView):
    model = CartaoCredito
    template_name = 'cartoes/deletar.html'
    success_url = reverse_lazy('lista_cartoes')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cartao = self.get_object()
        
        # Verificar se há lançamentos associados
        context['lancamentos_associados'] = Lancamento.objects.filter(
            cartao_credito=cartao
        ).count()
        
        return context

    def form_valid(self, form):
        cartao = self.get_object()
        
        # Verificar se há lançamentos associados
        if Lancamento.objects.filter(cartao_credito=cartao).exists():
            messages.error(
                self.request, 
                'Não é possível excluir este cartão pois há lançamentos associados a ele.'
            )
            return redirect('lista_cartoes')
        
        response = super().form_valid(form)
        messages.success(self.request, 'Cartão de crédito excluído com sucesso!')
        return response

class CartaoCreditoDetailView(TemplateView):
    template_name = 'cartoes/detalhes.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cartao_id = kwargs.get('pk')
        cartao = get_object_or_404(CartaoCredito, pk=cartao_id)
        
        context['cartao'] = cartao
        context['limite_usado_valor'] = cartao.limite_usado()
        context['percentual_usado_valor'] = cartao.percentual_usado()
        
        # Lançamentos do cartão
        context['lancamentos'] = Lancamento.objects.filter(
            cartao_credito=cartao
        ).order_by('-data')
        
        # Estatísticas por mês
        hoje = timezone.now().date()
        primeiro_dia_mes = hoje.replace(day=1)
        
        context['gasto_mes_atual'] = Lancamento.objects.filter(
            cartao_credito=cartao,
            data__gte=primeiro_dia_mes,
            tipo='saida'
        ).aggregate(Sum('valor'))['valor__sum'] or 0
        
        # Próximo vencimento
        if cartao.dia_vencimento:
            try:
                proximo_vencimento = hoje.replace(day=cartao.dia_vencimento)
                if proximo_vencimento <= hoje:
                    # Se já passou este mês, próximo mês
                    if proximo_vencimento.month == 12:
                        proximo_vencimento = proximo_vencimento.replace(year=proximo_vencimento.year + 1, month=1)
                    else:
                        proximo_vencimento = proximo_vencimento.replace(month=proximo_vencimento.month + 1)
                context['proximo_vencimento'] = proximo_vencimento
            except ValueError:
                # Dia inválido (ex: 31 em fevereiro)
                context['proximo_vencimento'] = None
        
        return context

class ResetarLimiteCartaoView(View):
    """View para resetar o limite do cartão (simular pagamento da fatura)"""
    
    def post(self, request, pk):
        cartao = get_object_or_404(CartaoCredito, pk=pk)
        
        # Resetar limite disponível para o limite total
        cartao.limite_disponivel = cartao.limite_total
        cartao.save()
        
        messages.success(
            request, 
            f'Limite do cartão {cartao.nome} foi resetado. Limite disponível: R$ {cartao.limite_disponivel}'
        )
        
        return redirect('detalhes_cartao', pk=pk)

# --- Views de Cofrinhos ---
class CofrinhoListView(ListView):
    model = Cofrinho
    template_name = 'cofrinhos/lista.html'
    context_object_name = 'cofrinhos'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cofrinhos = context['cofrinhos']
        for cofrinho in cofrinhos:
            if cofrinho.meta > 0:
                cofrinho.progresso = (cofrinho.saldo / cofrinho.meta) * 100
            else:
                cofrinho.progresso = 0
        return context

class CofrinhoCreateView(CreateView):
    model = Cofrinho
    form_class = CofrinhoForm
    template_name = 'cofrinhos/adicionar.html'
    success_url = reverse_lazy('lista_cofrinhos')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Cofrinho adicionado com sucesso!')
        return response

class CofrinhoUpdateView(UpdateView):
    model = Cofrinho
    form_class = CofrinhoForm
    template_name = 'cofrinhos/editar.html'
    success_url = reverse_lazy('lista_cofrinhos')

class CofrinhoDeleteView(DeleteView):
    model = Cofrinho
    template_name = 'cofrinhos/deletar.html'
    success_url = reverse_lazy('lista_cofrinhos')
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Cofrinho excluído com sucesso!')
        return response

class TransferirParaCofrinhoView(View):
    def get(self, request):
        form = TransferirParaCofrinhoForm()
        return render(request, 'cofrinhos/transferir.html', {'form': form})

    def post(self, request):
        form = TransferirParaCofrinhoForm(request.POST)
        if form.is_valid():
            valor = form.cleaned_data['valor']
            cofrinho = form.cleaned_data['cofrinho_destino']
            
            saldo_atual = (Lancamento.objects.filter(tipo='entrada').aggregate(Sum('valor'))['valor__sum'] or 0) - \
                          (Lancamento.objects.filter(tipo='saida').aggregate(Sum('valor'))['valor__sum'] or 0)
            
            if valor > saldo_atual:
                messages.error(request, 'Saldo insuficiente para a transferência.')
                return redirect('transferir_cofrinho')

            with transaction.atomic():
                cofrinho.saldo += valor
                cofrinho.save()
                Lancamento.objects.create(
                    descricao=f'Transferência para cofrinho {cofrinho.nome}',
                    tipo='saida',
                    valor=valor,
                    data=timezone.now(),
                    cofrinho_destino=cofrinho,
                    observacoes='Transferência interna.'
                )
            
            messages.success(request, f'R$ {valor} transferido com sucesso para o cofrinho {cofrinho.nome}.')
            return redirect('lista_cofrinhos')
        
        return render(request, 'cofrinhos/transferir.html', {'form': form})


# --- Views de Fornecedores ---
class FornecedorListView(ListView):
    model = Fornecedor
    template_name = 'fornecedores/lista.html'
    context_object_name = 'fornecedores'

class FornecedorCreateView(CreateView):
    model = Fornecedor
    form_class = FornecedorForm
    template_name = 'fornecedores/adicionar.html'
    success_url = reverse_lazy('lista_fornecedores')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Fornecedor adicionado com sucesso!')
        return response

class FornecedorUpdateView(UpdateView):
    model = Fornecedor
    form_class = FornecedorForm
    template_name = 'fornecedores/editar.html'
    success_url = reverse_lazy('lista_fornecedores')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Fornecedor atualizado com sucesso!')
        return response

class FornecedorDeleteView(DeleteView):
    model = Fornecedor
    template_name = 'fornecedores/deletar.html'
    success_url = reverse_lazy('lista_fornecedores')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Fornecedor excluído com sucesso!')
        return response

# --- Views de Categorias ---
class CategoriaListView(ListView):
    model = Categoria
    template_name = 'categorias/lista.html'
    context_object_name = 'categorias'

class CategoriaCreateView(CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'categorias/adicionar.html'
    success_url = reverse_lazy('lista_categorias')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Categoria adicionada com sucesso!')
        return response

class CategoriaUpdateView(UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'categorias/editar.html'
    success_url = reverse_lazy('lista_categorias')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categoria'] = self.get_object()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Categoria atualizada com sucesso!')
        return response

class CategoriaDeleteView(DeleteView):
    model = Categoria
    template_name = 'categorias/deletar.html'
    success_url = reverse_lazy('lista_categorias')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Categoria excluída com sucesso!')
        return response

# --- View da Home Page ---
class HomeView(TemplateView):
    template_name = 'home/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
                
        hoje = timezone.now().date()
        dia_de_corte = 11

        if hoje.day < dia_de_corte:
            # Estamos ANTES do dia de corte. O período termina no mês atual.
            # Ex: hoje é 06/09. Período é de 11/08 a 10/09.
            ano_fim = hoje.year
            mes_fim = hoje.month
            
            # Para o início, voltamos um mês.
            data_inicio_provisoria = hoje - relativedelta(months=1)
            ano_inicio = data_inicio_provisoria.year
            mes_inicio = data_inicio_provisoria.month
        
        else:
            # Estamos NO DIA de corte ou DEPOIS. O período começa no mês atual.
            # Ex: hoje é 15/09. Período é de 11/09 a 10/10.
            ano_inicio = hoje.year
            mes_inicio = hoje.month

            # Para o fim, avançamos um mês.
            data_fim_provisoria = hoje + relativedelta(months=1)
            ano_fim = data_fim_provisoria.year
            mes_fim = data_fim_provisoria.month

        data_inicio = date(ano_inicio, mes_inicio, dia_de_corte)
        data_fim = date(ano_fim, mes_fim, dia_de_corte - 1) # Dia 10

        context['periodo_inicio'] = data_inicio
        context['periodo_fim'] = data_fim


        # 1. lançamentos dentro do periodo contabil:

        lancamentos_periodo = Lancamento.objects.filter(data__gte=data_inicio, data__lte=data_fim)


        # 2. SOMA todas as entradas do periodo

        total_entradas = lancamentos_periodo.filter(
            tipo="entrada"
        ).aggregate(total=Sum("valor"))['total'] or Decimal('0.00')

        # 3. SOMA todas as saidas (excluindo cartao de credito)

        total_saidas = lancamentos_periodo.filter(
            tipo="saida"
        ).exclude(
            metodo_pagamento='cartao_credito'
        ).aggregate(total=Sum("valor"))['total'] or Decimal('0.00') # CORREÇÃO: Acessar ['total']


        saldo_total = total_entradas - total_saidas
        
        ultimos_lancamentos = Lancamento.objects.order_by("-data")[:5]
        cofrinhos = Cofrinho.objects.all()
        for cofrinho in cofrinhos:
            if cofrinho.meta > 0:
                cofrinho.progresso = (cofrinho.saldo / cofrinho.meta) * 100
            else:
                cofrinho.progresso = 0

        metodos_resumo = Lancamento.objects.values('metodo_pagamento').annotate(
            total_entradas=Sum('valor', filter=models.Q(tipo='entrada')),
            total_saidas=Sum('valor', filter=models.Q(tipo='saida'))
        )
        
        cartoes_credito = CartaoCredito.objects.filter(ativo=True)
        for cartao in cartoes_credito:
            cartao.limite_usado_valor = cartao.limite_usado()
            cartao.percentual_usado_valor = cartao.percentual_usado()
        
        context.update({
            "ultimos_lancamentos": ultimos_lancamentos,
            "total_entradas": total_entradas,
            "total_saidas": total_saidas,
            "saldo_total": saldo_total,
            "cofrinhos": cofrinhos,
            "metodos_resumo": metodos_resumo,
            "cartoes_credito": cartoes_credito,
        })
        return context

# --- Views de Relatórios ---

