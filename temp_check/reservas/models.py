from django.db import models
from django.db.models import Sum
from decimal import Decimal
from pousada.models import Pousada, Quarto # Adicionamos o Quarto aqui
from hospedes.models import Hospede
import uuid

class Grupo(models.Model):
    nome = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nome")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")

    class Meta:
        verbose_name = "Grupo de Reserva"
        verbose_name_plural = "Grupos de Reservas"

    def __str__(self):
        return self.nome or f"Grupo {self.id}"

class Reserva(models.Model):
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='reservas', verbose_name="Pousada")
    grupo = models.ForeignKey(Grupo, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservas', verbose_name="Grupo")
    hospede = models.ForeignKey(Hospede, on_delete=models.CASCADE, related_name='reservas', null=True, blank=True, verbose_name="Hóspede")
    quarto = models.ForeignKey(Quarto, on_delete=models.PROTECT, related_name='reservas', verbose_name="Quarto")

    data_checkin = models.DateField(verbose_name="Data de Check-in")
    data_checkout = models.DateField(verbose_name="Data de Check-out")
    
    motivo_viagem = models.CharField(
        max_length=50, 
        choices=[
            ('lazer', 'Lazer'), 
            ('negocios', 'Negócios'),
            ('congresso', 'Congresso/Convenção'),
            ('parentes', 'Parentes/Amigos'),
            ('estudos', 'Estudos'),
            ('saude', 'Saúde'),
            ('compras', 'Compras'),
            ('outro', 'Outro')
        ], 
        blank=True, 
        null=True,
        verbose_name="Motivo da Viagem"
    )
    meio_transporte = models.CharField(
        max_length=50,
        choices=[
            ('aviao', 'Avião'),
            ('automovel', 'Automóvel'),
            ('onibus', 'Ônibus'),
            ('trem', 'Trem'),
            ('embarcacao', 'Embarcação'),
            ('outro', 'Outro')
        ],
        blank=True,
        null=True,
        verbose_name="Meio de Transporte"
    )
    placa_veiculo = models.CharField(max_length=10, blank=True, null=True, verbose_name="Placa do Veículo")
    ultima_procedencia = models.CharField(max_length=255, blank=True, null=True, verbose_name="Última Procedência")
    proximo_destino = models.CharField(max_length=255, blank=True, null=True, verbose_name="Próximo Destino")
    
    checkin_concluido = models.BooleanField(default=False, verbose_name="Check-in Concluído")
    checkin_online_realizado = models.BooleanField(default=False, verbose_name="Check-in Online Realizado")
    hospede_cpf = models.CharField(max_length=14, blank=True, null=True, verbose_name="CPF do Hóspede")
    fnrh_exportado = models.BooleanField(default=False, verbose_name="FNRH Exportada")
    
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Valor Total")
    status = models.CharField(
        max_length=20, 
        choices=[
            ('pendente', 'Pendente'), 
            ('sinal', 'Sinal'), 
            ('confirmada', 'Confirmada'), 
            ('finalizada', 'Finalizada'), 
            ('cancelada', 'Cancelada')
        ], 
        default='pendente',
        verbose_name="Status"
    )
    
    tags = models.ManyToManyField('hospedes.Tag', blank=True, verbose_name="Tags")
    is_bloqueio = models.BooleanField(default=False, verbose_name="É Bloqueio")
    motivo_bloqueio = models.ForeignKey('pousada.MotivoBloqueio', null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Motivo de Bloqueio")
    senha_fechadura = models.CharField(max_length=20, blank=True, null=True, verbose_name="Senha da Fechadura")
    token_acesso = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Token de Acesso")

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"

    def __str__(self):
        nome_hospede = self.hospede.nome_completo if self.hospede else f"Bloqueio ({self.motivo_bloqueio.nome if self.motivo_bloqueio else 'Manutenção'})"
        return f"Reserva {self.id}: {nome_hospede} - {self.quarto.nome_identificacao}"

    @property
    def total_pago(self):
        resultado = self.pagamentos.filter(status='pago').aggregate(soma=Sum('valor'))['soma']
        return resultado if resultado is not None else Decimal('0.00')

    @property
    def saldo_devedor(self):
        return self.valor_total - self.total_pago

    @property
    def status_financeiro(self):
        saldo = self.saldo_devedor
        if saldo <= 0:
            return 'quitado'
        elif self.total_pago > 0:
            return 'parcial'
        else:
            return 'pendente'


class Acompanhante(models.Model):
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='acompanhantes', verbose_name="Reserva")
    nome = models.CharField(max_length=255, verbose_name="Nome")
    cpf = models.CharField(max_length=20, blank=True, null=True, verbose_name="CPF")

    class Meta:
        verbose_name = "Acompanhante"
        verbose_name_plural = "Acompanhantes"

    def __str__(self):
        return self.nome


class FichaFNRH(models.Model):
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE, related_name='ficha_fnrh', verbose_name="Reserva")
    nome_completo = models.CharField(max_length=255, verbose_name="Nome Completo")
    email = models.EmailField(verbose_name="E-mail")
    telefone = models.CharField(max_length=20, verbose_name="Telefone")
    data_nascimento = models.DateField(verbose_name="Data de Nascimento")
    nacionalidade = models.CharField(max_length=100, default='Brasileira', verbose_name="Nacionalidade")
    cpf_passaporte = models.CharField(max_length=50, verbose_name="CPF/Passaporte")
    documento_identidade = models.CharField(max_length=50, verbose_name="Documento de Identidade")
    
    cep = models.CharField(max_length=20, verbose_name="CEP")
    logradouro = models.CharField(max_length=255, verbose_name="Logradouro")
    numero = models.CharField(max_length=20, verbose_name="Número")
    complemento = models.CharField(max_length=100, blank=True, null=True, verbose_name="Complemento")
    bairro = models.CharField(max_length=100, verbose_name="Bairro")
    cidade = models.CharField(max_length=100, verbose_name="Cidade")
    estado = models.CharField(max_length=50, verbose_name="Estado")
    pais = models.CharField(max_length=100, default='Brasil', verbose_name="País")
    
    placa_veiculo = models.CharField(max_length=10, blank=True, null=True, verbose_name="Placa do Veículo")
    motivo_viagem = models.CharField(
        max_length=50,
        choices=[
            ('lazer', 'Lazer'),
            ('negocios', 'Negócios'),
            ('outro', 'Outros')
        ],
        verbose_name="Motivo da Viagem"
    )
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")

    class Meta:
        verbose_name = "Ficha FNRH"
        verbose_name_plural = "Fichas FNRH"

    def __str__(self):
        return f"FNRH #{self.id} - Hóspede: {self.nome_completo}"


