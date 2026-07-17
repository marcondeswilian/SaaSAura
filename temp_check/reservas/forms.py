from django import forms
from .models import Reserva
from financeiro.models import Pagamento

class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = [
            'hospede', 'quarto', 'data_checkin', 'data_checkout',
            'motivo_viagem', 'meio_transporte', 'placa_veiculo',
            'ultima_procedencia', 'proximo_destino', 'status',
            'valor_total', 'is_bloqueio', 'motivo_bloqueio'
        ]
        widgets = {
            'data_checkin': forms.DateInput(attrs={'type': 'date'}),
            'data_checkout': forms.DateInput(attrs={'type': 'date'}),
        }

class PagamentoForm(forms.ModelForm):
    class Meta:
        model = Pagamento
        fields = ['tipo', 'valor', 'metodo_pagamento', 'data_pagamento']
        widgets = {
            'data_pagamento': forms.DateInput(attrs={'type': 'date'}),
        }
