from django.urls import path
from .views import (
    ReservaListAPI, 
    QuartoListAPI, 
    CalendarioView, 
    ReservaUpdateAPI,
    reserva_lista_view,
    reserva_criar_view,
    api_hospedes_list_create,
    exportar_fnrh_csv,
    reserva_editar_view,
    api_quartos_disponiveis,
    registrar_pagamento,
    editar_pagamento,
    dashboard_view,
    portal_hospede,
    imprimir_fnrh_view
)

urlpatterns = [
    path('api/reservas/', ReservaListAPI.as_view(), name='api-reservas'),
    path('api/reservas/<int:pk>/update/', ReservaUpdateAPI.as_view(), name='api-reserva-update'),
    path('api/quartos/', QuartoListAPI.as_view(), name='api-quartos'),
    path('calendario/', CalendarioView.as_view(), name='calendario'),
    
    # Novas rotas customizadas
    path('painel/reservas/', reserva_lista_view, name='reserva-lista'),
    path('painel/reservas/criar/', reserva_criar_view, name='reserva-criar'),
    path('painel/reservas/api/quartos-disponiveis/', api_quartos_disponiveis, name='api-quartos-disponiveis'),
    path('api/hospedes/', api_hospedes_list_create, name='api-hospedes-list-create'),
    path('painel/reservas/exportar-fnrh/', exportar_fnrh_csv, name='exportar-fnrh'),
    path('painel/reservas/<int:pk>/editar/', reserva_editar_view, name='reserva-editar'),
    path('painel/reservas/registrar-pagamento/', registrar_pagamento, name='registrar-pagamento'),
    path('painel/reservas/pagamentos/<int:pk>/editar/', editar_pagamento, name='editar-pagamento'),
    path('checkin/online/', lambda r: __import__('django.http', fromlist=['HttpResponseGone']).HttpResponseGone(), name='checkin-online-legado'),  # rota legada removida
    # Portal unificado do hóspede — única porta de entrada
    path('hospede/meu-acesso/<uuid:token>/', portal_hospede, name='portal_hospede'),
    path('painel/dashboard/', dashboard_view, name='dashboard'),
    path('reserva/<int:pk>/fnrh/imprimir/', imprimir_fnrh_view, name='imprimir_fnrh'),
]