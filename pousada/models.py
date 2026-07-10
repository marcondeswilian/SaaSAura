from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone # Importante para a data

class Pousada(models.Model):
    dono = models.OneToOneField(User, on_delete=models.CASCADE, related_name='pousada_owner')
    nome = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    usa_checklist_limpeza = models.BooleanField(default=False)
    whatsapp_recepcao = models.CharField(max_length=20, blank=True, null=True)
    prefixo_pin_padrao = models.CharField(max_length=3, default="101")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome

class CategoriaQuarto(models.Model):
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='categorias')
    nome = models.CharField(max_length=100) # Ex: Suíte, Standard, Deluxe
    valor_diaria = models.DecimalField(max_digits=10, decimal_places=2)
    capacidade = models.IntegerField(default=2)

    class Meta:
        unique_together = ('pousada', 'nome')

    def __str__(self):
        return f"{self.nome} - R$ {self.valor_diaria}"

class Quarto(models.Model):
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='quartos')
    categoria = models.ForeignKey(CategoriaQuarto, on_delete=models.PROTECT, related_name='quartos')
    nome_identificacao = models.CharField(max_length=50) # Ex: 101, 102, Suíte do Lago
    ativo = models.BooleanField(default=True)
    status_limpeza = models.CharField(
        max_length=20, 
        choices=[('sujo', 'Sujo'), ('em_limpeza', 'Em Limpeza'), ('limpo', 'Limpo')], 
        default='limpo',
        db_index=True
    )

    def __str__(self):
        return f"{self.nome_identificacao} ({self.categoria.nome})"

class MotivoBloqueio(models.Model):
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='motivos_bloqueio')
    nome = models.CharField(max_length=100)
    cor = models.CharField(max_length=7, default='#475569')

    def __str__(self):
        return f"{self.nome} ({self.pousada.nome})"

class MetodoPagamentoConfig(models.Model):
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='metodos_pagamento')
    nome = models.CharField(max_length=100)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nome} ({self.pousada.nome})"


class LogAuditoria(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs_auditoria')
    acao = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    alvo_id = models.IntegerField(null=True, blank=True)
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, null=True, blank=True, related_name='logs_auditoria')

    def __str__(self):
        return f"{self.usuario} - {self.acao} - {self.timestamp}"


# Propriedade dinâmica para resolver a pousada associada ao usuário (dono ou funcionário)
@property
def get_user_pousada(self):
    try:
        if hasattr(self, 'pousada_owner'):
            return self.pousada_owner
    except Exception:
        pass
    
    cliente = getattr(self, 'cliente_saas', None)
    if cliente and cliente.pousada:
        return cliente.pousada
        
    raise AttributeError("Usuário não possui pousada vinculada.")

User.pousada = get_user_pousada


class ChecklistItem(models.Model):
    pousada = models.ForeignKey(Pousada, on_delete=models.SET_NULL, null=True, related_name='checklist_itens')
    descricao = models.CharField(max_length=255)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        nome_pousada = self.pousada.nome if self.pousada else "Pousada Removida"
        return f"{self.descricao} ({nome_pousada})"



class OrdemServico(models.Model):
    quarto = models.ForeignKey(Quarto, on_delete=models.CASCADE, related_name='ordens_servico')
    tipo_servico = models.CharField(
        max_length=20,
        choices=[
            ('limpeza', 'Limpeza'),
            ('encanamento', 'Encanamento'),
            ('eletrica', 'Elétrica'),
            ('outros', 'Outros')
        ],
        db_index=True
    )
    prioridade = models.CharField(
        max_length=15,
        choices=[
            ('baixa', 'Baixa'),
            ('media', 'Média'),
            ('alta', 'Alta')
        ],
        default='media'
    )
    descricao = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pendente', 'Pendente'),
            ('em_andamento', 'Em Andamento'),
            ('concluido', 'Concluído')
        ],
        default='pendente',
        db_index=True
    )
    criado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ordens_criadas')
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ordens_atribuidas')
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='ordens_servico')
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        tipo_display = dict([
            ('limpeza', 'Limpeza'),
            ('encanamento', 'Encanamento'),
            ('eletrica', 'Elétrica'),
            ('outros', 'Outros')
        ]).get(self.tipo_servico, self.tipo_servico)
        return f"OS #{self.id} - {tipo_display} - Quarto {self.quarto.nome_identificacao}"


class RegistroLimpeza(models.Model):
    quarto = models.ForeignKey(Quarto, on_delete=models.CASCADE, related_name='registros_limpeza')
    funcionario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registros_limpeza')
    data = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=20, 
        choices=[('sujo', 'Sujo'), ('em_limpeza', 'Em Limpeza'), ('limpo', 'Limpo')], 
        default='sujo',
        db_index=True
    )
    reserva_relacionada = models.ForeignKey('reservas.Reserva', on_delete=models.SET_NULL, null=True, blank=True, related_name='registros_limpeza')
    ordem_servico = models.OneToOneField(OrdemServico, on_delete=models.CASCADE, null=True, blank=True, related_name='registro_limpeza')


    def save(self, *args, **kwargs):
        if not hasattr(self, 'funcionario') or self.funcionario is None:
            from pousada.middleware import get_current_user
            user = get_current_user()
            if user and user.is_authenticated:
                self.funcionario = user
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Limpeza {self.quarto} - {self.status} - {self.data.strftime('%d/%m/%Y %H:%M')}"



class ItemLimpezaConcluido(models.Model):
    registro_limpeza = models.ForeignKey(RegistroLimpeza, on_delete=models.CASCADE, related_name='itens_concluidos')
    checklist_item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE)
    concluido = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.checklist_item.descricao} - {'OK' if self.concluido else 'Pendente'}"


class ConfiguracaoTuya(models.Model):
    access_id = models.CharField(max_length=100)
    access_secret = models.CharField(max_length=100)
    region = models.CharField(max_length=50, default='western_america')
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tuya Config - Region: {self.region}"


class Fechadura(models.Model):
    quarto = models.ForeignKey(Quarto, on_delete=models.CASCADE, related_name='fechaduras')
    device_id = models.CharField(max_length=100, unique=True)
    nome_exibicao = models.CharField(max_length=100)
    is_online = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome_exibicao} (Quarto {self.quarto.nome_identificacao})"

