from django.shortcuts import redirect
from django.contrib import messages
from django.urls import resolve
from django.contrib.auth import logout
from django.http import JsonResponse
from django.utils import timezone

class CheckAcessoSaaS:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_superuser:
            cliente = getattr(request.user, 'cliente_saas', None)
            if not cliente or not cliente.ativo:
                logout(request)
                return redirect('/admin/login/')

            if not cliente.plano_ativo:
                logout(request)
                messages.error(request, 'Seu plano está inativo. Entre em contato com o suporte.')
                return redirect('/login/')

            # Verificar expiração de data se houver
            if cliente.data_expiracao and cliente.data_expiracao < timezone.localdate():
                logout(request)
                return redirect('/admin/login/')

            # Se tiver nivel de acesso, verificar as permissões
            nivel = cliente.nivel_acesso
            if nivel:
                try:
                    match = resolve(request.path_info)
                    url_name = match.url_name
                except Exception:
                    url_name = None

                if url_name:
                    perm_map = {
                        # Reservas
                        'calendario': 'pode_acessar_reservas',
                        'reserva-lista': 'pode_acessar_reservas',
                        'reserva-criar': 'pode_acessar_reservas',
                        'reserva-editar': 'pode_acessar_reservas',
                        'api-reservas': 'pode_acessar_reservas',
                        'api-reserva-update': 'pode_acessar_reservas',
                        'api-quartos': 'pode_acessar_reservas',
                        'api-quartos-disponiveis': 'pode_acessar_reservas',
                        # CRM / Clientes
                        'hospede-lista': 'pode_acessar_crm',
                        'hospede-criar': 'pode_acessar_crm',
                        'hospede-editar': 'pode_acessar_crm',
                        'api-hospedes-list-create': 'pode_acessar_crm',
                        'exportar-fnrh': 'pode_acessar_crm',
                        # Configurações
                        'pousada-config': 'pode_acessar_configuracoes',
                        # Financeiro
                        'registrar-pagamento': 'pode_acessar_financeiro',
                        'editar-pagamento': 'pode_acessar_financeiro',
                    }

                    if url_name in perm_map:
                        perm_field = perm_map[url_name]
                        if not getattr(nivel, perm_field, False):
                            # Se for API, retornar 403
                            if request.path_info.startswith('/api/') or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                                return JsonResponse({'error': 'Você não tem permissão para acessar este recurso.'}, status=403)
                            
                            # Encontrar fallback url
                            fallback_url = None
                            if nivel.pode_acessar_reservas:
                                fallback_url = 'calendario'
                            elif nivel.pode_acessar_crm:
                                fallback_url = 'hospede-lista'
                            elif nivel.pode_acessar_configuracoes:
                                fallback_url = 'pousada-config'

                            if fallback_url and url_name != fallback_url:
                                messages.error(request, 'Você não tem permissão para acessar essa seção.')
                                return redirect(fallback_url)
                            elif not fallback_url:
                                logout(request)
                                return redirect('/admin/login/')

        response = self.get_response(request)
        return response
