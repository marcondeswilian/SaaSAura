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
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # BUGFIX: Garantir que apenas nome_completo seja obrigatório no CRM interno
        for field_name, field in self.fields.items():
            if field_name != 'nome_completo':
                field.required = False

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['nome', 'cor', 'tipo']
