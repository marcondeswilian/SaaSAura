from django.db import models
from django.db.models import Sum
from decimal import Decimal
from pousada.models import Pousada, Quarto # Adicionamos o Quarto aqui
from hospedes.models import Hospede
import uuid

class Grupo(models.Model):
    nome = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome or f"Grupo {self.id}"

class Reserva(models.Model):
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='reservas')
    grupo = models.ForeignKey(Grupo, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservas')
    hospede = models.ForeignKey(Hospede, on_delete=models.CASCADE, related_name='reservas', null=True, blank=True)
    quarto = models.ForeignKey(Quarto, on_delete=models.PROTECT, related_name='reservas')

    
    data_checkin = models.DateField()
    data_checkout = models.DateField()
    
    # Campos FNRH da Viagem
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
        null=True
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
        null=True
    )
    placa_veiculo = models.CharField(max_length=10, blank=True, null=True)
    ultima_procedencia = models.CharField(max_length=255, blank=True, null=True)
    proximo_destino = models.CharField(max_length=255, blank=True, null=True)
    
    # Token Seguro e Status de Check-in
    # token_acesso: UUID único para o portal unificado do hóspede (portal_hospede view)
    checkin_concluido = models.BooleanField(default=False)
    checkin_online_realizado = models.BooleanField(default=False)
    hospede_cpf = models.CharField(max_length=14, blank=True, null=True)
    fnrh_exportado = models.BooleanField(default=False)
    
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(
        max_length=20, 
        choices=[
            ('pendente', 'Pendente'), 
            ('confirmada', 'Confirmada'), 
            ('finalizada', 'Finalizada'), 
            ('cancelada', 'Cancelada')
        ], 
        default='pendente'
    )
    
    # Novos campos para Bloqueios e Tags de Reserva
    tags = models.ManyToManyField('hospedes.Tag', blank=True)
    is_bloqueio = models.BooleanField(default=False)
    motivo_bloqueio = models.ForeignKey('pousada.MotivoBloqueio', null=True, blank=True, on_delete=models.SET_NULL)
    senha_fechadura = models.CharField(max_length=20, blank=True, null=True)
    token_acesso = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)



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
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='acompanhantes')
    nome = models.CharField(max_length=255)
    cpf = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nome


class FichaFNRH(models.Model):
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE, related_name='ficha_fnrh')
    nome_completo = models.CharField(max_length=255)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    data_nascimento = models.DateField()
    nacionalidade = models.CharField(max_length=100, default='Brasileira')
    cpf_passaporte = models.CharField(max_length=50)
    documento_identidade = models.CharField(max_length=50)  # RG / CNH
    
    # Endereço
    cep = models.CharField(max_length=20)
    logradouro = models.CharField(max_length=255)
    numero = models.CharField(max_length=20)
    complemento = models.CharField(max_length=100, blank=True, null=True)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=50)
    pais = models.CharField(max_length=100, default='Brasil')
    
    # Viagem
    placa_veiculo = models.CharField(max_length=10, blank=True, null=True)
    motivo_viagem = models.CharField(
        max_length=50,
        choices=[
            ('lazer', 'Lazer'),
            ('negocios', 'Negócios'),
            ('outro', 'Outros')
        ]
    )
    data_criacao = models.DateTimeField(auto_now_add=True)

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

    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='templates_mensagem')
    nome = models.CharField(max_length=100)
    canal = models.CharField(max_length=20, choices=CANAL_CHOICES)
    gatilho = models.CharField(max_length=55, choices=GATILHO_CHOICES)
    dias_offset = models.IntegerField(default=0)
    assunto = models.CharField(max_length=255, null=True, blank=True)
    corpo_mensagem = models.TextField()
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nome} ({self.get_canal_display()} - {self.get_gatilho_display()})"


class LogDisparoMensagem(models.Model):
    STATUS_CHOICES = [
        ('sucesso', 'Sucesso'),
        ('falha', 'Falha'),
        ('pendente_whatsapp', 'Pendente WhatsApp'),
    ]

    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='logs_disparo')
    template = models.ForeignKey(TemplateMensagem, on_delete=models.CASCADE, related_name='logs_disparo')
    data_disparo = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES)

    def __str__(self):
        return f"Log {self.id}: Reserva {self.reserva_id} - Template {self.template_id} ({self.status})"



