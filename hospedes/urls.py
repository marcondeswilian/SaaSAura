from django.urls import path
from .views import hospede_lista_view, hospede_criar_view, hospede_editar_view

urlpatterns = [
    path('painel/hospedes/', hospede_lista_view, name='hospede-lista'),
    path('painel/hospedes/criar/', hospede_criar_view, name='hospede-criar'),
    path('painel/hospedes/<int:pk>/editar/', hospede_editar_view, name='hospede-editar'),
]
