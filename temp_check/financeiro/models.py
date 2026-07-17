from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator
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

    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='pagamentos', verbose_name="Pousada")
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='pagamentos', verbose_name="Reserva")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='saldo_final', verbose_name="Tipo")
    valor = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], verbose_name="Valor")
    metodo_pagamento = models.CharField(max_length=20, choices=METODO_PAGAMENTO_CHOICES, null=True, blank=True, verbose_name="Método de Pagamento")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente', verbose_name="Status")
    data_vencimento = models.DateField(verbose_name="Data de Vencimento")
    data_pagamento = models.DateField(null=True, blank=True, verbose_name="Data de Pagamento")
    observacao = models.CharField(max_length=255, blank=True, verbose_name="Observação")
    data_registro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Registro")

    class Meta:
        ordering = ['-data_vencimento']
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"
        indexes = [
            models.Index(fields=['pousada', 'status']),
            models.Index(fields=['reserva', 'status']),
        ]

    def __str__(self):
        return f"Pagamento {self.id} - {self.get_tipo_display()} ({self.get_status_display()}) - R$ {self.valor}"
