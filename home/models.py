from django.db import models
from django.db.models import Sum

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

class Lancamento(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saida'),
    ]
    PAGAMENTO_CHOICES = [
        ('dinheiro', 'Dinheiro'),
        ('pix', 'PIX'),
        ('cartao_credito', 'Cartão de Crédito'),
        ('cartao_debito', 'Cartão de Débito'),
        ('caderno', 'Caderno'),
    ]

    descricao = models.CharField(max_length=255)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateField()
    categoria = models.ForeignKey(
        'Categoria',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lancamentos'
    )
    fornecedor = models.ForeignKey(
        'Fornecedor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='Lancamentos'
    )
    observacoes = models.TextField(blank=True, null=True)
    metodo_pagamento = models.CharField(max_length=100, choices=PAGAMENTO_CHOICES, null=True, blank=True)
    cofrinho_destino = models.ForeignKey(
        'Cofrinho',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transferencias'
    )
    

    def __str__(self):
        return f'{self.descricao} ({self.tipo.capitalize()}) - R$ {self.valor}'