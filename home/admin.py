from django.contrib import admin
from .models import Categoria, Lancamento, Fornecedor, Cofrinho, CartaoCredito # Adicione Categoria se não estiver

# Register your models here.
admin.site.register(Cofrinho)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria_pai', 'descricao') # colunas q vao ser mostradas
    list_filter = ('categoria_pai',)
    search_fields = ('nome', 'categoria_pai__nome')

    fieldsets = (
        (None, {
            'fields': ('nome', 'descricao')
        }),
        ('Hierarquia', {
            'fields': ('categoria_pai',)
        }),
    )
