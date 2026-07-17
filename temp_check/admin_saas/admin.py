from django.contrib import admin
from .models import ClienteSaaS

@admin.register(ClienteSaaS)
class ClienteSaaSAdmin(admin.ModelAdmin):
    list_display = ('user', 'plano_ativo', 'ativo', 'data_expiracao')
    list_filter = ('plano_ativo', 'ativo', 'data_expiracao')
    search_fields = ('user__username', 'user__email')
