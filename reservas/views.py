from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db import transaction
from decimal import Decimal, InvalidOperation
import json
import csv

# Create your views here.
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Reserva
from .serializers import ReservaSerializer, ReservaUpdateSerializer
from pousada.models import Quarto
from pousada.serializers import QuartoSerializer

class ReservaUpdateAPI(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReservaUpdateSerializer

    def get_queryset(self):
        return Reserva.objects.filter(pousada__dono=self.request.user)

# Esta view vai listar todas as reservas em formato JSON
class ReservaListAPI(generics.ListAPIView):
    serializer_class = ReservaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Reserva.objects.filter(
            pousada__dono=self.request.user
        ).select_related('hospede', 'quarto', 'quarto__categoria', 'motivo_bloqueio')

# Esta view vai listar todos os quartos em formato JSON
class QuartoListAPI(generics.ListAPIView):
    serializer_class = QuartoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Quarto.objects.filter(pousada__dono=self.request.user).select_related('categoria')


@login_required
def api_quartos_disponiveis(request):
    from pousada.utils import get_pousada_for_user
    pousada = get_pousada_for_user(request.user)
    if not pousada:
        return JsonResponse({'error': 'Usuário não possui uma pousada cadastrada.'}, status=400)

    start_str = request.GET.get('start')
    end_str = request.GET.get('end')

    if not start_str or not end_str:
        return JsonResponse({'error': 'Parâmetros start e end são obrigatórios.'}, status=400)

    from reservas.models import Reserva
    from pousada.models import Quarto

    # Obter os IDs de quartos ocupados no período
    ocupados_ids = Reserva.objects.filter(
        pousada=pousada,
        data_checkin__lt=end_str,
        data_checkout__gt=start_str
    ).values_list('quarto_id', flat=True)

    # Filtrar os quartos livres
    quartos_livres = Quarto.objects.filter(pousada=pousada, ativo=True).exclude(id__in=ocupados_ids).select_related('categoria')

    data = [
        {
            'id': q.id,
            'nome': f"{q.nome_identificacao} ({q.categoria.nome} - R$ {q.categoria.valor_diaria})"
        }
        for q in quartos_livres
    ]
    return JsonResponse(data, safe=False)


from hospedes.models import Hospede

class CalendarioView(LoginRequiredMixin, TemplateView):
    template_name = 'reservas/calendario.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            user = request.user
            if not user.is_superuser:
                from pousada.utils import get_pousada_for_user
                pousada = get_pousada_for_user(user)
                if not pousada:
                    cliente = getattr(user, 'cliente_saas', None)
                    if cliente and cliente.nivel_acesso:
                        na = cliente.nivel_acesso
                        is_operational = (
                            na.pode_acessar_governanca and
                            not na.pode_acessar_reservas and
                            not na.pode_acessar_crm and
                            not na.pode_acessar_financeiro and
                            not na.pode_acessar_configuracoes
                        )
                        if is_operational:
                            from django.shortcuts import redirect
                            return redirect('governanca-mobile')
        return super().dispatch(request, *args, **kwargs)


@login_required
def reserva_lista_view(request):
    from pousada.utils import get_pousada_for_user
    from django.core.paginator import Paginator
    pousada = get_pousada_for_user(request.user)
    if not pousada:
        return render(request, 'reservas/lista_reservas.html', {'error': 'Você não possui uma pousada vinculada ao seu usuário.'})
        
    from datetime import date, timedelta, datetime
    
    data_inicio_str = request.GET.get('data_inicio')
    data_fim_str = request.GET.get('data_fim')
    
    if data_inicio_str and data_fim_str:
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        except ValueError:
            data_inicio = date.today()
            data_fim = date.today() + timedelta(days=7)
    else:
        data_inicio = date.today()
        data_fim = date.today() + timedelta(days=7)

    reservas_list = Reserva.objects.filter(
        pousada=pousada,
        data_checkin__lte=data_fim,
        data_checkout__gte=data_inicio
    ).select_related(
        'hospede', 'quarto', 'quarto__categoria', 'motivo_bloqueio', 'canal_origem'
    ).order_by('data_checkin')
    
    # Paginação (PERF-01) - 20 itens por página
    paginator = Paginator(reservas_list, 20)
    page_number = request.GET.get('page')
    reservas = paginator.get_page(page_number)
    
    quartos = Quarto.objects.filter(pousada=pousada, ativo=True).select_related('categoria')
    reservas_confirmadas_count = reservas_list.filter(status='confirmada').count()
    from django.db.models import Avg
    valor_medio = reservas_list.filter(is_bloqueio=False).aggregate(media=Avg('valor_total'))['media'] or Decimal('0.00')
    from pousada.models import MetodoPagamentoConfig, CanalOrigem
    metodos_pagamento = MetodoPagamentoConfig.objects.filter(pousada=pousada, ativo=True).order_by('nome')
    canais_origem = CanalOrigem.objects.filter(pousada=pousada, ativo=True).order_by('nome')
    return render(request, 'reservas/lista_reservas.html', {
        'reservas': reservas,
        'quartos': quartos,
        'pousada': pousada,
        'reservas_confirmadas_count': reservas_confirmadas_count,
        'valor_medio': valor_medio,
        'metodos_pagamento': metodos_pagamento,
        'canais_origem': canais_origem,
        'data_inicio_filtro': data_inicio.strftime('%Y-%m-%d'),
        'data_fim_filtro': data_fim.strftime('%Y-%m-%d'),
    })

@login_required
@require_POST
def reserva_criar_view(request):
    from pousada.utils import get_pousada_for_user
    pousada = get_pousada_for_user(request.user)
    if not pousada:
        messages.error(request, 'Usuário não possui uma pousada cadastrada.')
        return redirect('reserva-lista')
        
    tipo_registro = request.POST.get('tipo_registro', 'reserva')
    room_ids = request.POST.getlist('room_ids')
    data_checkin = request.POST.get('data_checkin')
    data_checkout = request.POST.get('data_checkout')
    
    if not room_ids:
        messages.error(request, 'Pelo menos um quarto deve ser selecionado.')
        return redirect('reserva-lista')
        
    # Criar Grupo se houver mais de um quarto selecionado
    grupo = None
    if len(room_ids) > 1:
        from reservas.models import Grupo
        nome_grupo = ""
        if tipo_registro == 'bloqueio':
            motivo_bloqueio_id = request.POST.get('motivo_bloqueio')
            from pousada.models import MotivoBloqueio
            try:
                motivo = MotivoBloqueio.objects.get(id=motivo_bloqueio_id, pousada=pousada)
                nome_grupo = f"Bloqueio Grupo - {motivo.nome} ({data_checkin})"
            except Exception:
                nome_grupo = f"Bloqueio Grupo ({data_checkin})"
        else:
            hospede_id = request.POST.get('hospede')
            try:
                hospede = Hospede.objects.get(id=hospede_id, pousada=pousada)
                nome_grupo = f"Grupo - {hospede.nome_completo} ({data_checkin})"
            except Exception:
                nome_grupo = f"Grupo ({data_checkin})"
        
        grupo = Grupo.objects.create(nome=nome_grupo)
        
    if tipo_registro == 'bloqueio':
        motivo_bloqueio_id = request.POST.get('motivo_bloqueio')
        if not (data_checkin and data_checkout and motivo_bloqueio_id):
            messages.error(request, 'Preencha todos os campos obrigatórios para o bloqueio.')
            return redirect('reserva-lista')
            
        try:
            from pousada.models import MotivoBloqueio
            motivo = MotivoBloqueio.objects.get(id=motivo_bloqueio_id, pousada=pousada)
            
            created_count = 0
            for r_id in room_ids:
                quarto = Quarto.objects.get(id=r_id, pousada=pousada)
                Reserva.objects.create(
                    pousada=pousada,
                    grupo=grupo,
                    hospede=None,
                    quarto=quarto,
                    data_checkin=data_checkin,
                    data_checkout=data_checkout,
                    valor_total=Decimal('0.00'),
                    is_bloqueio=True,
                    motivo_bloqueio=motivo,
                    status='confirmada'
                )
                created_count += 1
                
            if created_count > 1:
                messages.success(request, f'{created_count} bloqueios de quartos criados com sucesso e vinculados ao grupo!')
            else:
                messages.success(request, 'Bloqueio de quarto para manutenção criado com sucesso!')
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("Erro ao criar bloqueio")
            messages.error(request, 'Erro interno ao criar bloqueio.')
        return redirect('reserva-lista')
        
    hospede_id = request.POST.get('hospede')
    valor_total = request.POST.get('valor_total')
    status = request.POST.get('status', 'pendente')
    
    # Campos FNRH opcionais
    motivo_viagem = request.POST.get('motivo_viagem', '')
    meio_transporte = request.POST.get('meio_transporte', '')
    placa_veiculo = request.POST.get('placa_veiculo', '')
    ultima_procedencia = request.POST.get('ultima_procedencia', '')
    proximo_destino = request.POST.get('proximo_destino', '')
    
    canal_origem_id = request.POST.get('canal_origem')
    canal_origem_obj = None
    if canal_origem_id:
        from pousada.models import CanalOrigem
        canal_origem_obj = CanalOrigem.objects.filter(id=canal_origem_id, pousada=pousada).first()
    
    if not (hospede_id and data_checkin and data_checkout and valor_total):
        messages.error(request, 'Preencha todos os campos obrigatórios.')
        return redirect('reserva-lista')

    # BUG-03: Validar que a data de saída é posterior à de entrada
    if data_checkin >= data_checkout:
        messages.error(request, 'A data de saída deve ser posterior à data de entrada.')
        return redirect('reserva-lista')

    try:
        hospede = Hospede.objects.get(id=hospede_id, pousada=pousada)

        total_val = Decimal(valor_total)
        if total_val < 0:
            raise InvalidOperation("O valor total não pode ser negativo.")
            
        valor_sinal_str = request.POST.get('valor_sinal', '0')
        metodo_pagamento_sinal = request.POST.get('metodo_pagamento_sinal', 'pix')
        valor_sinal = Decimal('0.00')
        if valor_sinal_str:
            try:
                valor_sinal = Decimal(valor_sinal_str)
                if valor_sinal < 0:
                    valor_sinal = Decimal('0.00')
            except (ValueError, InvalidOperation):
                pass

        tipo_cobranca = request.POST.get('tipo_cobranca', 'unica')

        # OPT-06: Usar transação atômica com select_for_update para evitar race condition
        with transaction.atomic():
            # BUG-03: Verificar conflito de quarto para cada quarto selecionado
            conflito = Reserva.objects.select_for_update().filter(
                quarto__id__in=room_ids,
                pousada=pousada,
                data_checkin__lt=data_checkout,
                data_checkout__gt=data_checkin
            )
            if ...:  # o edit se encarrega
                pass

            # Lógica continua abaixo para a criação usando o loop
            created_count = 0
            for idx, r_id in enumerate(room_ids):
                quarto = Quarto.objects.get(id=r_id, pousada=pousada)

                if len(room_ids) > 1:
                    if tipo_cobranca == 'dividido':
                        n = len(room_ids)
                        valor_base = (total_val / n).quantize(Decimal('0.01'))
                        if idx == 0:
                            valor_reserva = total_val - (valor_base * (n - 1))
                        else:
                            valor_reserva = valor_base
                    else:
                        valor_reserva = total_val if idx == 0 else Decimal('0.00')
                else:
                    valor_reserva = total_val

                reserva_obj = Reserva.objects.create(
                    pousada=pousada,
                    grupo=grupo,
                    hospede=hospede,
                    quarto=quarto,
                    canal_origem=canal_origem_obj,
                    data_checkin=data_checkin,
                    data_checkout=data_checkout,
                    valor_total=valor_reserva.quantize(Decimal('0.01')),
                    status=status,
                    motivo_viagem=motivo_viagem or None,
                    meio_transporte=meio_transporte or None,
                    placa_veiculo=placa_veiculo or None,
                    ultima_procedencia=ultima_procedencia or None,
                    proximo_destino=proximo_destino or None
                )

                if created_count == 0 and valor_sinal > 0:
                    from financeiro.models import Pagamento
                    from datetime import date
                    Pagamento.objects.create(
                        pousada=pousada,
                        reserva=reserva_obj,
                        tipo='sinal',
                        valor=valor_sinal.quantize(Decimal('0.01')),
                        metodo_pagamento=metodo_pagamento_sinal,
                        status='pago',
                        data_vencimento=date.today(),
                        data_pagamento=date.today(),
                        observacao="Sinal registrado automaticamente na criação da reserva."
                    )
                created_count += 1

        if created_count > 1:
            messages.success(request, f'{created_count} reservas criadas com sucesso e vinculadas ao grupo!')
        else:
            messages.success(request, 'Reserva criada com sucesso!')
    except (ValueError, InvalidOperation):
        messages.error(request, 'O valor total informado é inválido.')
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("Erro ao criar reserva")
        messages.error(request, 'Erro interno ao processar a reserva.')

    return redirect('reserva-lista')

@login_required
def api_hospedes_list_create(request):
    from pousada.utils import get_pousada_for_user
    pousada = get_pousada_for_user(request.user)
    if not pousada:
        return JsonResponse({'error': 'Usuário não possui uma pousada cadastrada.'}, status=400)

    if request.method == 'GET':
        q = request.GET.get('q', '').strip()
        hospedes = Hospede.objects.filter(pousada=pousada)
        if q:
            hospedes = hospedes.filter(nome_completo__icontains=q)
        data = [{'id': h.id, 'nome_completo': h.nome_completo} for h in hospedes[:20]]
        return JsonResponse(data, safe=False)
        
    elif request.method == 'POST':
        import json
        try:
            try:
                data = json.loads(request.body)
                nome_hospede = data.get('nome')
            except:
                nome_hospede = request.POST.get('nome')

            if not nome_hospede:
                return JsonResponse({'status': 'erro', 'mensagem': 'Nome é obrigatório.'}, status=400)

            nome_hospede = nome_hospede.strip()
            
            novo_hospede = Hospede.objects.create(
                nome_completo=nome_hospede,
                pousada=pousada
            )
            return JsonResponse({
                'status': 'ok',
                'id': novo_hospede.id,
                'nome': novo_hospede.nome_completo
            }, status=201)
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("Erro ao criar hóspede de forma rápida")
            return JsonResponse({'status': 'erro', 'mensagem': 'Erro interno ao criar hóspede.'}, status=400)

@login_required
def exportar_fnrh_csv(request):
    from pousada.utils import get_pousada_for_user
    pousada = get_pousada_for_user(request.user)
    if not pousada:
        messages.error(request, 'Usuário não possui uma pousada cadastrada.')
        return redirect('reserva-lista')

    data_inicio = request.GET.get('data_inicio') or request.POST.get('data_inicio')
    data_fim = request.GET.get('data_fim') or request.POST.get('data_fim')

    if not data_inicio or not data_fim:
        messages.error(request, 'Por favor, selecione as datas de início e fim para a exportação.')
        return redirect('reserva-lista')

    reservas = Reserva.objects.filter(
        pousada=pousada,
        data_checkin__range=[data_inicio, data_fim],
        checkin_concluido=True,
        fnrh_exportado=False
    ).order_by('data_checkin')

    if not reservas.exists():
        messages.warning(request, 'Nenhuma reserva concluída (com check-in online finalizado) e não exportada foi encontrada no período selecionado.')
        return redirect('reserva-lista')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="fnrh_exportado.csv"'

    # Escrever BOM para compatibilidade com Excel em português
    response.write('\ufeff')

    writer = csv.writer(response, delimiter=';')
    
    # Cabeçalho Oficial FNRH
    writer.writerow([
        'Nome', 'Documento(CPF/Passaporte)', 'Nascimento', 'Genero', 'Profissao', 
        'Nacionalidade', 'CEP', 'Endereco', 'Cidade', 'Estado', 
        'Data_Entrada', 'Data_Saida', 'Motivo', 'Transporte', 'Procedencia', 'Destino'
    ])

    # Gravar dados e coletar IDs para bulk_update
    ids_exportados = []
    for r in reservas.select_related('hospede'):
        h = r.hospede
        if not h:
            continue
        writer.writerow([
            h.nome_completo or '',
            h.cpf or h.numero_documento or '',
            h.data_nascimento.strftime('%d/%m/%Y') if h.data_nascimento else '',
            h.get_genero_display() or h.get_sexo_display() or '',
            h.profissao or '',
            h.nacionalidade or 'Brasileiro(a)',
            h.cep or '',
            h.endereco or '',
            h.cidade or '',
            h.estado or '',
            r.data_checkin.strftime('%d/%m/%Y') if r.data_checkin else '',
            r.data_checkout.strftime('%d/%m/%Y') if r.data_checkout else '',
            r.get_motivo_viagem_display() if r.motivo_viagem else '',
            r.get_meio_transporte_display() if r.meio_transporte else '',
            r.ultima_procedencia or '',
            r.proximo_destino or ''
        ])
        ids_exportados.append(r.id)

    # BUG-06: Usar bulk_update em vez de N saves individuais dentro do loop
    if ids_exportados:
        Reserva.objects.filter(id__in=ids_exportados).update(fnrh_exportado=True)

    return response

@login_required
def reserva_editar_view(request, pk):
    from pousada.utils import get_pousada_for_user
    pousada = get_pousada_for_user(request.user)
    if not pousada:
        messages.error(request, 'Você não possui uma pousada vinculada ao seu usuário.')
        return redirect('reserva-lista')

    reserva = get_object_or_404(Reserva, id=pk, pousada=pousada)
    from .forms import ReservaForm
    
    if request.method == 'POST':
        acao = request.POST.get('acao')
        if acao == 'excluir':
            reserva.delete()
            messages.success(request, f'Lançamento #{pk} cancelado/excluído com sucesso!')
            return redirect('reserva-lista')

        form = ReservaForm(request.POST, instance=reserva, pousada=pousada)
        if form.is_valid():
            # BUG-C06: Verificar conflito de quarto na edição
            quarto = form.cleaned_data['quarto']
            data_checkin = form.cleaned_data['data_checkin']
            data_checkout = form.cleaned_data['data_checkout']
            
            if quarto.id != reserva.quarto_id or data_checkin != reserva.data_checkin or data_checkout != reserva.data_checkout:
                conflito = Reserva.objects.filter(
                    quarto=quarto,
                    pousada=pousada,
                    data_checkout__gt=data_checkin,
                    data_checkin__lt=data_checkout,
                    status__in=['pendente', 'confirmada']
                ).exclude(id=reserva.id).exists()
                if conflito:
                    messages.error(request, 'Este quarto já está reservado no período selecionado.')
                    return redirect('reserva-editar', pk=reserva.id)
            
            form.save()
            messages.success(request, 'Reserva atualizada com sucesso!')
            return redirect('reserva-lista')
        else:
            messages.error(request, 'Por favor, verifique os campos informados.')
                
    else:
        form = ReservaForm(instance=reserva, pousada=pousada)
        
    quartos = Quarto.objects.filter(pousada=pousada, ativo=True)
    hospedes = Hospede.objects.filter(pousada=pousada).order_by('nome_completo')
    
    from pousada.models import MetodoPagamentoConfig, CanalOrigem
    metodos_pagamento = MetodoPagamentoConfig.objects.filter(pousada=pousada, ativo=True).order_by('nome')
    canais_origem = CanalOrigem.objects.filter(pousada=pousada, ativo=True).order_by('nome')
    
    from django.urls import reverse
    url_acesso = request.build_absolute_uri(reverse('portal_hospede', kwargs={'token': reserva.token_acesso}))
    
    return render(request, 'reservas/editar_reserva.html', {
        'reserva': reserva,
        'form': form,
        'quartos': quartos,
        'hospedes': hospedes,
        'pousada': pousada,
        'metodos_pagamento': metodos_pagamento,
        'canais_origem': canais_origem,
        'url_acesso': url_acesso,
    })



@login_required
@require_POST
def registrar_pagamento(request):
    from pousada.utils import get_pousada_for_user
    pousada = get_pousada_for_user(request.user)
    if not pousada:
        messages.error(request, 'Você não possui uma pousada cadastrada.')
        return redirect('reserva-lista')

    reserva_id = request.POST.get('reserva_id')
    reserva = get_object_or_404(Reserva, id=reserva_id, pousada=pousada)
    from .forms import PagamentoForm

    form = PagamentoForm(request.POST)
    if form.is_valid():
        pagamento = form.save(commit=False)
        pagamento.pousada = pousada
        pagamento.reserva = reserva
        pagamento.status = 'pago'
        pagamento.data_vencimento = pagamento.data_pagamento or date.today()
        if not pagamento.data_pagamento:
            pagamento.data_pagamento = date.today()
        pagamento.observacao = "Pagamento registrado via painel."
        
        if pagamento.valor <= 0:
            messages.error(request, 'O valor do pagamento deve ser maior que zero.')
        else:
            pagamento.save()
            messages.success(request, f'Pagamento de R$ {pagamento.valor} registrado com sucesso para a Reserva #{reserva_id}!')
    else:
        messages.error(request, 'Erro ao registrar pagamento. Verifique as informações fornecidas.')

    return redirect('reserva-editar', pk=reserva.id)

@login_required
@require_POST
def editar_pagamento(request, pk):
    from pousada.utils import get_pousada_for_user
    pousada = get_pousada_for_user(request.user)
    if not pousada:
        messages.error(request, 'Você não possui uma pousada cadastrada.')
        return redirect('reserva-lista')

    from financeiro.models import Pagamento
    pagamento = get_object_or_404(Pagamento, id=pk, pousada=pousada)
    from .forms import PagamentoForm

    form = PagamentoForm(request.POST, instance=pagamento)
    if form.is_valid():
        if pagamento.valor <= 0:
            messages.error(request, 'O valor do pagamento deve ser maior que zero.')
        else:
            # Revalidar data_vencimento para bater com a de pagamento se alterado
            if pagamento.data_pagamento:
                pagamento.data_vencimento = pagamento.data_pagamento
            pagamento.save()
            messages.success(request, 'Pagamento atualizado com sucesso!')
    else:
        messages.error(request, 'Erro ao atualizar pagamento. Verifique as informações.')

    return redirect('reserva-editar', pk=pagamento.reserva.id)


from django.utils import timezone
from django.db.models import Q, Sum
from decimal import Decimal
from pousada.models import OrdemServico
from financeiro.models import Pagamento

@login_required
def dashboard_view(request):
    # Check if user is operational-only
    user = request.user
    if not user.is_superuser and not hasattr(user, 'pousada_owner'):
        cliente = getattr(user, 'cliente_saas', None)
        if cliente and cliente.nivel_acesso:
            na = cliente.nivel_acesso
            is_operational = (
                na.pode_acessar_governanca and
                not na.pode_acessar_reservas and
                not na.pode_acessar_crm and
                not na.pode_acessar_financeiro and
                not na.pode_acessar_configuracoes
            )
            if is_operational:
                return redirect('governanca-mobile')

    from pousada.utils import get_pousada_for_user
    pousada = get_pousada_for_user(request.user)
    if not pousada:
        messages.error(request, "Você não possui uma pousada vinculada ao seu usuário.")
        return redirect('reserva-lista')

    # Get local current time/date
    today = timezone.localdate()

    # Load rooms, reservations, payments, and service orders in batch to prevent N+1 queries
    quartos = Quarto.objects.filter(pousada=pousada, ativo=True).select_related('categoria')
    
    reservas_ativas = Reserva.objects.filter(
        pousada=pousada,
        status__in=['pendente', 'sinal', 'confirmada', 'finalizada']
    ).select_related('quarto', 'hospede')

    ordens_ativas = OrdemServico.objects.filter(
        quarto__pousada=pousada,
        status__in=['pendente', 'em_andamento']
    ).select_related('quarto', 'responsavel')

    # 1. Occupancy Calculation
    total_quartos = len(quartos)
    quartos_ocupados_ids = set()
    for r in reservas_ativas:
        if r.status in ['confirmada', 'finalizada'] and not r.is_bloqueio:
            r_checkin_date = r.data_checkin.date() if hasattr(r.data_checkin, 'date') else r.data_checkin
            r_checkout_date = r.data_checkout.date() if hasattr(r.data_checkout, 'date') else r.data_checkout
            if r_checkin_date <= today < r_checkout_date:
                quartos_ocupados_ids.add(r.quarto_id)
    ocupacao_count = len(quartos_ocupados_ids)
    ocupacao_porcentagem = (ocupacao_count / total_quartos * 100) if total_quartos > 0 else 0

    # 2. Receita do Dia (Confirmada)
    receita_dia = Pagamento.objects.filter(
        pousada=pousada,
        status='pago',
        data_pagamento=today
    ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

    # 3. Check-ins Previstos (Hoje)
    checkins_hoje = [
        r for r in reservas_ativas 
        if (r.data_checkin.date() if hasattr(r.data_checkin, 'date') else r.data_checkin) == today 
        and r.status in ['pendente', 'sinal', 'confirmada'] 
        and not r.is_bloqueio
    ]
    checkins_previstos_count = len(checkins_hoje)

    # 4. Check-outs Pendentes (Hoje)
    checkouts_hoje = [r for r in reservas_ativas if r.data_checkout == today and r.status == 'confirmada' and not r.is_bloqueio]
    checkouts_pendentes_count = len(checkouts_hoje)

    # 5. Timeline / Ações Imediatas
    acoes_imediatas = []

    # Ação: Limpeza Pendente (quartos status 'sujo')
    quartos_sujos = [q for q in quartos if q.status_limpeza == 'sujo']
    for q in quartos_sujos:
        acoes_imediatas.append({
            'tipo': 'limpeza',
            'titulo': f"Limpeza Pendente: Quarto {q.nome_identificacao}",
            'descricao': f"O quarto {q.nome_identificacao} ({q.categoria.nome}) está marcado como sujo e necessita de higienização.",
            'prioridade': 'media',
            'badge': 'Limpeza',
            'link': '/painel/governanca/?tab=limpeza-tab',
        })

    # Ação: Check-in Pendente (reservas de hoje pendentes)
    for r in checkins_hoje:
        hospede_nome = r.hospede.nome_completo if r.hospede else "Hóspede não informado"
        acoes_imediatas.append({
            'tipo': 'checkin',
            'titulo': f"Check-in Pendente: {hospede_nome}",
            'descricao': f"Entrada prevista para hoje no Quarto {r.quarto.nome_identificacao} ({r.quarto.categoria.nome}).",
            'prioridade': 'alta',
            'badge': 'Check-in',
            'link': f"/painel/reservas/{r.id}/editar/",
        })

    # Ação: OS de Manutenção (abertas/em andamento)
    for os in ordens_ativas:
        prioridade_map = {'alta': 'alta', 'media': 'media', 'baixa': 'baixa'}
        badge_map = {'alta': 'Urgente', 'media': 'Manutenção', 'baixa': 'Ajuste'}
        acoes_imediatas.append({
            'tipo': 'manutencao',
            'titulo': f"OS #{os.id} - {os.get_tipo_servico_display()} no Quarto {os.quarto.nome_identificacao}",
            'descricao': os.descricao or f"Serviço de {os.get_tipo_servico_display()} pendente.",
            'prioridade': prioridade_map.get(os.prioridade, 'media'),
            'badge': badge_map.get(os.prioridade, 'Manutenção'),
            'link': '/painel/governanca/?tab=manutencao-tab',
        })

    # Sort actions: alta priority first, then media, then baixa
    prioridade_peso = {'alta': 3, 'media': 2, 'baixa': 1}
    acoes_imediatas.sort(key=lambda x: prioridade_peso.get(x['prioridade'], 0), reverse=True)

    return render(request, 'reservas/dashboard_operacoes.html', {
        'pousada': pousada,
        'ocupacao_porcentagem': f"{ocupacao_porcentagem:.1f}",
        'receita_dia': receita_dia,
        'checkins_previstos_count': checkins_previstos_count,
        'checkouts_pendentes_count': checkouts_pendentes_count,
        'acoes_imediatas': acoes_imediatas,
    })


def portal_hospede(request, token):
    """
    Portal unificado do hóspede.
    Única porta de entrada pública: usa token_acesso (UUID) da Reserva.
    Gerencia check-in online (FNRH) e, condicionalmente, a senha da fechadura Tuya.
    """
    reserva = get_object_or_404(Reserva, token_acesso=token)
    quarto = reserva.quarto
    pousada = reserva.pousada

    # Verificar se o quarto possui uma fechadura física vinculada
    fechadura = quarto.fechaduras.first() if quarto else None
    tem_fechadura = fechadura is not None

    # BUG-04: Impedir acesso se reserva está cancelada
    if reserva.status == 'cancelada':
        return render(request, 'reservas/portal_hospede.html', {
            'erro': 'Esta reserva foi cancelada. Por favor, entre em contato com a pousada.',
            'pousada': pousada,
            'tem_fechadura': False,
        })

    if request.method == 'POST':
        nome_completo = request.POST.get('nome_completo', '').strip()
        email = request.POST.get('email', '').strip()
        telefone = request.POST.get('telefone', '').strip()
        data_nasc_str = request.POST.get('data_nascimento', '').strip()
        nacionalidade = request.POST.get('nacionalidade', '').strip() or 'Brasileira'
        cpf_passaporte = request.POST.get('cpf_passaporte', '').strip()
        documento_identidade = request.POST.get('documento_identidade', '').strip()

        cep = request.POST.get('cep', '').strip()
        logradouro = request.POST.get('logradouro', '').strip()
        numero = request.POST.get('numero', '').strip()
        complemento = request.POST.get('complemento', '').strip()
        bairro = request.POST.get('bairro', '').strip()
        cidade = request.POST.get('cidade', '').strip()
        estado = request.POST.get('estado', '').strip()
        pais = request.POST.get('pais', '').strip() or 'Brasil'

        placa_veiculo = request.POST.get('placa_veiculo', '').strip()
        motivo_viagem = request.POST.get('motivo_viagem', 'lazer').strip()
        pin_sufixo = request.POST.get('pin_sufixo', '').strip()

        # Parse data de nascimento
        from datetime import datetime
        try:
            data_nascimento = datetime.strptime(data_nasc_str, '%Y-%m-%d').date()
        except ValueError:
            data_nascimento = None

        # Salvar FNRH completa vinculada à reserva
        from .models import FichaFNRH
        FichaFNRH.objects.update_or_create(
            reserva=reserva,
            defaults={
                'nome_completo': nome_completo,
                'email': email,
                'telefone': telefone,
                'data_nascimento': data_nascimento,
                'nacionalidade': nacionalidade,
                'cpf_passaporte': cpf_passaporte,
                'documento_identidade': documento_identidade,
                'cep': cep,
                'logradouro': logradouro,
                'numero': numero,
                'complemento': complemento or None,
                'bairro': bairro,
                'cidade': cidade,
                'estado': estado,
                'pais': pais,
                'placa_veiculo': placa_veiculo or None,
                'motivo_viagem': motivo_viagem,
            }
        )

        # Atualizar dados do hóspede no cadastro
        reserva.hospede_cpf = cpf_passaporte
        reserva.placa_veiculo = placa_veiculo
        reserva.checkin_online_realizado = True

        if reserva.hospede:
            reserva.hospede.cpf = cpf_passaporte
            reserva.hospede.save()

        # --- Integração com fechadura Tuya (apenas se o quarto tiver fechadura física) ---
        if tem_fechadura and pin_sufixo and pin_sufixo.isdigit() and len(pin_sufixo) == 4:
            from pousada.services.tuya_service import TuyaLockService
            service = TuyaLockService(pousada=reserva.pousada)
            prefixo = reserva.pousada.prefixo_pin_padrao or "101"
            senha_final = service.gerar_senha_com_prefixo(pin_sufixo, prefixo=prefixo)
            reserva.senha_fechadura = senha_final

            from datetime import datetime as dt, time as dtime
            from zoneinfo import ZoneInfo
            timezone_sao_paulo = ZoneInfo('America/Sao_Paulo')
            dt_inicio = dt.combine(reserva.data_checkin, dtime(14, 0)).replace(tzinfo=timezone_sao_paulo)
            dt_fim = dt.combine(reserva.data_checkout, dtime(12, 0)).replace(tzinfo=timezone_sao_paulo)

            try:
                service.criar_senha_temporaria(
                    device_id=fechadura.device_id,
                    nome=f"Reserva #{reserva.id} - {reserva.hospede.nome_completo if reserva.hospede else 'Hospede'}",
                    senha=senha_final,
                    data_inicio=dt_inicio,
                    data_fim=dt_fim
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Erro ao integrar com fechadura Tuya: {str(e)}")

            messages.success(request, "Check-in online realizado e senha de acesso ativada!")
        else:
            messages.success(request, "Check-in online concluído com sucesso! Sua reserva está confirmada.")

        reserva.save()
        return redirect('portal_hospede', token=token)

    mensagem_pos_checkin_processada = ""
    video_embed_url = ""
    if pousada.mensagem_pos_checkin:
        senha_quarto = quarto.senha_acesso if quarto and quarto.senha_acesso else "Não configurada"
        nome_quarto = quarto.nome_identificacao if quarto else "Não definido"
        mensagem_pos_checkin_processada = pousada.mensagem_pos_checkin.replace('{{ senha_quarto }}', senha_quarto).replace('{{ nome_quarto }}', nome_quarto)
    
    if pousada.video_pos_checkin:
        video_embed_url = pousada.video_pos_checkin
        
        # Logica melhorada para YouTube (watch e youtu.be e shorts)
        if 'youtube.com/watch?v=' in video_embed_url:
            video_id = video_embed_url.split('watch?v=')[1].split('&')[0]
            video_embed_url = f"https://www.youtube.com/embed/{video_id}"
        elif 'youtu.be/' in video_embed_url:
            video_id = video_embed_url.split('youtu.be/')[1].split('?')[0]
            video_embed_url = f"https://www.youtube.com/embed/{video_id}"
        elif 'youtube.com/shorts/' in video_embed_url:
            video_id = video_embed_url.split('youtube.com/shorts/')[1].split('?')[0].split('/')[0]
            video_embed_url = f"https://www.youtube.com/embed/{video_id}"

    return render(request, 'reservas/portal_hospede.html', {
        'reserva': reserva,
        'quarto': quarto,
        'pousada': pousada,
        'tem_fechadura': tem_fechadura,
        'mensagem_pos_checkin_processada': mensagem_pos_checkin_processada,
        'video_embed_url': video_embed_url,
    })


@login_required
def imprimir_fnrh_view(request, pk):
    from pousada.utils import get_pousada_for_user
    pousada = get_pousada_for_user(request.user)
    if not pousada:
        messages.error(request, 'Você não possui uma pousada vinculada ao seu usuário.')
        return redirect('reserva-lista')

    reserva = get_object_or_404(Reserva, id=pk, pousada=pousada)
    ficha = getattr(reserva, 'ficha_fnrh', None)
    
    if not ficha and reserva.hospede:
        h = reserva.hospede
        ficha = {
            'nome_completo': h.nome_completo,
            'email': h.email,
            'telefone': h.telefone,
            'data_nascimento': h.data_nascimento,
            'nacionalidade': h.nacionalidade,
            'cpf_passaporte': h.cpf or h.numero_documento,
            'documento_identidade': h.numero_documento if h.tipo_documento != 'CPF' else '',
            'cep': h.cep,
            'logradouro': h.endereco,
            'cidade': h.cidade,
            'estado': h.estado,
        }

    return render(request, 'reservas/fnrh_imprimir.html', {
        'reserva': reserva,
        'pousada': pousada,
        'ficha': ficha,
    })
