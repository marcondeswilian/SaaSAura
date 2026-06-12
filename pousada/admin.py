from django.contrib import admin
from .models import Pousada

@admin.register(Pousada)
class PousadaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo', 'dono') # Removi o 'plano' daqui

from .models import CategoriaQuarto, Quarto, MotivoBloqueio

@admin.register(CategoriaQuarto)
class CategoriaQuartoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'valor_diaria', 'capacidade')

@admin.register(Quarto)
class QuartoAdmin(admin.ModelAdmin):
    list_display = ('nome_identificacao', 'categoria', 'ativo')

@admin.register(MotivoBloqueio)
class MotivoBloqueioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'pousada')
    list_filter = ('pousada',)

from .models import ConfiguracaoTuya, Fechadura

@admin.register(ConfiguracaoTuya)
class ConfiguracaoTuyaAdmin(admin.ModelAdmin):
    list_display = ('region', 'data_criacao')

@admin.register(Fechadura)
class FechaduraAdmin(admin.ModelAdmin):
    list_display = ('nome_exibicao', 'quarto', 'device_id', 'is_online')
