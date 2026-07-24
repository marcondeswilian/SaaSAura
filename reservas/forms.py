from django import forms
from .models import Reserva
from pousada.models import CanalOrigem, Quarto
from financeiro.models import Pagamento

class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = [
            'hospede', 'quarto', 'canal_origem', 'data_checkin', 'data_checkout',
            'motivo_viagem', 'meio_transporte', 'placa_veiculo',
            'ultima_procedencia', 'proximo_destino', 'status',
            'valor_total', 'is_bloqueio', 'motivo_bloqueio'
        ]
        widgets = {
            'data_checkin': forms.DateInput(attrs={'type': 'date'}),
            'data_checkout': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        pousada = kwargs.pop('pousada', None)
        super().__init__(*args, **kwargs)
        pousada_obj = pousada or (self.instance.pousada if self.instance and self.instance.pk else None)
        if pousada_obj:
            self.fields['canal_origem'].queryset = CanalOrigem.objects.filter(pousada=pousada_obj, ativo=True)
            self.fields['quarto'].queryset = Quarto.objects.filter(pousada=pousada_obj, ativo=True)


class PagamentoForm(forms.ModelForm):
    class Meta:
        model = Pagamento
        fields = ['tipo', 'valor', 'metodo_pagamento', 'data_pagamento']
        widgets = {
            'data_pagamento': forms.DateInput(attrs={'type': 'date'}),
        }
