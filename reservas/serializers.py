from rest_framework import serializers
from .models import Reserva

class ReservaSerializer(serializers.ModelSerializer):
    # O FullCalendar (Javascript) exige esses nomes exatos de campos:
    start = serializers.SerializerMethodField()
    end = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    resourceId = serializers.IntegerField(source='quarto.id')
    color = serializers.SerializerMethodField()
    allDay = serializers.SerializerMethodField()
    hospede_nome = serializers.SerializerMethodField()
    celular = serializers.SerializerMethodField()
    valor_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    saldo_devedor = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Reserva
        fields = [
            'id', 'start', 'end', 'title', 'resourceId', 'status', 'color', 'allDay', 'is_bloqueio',
            'hospede_nome', 'celular', 'valor_total', 'saldo_devedor'
        ]

    def get_allDay(self, obj):
        return False

    def get_start(self, obj):
        return f"{obj.data_checkin}T14:00:00"

    def get_end(self, obj):
        return f"{obj.data_checkout}T10:00:00"

    def get_title(self, obj):
        if obj.is_bloqueio:
            return obj.motivo_bloqueio.nome if obj.motivo_bloqueio else "Bloqueio"
        return obj.hospede.nome_completo if obj.hospede else "Reserva"

    def get_color(self, obj):
        if obj.is_bloqueio:
            return obj.motivo_bloqueio.cor if (obj.motivo_bloqueio and obj.motivo_bloqueio.cor) else '#475569'
        return '#3b82f6'

    def get_hospede_nome(self, obj):
        return obj.hospede.nome_completo if obj.hospede else "Bloqueio"

    def get_celular(self, obj):
        return obj.hospede.telefone if (obj.hospede and obj.hospede.telefone) else ""


class ReservaUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reserva
        fields = ['data_checkin', 'data_checkout', 'quarto']

    def validate(self, data):
        # Extract fields from payload or from existing instance
        quarto = data.get('quarto', self.instance.quarto if self.instance else None)
        data_checkin = data.get('data_checkin', self.instance.data_checkin if self.instance else None)
        data_checkout = data.get('data_checkout', self.instance.data_checkout if self.instance else None)

        if not quarto or not data_checkin or not data_checkout:
            return data

        # Check for overlapping reservations
        overlaps = Reserva.objects.filter(
            quarto=quarto,
            data_checkin__lt=data_checkout,
            data_checkout__gt=data_checkin
        )

        if self.instance and self.instance.pk:
            overlaps = overlaps.exclude(pk=self.instance.pk)

        if overlaps.exists():
            raise serializers.ValidationError('Este quarto já possui uma reserva para o período selecionado.')

        return data