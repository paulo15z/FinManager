from django.urls import path
from .views import (
    HomeView,
    LancamentoListView, LancamentoCreateView, LancamentoUpdateView, LancamentoDeleteView,
    FornecedorListView, FornecedorCreateView, FornecedorUpdateView, FornecedorDeleteView,
    CategoriaListView, CategoriaCreateView, CategoriaUpdateView, CategoriaDeleteView,
    CofrinhoListView, CofrinhoCreateView, CofrinhoUpdateView, CofrinhoDeleteView, TransferirParaCofrinhoView,
    TransferirParaCofrinhoView, CartaoCreditoCreateView, CartaoCreditoDeleteView, CartaoCreditoDetailView, CartaoCreditoListView, CartaoCreditoUpdateView, ResetarLimiteCartaoView
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

    # Rotas de cartao de credito

    path('cartoes/', CartaoCreditoListView.as_view(), name='lista_cartoes'),
    path('cartoes/adicionar/', CartaoCreditoCreateView.as_view(), name='adicionar_cartao'),
    path('cartoes/<int:pk>/editar/', CartaoCreditoUpdateView.as_view(), name='editar_cartao'),
    path('cartoes/<int:pk>/deletar/', CartaoCreditoDeleteView.as_view(), name='deletar_cartao'),
    path('cartoes/<int:pk>/detalhes/', CartaoCreditoDetailView.as_view(), name='detalhes_cartao'),
    path('cartoes/<int:pk>/resetar-limite/', ResetarLimiteCartaoView.as_view(), name='resetar_limite_cartao'),
    
]