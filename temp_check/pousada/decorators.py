from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .utils import get_pousada_for_user

def pousada_required(view_func):
    """
    Decorator que garante que o usuário possui uma pousada vinculada.
    Injeta o objeto 'pousada' em request.pousada para uso na view.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        pousada = get_pousada_for_user(request.user)
        if not pousada:
            messages.error(request, "Você não possui uma pousada vinculada ao seu usuário.")
            return redirect('reserva-lista')
        request.pousada = pousada
        return view_func(request, *args, **kwargs)
    return wrapper
