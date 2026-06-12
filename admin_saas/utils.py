from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect

class SuperuserRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return redirect('reserva-lista')
        return super().dispatch(request, *args, **kwargs)
