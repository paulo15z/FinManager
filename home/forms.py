from django import forms
from .models import Categoria, Lancamento, Fornecedor, Cofrinho

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome', 'descricao']
        labels = {
            'nome': 'Nome',
            'descricao': 'Descrição'
        }

class LancamentoForm(forms.ModelForm):
    class Meta:
        model = Lancamento
        fields = '__all__'
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_valor(self):
        valor = self.cleaned_data['valor']
        if valor <= 0:
            raise forms.ValidationError("O valor deve ser maior que zero.")
        return valor

class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = '__all__'

class CofrinhoForm(forms.ModelForm):
    class Meta:
        model = Cofrinho
        fields = ["nome", "objetivo", "meta"]

class TransferirParaCofrinhoForm(forms.Form):
    cofrinho_destino = forms.ModelChoiceField(queryset=Cofrinho.objects.all(), label="Cofrinho de Destino")
    valor = forms.DecimalField(max_digits=10, decimal_places=2, label="Valor a Transferir")

    def clean_valor(self):
        valor = self.cleaned_data['valor']
        if valor <= 0:
            raise forms.ValidationError("O valor deve ser maior que zero!")
        return valor

class RelatorioPeriodoForm(forms.Form):
    data_inicio = forms.DateField(label="Data de Início", widget=forms.DateInput(attrs={"type": "date"}), required=False)
    data_fim = forms.DateField(label="Data de Fim", widget=forms.DateInput(attrs={"type": "date"}), required=False)
    metodo_pagamento = forms.ChoiceField(choices=Lancamento.PAGAMENTO_CHOICES, label="Método de Pagamento", required=False)