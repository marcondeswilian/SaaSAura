from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
from .models import Pagamento

@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ('reserva', 'tipo', 'valor', 'metodo_pagamento', 'status', 'data_pagamento')
    list_filter = ('status', 'tipo', 'metodo_pagamento', 'pousada')
    search_fields = ('reserva__hospede__nome_completo', 'observacao')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        try:
            return qs.filter(pousada=request.user.pousada)
        except (AttributeError, ObjectDoesNotExist):
            return qs.none()
