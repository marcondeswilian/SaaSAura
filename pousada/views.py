from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Case, When, Value, IntegerField
from admin_saas.models import ClienteSaaS, NivelAcesso
from .models import Pousada, MotivoBloqueio, CategoriaQuarto, Quarto, MetodoPagamentoConfig, CanalOrigem, LogAuditoria, ChecklistItem, RegistroLimpeza, ItemLimpezaConcluido, OrdemServico, Fechadura
from hospedes.models import Tag
from django.utils import timezone
from reservas.models import TemplateMensagem
from .decorators import pousada_required

@login_required
@pousada_required
def pousada_config_view(request):
    pousada = request.pousada
    tab = request.GET.get('tab', 'geral')
    from .forms import PousadaForm, ChecklistItemForm, QuartoForm

    if request.method == 'POST':
        acao = request.POST.get('acao', 'config_geral')

        if acao == 'config_geral':
            form = PousadaForm(request.POST, request.FILES, instance=pousada)
            if form.is_valid():
                form.save()
                messages.success(request, "Configurações da pousada atualizadas com sucesso!")
            else:
                messages.error(request, "Erro ao salvar as configurações.")
            return redirect('/painel/pousada/config/?tab=geral')

        elif acao == 'config_governanca':
            usa_checklist = request.POST.get('usa_checklist_limpeza') == 'on'
            pousada.usa_checklist_limpeza = usa_checklist
            pousada.save()
            messages.success(request, "Configuração de checklist de limpeza salva com sucesso!")
            return redirect('/painel/pousada/config/?tab=governanca_config')

        elif acao == 'novo_checklist_item':
            form = ChecklistItemForm(request.POST)
            if form.is_valid():
                item = form.save(commit=False)
                item.pousada = pousada
                item.save()
                messages.success(request, "Item adicionado ao checklist com sucesso!")
            else:
                messages.error(request, "A descrição do item é obrigatória.")
            return redirect('/painel/pousada/config/?tab=governanca_config')

        elif acao == 'excluir_checklist_item':
            item_id = request.POST.get('item_id')
            if item_id:
                item = get_object_or_404(ChecklistItem, id=item_id, pousada=pousada)
                item.ativo = False
                item.save()
                messages.success(request, "Item removido do checklist com sucesso!")
            else:
                messages.error(request, "Item não especificado.")
            return redirect('/painel/pousada/config/?tab=governanca_config')

        elif acao == 'nova_tag':
            nome_tag = request.POST.get('nome_tag')
            cor_tag = request.POST.get('cor_tag', '#3b82f6')
            tipo_tag = request.POST.get('tipo_tag', 'H')

            if nome_tag:
                Tag.objects.create(
                    pousada=pousada,
                    nome=nome_tag,
                    cor=cor_tag,
                    tipo=tipo_tag
                )
                messages.success(request, f"Tag '{nome_tag}' criada com sucesso!")
            else:
                messages.error(request, "O nome da tag é obrigatório.")
            return redirect('/painel/pousada/config/?tab=tags')

        elif acao == 'novo_bloqueio':
            nome_bloqueio = request.POST.get('nome_bloqueio')
            cor_bloqueio = request.POST.get('cor_bloqueio', '#475569')

            if nome_bloqueio:
                MotivoBloqueio.objects.create(
                    pousada=pousada,
                    nome=nome_bloqueio,
                    cor=cor_bloqueio
                )
                messages.success(request, f"Motivo de bloqueio '{nome_bloqueio}' criado com sucesso!")
            else:
                messages.error(request, "O nome do motivo de bloqueio é obrigatório.")
            return redirect('/painel/pousada/config/?tab=bloqueios')

        elif acao == 'nova_categoria':
            nome = request.POST.get('nome_categoria')
            capacidade_str = request.POST.get('capacidade_categoria')
            valor_diaria_str = request.POST.get('valor_diaria_categoria')

            if nome and capacidade_str and valor_diaria_str:
                try:
                    capacidade = int(capacidade_str)
                    valor_diaria = Decimal(valor_diaria_str)
                    CategoriaQuarto.objects.create(
                        pousada=pousada,
                        nome=nome,
                        capacidade=capacidade,
                        valor_diaria=valor_diaria
                    )
                    messages.success(request, f"Categoria '{nome}' criada com sucesso!")
                except ValueError:
                    messages.error(request, "Capacidade ou valor diário inválido.")
            else:
                messages.error(request, "Todos os campos da categoria são obrigatórios.")
            return redirect('/painel/pousada/config/?tab=quartos')

        elif acao == 'novo_quarto':
            form = QuartoForm(request.POST)
            if form.is_valid():
                quarto = form.save(commit=False)
                quarto.pousada = pousada
                quarto.save()
                messages.success(request, f"Quarto '{quarto.nome_identificacao}' criado com sucesso!")
            else:
                errors_str = " | ".join([f"{f}: {e}" for f, e in form.errors.items()])
                messages.error(request, f"Falha ao criar o quarto. Erros: {errors_str}")
            return redirect('/painel/pousada/config/?tab=quartos')

        elif acao == 'excluir_quarto':
            quarto_id = request.POST.get('quarto_id')
            if quarto_id:
                quarto = get_object_or_404(Quarto, id=quarto_id, pousada=pousada)
                nome_identificacao = quarto.nome_identificacao
                try:
                    quarto.delete()
                    messages.success(request, f"Quarto '{nome_identificacao}' excluído com sucesso!")
                except Exception as e:
                    messages.error(request, f"Não foi possível excluir o quarto '{nome_identificacao}': {str(e)}")
            else:
                messages.error(request, "ID do quarto não fornecido.")
            return redirect('/painel/pousada/config/?tab=quartos')

        elif acao == 'editar_quarto':
            quarto_id = request.POST.get('quarto_id')
            if quarto_id:
                quarto = get_object_or_404(Quarto, id=quarto_id, pousada=pousada)
                form = QuartoForm(request.POST, instance=quarto)
                if form.is_valid():
                    form.save()
                    messages.success(request, f"Quarto '{quarto.nome_identificacao}' atualizado com sucesso!")
                else:
                    errors_str = " | ".join([f"{f}: {e}" for f, e in form.errors.items()])
                    messages.error(request, f"Falha ao atualizar o quarto. Erros: {errors_str}")
            return redirect('/painel/pousada/config/?tab=quartos')

        elif acao == 'excluir_categoria':
            categoria_id = request.POST.get('categoria_id')
            if categoria_id:
                categoria = get_object_or_404(CategoriaQuarto, id=categoria_id, pousada=pousada)
                nome = categoria.nome
                try:
                    categoria.delete()
                    messages.success(request, f"Categoria '{nome}' excluída com sucesso!")
                except Exception as e:
                    messages.error(request, f"Não foi possível excluir a categoria '{nome}'. Certifique-se de que não há quartos vinculados a ela.")
            else:
                messages.error(request, "ID da categoria não fornecido.")
            return redirect('/painel/pousada/config/?tab=quartos')

        elif acao == 'novo_metodo_pagamento':
            nome_metodo = request.POST.get('nome_metodo')
            if nome_metodo:
                MetodoPagamentoConfig.objects.create(
                    pousada=pousada,
                    nome=nome_metodo,
                    ativo=True
                )
                messages.success(request, f"Método de pagamento '{nome_metodo}' criado com sucesso!")
            else:
                messages.error(request, "O nome do método de pagamento é obrigatório.")
            return redirect('/painel/pousada/config/?tab=pagamentos')

        elif acao == 'excluir_metodo_pagamento':
            metodo_id = request.POST.get('metodo_id')
            if metodo_id:
                metodo = get_object_or_404(MetodoPagamentoConfig, id=metodo_id, pousada=pousada)
                metodo.ativo = False
                metodo.save()
                messages.success(request, f"Método de pagamento '{metodo.nome}' desativado com sucesso!")
            else:
                messages.error(request, "ID do método de pagamento não fornecido.")
            return redirect('/painel/pousada/config/?tab=pagamentos')

        elif acao == 'nova_fechadura':
            quarto_id = request.POST.get('quarto_id')
            device_id = request.POST.get('device_id', '').strip()
            nome_exibicao = request.POST.get('nome_exibicao', '').strip()

            if not (quarto_id and device_id and nome_exibicao):
                messages.error(request, 'Todos os campos da fechadura são obrigatórios.')
            elif Fechadura.objects.filter(device_id=device_id).exists():
                messages.error(request, f'Já existe uma fechadura cadastrada com o Device ID "{device_id}".')
            else:
                quarto = get_object_or_404(Quarto, id=quarto_id, pousada=pousada)
                Fechadura.objects.create(
                    quarto=quarto,
                    device_id=device_id,
                    nome_exibicao=nome_exibicao,
                )
                messages.success(request, f'Fechadura "{nome_exibicao}" vinculada ao quarto {quarto.nome_identificacao} com sucesso!')
            return redirect('/painel/pousada/config/?tab=fechaduras')

        elif acao == 'excluir_fechadura':
            fechadura_id = request.POST.get('fechadura_id')
            if fechadura_id:
                fechadura = get_object_or_404(Fechadura, id=fechadura_id, quarto__pousada=pousada)
                nome = fechadura.nome_exibicao
                fechadura.delete()
                messages.success(request, f'Fechadura "{nome}" removida com sucesso.')
            else:
                messages.error(request, 'ID da fechadura não fornecido.')
            return redirect('/painel/pousada/config/?tab=fechaduras')

        elif acao == 'salvar_mensagem_pos_checkin':
            pousada.mensagem_pos_checkin = request.POST.get('mensagem_pos_checkin', '').strip()
            pousada.video_pos_checkin = request.POST.get('video_pos_checkin', '').strip()
            pousada.save()
            messages.success(request, 'Mensagem pós check-in online atualizada com sucesso.')
            return redirect('/painel/pousada/config/?tab=mensagens')

        elif acao == 'novo_template_mensagem':
            nome = request.POST.get('nome', '').strip()
            canal = request.POST.get('canal', '').strip()
            gatilho = request.POST.get('gatilho', '').strip()
            dias_offset_str = request.POST.get('dias_offset', '0')
            assunto = request.POST.get('assunto', '').strip() or None
            corpo_mensagem = request.POST.get('corpo_mensagem', '').strip()
            ativo = request.POST.get('ativo') == 'on'

            try:
                dias_offset = int(dias_offset_str)
            except ValueError:
                dias_offset = 0

            if not nome or not canal or not gatilho or not corpo_mensagem:
                messages.error(request, "Todos os campos obrigatórios devem ser preenchidos.")
            else:
                TemplateMensagem.objects.create(
                    pousada=pousada,
                    nome=nome,
                    canal=canal,
                    gatilho=gatilho,
                    dias_offset=dias_offset,
                    assunto=assunto if canal == 'email' else None,
                    corpo_mensagem=corpo_mensagem,
                    ativo=ativo
                )
                messages.success(request, f"Template '{nome}' criado com sucesso!")
            return redirect('/painel/pousada/config/?tab=mensagens')

        elif acao == 'editar_template_mensagem':
            template_id = request.POST.get('template_id')
            template = get_object_or_404(TemplateMensagem, id=template_id, pousada=pousada)
            
            nome = request.POST.get('nome', '').strip()
            canal = request.POST.get('canal', '').strip()
            gatilho = request.POST.get('gatilho', '').strip()
            dias_offset_str = request.POST.get('dias_offset', '0')
            assunto = request.POST.get('assunto', '').strip() or None
            corpo_mensagem = request.POST.get('corpo_mensagem', '').strip()
            ativo = request.POST.get('ativo') == 'on'

            try:
                dias_offset = int(dias_offset_str)
            except ValueError:
                dias_offset = 0

            if not nome or not canal or not gatilho or not corpo_mensagem:
                messages.error(request, "Todos os campos obrigatórios devem ser preenchidos.")
            else:
                template.nome = nome
                template.canal = canal
                template.gatilho = gatilho
                template.dias_offset = dias_offset
                template.assunto = assunto if canal == 'email' else None
                template.corpo_mensagem = corpo_mensagem
                template.ativo = ativo
                template.save()
                messages.success(request, f"Template '{nome}' atualizado com sucesso!")
            return redirect('/painel/pousada/config/?tab=mensagens')

        elif acao == 'excluir_template_mensagem':
            template_id = request.POST.get('template_id')
            template = get_object_or_404(TemplateMensagem, id=template_id, pousada=pousada)
            nome = template.nome
            template.delete()
            messages.success(request, f"Template '{nome}' excluído com sucesso.")
            return redirect('/painel/pousada/config/?tab=mensagens')

        elif acao == 'novo_canal_origem':
            nome = request.POST.get('nome', '').strip()
            cor = request.POST.get('cor', '#6b7280').strip()
            if not nome:
                messages.error(request, "O nome do canal de origem é obrigatório.")
            else:
                CanalOrigem.objects.create(pousada=pousada, nome=nome, cor=cor)
                messages.success(request, f"Canal de origem '{nome}' criado com sucesso!")
            return redirect('/painel/pousada/config/?tab=canais')

        elif acao == 'editar_canal_origem':
            canal_id = request.POST.get('canal_id')
            canal = get_object_or_404(CanalOrigem, id=canal_id, pousada=pousada)
            nome = request.POST.get('nome', '').strip()
            cor = request.POST.get('cor', '#6b7280').strip()
            ativo = request.POST.get('ativo') == 'on'
            if not nome:
                messages.error(request, "O nome do canal de origem é obrigatório.")
            else:
                canal.nome = nome
                canal.cor = cor
                canal.ativo = ativo
                canal.save()
                messages.success(request, f"Canal de origem '{nome}' atualizado com sucesso!")
            return redirect('/painel/pousada/config/?tab=canais')

        elif acao == 'excluir_canal_origem':
            canal_id = request.POST.get('canal_id')
            canal = get_object_or_404(CanalOrigem, id=canal_id, pousada=pousada)
            nome = canal.nome
            canal.delete()
            messages.success(request, f"Canal de origem '{nome}' excluído com sucesso.")
            return redirect('/painel/pousada/config/?tab=canais')

    # Seed default channels if empty
    if CanalOrigem.objects.filter(pousada=pousada).count() == 0:
        canais_padrao = [
            ('Booking.com', '#003580'),
            ('Airbnb', '#FF5A5F'),
            ('WhatsApp', '#25D366'),
            ('Balcão / Direto', '#4F46E5'),
            ('Site / Motor', '#0D9488'),
            ('Instagram', '#E1306C'),
        ]
        for nome_c, cor_c in canais_padrao:
            CanalOrigem.objects.get_or_create(pousada=pousada, nome=nome_c, defaults={'cor': cor_c})

    # Read lists
    tags = Tag.objects.filter(pousada=pousada).order_by('nome')
    motivos_bloqueio = MotivoBloqueio.objects.filter(pousada=pousada).order_by('nome')
    categorias = CategoriaQuarto.objects.filter(pousada=pousada).order_by('nome')
    quartos = Quarto.objects.filter(pousada=pousada).select_related('categoria').order_by('nome_identificacao')
    metodos_pagamento = MetodoPagamentoConfig.objects.filter(pousada=pousada, ativo=True).order_by('nome')
    checklist_itens = ChecklistItem.objects.filter(pousada=pousada, ativo=True).order_by('id')
    canais_origem = CanalOrigem.objects.filter(pousada=pousada).order_by('nome')

    fechaduras = Fechadura.objects.filter(quarto__pousada=pousada).select_related('quarto').order_by('quarto__nome_identificacao')
    templates_mensagem = TemplateMensagem.objects.filter(pousada=pousada).order_by('nome')

    # Lógica de Pré-visualização do Template
    preview_template = None
    preview_assunto = None
    preview_corpo = None
    preview_html = None
    preview_id = request.GET.get('preview_id')
    if preview_id and tab == 'mensagens':
        try:
            preview_template = TemplateMensagem.objects.get(id=preview_id, pousada=pousada)
            from reservas.models import Reserva
            reserva = Reserva.objects.filter(pousada=pousada).first()
            if not reserva:
                from hospedes.models import Hospede
                mock_hospede = Hospede(nome_completo="José da Silva")
                mock_quarto = Quarto(nome_identificacao="Suíte Luxo 102")
                reserva = Reserva(
                    pousada=pousada,
                    hospede=mock_hospede,
                    quarto=mock_quarto,
                    data_checkin=timezone.localdate(),
                    data_checkout=timezone.localdate() + timezone.timedelta(days=3),
                    token_acesso="00000000-0000-0000-0000-000000000000"
                )
            from reservas.services.mensageria import renderizar_template_mensagem
            preview_assunto, preview_corpo, preview_html = renderizar_template_mensagem(reserva, preview_template)
        except TemplateMensagem.DoesNotExist:
            pass

    return render(request, 'pousada/configuracoes_pousada.html', {
        'pousada': pousada,
        'tab': tab,
        'tags': tags,
        'motivos_bloqueio': motivos_bloqueio,
        'categorias': categorias,
        'quartos': quartos,
        'metodos_pagamento': metodos_pagamento,
        'checklist_itens': checklist_itens,
        'canais_origem': canais_origem,
        'fechaduras': fechaduras,
        'templates_mensagem': templates_mensagem,
        'preview_template': preview_template,
        'preview_assunto': preview_assunto,
        'preview_corpo': preview_html or preview_corpo,
    })


