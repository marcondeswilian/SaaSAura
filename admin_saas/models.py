from django.db import models
from django.contrib.auth.models import User

class NivelAcesso(models.Model):
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome")
    pode_acessar_reservas = models.BooleanField(default=True, verbose_name="Acesso a Reservas")
    pode_acessar_crm = models.BooleanField(default=True, verbose_name="Acesso a CRM")
    pode_acessar_financeiro = models.BooleanField(default=True, verbose_name="Acesso ao Financeiro")
    pode_acessar_configuracoes = models.BooleanField(default=True, verbose_name="Acesso a Configurações")
    pode_acessar_governanca = models.BooleanField(default=True, verbose_name="Acesso a Governança")
    pode_apenas_bloquear_mapa = models.BooleanField(default=False, verbose_name="Apenas Bloqueio de Mapa")

    class Meta:
        verbose_name = "Nível de Acesso"
        verbose_name_plural = "Níveis de Acesso"

    def __str__(self):
        return self.nome

class ClienteSaaS(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cliente_saas', verbose_name="Usuário")
    nivel_acesso = models.ForeignKey(NivelAcesso, on_delete=models.SET_NULL, null=True, blank=True, related_name='clientes', verbose_name="Nível de Acesso")
    pousada = models.ForeignKey('pousada.Pousada', on_delete=models.SET_NULL, null=True, blank=True, related_name='funcionarios', verbose_name="Pousada")
    plano_ativo = models.BooleanField(default=True, verbose_name="Plano Ativo")
    data_expiracao = models.DateField(null=True, blank=True, verbose_name="Data de Expiração")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Cliente SaaS"
        verbose_name_plural = "Clientes SaaS"

    def __str__(self):
        return f"Cliente SaaS: {self.user.username} - {'Ativo' if self.ativo else 'Inativo'}"
