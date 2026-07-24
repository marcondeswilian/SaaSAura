from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone # Importante para a data

class Pousada(models.Model):
    dono = models.OneToOneField(User, on_delete=models.CASCADE, related_name='pousada_owner', verbose_name="Dono")
    nome = models.CharField(max_length=255, verbose_name="Nome")
    slug = models.SlugField(unique=True, blank=True, verbose_name="Slug")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True, verbose_name="Logo")
    usa_checklist_limpeza = models.BooleanField(default=False, verbose_name="Usa Checklist de Limpeza")
    whatsapp_recepcao = models.CharField(max_length=20, blank=True, null=True, verbose_name="WhatsApp da Recepção")
    prefixo_pin_padrao = models.CharField(max_length=3, default="101", verbose_name="Prefixo PIN Padrão")
    mensagem_pos_checkin = models.TextField(blank=True, null=True, verbose_name="Mensagem Pós Check-in Online")
    video_pos_checkin = models.URLField(blank=True, null=True, verbose_name="Vídeo Pós Check-in (YouTube/Vimeo)")

    class Meta:
        verbose_name = "Pousada"
        verbose_name_plural = "Pousadas"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nome)
            slug = base_slug
            counter = 1
            while Pousada.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome

class CategoriaQuarto(models.Model):
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='categorias', verbose_name="Pousada")
    nome = models.CharField(max_length=100, verbose_name="Nome")
    valor_diaria = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor da Diária")
    capacidade = models.IntegerField(default=2, verbose_name="Capacidade")

    class Meta:
        verbose_name = "Categoria de Quarto"
        verbose_name_plural = "Categorias de Quartos"
        unique_together = ('pousada', 'nome')

    def __str__(self):
        return f"{self.nome} - R$ {self.valor_diaria}"

class Quarto(models.Model):
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='quartos', verbose_name="Pousada")
    categoria = models.ForeignKey(CategoriaQuarto, on_delete=models.PROTECT, related_name='quartos', verbose_name="Categoria")
    nome_identificacao = models.CharField(max_length=50, verbose_name="Identificação do Quarto")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    status_limpeza = models.CharField(
        max_length=20, 
        choices=[('sujo', 'Sujo'), ('em_limpeza', 'Em Limpeza'), ('limpo', 'Limpo')], 
        default='limpo',
        db_index=True,
        verbose_name="Status da Limpeza"
    )
    senha_acesso = models.CharField(max_length=50, blank=True, null=True, verbose_name="Senha de Acesso (Manual)")

    class Meta:
        verbose_name = "Quarto"
        verbose_name_plural = "Quartos"

    def __str__(self):
        return f"{self.nome_identificacao} ({self.categoria.nome})"

class MotivoBloqueio(models.Model):
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='motivos_bloqueio', verbose_name="Pousada")
    nome = models.CharField(max_length=100, verbose_name="Nome")
    cor = models.CharField(max_length=7, default='#475569', verbose_name="Cor")

    class Meta:
        verbose_name = "Motivo de Bloqueio"
        verbose_name_plural = "Motivos de Bloqueios"

    def __str__(self):
        return f"{self.nome} ({self.pousada.nome})"

class MetodoPagamentoConfig(models.Model):
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='metodos_pagamento', verbose_name="Pousada")
    nome = models.CharField(max_length=100, verbose_name="Nome")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Método de Pagamento"
        verbose_name_plural = "Métodos de Pagamento"

    def __str__(self):
        return f"{self.nome} ({self.pousada.nome})"

class CanalOrigem(models.Model):
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='canais_origem', verbose_name="Pousada")
    nome = models.CharField(max_length=100, verbose_name="Nome do Canal")
    cor = models.CharField(max_length=20, default='#6b7280', verbose_name="Cor da Badge")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Canal de Origem"
        verbose_name_plural = "Canais de Origem"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.pousada.nome})"



class LogAuditoria(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs_auditoria', verbose_name="Usuário")
    acao = models.CharField(max_length=255, verbose_name="Ação")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Data/Hora")
    alvo_id = models.IntegerField(null=True, blank=True, verbose_name="ID Alvo")
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, null=True, blank=True, related_name='logs_auditoria', verbose_name="Pousada")

    class Meta:
        verbose_name = "Log de Auditoria"
        verbose_name_plural = "Logs de Auditorias"

    def __str__(self):
        return f"{self.usuario} - {self.acao} - {self.timestamp}"


class ChecklistItem(models.Model):
    pousada = models.ForeignKey(Pousada, on_delete=models.SET_NULL, null=True, related_name='checklist_itens', verbose_name="Pousada")
    descricao = models.CharField(max_length=255, verbose_name="Descrição")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Item de Checklist"
        verbose_name_plural = "Itens de Checklist"

    def __str__(self):
        nome_pousada = self.pousada.nome if self.pousada else "Pousada Removida"
        return f"{self.descricao} ({nome_pousada})"