@login_required
@pousada_required
def gerenciar_equipe(request):
    pousada = request.pousada

    if request.method == 'POST':
        acao = request.POST.get('acao')

        if acao == 'novo_funcionario':
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '')
            nivel_acesso_id = request.POST.get('nivel_acesso')

            if not username or not email or not password or not nivel_acesso_id:
                messages.error(request, "Todos os campos do funcionário são obrigatórios.")
                return redirect('/painel/pousada/config/equipe/')

            if User.objects.filter(username=username).exists():
                messages.error(request, "Este nome de usuário já está sendo utilizado.")
                return redirect('/painel/pousada/config/equipe/')

            if User.objects.filter(email=email).exists():
                messages.error(request, "Este endereço de e-mail já está sendo utilizado.")
                return redirect('/painel/pousada/config/equipe/')

            try:
                user = User.objects.create_user(username=username, email=email, password=password)
                # NivelAcesso is a global model (no pousada FK) — shared across all pousadas
                nivel = get_object_or_404(NivelAcesso, id=nivel_acesso_id)
                ClienteSaaS.objects.create(
                    user=user,
                    nivel_acesso=nivel,
                    pousada=pousada,
                    plano_ativo=True,
                    ativo=True
                )
                messages.success(request, f"Funcionário {username} criado com sucesso!")
            except Exception as e:
                messages.error(request, f"Erro ao criar funcionário: {str(e)}")

        elif acao == 'excluir_funcionario':
            funcionario_id = request.POST.get('funcionario_id')
            if funcionario_id:
                funcionario = get_object_or_404(ClienteSaaS, id=funcionario_id, pousada=pousada)
                username = funcionario.user.username
                try:
                    funcionario.user.delete()
                    messages.success(request, f"Funcionário {username} excluído com sucesso!")
                except Exception as e:
                    messages.error(request, f"Erro ao excluir funcionário: {str(e)}")
            else:
                messages.error(request, "ID do funcionário não fornecido.")

        elif acao == 'toggle_funcionario':
            funcionario_id = request.POST.get('funcionario_id')
            if funcionario_id:
                funcionario = get_object_or_404(ClienteSaaS, id=funcionario_id, pousada=pousada)
                funcionario.ativo = not funcionario.ativo
                funcionario.save()
                status = "ativado" if funcionario.ativo else "desativado"
                messages.success(request, f"Funcionário {funcionario.user.username} foi {status} com sucesso!")
            else:
                messages.error(request, "ID do funcionário não fornecido.")

        return redirect('/painel/pousada/config/equipe/')

    # GET request
    funcionarios = ClienteSaaS.objects.filter(pousada=pousada).select_related('user', 'nivel_acesso')
    # NivelAcesso is a global model (no pousada FK) — shared across all pousadas
    niveis_acesso = NivelAcesso.objects.all()

    return render(request, 'pousada/configuracoes_pousada.html', {
        'pousada': pousada,
        'tab': 'equipe',
        'funcionarios': funcionarios,
        'niveis_acesso': niveis_acesso,
    })


