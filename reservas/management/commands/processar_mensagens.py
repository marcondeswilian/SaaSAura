from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta

from reservas.models import Reserva, TemplateMensagem, LogDisparoMensagem
from reservas.services.mensageria import renderizar_template_mensagem

class Command(BaseCommand):
    help = 'Processa as reservas e envia mensagens automáticas de e-mail e logs de WhatsApp de acordo com os templates e triggers cadastrados.'

    def handle(self, *args, **options):
        today = timezone.localtime().date()
        self.stdout.write(self.style.NOTICE(f"Processando mensagens para a data de hoje: {today}"))
        
        templates = TemplateMensagem.objects.filter(ativo=True)
        self.stdout.write(self.style.NOTICE(f"Encontrados {templates.count()} templates ativos."))
        
        for template in templates:
            self.stdout.write(self.style.NOTICE(f"Verificando template '{template.nome}' (Canal: {template.canal}, Gatilho: {template.gatilho})"))
            
            # Busca todas as reservas da pousada associada que ainda não receberam esse template específico
            # Excluímos as reservas canceladas para evitar disparos desnecessários
            reservas = Reserva.objects.filter(pousada=template.pousada).exclude(
                logs_disparo__template=template
            ).exclude(status='cancelada')
            
            for reserva in reservas:
                deve_disparar = False
                
                if template.gatilho == 'criacao_reserva':
                    # Triga no momento de criação da reserva. 
                    # Filtramos para enviar apenas se o checkin ainda não passou para não disparar mensagens legadas para reservas antigas.
                    if today <= reserva.data_checkin:
                        deve_disparar = True
                        
                elif template.gatilho == 'confirmacao_reserva':
                    # Triga quando a reserva está confirmada.
                    # Filtramos para enviar apenas se o checkin ainda não passou e o status é 'confirmada'.
                    if reserva.status == 'confirmada' and today <= reserva.data_checkin:
                        deve_disparar = True
                        
                elif template.gatilho == 'antes_checkin':
                    # Triga X dias antes do checkin
                    target_date = reserva.data_checkin - timedelta(days=template.dias_offset)
                    # Dispara se já chegamos ou passamos da data de target, check-in online/físico não foi concluído, e reserva está pendente/confirmada
                    if today >= target_date and not reserva.checkin_concluido and reserva.status in ['confirmada', 'pendente']:
                        deve_disparar = True
                        
                elif template.gatilho == 'depois_checkout':
                    # Triga X dias após o checkout
                    target_date = reserva.data_checkout + timedelta(days=template.dias_offset)
                    if today >= target_date:
                        deve_disparar = True
                
                if deve_disparar:
                    # Tenta obter o e-mail do hóspede
                    recipient_email = None
                    if reserva.hospede and reserva.hospede.email:
                        recipient_email = reserva.hospede.email.strip()
                    elif hasattr(reserva, 'ficha_fnrh') and reserva.ficha_fnrh.email:
                        recipient_email = reserva.ficha_fnrh.email.strip()
                    
                    if template.canal == 'email':
                        if not recipient_email:
                            self.stdout.write(self.style.WARNING(
                                f"  -> Reserva {reserva.id}: Sem e-mail cadastrado. Gravando log de falha."
                            ))
                            LogDisparoMensagem.objects.create(
                                reserva=reserva,
                                template=template,
                                status='falha'
                            )
                            continue
                        
                        try:
                            # Renderiza as variáveis dinâmicas
                            assunto, corpo_txt, corpo_html = renderizar_template_mensagem(reserva, template)
                            assunto = assunto or f"Notificação - {reserva.pousada.nome}"
                            
                            self.stdout.write(self.style.SUCCESS(
                                f"  -> Enviando e-mail para {recipient_email} (Reserva {reserva.id})"
                            ))
                            
                            # Envia o e-mail real utilizando o backend SMTP/Console configurado no Django
                            send_mail(
                                subject=assunto,
                                message=corpo_txt,
                                from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@aurasaas.com.br',
                                recipient_list=[recipient_email],
                                fail_silently=False,
                                html_message=corpo_html,
                            )
                            
                            LogDisparoMensagem.objects.create(
                                reserva=reserva,
                                template=template,
                                status='sucesso'
                            )
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(
                                f"  -> Falha ao enviar e-mail para Reserva {reserva.id}: {str(e)}"
                            ))
                            LogDisparoMensagem.objects.create(
                                reserva=reserva,
                                template=template,
                                status='falha'
                            )
                            
                    elif template.canal == 'whatsapp':
                        self.stdout.write(self.style.SUCCESS(
                            f"  -> Criando log 'pendente_whatsapp' para Reserva {reserva.id}"
                        ))
                        # WhatsApp apenas registra o log com o status 'pendente_whatsapp' para ser processado posteriormente ou exibido
                        LogDisparoMensagem.objects.create(
                            reserva=reserva,
                            template=template,
                            status='pendente_whatsapp'
                        )
                        
        self.stdout.write(self.style.SUCCESS("Processamento de mensagens concluído com sucesso!"))
