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

from .models import MetodoPagamentoConfig, CanalOrigem, LogAuditoria, ChecklistItem, OrdemServico, RegistroLimpeza

@admin.register(MetodoPagamentoConfig)
class MetodoPagamentoConfigAdmin(admin.ModelAdmin):
    list_display = ('nome', 'pousada', 'ativo')

@admin.register(CanalOrigem)
class CanalOrigemAdmin(admin.ModelAdmin):
    list_display = ('nome', 'pousada', 'cor', 'ativo')
    list_filter = ('pousada', 'ativo')


@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'acao', 'timestamp', 'pousada')

@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'pousada', 'ativo')

@admin.register(OrdemServico)
class OrdemServicoAdmin(admin.ModelAdmin):
    list_display = ('id', 'quarto', 'tipo_servico', 'prioridade', 'status', 'responsavel')

@admin.register(RegistroLimpeza)
class RegistroLimpezaAdmin(admin.ModelAdmin):
    list_display = ('quarto', 'funcionario', 'data', 'status')
