from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from reservas.models import Reserva
from financeiro.models import Pagamento
from admin_saas.models import ClienteSaaS
from .models import LogAuditoria
from .middleware import get_current_user

@receiver(post_save, sender=Reserva)
def log_reserva_save(sender, instance, created, **kwargs):
    user = get_current_user()
    if user and user.is_authenticated:
        acao = f"Criou a reserva de check-in {instance.data_checkin} e check-out {instance.data_checkout} para o hóspede {instance.hospede}" if created else f"Editou a reserva {instance.id} (Hóspede: {instance.hospede})"
        LogAuditoria.objects.create(
            usuario=user,
            acao=acao,
            alvo_id=instance.id,
            pousada=instance.pousada
        )

@receiver(post_delete, sender=Reserva)
def log_reserva_delete(sender, instance, **kwargs):
    user = get_current_user()
    if user and user.is_authenticated:
        try:
            hospede_nome = str(instance.hospede) if instance.hospede_id else "Nenhum"
        except Exception:
            hospede_nome = f"Desconhecido (ID {instance.hospede_id})"
            
        LogAuditoria.objects.create(
            usuario=user,
            acao=f"Excluiu/Cancelou a reserva {instance.id} (Hóspede: {hospede_nome})",
            alvo_id=instance.id,
            pousada=instance.pousada
        )

@receiver(post_save, sender=Pagamento)
def log_pagamento_save(sender, instance, created, **kwargs):
    user = get_current_user()
    if user and user.is_authenticated:
        acao = f"Registrou novo pagamento de R$ {instance.valor} ({instance.get_tipo_display()}) para a reserva {instance.reserva_id}" if created else f"Editou o pagamento {instance.id} da reserva {instance.reserva_id} (novo valor: R$ {instance.valor})"
        LogAuditoria.objects.create(
            usuario=user,
            acao=acao,
            alvo_id=instance.id,
            pousada=instance.pousada
        )

@receiver(post_delete, sender=Pagamento)
def log_pagamento_delete(sender, instance, **kwargs):
    user = get_current_user()
    if user and user.is_authenticated:
        LogAuditoria.objects.create(
            usuario=user,
            acao=f"Excluiu o pagamento {instance.id} no valor de R$ {instance.valor} da reserva {instance.reserva_id}",
            alvo_id=instance.id,
            pousada=instance.pousada
        )

@receiver(post_save, sender=ClienteSaaS)
def log_cliente_save(sender, instance, created, **kwargs):
    user = get_current_user()
    if user and user.is_authenticated:
        # Tenta obter a pousada associada ao cliente
        pousada = getattr(instance, 'pousada', None)
        if not pousada:
            try:
                pousada = instance.user.pousada_owner
            except Exception:
                pass
        
        acao = f"Criou o cliente/dono {instance.user.username}" if created else f"Editou as configurações do cliente {instance.user.username}"
        LogAuditoria.objects.create(
            usuario=user,
            acao=acao,
            alvo_id=instance.id,
            pousada=pousada
        )

@receiver(post_delete, sender=ClienteSaaS)
def log_cliente_delete(sender, instance, **kwargs):
    user = get_current_user()
    if user and user.is_authenticated:
        pousada = getattr(instance, 'pousada', None)
        if not pousada:
            try:
                pousada = instance.user.pousada_owner
            except Exception:
                pass
                
        LogAuditoria.objects.create(
            usuario=user,
            acao=f"Excluiu o cliente {instance.user.username}",
            alvo_id=instance.id,
            pousada=pousada
        )

@receiver(pre_save, sender=Reserva)
def track_previous_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            original = Reserva.objects.get(pk=instance.pk)
            instance._original_status = original.status
        except Reserva.DoesNotExist:
            instance._original_status = None
    else:
        instance._original_status = None

@receiver(post_save, sender=Reserva)
def verificar_checkout_limpeza(sender, instance, created, **kwargs):
    original_status = getattr(instance, '_original_status', None)
    if instance.status == 'finalizada' and original_status != 'finalizada' and not instance.is_bloqueio:
        quarto = instance.quarto
        quarto.status_limpeza = 'sujo'
        quarto.save()
        
        # Automatically create a pending cleaning order of service if none active
        from pousada.models import OrdemServico
        os_existente = OrdemServico.objects.filter(
            quarto=quarto,
            tipo_servico='limpeza',
            status__in=['pendente', 'em_andamento']
        ).exists()
        if not os_existente:
            OrdemServico.objects.create(
                quarto=quarto,
                tipo_servico='limpeza',
                prioridade='media',
                descricao=f"Limpeza pós check-out da reserva #{instance.id} (Hóspede: {instance.hospede.nome_completo if instance.hospede else 'Não informado'}).",
                status='pendente',
                criado_por=instance.pousada.dono,
                pousada=instance.pousada
            )






