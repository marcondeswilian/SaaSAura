from django.db import models
from django.contrib.auth.models import User

class NivelAcesso(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    pode_acessar_reservas = models.BooleanField(default=True)
    pode_acessar_crm = models.BooleanField(default=True)
    pode_acessar_financeiro = models.BooleanField(default=True)
    pode_acessar_configuracoes = models.BooleanField(default=True)
    pode_acessar_governanca = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

class ClienteSaaS(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cliente_saas')
    nivel_acesso = models.ForeignKey(NivelAcesso, on_delete=models.SET_NULL, null=True, blank=True, related_name='clientes')
    pousada = models.ForeignKey('pousada.Pousada', on_delete=models.SET_NULL, null=True, blank=True, related_name='funcionarios')
    plano_ativo = models.BooleanField(default=True)
    data_expiracao = models.DateField(null=True, blank=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"Cliente SaaS: {self.user.username} - {'Ativo' if self.ativo else 'Inativo'}"
