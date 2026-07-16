from django.contrib import admin
from .models import Reserva

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('quarto', 'hospede', 'data_checkin', 'data_checkout', 'status')
    
    # Isso cria uma navegação por datas no topo da tela
    date_hierarchy = 'data_checkin'
    
    # Isso permite filtrar por status e pelo quarto
    list_filter = ('status', 'data_checkin')
    
    # Campo de busca para achar o hóspede rapidamente
    search_fields = ('hospede__nome_completo',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'hospede', 'quarto', 'quarto__categoria', 'pousada'
        )

    def has_change_permission(self, request, obj=None):
        if obj and obj.status in ('finalizada', 'cancelada'):
            return False
        return True

from .models import Grupo, Acompanhante, FichaFNRH, TemplateMensagem, LogDisparoMensagem

@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'created_at')

@admin.register(Acompanhante)
class AcompanhanteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'reserva', 'cpf')

@admin.register(FichaFNRH)
class FichaFNRHAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'reserva', 'cpf_passaporte', 'telefone', 'email')

@admin.register(TemplateMensagem)
class TemplateMensagemAdmin(admin.ModelAdmin):
    list_display = ('nome', 'canal', 'gatilho', 'ativo')

@admin.register(LogDisparoMensagem)
class LogDisparoMensagemAdmin(admin.ModelAdmin):
    list_display = ('reserva', 'template', 'data_disparo', 'status')