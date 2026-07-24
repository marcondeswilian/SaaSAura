import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from hospedes.models import Hospede
h = Hospede.objects.filter(nome_completo__icontains='Ediney').first()
if h:
    print(f'Phone: {h.telefone}')
    print(f'WhatsApp Link: {h.link_whatsapp}')
else:
    print('Guest not found locally')
