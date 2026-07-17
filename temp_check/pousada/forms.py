from django import forms
from .models import Pousada, OrdemServico, ChecklistItem, Quarto, CategoriaQuarto

class PousadaForm(forms.ModelForm):
    class Meta:
        model = Pousada
        fields = ['nome', 'logo', 'whatsapp_recepcao', 'prefixo_pin_padrao']

class OrdemServicoForm(forms.ModelForm):
    class Meta:
        model = OrdemServico
        fields = ['quarto', 'tipo_servico', 'prioridade', 'descricao', 'status', 'responsavel']

class ChecklistItemForm(forms.ModelForm):
    class Meta:
        model = ChecklistItem
        fields = ['descricao', 'ativo']

class QuartoForm(forms.ModelForm):
    class Meta:
        model = Quarto
        fields = ['categoria', 'nome_identificacao', 'senha_acesso']
