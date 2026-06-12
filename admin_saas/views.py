from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from django.utils.text import slugify
from pousada.models import Pousada
from .models import ClienteSaaS, NivelAcesso

@login_required
def admin_saas_dashboard(request):
    if not request.user.is_superuser:
        return redirect('reserva-lista')

    # Garante que pelo menos um nível de acesso padrão exista
    default_nivel, created = NivelAcesso.objects.get_or_create(
        nome="Administrador Padrão",
        defaults={
            'pode_acessar_reservas': True,
            'pode_acessar_crm': True,
            'pode_acessar_financeiro': True,
            'pode_acessar_configuracoes': True,
            'pode_acessar_governanca': True,
        }
    )

    # BUG-08: Criar ClienteSaaS apenas para usuários que não possuem um (bulk, sem N+1)
    users_sem_cliente = User.objects.filter(is_superuser=False, cliente_saas__isnull=True)
    if users_sem_cliente.exists():
        ClienteSaaS.objects.bulk_create([
            ClienteSaaS(user=u, nivel_acesso=default_nivel, ativo=True)
            for u in users_sem_cliente
        ], ignore_conflicts=True)

    clientes = ClienteSaaS.objects.all().select_related('user', 'nivel_acesso', 'pousada', 'user__pousada_owner')
    niveis = NivelAcesso.objects.all()
    ativos_count = sum(1 for c in clientes if c.ativo)
    inativos_count = sum(1 for c in clientes if not c.ativo)

    # Obter aba ativa para renderizar corretamente
    active_tab = request.GET.get('tab', 'clientes')

    return render(request, 'admin_saas/dashboard.html', {
        'clientes': clientes,
        'niveis': niveis,
        'ativos_count': ativos_count,
        'inativos_count': inativos_count,
        'default_nivel_id': default_nivel.id,
        'active_tab': active_tab,
    })

@login_required
@require_POST
def toggle_cliente_ativo(request, pk):
    if not request.user.is_superuser:
        return redirect('reserva-lista')
    cliente = get_object_or_404(ClienteSaaS, id=pk)
    cliente.ativo = not cliente.ativo
    cliente.save()
    status = "ativado" if cliente.ativo else "desativado"
    messages.success(request, f"O status do cliente {cliente.user.username} foi {status} com sucesso!")
    return redirect('/painel-saas/?tab=clientes')

@login_required
@require_POST
def criar_cliente_saas(request):
    if not request.user.is_superuser:
        return redirect('reserva-lista')
        
    username = request.POST.get('username', '').strip()
    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '')
    pousada_nome = request.POST.get('pousada_nome', '').strip()
    nivel_acesso_id = request.POST.get('nivel_acesso')
    plano_ativo_val = request.POST.get('plano_ativo') == 'true'
    data_exp = request.POST.get('data_expiracao') or None

    # Validações básicas
    if not username or not email or not password or not pousada_nome:
        messages.error(request, "Todos os campos obrigatórios devem ser preenchidos.")
        return redirect('/painel-saas/?tab=clientes')

    if User.objects.filter(username=username).exists():
        messages.error(request, "Este nome de usuário já está em uso.")
        return redirect('/painel-saas/?tab=clientes')

    if User.objects.filter(email=email).exists():
        messages.error(request, "Este endereço de e-mail já está em uso.")
        return redirect('/painel-saas/?tab=clientes')

    try:
        with transaction.atomic():
            # 1. Criar o Usuário
            user = User.objects.create_user(username=username, email=email, password=password)
            
            # 2. Criar a Pousada vinculada
            slug = slugify(pousada_nome)
            if not slug:
                slug = f"pousada-{user.id}"
            if Pousada.objects.filter(slug=slug).exists():
                slug = f"{slug}-{user.id}"
            Pousada.objects.create(dono=user, nome=pousada_nome, slug=slug)
            
            # 3. Criar Perfil do Cliente
            nivel_acesso = get_object_or_404(NivelAcesso, id=nivel_acesso_id) if nivel_acesso_id else None
            ClienteSaaS.objects.create(
                user=user,
                nivel_acesso=nivel_acesso,
                plano_ativo=plano_ativo_val,
                data_expiracao=data_exp,
                ativo=True
            )
            
        messages.success(request, f"Cliente {username} e sua pousada '{pousada_nome}' foram criados com sucesso!")
    except Exception as e:
        messages.error(request, f"Erro ao criar cliente: {str(e)}")
        
    return redirect('/painel-saas/?tab=clientes')

