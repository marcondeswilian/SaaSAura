from django import forms
from .models import Hospede, Tag

class HospedeForm(forms.ModelForm):
    class Meta:
        model = Hospede
        fields = [
            'nome_completo', 'data_nascimento', 'nacionalidade', 'sexo',
            'tipo_documento', 'numero_documento', 'cpf', 'genero',
            'profissao', 'cep', 'endereco', 'cidade', 'estado',
            'telefone', 'email', 'endereco_completo', 'dados_extras'
        ]
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
        }

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['nome', 'cor', 'tipo']
