from django.db import models
from pousada.models import Pousada

class Tag(models.Model):
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='tags', verbose_name="Pousada")
    nome = models.CharField(max_length=50, verbose_name="Nome")
    cor = models.CharField(max_length=7, default='#3b82f6', verbose_name="Cor")
    tipo = models.CharField(max_length=10, choices=[('H', 'Hóspede'), ('R', 'Reserva')], default='H', verbose_name="Tipo")

    class Meta:
        ordering = ['nome']
        unique_together = ('pousada', 'nome')
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __str__(self):
        return f"{self.nome} ({self.pousada.nome})"

class Hospede(models.Model):
    ESTADOS_CHOICES = [
        ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
        ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
        ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
        ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
        ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins')
    ]

    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='hospedes', verbose_name="Pousada")
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="Tags")
    nome_completo = models.CharField(max_length=255, db_index=True, verbose_name="Nome Completo")
    data_nascimento = models.DateField(null=True, blank=True, verbose_name="Data de Nascimento")
    nacionalidade = models.CharField(max_length=100, default='Brasileira', blank=True, verbose_name="Nacionalidade")
    sexo = models.CharField(max_length=20, choices=[('M', 'Masculino'), ('F', 'Feminino'), ('O', 'Outro')], null=True, blank=True, verbose_name="Sexo")
    tipo_documento = models.CharField(max_length=50, choices=[('CPF', 'CPF'), ('RG', 'RG'), ('PAS', 'Passaporte')], default='CPF', blank=True, verbose_name="Tipo de Documento")
    numero_documento = models.CharField(max_length=50, null=True, blank=True, verbose_name="Número do Documento")
    cpf = models.CharField(max_length=20, null=True, blank=True, db_index=True, verbose_name="CPF")
    genero = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Feminino'), ('O', 'Outro')], null=True, blank=True, verbose_name="Gênero")
    profissao = models.CharField(max_length=100, null=True, blank=True, verbose_name="Profissão")
    cep = models.CharField(max_length=20, null=True, blank=True, verbose_name="CEP")
    endereco = models.CharField(max_length=255, null=True, blank=True, verbose_name="Endereço")
    cidade = models.CharField(max_length=100, null=True, blank=True, verbose_name="Cidade")
    estado = models.CharField(max_length=2, choices=ESTADOS_CHOICES, null=True, blank=True, verbose_name="Estado")
    telefone = models.CharField(max_length=20, null=True, blank=True, db_index=True, verbose_name="Telefone")
    email = models.EmailField(null=True, blank=True, db_index=True, verbose_name="E-mail")
    endereco_completo = models.TextField(null=True, blank=True, verbose_name="Endereço Completo")
    dados_extras = models.JSONField(default=dict, blank=True, verbose_name="Dados Extras")

    @property
    def link_whatsapp(self):
        if not self.telefone:
            return ""
        num_limpo = "".join([c for c in self.telefone if c.isdigit()])
        if not num_limpo:
            return ""
        if not num_limpo.startswith('55') and len(num_limpo) >= 10:
            num_limpo = f"55{num_limpo}"
        return f"https://wa.me/{num_limpo}"

    class Meta:
        ordering = ['nome_completo']
        verbose_name = "Hóspede"
        verbose_name_plural = "Hóspedes"
        indexes = [
            models.Index(fields=['pousada', 'nome_completo']),
            models.Index(fields=['pousada', 'cpf']),
        ]

    def __str__(self):
        return self.nome_completo