@login_required
@require_POST
def atualizar_cliente_saas(request, pk):
    if not request.user.is_superuser:
        return redirect('reserva-lista')
    cliente = get_object_or_404(ClienteSaaS, id=pk)
    data_exp = request.POST.get('data_expiracao') or None
    plano_ativo_val = request.POST.get('plano_ativo') == 'true'
    nivel_acesso_id = request.POST.get('nivel_acesso')
    
    try:
        cliente.data_expiracao = data_exp
        cliente.plano_ativo = plano_ativo_val
        if nivel_acesso_id:
            cliente.nivel_acesso = get_object_or_404(NivelAcesso, id=nivel_acesso_id)
        else:
            cliente.nivel_acesso = None
        cliente.save()
        messages.success(request, f"Configurações do cliente {cliente.user.username} atualizadas com sucesso!")
    except Exception as e:
        messages.error(request, f"Erro ao atualizar configurações: {str(e)}")
        
    return redirect('/painel-saas/?tab=clientes')

@login_required
@require_POST
def criar_nivel_acesso(request):
    if not request.user.is_superuser:
        return redirect('reserva-lista')
    
    nome = request.POST.get('nome', '').strip()
    if not nome:
        messages.error(request, "O nome do nível de acesso é obrigatório.")
        return redirect('/painel-saas/?tab=niveis')

    pode_reservas = request.POST.get('pode_acessar_reservas') == 'on'
    pode_crm = request.POST.get('pode_acessar_crm') == 'on'
    pode_financeiro = request.POST.get('pode_acessar_financeiro') == 'on'
    pode_config = request.POST.get('pode_acessar_configuracoes') == 'on'
    pode_governanca = request.POST.get('pode_acessar_governanca') == 'on'

    try:
        NivelAcesso.objects.create(
            nome=nome,
            pode_acessar_reservas=pode_reservas,
            pode_acessar_crm=pode_crm,
            pode_acessar_financeiro=pode_financeiro,
            pode_acessar_configuracoes=pode_config,
            pode_acessar_governanca=pode_governanca,
        )
        messages.success(request, f"Nível de acesso '{nome}' criado com sucesso!")
    except Exception as e:
        messages.error(request, f"Erro ao criar nível de acesso: {str(e)}")

    return redirect('/painel-saas/?tab=niveis')

@login_required
@require_POST
def atualizar_nivel_acesso(request, pk):
    if not request.user.is_superuser:
        return redirect('reserva-lista')
    
    nivel = get_object_or_404(NivelAcesso, id=pk)
    nome = request.POST.get('nome', '').strip()
    if not nome:
        messages.error(request, "O nome do nível de acesso é obrigatório.")
        return redirect('/painel-saas/?tab=niveis')

    pode_reservas = request.POST.get('pode_acessar_reservas') == 'on'
    pode_crm = request.POST.get('pode_acessar_crm') == 'on'
    pode_financeiro = request.POST.get('pode_acessar_financeiro') == 'on'
    pode_config = request.POST.get('pode_acessar_configuracoes') == 'on'
    pode_governanca = request.POST.get('pode_acessar_governanca') == 'on'

    try:
        nivel.nome = nome
        nivel.pode_acessar_reservas = pode_reservas
        nivel.pode_acessar_crm = pode_crm
        nivel.pode_acessar_financeiro = pode_financeiro
        nivel.pode_acessar_configuracoes = pode_config
        nivel.pode_acessar_governanca = pode_governanca
        nivel.save()
        messages.success(request, f"Nível de acesso '{nome}' atualizado com sucesso!")
    except Exception as e:
        messages.error(request, f"Erro ao atualizar nível de acesso: {str(e)}")

    return redirect('/painel-saas/?tab=niveis')

@login_required
@require_POST
def excluir_nivel_acesso(request, pk):
    if not request.user.is_superuser:
        return redirect('reserva-lista')
    
    nivel = get_object_or_404(NivelAcesso, id=pk)
    
    # Impedir de excluir se houver clientes associados
    if nivel.clientes.exists():
        messages.error(request, f"Não é possível excluir o nível '{nivel.nome}' pois ele está sendo utilizado por clientes.")
        return redirect('/painel-saas/?tab=niveis')

    try:
        nivel.delete()
        messages.success(request, f"Nível de acesso excluído com sucesso!")
    except Exception as e:
        messages.error(request, f"Erro ao excluir nível de acesso: {str(e)}")

    return redirect('/painel-saas/?tab=niveis')

@login_required
def testar_email(request):
    if not request.user.is_superuser:
        return redirect('reserva-lista')
    from django.core.mail import send_mail
    from django.http import HttpResponse
    try:
        destinatario = request.user.email or 'auradecunha@gmail.com'
        send_mail(
            subject='E-mail de Teste - AuraSaaS SMTP',
            message='Este é um e-mail de teste enviado para validar as configurações de SMTP do AuraSaaS.',
            from_email=None,
            recipient_list=[destinatario],
            fail_silently=False,
        )
        return HttpResponse(f"E-mail de teste enviado com sucesso para {destinatario}! Verifique sua caixa de entrada (incluindo spam).")
    except Exception as e:
        return HttpResponse(f"Erro ao enviar e-mail: {str(e)}", status=500)
