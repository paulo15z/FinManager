from django.db import models
from django.db.models import Sum
from django.core.exceptions import ValidationError
from decimal import Decimal

class Categoria(models.Model):
    nome = models.CharField(max_length=50, unique=True)
    descricao = models.TextField(blank=True, max_length=254, null=True)
    
    def __str__(self):
        return self.nome

class Fornecedor(models.Model):
    nome = models.CharField(max_length=100)
    cnpj = models.CharField(max_length=14, unique=True, blank=True, null=True)
    contato = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.nome


class Cofrinho(models.Model):
    nome = models.CharField(max_length=100)
    objetivo = models.TextField(blank=True)
    saldo = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    meta = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.nome


class CartaoCredito(models.Model):
    nome = models.CharField(max_length=100, help_text="Nome do cartão (ex: Nubank, Itaú, etc)")
    limite_total = models.DecimalField(max_digits=10, decimal_places=2, help_text="Limite total do cartão")
    limite_disponivel = models.DecimalField(max_digits=10, decimal_places=2, help_text="Limite disponível atual")
    dia_vencimento = models.IntegerField(help_text="Dia do vencimento da fatura (1-31)")
    dia_fechamento = models.IntegerField(help_text="Dia do fechamento da fatura (1-31)")
    ativo = models.BooleanField(default=True, help_text="Se o cartão está ativo para uso")
    observacoes = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Cartão de Crédito"
        verbose_name_plural = "Cartões de Crédito"
    
    def __str__(self):
        return f"{self.nome} - Limite: R$ {self.limite_disponivel}/{self.limite_total}"
    
    def limite_usado(self):
        """Retorna o valor do limite já utilizado"""
        return self.limite_total - self.limite_disponivel
    
    def percentual_usado(self):
        """Retorna o percentual do limite utilizado"""
        if self.limite_total > 0:
            return (self.limite_usado() / self.limite_total) * 100
        return 0
    
    def tem_limite_disponivel(self, valor):
        """Verifica se há limite disponível para uma compra"""
        return self.limite_disponivel >= valor
    
    def usar_limite(self, valor):
        """Usa uma parte do limite do cartão"""
        if not self.tem_limite_disponivel(valor):
            raise ValidationError(f"Limite insuficiente. Disponível: R$ {self.limite_disponivel}, Solicitado: R$ {valor}")
        self.limite_disponivel -= valor
        self.save(update_fields=['limite_disponivel'])
    
    def liberar_limite(self, valor):
        """Libera limite do cartão (para estornos ou exclusão de compras)"""
        novo_limite = self.limite_disponivel + valor
        if novo_limite > self.limite_total:
            novo_limite = self.limite_total
        self.limite_disponivel = novo_limite
        self.save(update_fields=['limite_disponivel'])


class Lancamento(models.Model):
    TIPO_CHOICES = [
        ("entrada", "Entrada"),
        ("saida", "Saida"),
    ]
    PAGAMENTO_CHOICES = [
        ("dinheiro", "Dinheiro"),
        ("pix", "PIX"),
        ("cartao_credito", "Cartão de Crédito"),
        ("cartao_debito", "Cartão de Débito"),
        ("caderno", "Caderno"),
    ]

    descricao = models.CharField(max_length=255)

    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)

    valor = models.DecimalField(max_digits=10, decimal_places=2)

    data = models.DateField()

    categoria = models.ForeignKey("Categoria", on_delete=models.SET_NULL, null=True, blank=True, related_name="lancamentos")

    fornecedor = models.ForeignKey("Fornecedor", on_delete=models.SET_NULL, null=True, blank=True, related_name="Lancamentos")

    observacoes = models.TextField(blank=True, null=True)

    metodo_pagamento = models.CharField(max_length=100, choices=PAGAMENTO_CHOICES, null=True, blank=True)

    cofrinho_destino = models.ForeignKey("Cofrinho", on_delete=models.SET_NULL, null=True, blank=True, related_name="transferencias")

    cartao_credito = models.ForeignKey("CartaoCredito", on_delete=models.SET_NULL, null=True, blank=True, related_name="lancamentos")
    
    
    def __str__(self):
        cartao_info = f" - {self.cartao_credito.nome}" if self.cartao_credito else ""
        return f"{self.descricao} ({self.tipo.capitalize()}) - R$ {self.valor}{cartao_info}"
