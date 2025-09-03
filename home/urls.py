from django.urls import path
from .views import (
    HomeView,
    LancamentoListView, LancamentoCreateView, LancamentoUpdateView, LancamentoDeleteView,
    FornecedorListView, FornecedorCreateView, FornecedorUpdateView, FornecedorDeleteView,
    CategoriaListView, CategoriaCreateView, CategoriaUpdateView, CategoriaDeleteView,
    CofrinhoListView, CofrinhoCreateView, CofrinhoUpdateView, CofrinhoDeleteView,
    TransferirParaCofrinhoView,
    RelatorioEntradasSaidasView
)

urlpatterns = [
    # Rotas da Home
    path('', HomeView.as_view(), name='home'),

    # Rotas de Lançamentos
    path('lancamentos/', LancamentoListView.as_view(), name='lista_lancamentos'),
    path('lancamentos/adicionar/', LancamentoCreateView.as_view(), name='adicionar_lancamento'),
    path('lancamentos/editar/<int:pk>/', LancamentoUpdateView.as_view(), name='editar_lancamento'),
    path('lancamentos/deletar/<int:pk>/', LancamentoDeleteView.as_view(), name='deletar_lancamento'),

    # Rotas de Cofrinhos
    path('cofrinhos/', CofrinhoListView.as_view(), name='lista_cofrinhos'),
    path('cofrinhos/adicionar/', CofrinhoCreateView.as_view(), name='adicionar_cofrinho'),
    path('cofrinhos/editar/<int:pk>/', CofrinhoUpdateView.as_view(), name='editar_cofrinho'),
    path('cofrinhos/deletar/<int:pk>/', CofrinhoDeleteView.as_view(), name='deletar_cofrinho'),
    path('cofrinhos/transferir/', TransferirParaCofrinhoView.as_view(), name='transferir_cofrinho'),

    # Rotas de Fornecedores
    path('fornecedores/', FornecedorListView.as_view(), name='lista_fornecedores'),
    path('fornecedores/adicionar/', FornecedorCreateView.as_view(), name='adicionar_fornecedor'),
    path('fornecedores/editar/<int:pk>/', FornecedorUpdateView.as_view(), name='editar_fornecedor'),
    path('fornecedores/deletar/<int:pk>/', FornecedorDeleteView.as_view(), name='deletar_fornecedor'),

    # Rotas de Categorias
    path('categorias/', CategoriaListView.as_view(), name='lista_categorias'),
    path('categorias/adicionar/', CategoriaCreateView.as_view(), name='adicionar_categoria'),
    path('categorias/editar/<int:pk>/', CategoriaUpdateView.as_view(), name='editar_categoria'),
    path('categorias/deletar/<int:pk>/', CategoriaDeleteView.as_view(), name='deletar_categoria'),

    # Rotas de Relatórios
    path('relatorios/entradas-saidas/', RelatorioEntradasSaidasView.as_view(), name='relatorio_entradas_saidas'),
]