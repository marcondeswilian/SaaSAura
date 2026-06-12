from django.db import models
from pousada.models import Pousada
from reservas.models import Reserva

class Pagamento(models.Model):
    TIPO_CHOICES = [
        ('sinal', 'Sinal'),
        ('saldo_final', 'Saldo Final'),
        ('consumo', 'Consumo'),
    ]

    METODO_PAGAMENTO_CHOICES = [
        ('pix', 'Pix'),
        ('credito', 'Crédito'),
        ('debito', 'Débito'),
        ('dinheiro', 'Dinheiro'),
        ('transferencia', 'Transferência'),
    ]

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
        ('estornado', 'Estornado'),
    ]

    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='pagamentos')
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='pagamentos')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='saldo_final')
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pagamento = models.CharField(max_length=20, choices=METODO_PAGAMENTO_CHOICES, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    data_vencimento = models.DateField()
    data_pagamento = models.DateField(null=True, blank=True)
    observacao = models.CharField(max_length=255, blank=True)
    data_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pagamento {self.id} - {self.get_tipo_display()} ({self.get_status_display()}) - R$ {self.valor}"