@login_required
@pousada_required
def ver_logs(request):
    from django.core.paginator import Paginator
    pousada = request.pousada

    logs_list = LogAuditoria.objects.filter(pousada=pousada).select_related('usuario').order_by('-timestamp')
    
    # Paginação (PERF-01) - 20 itens por página
    paginator = Paginator(logs_list, 20)
    page_number = request.GET.get('page')
    logs = paginator.get_page(page_number)

    return render(request, 'pousada/configuracoes_pousada.html', {
        'pousada': pousada,
        'tab': 'auditoria',
        'logs': logs,
    })


@login_required
@pousada_required
def governanca_dashboard(request):
    # Enforce access permissions
    def check_governanca_permission(user):
        if user.is_superuser:
            return True
        cliente = getattr(user, 'cliente_saas', None)
        if cliente and cliente.nivel_acesso:
            return cliente.nivel_acesso.pode_acessar_governanca
        return False

    if not check_governanca_permission(request.user):
        messages.error(request, "Você não possui permissão para acessar a área de Governança.")
        return redirect('reserva-lista')

    pousada = request.pousada

    from reservas.models import Reserva
    from django.db.models import Q

    if request.method == 'POST':
        acao = request.POST.get('acao')

        if acao == 'iniciar_limpeza':
            quarto_id = request.POST.get('quarto_id')
            quarto = get_object_or_404(Quarto, id=quarto_id, pousada=pousada)

            # Alterar o status do quarto
            quarto.status_limpeza = 'em_limpeza'
            quarto.save()

            # Tentar encontrar a reserva finalizada correspondente
            reserva_relacionada = Reserva.objects.filter(
                quarto=quarto, 
                status='finalizada'
            ).order_by('-data_checkout').first()

            # Encontrar ou criar ordem de serviço de limpeza
            ordem = OrdemServico.objects.filter(
                quarto=quarto,
                tipo_servico='limpeza',
                status='pendente'
            ).first()
            if not ordem:
                ordem = OrdemServico.objects.create(
                    quarto=quarto,
                    tipo_servico='limpeza',
                    prioridade='media',
                    descricao="Limpeza iniciada diretamente no painel.",
                    criado_por=request.user,
                    responsavel=request.user,
                    status='em_andamento',
                    pousada=pousada
                )
            else:
                ordem.status = 'em_andamento'
                ordem.responsavel = request.user
                ordem.save()

            # Criar o registro de limpeza
            registro = RegistroLimpeza.objects.create(
                quarto=quarto,
                funcionario=request.user,
                status='em_limpeza',
                reserva_relacionada=reserva_relacionada,
                ordem_servico=ordem
            )

            # Se o checklist estiver ativo, pré-popular os itens
            if pousada.usa_checklist_limpeza:
                itens = ChecklistItem.objects.filter(pousada=pousada, ativo=True)
                for item in itens:
                    ItemLimpezaConcluido.objects.create(
                        registro_limpeza=registro,
                        checklist_item=item,
                        concluido=False
                    )

            messages.success(request, f"Limpeza do quarto {quarto.nome_identificacao} iniciada com sucesso!")
            return redirect('governanca-dashboard')

        elif acao == 'salvar_checklist':
            registro_id = request.POST.get('registro_id')
            registro = get_object_or_404(RegistroLimpeza, id=registro_id, quarto__pousada=pousada)

            # Obter itens do checklist marcados (concluidos)
            concluidos_ids = request.POST.getlist('itens_concluidos[]')
            
            # Converter ids para inteiros para comparação segura
            concluidos_ids = [int(i_id) for i_id in concluidos_ids if i_id.isdigit()]

            # Atualizar os itens no banco
            itens_concluidos = list(ItemLimpezaConcluido.objects.filter(registro_limpeza=registro))
            for item in itens_concluidos:
                item.concluido = item.id in concluidos_ids
            ItemLimpezaConcluido.objects.bulk_update(itens_concluidos, ['concluido'])

            messages.success(request, "Progresso do checklist salvo!")
            return redirect('governanca-dashboard')

        elif acao == 'finalizar_limpeza':
            registro_id = request.POST.get('registro_id')
            quarto_id = request.POST.get('quarto_id')

            if registro_id:
                registro = get_object_or_404(RegistroLimpeza, id=registro_id, quarto__pousada=pousada)
                quarto = registro.quarto

                # Se checklist ativo, verificar se todos estão concluídos
                if pousada.usa_checklist_limpeza:
                    itens_pendentes = ItemLimpezaConcluido.objects.filter(registro_limpeza=registro, concluido=False)
                    if itens_pendentes.exists():
                        messages.error(request, f"Não é possível finalizar a limpeza do quarto {quarto.nome_identificacao}. Existem itens do checklist pendentes!")
                        return redirect('governanca-dashboard')

                # Finalizar registro e atualizar quarto
                registro.status = 'limpo'
                registro.save()
                
                quarto.status_limpeza = 'limpo'
                quarto.save()

                if registro.ordem_servico:
                    ordem = registro.ordem_servico
                    ordem.status = 'concluido'
                    ordem.data_conclusao = timezone.now()
                    ordem.save()

                messages.success(request, f"Quarto {quarto.nome_identificacao} está limpo e liberado!")
            elif quarto_id:
                # Caso sem checklist onde não há registro ativo, cria um registro de limpeza limpo direto
                quarto = get_object_or_404(Quarto, id=quarto_id, pousada=pousada)
                
                ordem = OrdemServico.objects.filter(
                    quarto=quarto,
                    tipo_servico='limpeza',
                    status__in=['pendente', 'em_andamento']
                ).first()
                if not ordem:
                    ordem = OrdemServico.objects.create(
                        quarto=quarto,
                        tipo_servico='limpeza',
                        status='concluido',
                        criado_por=request.user,
                        responsavel=request.user,
                        pousada=pousada,
                        data_conclusao=timezone.now()
                    )
                else:
                    ordem.status = 'concluido'
                    ordem.responsavel = request.user
                    ordem.data_conclusao = timezone.now()
                    ordem.save()

                RegistroLimpeza.objects.create(
                    quarto=quarto,
                    funcionario=request.user,
                    status='limpo',
                    data=timezone.now(),
                    ordem_servico=ordem
                )

                quarto.status_limpeza = 'limpo'
                quarto.save()
                messages.success(request, f"Quarto {quarto.nome_identificacao} marcado como limpo diretamente!")

            return redirect('governanca-dashboard')

        elif acao == 'marcar_sujo':
            quarto_id = request.POST.get('quarto_id')
            quarto = get_object_or_404(Quarto, id=quarto_id, pousada=pousada)

            quarto.status_limpeza = 'sujo'
            quarto.save()

            # Criar ordem de serviço de limpeza se não existir
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
                    descricao="Quarto marcado como sujo manualmente.",
                    status='pendente',
                    criado_por=request.user,
                    pousada=pousada
                )

            messages.warning(request, f"Quarto {quarto.nome_identificacao} marcado como sujo manualmente.")
            return redirect('governanca-dashboard')

        elif acao == 'criar_ordem_servico':
            quarto_id = request.POST.get('quarto_id')
            tipo_servico = request.POST.get('tipo_servico')
            prioridade = request.POST.get('prioridade')
            descricao = request.POST.get('descricao', '').strip()
            responsavel_id = request.POST.get('responsavel_id')

            quarto = get_object_or_404(Quarto, id=quarto_id, pousada=pousada)
            responsavel = None
            if responsavel_id:
                responsavel = User.objects.filter(id=responsavel_id, cliente_saas__pousada=pousada).first()
                if not responsavel:
                    messages.error(request, "Responsável não encontrado ou não pertence a esta pousada.")
                    return redirect('governanca-dashboard')

            ordem = OrdemServico.objects.create(
                quarto=quarto,
                tipo_servico=tipo_servico,
                prioridade=prioridade,
                descricao=descricao,
                criado_por=request.user,
                responsavel=responsavel,
                status='pendente',
                pousada=pousada
            )

            # Se for do tipo limpeza, marcar o quarto como sujo se não estiver em limpeza/sujo
            if tipo_servico == 'limpeza' and quarto.status_limpeza == 'limpo':
                quarto.status_limpeza = 'sujo'
                quarto.save()

            messages.success(request, f"Ordem de Serviço #{ordem.id} criada com sucesso!")
            return redirect('governanca-dashboard')

        elif acao == 'alterar_status_ordem':
            ordem_id = request.POST.get('ordem_id')
            novo_status = request.POST.get('status')
            responsavel_id = request.POST.get('responsavel_id')

            ordem = get_object_or_404(OrdemServico, id=ordem_id, pousada=pousada)
            if responsavel_id:
                responsavel = User.objects.filter(id=responsavel_id, cliente_saas__pousada=pousada).first()
                if not responsavel:
                    messages.error(request, "Responsável não encontrado ou não pertence a esta pousada.")
                    return redirect('governanca-dashboard')
                ordem.responsavel = responsavel
            
            if novo_status:
                ordem.status = novo_status
                if novo_status == 'concluido':
                    ordem.data_conclusao = timezone.now()
                    # Se for limpeza, também atualiza quarto e RegistroLimpeza
                    if ordem.tipo_servico == 'limpeza':
                        quarto = ordem.quarto
                        quarto.status_limpeza = 'limpo'
                        quarto.save()
                        # Link/Atualizar RegistroLimpeza se houver
                        try:
                            registro = ordem.registro_limpeza
                            registro.status = 'limpo'
                            registro.save()
                        except RegistroLimpeza.DoesNotExist:
                            RegistroLimpeza.objects.create(
                                quarto=quarto,
                                funcionario=request.user,
                                status='limpo',
                                data=timezone.now(),
                                ordem_servico=ordem
                            )
                elif novo_status == 'em_andamento' and ordem.tipo_servico == 'limpeza':
                    # Se for limpeza e for iniciada, atualiza status do quarto
                    quarto = ordem.quarto
                    if quarto.status_limpeza != 'em_limpeza':
                        quarto.status_limpeza = 'em_limpeza'
                        quarto.save()
                    # Criar ou obter RegistroLimpeza
                    registro, created = RegistroLimpeza.objects.get_or_create(
                        ordem_servico=ordem,
                        defaults={
                            'quarto': quarto,
                            'funcionario': request.user,
                            'status': 'em_limpeza',
                            'data': timezone.now()
                        }
                    )
                    if created and pousada.usa_checklist_limpeza:
                        itens = ChecklistItem.objects.filter(pousada=pousada, ativo=True)
                        for item in itens:
                            ItemLimpezaConcluido.objects.create(
                                registro_limpeza=registro,
                                checklist_item=item,
                                concluido=False
                            )
            ordem.save()
            messages.success(request, f"Ordem de Serviço #{ordem.id} atualizada com sucesso!")
            return redirect('governanca-dashboard')

    # GET Request logic
    # List all active quartos
    quartos = Quarto.objects.filter(pousada=pousada, ativo=True).select_related('categoria')
    
    # Obter os registros de limpeza ativos (em_limpeza) com prefetch_related para evitar N+1 (PERF-03)
    registros_ativos = RegistroLimpeza.objects.filter(
        quarto__pousada=pousada, 
        status='em_limpeza'
    ).select_related('quarto', 'funcionario', 'reserva_relacionada', 'reserva_relacionada__hospede').prefetch_related('itens_concluidos', 'itens_concluidos__checklist_item')
    
    # Criar mapeamento do registro para facilitar consulta no template
    mapa_registros = {reg.quarto.id: reg for reg in registros_ativos}

    # Associar registros e itens de checklist aos quartos
    for q in quartos:
        q.active_registro = mapa_registros.get(q.id)
        if q.active_registro:
            q.itens_checklist = q.active_registro.itens_concluidos.all()

    # Separar os quartos por status para o painel principal
    quartos_sujos = [q for q in quartos if q.status_limpeza == 'sujo']
    quartos_em_limpeza = [q for q in quartos if q.status_limpeza == 'em_limpeza']
    quartos_limpos = [q for q in quartos if q.status_limpeza == 'limpo']

    # Ordens de serviço e funcionários para o painel
    ordens_servico = OrdemServico.objects.filter(pousada=pousada).select_related('quarto', 'criado_por', 'responsavel').order_by('-data_criacao')
    funcionarios = User.objects.filter(
        Q(cliente_saas__pousada=pousada) | Q(pousada_owner=pousada)
    ).distinct().order_by('username')

    return render(request, 'pousada/governanca.html', {
        'pousada': pousada,
        'quartos_sujos': quartos_sujos,
        'quartos_em_limpeza': quartos_em_limpeza,
        'quartos_limpos': quartos_limpos,
        'mapa_registros': mapa_registros,
        'ordens_servico': ordens_servico,
        'funcionarios': funcionarios,
    })