class TemplateMensagem(models.Model):
    CANAL_CHOICES = [
        ('email', 'E-mail'),
        ('whatsapp', 'WhatsApp'),
    ]
    GATILHO_CHOICES = [
        ('criacao_reserva', 'Criação da Reserva'),
        ('confirmacao_reserva', 'Confirmação da Reserva'),
        ('antes_checkin', 'Antes do Check-in'),
        ('depois_checkout', 'Depois do Check-out'),
    ]

    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='templates_mensagem', verbose_name="Pousada")
    nome = models.CharField(max_length=100, verbose_name="Nome")
    canal = models.CharField(max_length=20, choices=CANAL_CHOICES, verbose_name="Canal")
    gatilho = models.CharField(max_length=55, choices=GATILHO_CHOICES, verbose_name="Gatilho")
    dias_offset = models.IntegerField(default=0, verbose_name="Dias de Offset")
    assunto = models.CharField(max_length=255, null=True, blank=True, verbose_name="Assunto")
    corpo_mensagem = models.TextField(verbose_name="Corpo da Mensagem")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Template de Mensagem"
        verbose_name_plural = "Templates de Mensagens"

    def __str__(self):
        return f"{self.nome} ({self.get_canal_display()} - {self.get_gatilho_display()})"


class LogDisparoMensagem(models.Model):
    STATUS_CHOICES = [
        ('sucesso', 'Sucesso'),
        ('falha', 'Falha'),
        ('pendente_whatsapp', 'Pendente WhatsApp'),
    ]

    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='logs_disparo', verbose_name="Reserva")
    template = models.ForeignKey(TemplateMensagem, on_delete=models.CASCADE, related_name='logs_disparo', verbose_name="Template")
    data_disparo = models.DateTimeField(auto_now_add=True, verbose_name="Data do Disparo")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, verbose_name="Status")

    class Meta:
        verbose_name = "Log de Disparo de Mensagem"
        verbose_name_plural = "Logs de Disparos de Mensagens"

    def __str__(self):
        return f"Log {self.id}: Reserva {self.reserva_id} - Template {self.template_id} ({self.status})"



