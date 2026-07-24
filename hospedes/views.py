from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Hospede, Tag
from .forms import HospedeForm
from pousada.decorators import pousada_required
from pousada.utils import get_pousada_for_user

@login_required
@pousada_required
def hospede_lista_view(request):
    pousada = request.pousada
    hospedes_list = Hospede.objects.filter(pousada=pousada).prefetch_related('tags').order_by('nome_completo')

    query = request.GET.get('q', '').strip()
    if query:
        hospedes_list = hospedes_list.filter(
            Q(nome_completo__icontains=query) |
            Q(cpf__icontains=query) |
            Q(email__icontains=query) |
            Q(telefone__icontains=query)
        )

    # Paginação (PERF-01) - 20 itens por página
    paginator = Paginator(hospedes_list, 20)
    page_number = request.GET.get('page')
    hospedes = paginator.get_page(page_number)

    total_hospedes = hospedes_list.count()
    tags_count = Tag.objects.filter(pousada=pousada).count()
    contatos_count = hospedes_list.filter(
        ~Q(email='') & ~Q(email__isnull=True) |
        ~Q(telefone='') & ~Q(telefone__isnull=True)
    ).count()

    return render(request, 'hospedes/lista_hospedes.html', {
        'hospedes': hospedes,
        'query': query,
        'total_hospedes': total_hospedes,
        'tags_count': tags_count,
        'contatos_count': contatos_count,
    })

@login_required
@pousada_required
def hospede_criar_view(request):
    pousada = request.pousada
    tags_pousada = Tag.objects.filter(pousada=pousada).order_by('nome')

    if request.method == 'POST':
        form = HospedeForm(request.POST)
        if form.is_valid():
            hospede = form.save(commit=False)
            hospede.pousada = pousada
            hospede.save()
            
            tag_ids = request.POST.getlist('tags')
            if tag_ids:
                hospede.tags.set(Tag.objects.filter(pousada=pousada, id__in=tag_ids))
                
            messages.success(request, f"Hóspede {hospede.nome_completo} criado com sucesso!")
            return redirect('hospede-lista')
        else:
            messages.error(request, "Por favor, corrija os erros no formulário.")
    else:
        form = HospedeForm()

    return render(request, 'hospedes/hospede_form.html', {
        'form': form,
        'tags_pousada': tags_pousada,
        'action': 'Criar'
    })

@login_required
@pousada_required
def hospede_editar_view(request, pk):
    pousada = request.pousada
    hospede = get_object_or_404(Hospede, pk=pk, pousada=pousada)
    tags_pousada = Tag.objects.filter(pousada=pousada).order_by('nome')

    if request.method == 'POST':
        if request.POST.get('acao') == 'excluir':
            # BUG-12: Verificar reservas ativas antes de excluir (CASCADE apagaria as reservas!)
            reservas_ativas = hospede.reservas.filter(status__in=['pendente', 'confirmada'])
            if reservas_ativas.exists():
                count = reservas_ativas.count()
                messages.error(
                    request,
                    f'Não é possível excluir {hospede.nome_completo}: ele(a) possui {count} reserva(s) ativa(s). '
                    f'Cancele ou finalize as reservas antes de excluir o hóspede.'
                )
                return redirect('hospede-editar', pk=pk)
            hospede.delete()
            messages.success(request, 'Hóspede excluído com sucesso.')
            return redirect('hospede-lista')

        form = HospedeForm(request.POST, instance=hospede)
        if form.is_valid():
            form.save()
            tag_ids = request.POST.getlist('tags')
            hospede.tags.set(Tag.objects.filter(pousada=pousada, id__in=tag_ids))
            messages.success(request, f"Hóspede {hospede.nome_completo} atualizado com sucesso!")
            return redirect('hospede-lista')
        else:
            messages.error(request, "Por favor, corrija os erros no formulário.")
    else:
        form = HospedeForm(instance=hospede)

    hospede_tags_ids = list(hospede.tags.values_list('id', flat=True))
    reservas_hospede = hospede.reservas.all().order_by('-data_checkin')

    return render(request, 'hospedes/hospede_form.html', {
        'hospede': hospede,
        'form': form,
        'tags_pousada': tags_pousada,
        'hospede_tags_ids': hospede_tags_ids,
        'reservas_hospede': reservas_hospede,
        'action': 'Editar'
    })

