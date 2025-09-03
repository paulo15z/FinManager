from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Rota para o painel de administração do Django
    path('admin/', admin.site.urls),

    # Inclui todas as URLs do seu app 'home'.
    # A URL vazia '' indica que as rotas de 'home' serão acessadas
    # diretamente após o domínio, por exemplo: meuprojeto.com/adicionar-lancamento
    path('', include('home.urls')),

    # Se você tivesse outro app, por exemplo 'relatorios', a sintaxe seria:
    # path('relatorios/', include('relatorios.urls')),
    # que resultaria em URLs como: meuprojeto.com/relatorios/mensal/
]