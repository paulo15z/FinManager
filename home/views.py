from django.shortcuts import render, redirect
from django.db import models
from django.db.models import Sum
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, FormView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from .models import Lancamento, Cofrinho, Fornecedor, Categoria
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncWeek
from django.db.models import F


from .forms import LancamentoForm, CofrinhoForm, FornecedorForm, CategoriaForm, RelatorioPeriodoForm, TransferirParaCofrinhoForm

# --- Views de Lançamentos ---
class LancamentoListView(ListView):
    model = Lancamento
    template_name = 'lancamentos/lista.html'
    context_object_name = 'lancamentos'
    ordering = ['-data']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lancamentos = self.get_queryset()
        context['total_entradas'] = sum(l.valor for l in lancamentos if l.tipo == 'entrada')
        context['total_saidas'] = sum(l.valor for l in lancamentos if l.tipo == 'saida')
        context['saldo_total'] = context['total_entradas'] - context['total_saidas']
        return context

class LancamentoCreateView(CreateView):
    model = Lancamento
    form_class = LancamentoForm
    template_name = 'lancamentos/adicionar.html'
    success_url = reverse_lazy('lista_lancamentos')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Lançamento adicionado com sucesso!')
        return response

class LancamentoUpdateView(UpdateView):
    model = Lancamento
    form_class = LancamentoForm
    template_name = 'lancamentos/editar.html'
    success_url = reverse_lazy('lista_lancamentos')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Lançamento atualizado com sucesso!')
        return response

class LancamentoDeleteView(DeleteView):
    model = Lancamento
    template_name = 'lancamentos/deletar.html'
    success_url = reverse_lazy('lista_lancamentos')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Lançamento excluído com sucesso!')
        return response

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
        ultimos_lancamentos = Lancamento.objects.all().order_by("-data")[:5]
        total_entradas = Lancamento.objects.filter(tipo="entrada").aggregate(Sum("valor"))["valor__sum"] or 0
        total_saidas = Lancamento.objects.filter(tipo="saida").aggregate(Sum("valor"))["valor__sum"] or 0
        saldo_total = total_entradas - total_saidas
        
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
        context.update({
            "ultimos_lancamentos": ultimos_lancamentos,
            "total_entradas": total_entradas,
            "total_saidas": total_saidas,
            "saldo_total": saldo_total,
            "cofrinhos": cofrinhos,
            "metodos_resumo": metodos_resumo,
        })
        return context

# --- Views de Relatórios ---
