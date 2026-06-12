from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Hospede, Tag
from datetime import datetime

@login_required
def hospede_lista_view(request):
    try:
        pousada = request.user.pousada
    except Exception:
        # Fallback if no pousada
        return render(request, 'hospedes/lista_hospedes.html', {
            'hospedes': [],
            'query': ''
        })

    hospedes = Hospede.objects.filter(pousada=pousada).prefetch_related('tags').order_by('nome_completo')

    query = request.GET.get('q', '').strip()
    if query:
        hospedes = hospedes.filter(
            Q(nome_completo__icontains=query) |
            Q(cpf__icontains=query) |
            Q(email__icontains=query) |
            Q(telefone__icontains=query)
        )

    total_hospedes = hospedes.count()
    tags_count = Tag.objects.filter(pousada=pousada).count()
    contatos_count = hospedes.filter(
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
def hospede_criar_view(request):
    try:
        pousada = request.user.pousada
    except Exception:
        messages.error(request, "Você não possui uma pousada vinculada ao seu usuário.")
        return redirect('reserva-lista')

    tags_pousada = Tag.objects.filter(pousada=pousada).order_by('nome')

    if request.method == 'POST':
        nome_completo = request.POST.get('nome_completo')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        cpf = request.POST.get('cpf')
        data_nascimento_str = request.POST.get('data_nascimento')
        genero = request.POST.get('genero')
        profissao = request.POST.get('profissao')
        cep = request.POST.get('cep')
        endereco = request.POST.get('endereco')
        cidade = request.POST.get('cidade')
        estado = request.POST.get('estado')
        tag_ids = request.POST.getlist('tags')

        data_nascimento = None
        if data_nascimento_str:
            try:
                data_nascimento = datetime.strptime(data_nascimento_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        hospede = Hospede.objects.create(
            pousada=pousada,
            nome_completo=nome_completo,
            email=email,
            telefone=telefone,
            cpf=cpf,
            data_nascimento=data_nascimento,
            genero=genero,
            profissao=profissao,
            cep=cep,
            endereco=endereco,
            cidade=cidade,
            estado=estado,
        )

        if tag_ids:
            hospede.tags.set(Tag.objects.filter(pousada=pousada, id__in=tag_ids))

        messages.success(request, f"Hóspede {hospede.nome_completo} criado com sucesso!")
        return redirect('hospede-lista')

    return render(request, 'hospedes/hospede_form.html', {
        'tags_pousada': tags_pousada,
        'action': 'Criar'
    })

@login_required
def hospede_editar_view(request, pk):
    try:
        pousada = request.user.pousada
    except Exception:
        messages.error(request, "Você não possui uma pousada vinculada ao seu usuário.")
        return redirect('reserva-lista')

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

        hospede.nome_completo = request.POST.get('nome_completo')
        hospede.email = request.POST.get('email')
        hospede.telefone = request.POST.get('telefone')
        hospede.cpf = request.POST.get('cpf')
        data_nascimento_str = request.POST.get('data_nascimento')
        hospede.genero = request.POST.get('genero')
        hospede.profissao = request.POST.get('profissao')
        hospede.cep = request.POST.get('cep')
        hospede.endereco = request.POST.get('endereco')
        hospede.cidade = request.POST.get('cidade')
        hospede.estado = request.POST.get('estado')
        tag_ids = request.POST.getlist('tags')

        if data_nascimento_str:
            try:
                hospede.data_nascimento = datetime.strptime(data_nascimento_str, '%Y-%m-%d').date()
            except ValueError:
                hospede.data_nascimento = None
        else:
            hospede.data_nascimento = None

        hospede.save()
        hospede.tags.set(Tag.objects.filter(pousada=pousada, id__in=tag_ids))

        messages.success(request, f"Hóspede {hospede.nome_completo} atualizado com sucesso!")
        return redirect('hospede-lista')

    hospede_tags_ids = list(hospede.tags.values_list('id', flat=True))

    return render(request, 'hospedes/hospede_form.html', {
        'hospede': hospede,
        'tags_pousada': tags_pousada,
        'hospede_tags_ids': hospede_tags_ids,
        'action': 'Editar'
    })
