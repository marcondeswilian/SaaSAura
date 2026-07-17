from django.template import Template, Context
from django.urls import reverse
from django.conf import settings

def renderizar_template_mensagem(reserva, template_mensagem, site_url=None):
    """
    Renderiza o assunto (se e-mail) e o corpo de um TemplateMensagem
    injetando as variáveis reais de uma Reserva.
    """
    if not site_url:
        # Puxa das configurações ou usa um padrão razoável de desenvolvimento
        site_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
    
    # Remove barra final se existir para garantir formatação consistente
    site_url = site_url.rstrip('/')
    
    # Gera o link do portal do hóspede
    path_portal = reverse('portal_hospede', kwargs={'token': reserva.token_acesso})
    link_portal = f"{site_url}{path_portal}"
    
    # Prepara o contexto com as variáveis padrão solicitadas e adiciona 'reserva' por flexibilidade
    context_data = {
        'nome_hospede': reserva.hospede.nome_completo if reserva.hospede else "Hóspede",
        'data_checkin': reserva.data_checkin,
        'data_checkout': reserva.data_checkout,
        'link_portal': link_portal,
        'reserva': reserva,
    }
    
    context = Context(context_data)
    
    # Renderiza o assunto se for e-mail e estiver preenchido
    assunto_renderizado = None
    if template_mensagem.canal == 'email' and template_mensagem.assunto:
        tmpl_assunto = Template(template_mensagem.assunto)
        assunto_renderizado = tmpl_assunto.render(context)
        
    # Renderiza o corpo da mensagem
    tmpl_corpo = Template(template_mensagem.corpo_mensagem)
    corpo_renderizado = tmpl_corpo.render(context)
    
    # Formata como HTML se for canal e-mail
    if template_mensagem.canal == 'email':
        from django.utils.html import linebreaks
        # Se contiver tags HTML comuns, mantém como está. Caso contrário, converte quebras de linha em <br>
        common_tags = ["<a ", "<p>", "<div>", "<br", "<html>", "<strong>", "<b>", "<i>", "<u>"]
        if any(tag in corpo_renderizado.lower() for tag in common_tags):
            corpo_html = corpo_renderizado
        else:
            corpo_html = linebreaks(corpo_renderizado)
    else:
        corpo_html = corpo_renderizado
    
    return assunto_renderizado, corpo_renderizado, corpo_html
