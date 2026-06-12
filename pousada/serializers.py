from rest_framework import serializers
from .models import Quarto

class QuartoSerializer(serializers.ModelSerializer):
    # O FullCalendar chama as linhas do mapa de 'resources' e espera um 'title'
    title = serializers.CharField(source='nome_identificacao')
    categoria = serializers.CharField(source='categoria.nome')

    class Meta:
        model = Quarto
        fields = ['id', 'title', 'categoria']