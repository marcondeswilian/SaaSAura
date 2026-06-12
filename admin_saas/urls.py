from django.urls import path
from .views import (
    admin_saas_dashboard,
    toggle_cliente_ativo,
    atualizar_cliente_saas,
    criar_cliente_saas,
    criar_nivel_acesso,
    atualizar_nivel_acesso,
    excluir_nivel_acesso,
    testar_email,
)

urlpatterns = [
    path('', admin_saas_dashboard, name='admin-saas-dashboard'),
    path('clientes/criar/', criar_cliente_saas, name='admin-saas-criar-cliente'),
    path('clientes/<int:pk>/toggle/', toggle_cliente_ativo, name='admin-saas-toggle-ativo'),
    path('clientes/<int:pk>/atualizar/', atualizar_cliente_saas, name='admin-saas-atualizar-cliente'),
    path('niveis/criar/', criar_nivel_acesso, name='admin-saas-criar-nivel'),
    path('niveis/<int:pk>/atualizar/', atualizar_nivel_acesso, name='admin-saas-atualizar-nivel'),
    path('niveis/<int:pk>/excluir/', excluir_nivel_acesso, name='admin-saas-excluir-nivel'),
    path('testar-email/', testar_email, name='admin-saas-testar-email'),
]
