from django.urls import path
from . import views

urlpatterns = [

    path('entradas-saidas', views.RelatorioEntradasSaidasView.as_view(), name='relatorio_entradas_saidas')

]