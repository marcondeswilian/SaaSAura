from django.db import models
from pousada.models import Pousada

class Tag(models.Model):
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='tags')
    nome = models.CharField(max_length=50)
    cor = models.CharField(max_length=7, default='#3b82f6')
    tipo = models.CharField(max_length=10, choices=[('H', 'Hóspede'), ('R', 'Reserva')], default='H')

    def __str__(self):
        return f"{self.nome} ({self.pousada.nome})"

class Hospede(models.Model):
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='hospedes')
    tags = models.ManyToManyField(Tag, blank=True)

    
    # Campos Padrão FNRH
    nome_completo = models.CharField(max_length=255)
    data_nascimento = models.DateField(null=True, blank=True)
    nacionalidade = models.CharField(max_length=100, default='Brasileiro(a)')
    sexo = models.CharField(max_length=20, choices=[('M', 'Masculino'), ('F', 'Feminino'), ('O', 'Outro')], null=True, blank=True)
    tipo_documento = models.CharField(max_length=50, choices=[('CPF', 'CPF'), ('RG', 'RG'), ('PAS', 'Passaporte')], default='CPF')
    numero_documento = models.CharField(max_length=50, null=True, blank=True)
    
    # Novos Campos FNRH da Fase 4
    cpf = models.CharField(max_length=20, null=True, blank=True)
    genero = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Feminino'), ('O', 'Outro')], null=True, blank=True)
    profissao = models.CharField(max_length=100, null=True, blank=True)
    cep = models.CharField(max_length=20, null=True, blank=True)
    endereco = models.CharField(max_length=255, null=True, blank=True)
    cidade = models.CharField(max_length=100, null=True, blank=True)
    estado = models.CharField(max_length=100, null=True, blank=True)
    
    # Contato e Endereço
    telefone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    endereco_completo = models.TextField(null=True, blank=True)
    
    # Campo FLEXÍVEL para futuras mudanças da FNRH (Ex: Nome social, placa veículo)
    dados_extras = models.JSONField(default=dict, blank=True)

    @property
    def link_whatsapp(self):
        if not self.telefone:
            return ""
        # Limpa os caracteres do telefone mantendo apenas números
        num_limpo = "".join([c for c in self.telefone if c.isdigit()])
        if not num_limpo:
            return ""
        # Se o número não começar com 55 e tiver tamanho de DDD + número, adiciona o DDI 55 do Brasil
        if not num_limpo.startswith('55') and len(num_limpo) >= 10:
            num_limpo = f"55{num_limpo}"
        return f"https://wa.me/{num_limpo}"

    def __str__(self):
        return self.nome_completo