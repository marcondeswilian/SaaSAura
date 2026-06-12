from django.contrib import admin
from .models import Reserva

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('quarto', 'hospede', 'data_checkin', 'data_checkout', 'status')
    
    # Isso cria uma navegação por datas no topo da tela
    date_hierarchy = 'data_checkin'
    
    # Isso permite filtrar por status e pelo quarto
    list_filter = ('status', 'quarto', 'data_checkin')
    
    # Campo de busca para achar o hóspede rapidamente
    search_fields = ('hospede__nome_completo',)

    # Dica: Bloqueia a edição se a reserva já estiver encerrada (opcional)
    def has_change_permission(self, request, obj=None):
        return True # Aqui você pode adicionar lógica de permissão depois