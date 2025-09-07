from django.urls import path
from . import views
from .views import RelatorioDREView, RelatorioEntradasSaidasView, RelatoriosDashboardView

app_name = 'relatorios' # Boa prática para evitar conflito de nomes de URL

urlpatterns = [
    # A nova "home" do app de relatórios, acessível em /relatorios/
    path('', RelatoriosDashboardView.as_view(), name='dashboard'),
    
    # O relatório DRE detalhado, acessível em /relatorios/dre/
    path('dre/', RelatorioDREView.as_view(), name='dre_detalhado'),

    
]