@login_required
@pousada_required
def governanca_mobile_view(request):
    pousada = request.pousada

    if request.method == 'POST':
        acao = request.POST.get('acao')
        
        if acao == 'iniciar_ordem':
            ordem_id = request.POST.get('ordem_id')
            ordem = get_object_or_404(OrdemServico, id=ordem_id, responsavel=request.user, pousada=pousada)
            ordem.status = 'em_andamento'
            ordem.save()
            
            if ordem.tipo_servico == 'limpeza':
                quarto = ordem.quarto
                quarto.status_limpeza = 'em_limpeza'
                quarto.save()
                
                # Criar ou obter RegistroLimpeza
                registro, created = RegistroLimpeza.objects.get_or_create(
                    ordem_servico=ordem,
                    defaults={
                        'quarto': quarto,
                        'funcionario': request.user,
                        'status': 'em_limpeza',
                        'data': timezone.now()
                    }
                )
                if created and pousada.usa_checklist_limpeza:
                    itens = ChecklistItem.objects.filter(pousada=pousada, ativo=True)
                    for item in itens:
                        ItemLimpezaConcluido.objects.create(
                            registro_limpeza=registro,
                            checklist_item=item,
                            concluido=False
                        )
            messages.success(request, f"Serviço no quarto {ordem.quarto.nome_identificacao} iniciado!")
            return redirect('governanca-mobile')
            
        elif acao == 'salvar_checklist':
            registro_id = request.POST.get('registro_id')
            registro = get_object_or_404(RegistroLimpeza, id=registro_id, funcionario=request.user)
            concluidos_ids = request.POST.getlist('itens_concluidos[]')
            concluidos_ids = [int(i_id) for i_id in concluidos_ids if i_id.isdigit()]
            
            itens_checklist = list(registro.itens_concluidos.all())
            for item in itens_checklist:
                item.concluido = item.id in concluidos_ids
            ItemLimpezaConcluido.objects.bulk_update(itens_checklist, ['concluido'])
                
            messages.success(request, "Progresso do checklist salvo!")
            return redirect('governanca-mobile')
            
        elif acao == 'concluir_ordem':
            ordem_id = request.POST.get('ordem_id')
            ordem = get_object_or_404(OrdemServico, id=ordem_id, responsavel=request.user, pousada=pousada)
            
            if ordem.tipo_servico == 'limpeza':
                try:
                    registro = ordem.registro_limpeza
                    if pousada.usa_checklist_limpeza:
                        if registro.itens_concluidos.filter(concluido=False).exists():
                            messages.error(request, "Existem itens do checklist pendentes para este quarto!")
                            return redirect('governanca-mobile')
                    registro.status = 'limpo'
                    registro.save()
                except RegistroLimpeza.DoesNotExist:
                    RegistroLimpeza.objects.create(
                        quarto=ordem.quarto,
                        funcionario=request.user,
                        status='limpo',
                        data=timezone.now(),
                        ordem_servico=ordem
                    )
                quarto = ordem.quarto
                quarto.status_limpeza = 'limpo'
                quarto.save()
                
            ordem.status = 'concluido'
            ordem.data_conclusao = timezone.now()
            ordem.save()
            messages.success(request, f"Serviço no quarto {ordem.quarto.nome_identificacao} concluído!")
            return redirect('governanca-mobile')

    # GET Request
    ordens = OrdemServico.objects.filter(
        responsavel=request.user,
        status__in=['pendente', 'em_andamento'],
        pousada=pousada
    ).select_related('quarto', 'quarto__categoria').order_by(
        Case(
            When(prioridade='alta', then=Value(0)),
            When(prioridade='media', then=Value(1)),
            When(prioridade='baixa', then=Value(2)),
            default=Value(3),
            output_field=IntegerField(),
        ),
        'data_criacao'
    )
    
    # Adicionar checklist items
    for ordem in ordens:
        if ordem.tipo_servico == 'limpeza':
            try:
                ordem.registro = ordem.registro_limpeza
                ordem.itens_checklist = ordem.registro.itens_concluidos.all().select_related('checklist_item')
            except RegistroLimpeza.DoesNotExist:
                ordem.registro = None
                ordem.itens_checklist = []

    return render(request, 'pousada/governanca_mobile.html', {
        'pousada': pousada,
        'ordens': ordens,
    })


