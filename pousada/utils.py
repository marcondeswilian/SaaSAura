from django.core.exceptions import ObjectDoesNotExist

def get_pousada_for_user(user):
    """
    Retorna a pousada vinculada ao usuário (dono ou funcionário/cliente SaaS).
    Substitui de forma limpa o monkey-patch dinâmico em User.pousada.
    """
    if not user or not user.is_authenticated:
        return None
        
    # Verificar se é o dono da pousada
    if hasattr(user, 'pousada_owner'):
        return user.pousada_owner
        
    # Verificar se é funcionário vinculado a uma pousada via perfil ClienteSaaS
    cliente = getattr(user, 'cliente_saas', None)
    if cliente and cliente.pousada:
        return cliente.pousada
        
    return None
