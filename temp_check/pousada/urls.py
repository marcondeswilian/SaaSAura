from django.urls import path
from .views import pousada_config_view, gerenciar_equipe, ver_logs, governanca_dashboard, governanca_mobile_view

urlpatterns = [
    path('painel/pousada/config/', pousada_config_view, name='pousada-config'),
    path('painel/pousada/config/equipe/', gerenciar_equipe, name='gerenciar-equipe'),
    path('painel/pousada/config/auditoria/', ver_logs, name='ver-logs'),
    path('painel/governanca/', governanca_dashboard, name='governanca-dashboard'),
    path('painel/governanca/mobile/', governanca_mobile_view, name='governanca-mobile'),
]