class OrdemServico(models.Model):
    quarto = models.ForeignKey(Quarto, on_delete=models.CASCADE, related_name='ordens_servico', verbose_name="Quarto")
    tipo_servico = models.CharField(
        max_length=20,
        choices=[
            ('limpeza', 'Limpeza'),
            ('encanamento', 'Encanamento'),
            ('eletrica', 'Elétrica'),
            ('outros', 'Outros')
        ],
        db_index=True,
        verbose_name="Tipo de Serviço"
    )
    prioridade = models.CharField(
        max_length=15,
        choices=[
            ('baixa', 'Baixa'),
            ('media', 'Média'),
            ('alta', 'Alta')
        ],
        default='media',
        verbose_name="Prioridade"
    )
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    status = models.CharField(
        max_length=20,
        choices=[
            ('pendente', 'Pendente'),
            ('em_andamento', 'Em Andamento'),
            ('concluido', 'Concluído')
        ],
        default='pendente',
        db_index=True,
        verbose_name="Status"
    )
    criado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ordens_criadas', verbose_name="Criado Por")
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ordens_atribuidas', verbose_name="Responsável")
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='ordens_servico', verbose_name="Pousada")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    data_conclusao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Conclusão")

    class Meta:
        verbose_name = "Ordem de Serviço"
        verbose_name_plural = "Ordens de Serviço"

    def __str__(self):
        return f"OS #{self.id} - {self.get_tipo_servico_display()} - Quarto {self.quarto.nome_identificacao}"


class RegistroLimpeza(models.Model):
    quarto = models.ForeignKey(Quarto, on_delete=models.CASCADE, related_name='registros_limpeza', verbose_name="Quarto")
    funcionario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registros_limpeza', verbose_name="Funcionário")
    data = models.DateTimeField(default=timezone.now, verbose_name="Data")
    status = models.CharField(
        max_length=20, 
        choices=[('sujo', 'Sujo'), ('em_limpeza', 'Em Limpeza'), ('limpo', 'Limpo')], 
        default='sujo',
        db_index=True,
        verbose_name="Status"
    )
    reserva_relacionada = models.ForeignKey('reservas.Reserva', on_delete=models.SET_NULL, null=True, blank=True, related_name='registros_limpeza', verbose_name="Reserva Relacionada")
    ordem_servico = models.OneToOneField(OrdemServico, on_delete=models.CASCADE, null=True, blank=True, related_name='registro_limpeza', verbose_name="Ordem de Serviço")

    class Meta:
        verbose_name = "Registro de Limpeza"
        verbose_name_plural = "Registros de Limpezas"

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
    registro_limpeza = models.ForeignKey(RegistroLimpeza, on_delete=models.CASCADE, related_name='itens_concluidos', verbose_name="Registro de Limpeza")
    checklist_item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE, verbose_name="Item de Checklist")
    concluido = models.BooleanField(default=False, verbose_name="Concluído")

    class Meta:
        verbose_name = "Item de Checklist Concluído"
        verbose_name_plural = "Itens de Checklist Concluídos"

    def __str__(self):
        return f"{self.checklist_item.descricao} - {'OK' if self.concluido else 'Pendente'}"


class ConfiguracaoTuya(models.Model):
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='configuracoes_tuya', null=True, blank=True, verbose_name="Pousada")
    access_id = models.CharField(max_length=100, verbose_name="Access ID")
    access_secret = models.CharField(max_length=100, verbose_name="Access Secret")
    region = models.CharField(max_length=50, default='western_america', verbose_name="Região")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")

    class Meta:
        verbose_name = "Configuração da Tuya"
        verbose_name_plural = "Configurações da Tuya"

    def __str__(self):
        nome_pousada = self.pousada.nome if self.pousada else "Global"
        return f"Tuya Config ({nome_pousada}) - Region: {self.region}"


class Fechadura(models.Model):
    quarto = models.ForeignKey(Quarto, on_delete=models.CASCADE, related_name='fechaduras', verbose_name="Quarto")
    device_id = models.CharField(max_length=100, unique=True, verbose_name="Device ID")
    nome_exibicao = models.CharField(max_length=100, verbose_name="Nome de Exibição")
    is_online = models.BooleanField(default=True, verbose_name="Online")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")

    class Meta:
        verbose_name = "Fechadura"
        verbose_name_plural = "Fechaduras"

    def __str__(self):
        return f"{self.nome_exibicao} (Quarto {self.quarto.nome_identificacao})"

