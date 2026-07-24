import os
import sys
import django
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

def test():
    user = User.objects.first()
    if not user:
        return
    
    from pousada.models import Pousada
    pousada = getattr(user, 'pousada_owner', None) or Pousada.objects.first()
    
    from hospedes.models import Hospede
    h = Hospede.objects.filter(pousada=pousada).first()
    
    c = Client(SERVER_NAME='localhost')
    c.force_login(user)
    
    print(f'Testing POST invalid edit page for hospede {h.id}')
    try:
        response = c.post(f'/painel/hospedes/{h.id}/editar/', {
            'nome_completo': ''  # Invalid since it's required
        }, HTTP_HOST='localhost')
        print(f'Status: {response.status_code}')
        if response.status_code == 500:
            print('ERROR CONTENT:')
            print(response.content.decode('utf-8')[:2000])
    except Exception as e:
        print('EXCEPTION:')
        print(traceback.format_exc())

test()
