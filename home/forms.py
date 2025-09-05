from django import forms
from .models import Categoria, Lancamento, Fornecedor, Cofrinho, CartaoCredito

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome', 'descricao']
        labels = {
            'nome': 'Nome',
            'descricao': 'Descrição'
        }

""" 
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
    """

class LancamentoForm(forms.ModelForm):
    class Meta:
        model = Lancamento
        fields = ['descricao', 'tipo', 'valor', 'data', 'categoria', 'fornecedor', 
                 'metodo_pagamento', 'cartao_credito', 'cofrinho_destino', 'observacoes']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
            'valor': forms.NumberInput(attrs={'step': '0.01'}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar apenas cartões ativos
        self.fields['cartao_credito'].queryset = CartaoCredito.objects.filter(ativo=True)
        
        # Adicionar classes CSS
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
    
    def clean(self):
        cleaned_data = super().clean()
        metodo_pagamento = cleaned_data.get('metodo_pagamento')
        cartao_credito = cleaned_data.get('cartao_credito')
        tipo = cleaned_data.get('tipo')
        valor = cleaned_data.get('valor')
        
        # Validação: se método é cartão de crédito, cartão deve ser informado
        if metodo_pagamento == 'cartao_credito' and not cartao_credito:
            raise forms.ValidationError("Cartão de crédito deve ser selecionado quando o método de pagamento for 'Cartão de Crédito'")
        
        # Validação: se cartão informado, método deve ser cartão de crédito
        if cartao_credito and metodo_pagamento != 'cartao_credito':
            raise forms.ValidationError("Método de pagamento deve ser 'Cartão de Crédito' quando um cartão for selecionado")
        
        # Validação: verificar limite disponível para saídas
        if (tipo == 'saida' and metodo_pagamento == 'cartao_credito' and 
            cartao_credito and valor and not cartao_credito.tem_limite_disponivel(valor)):
            raise forms.ValidationError(
                f"Limite insuficiente no cartão {cartao_credito.nome}. "
                f"Disponível: R$ {cartao_credito.limite_disponivel}, "
                f"Solicitado: R$ {valor}"
            )
        
        return cleaned_data

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


class CartaoCreditoForm(forms.ModelForm):
    class Meta:
        model = CartaoCredito
        fields = ['nome', 'limite_total', 'dia_vencimento', 'dia_fechamento', 'ativo', 'observacoes']
        widgets = {
            'limite_total': forms.NumberInput(attrs={'step': '0.01'}),
            'dia_vencimento': forms.NumberInput(attrs={'min': 1, 'max': 31}),
            'dia_fechamento': forms.NumberInput(attrs={'min': 1, 'max': 31}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adicionar classes CSS
        for field in self.fields:
            if field == 'ativo':
                self.fields[field].widget.attrs.update({'class': 'form-check-input'})
            else:
                self.fields[field].widget.attrs.update({'class': 'form-control'})
    
    def clean_dia_vencimento(self):
        dia = self.cleaned_data.get('dia_vencimento')
        if dia and (dia < 1 or dia > 31):
            raise forms.ValidationError("Dia de vencimento deve estar entre 1 e 31")
        return dia
    
    def clean_dia_fechamento(self):
        dia = self.cleaned_data.get('dia_fechamento')
        if dia and (dia < 1 or dia > 31):
            raise forms.ValidationError("Dia de fechamento deve estar entre 1 e 31")
        return dia
    
    def clean_limite_total(self):
        limite = self.cleaned_data.get('limite_total')
        if limite and limite <= 0:
            raise forms.ValidationError("Limite total deve ser maior que zero")
        return limite