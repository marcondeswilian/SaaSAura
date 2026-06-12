import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from pousada.models import Pousada, Quarto, Fechadura
from reservas.models import Reserva
from django.contrib.auth.models import User

# Get or create a pousada, room, user to test
user = User.objects.first()
pousada = Pousada.objects.first()
quarto = Quarto.objects.first()

if not pousada or not quarto:
    print("Pre-requisitos não encontrados no banco. Cadastrando pousada e quarto temporários...")
    if not user:
        user = User.objects.create_user(username="temp_user", password="password")
    
    pousada, _ = Pousada.objects.get_or_create(dono=user, defaults={'nome': 'Pousada Teste'})
    
    from pousada.models import CategoriaQuarto
    categoria, _ = CategoriaQuarto.objects.get_or_create(pousada=pousada, defaults={'nome': 'Categoria Teste', 'valor_diaria': 100})
    quarto, _ = Quarto.objects.get_or_create(pousada=pousada, categoria=categoria, defaults={'nome_identificacao': '101'})

# Create a fechadura for the room
fechadura, created = Fechadura.objects.get_or_create(
    quarto=quarto,
    defaults={
        'device_id': 'eb0957acfe1234567890ab',
        'nome_exibicao': 'Fechadura Quarto ' + quarto.nome_identificacao,
        'is_online': True
    }
)

print(f"Fechadura vinculada ao Quarto {quarto.nome_identificacao}: {fechadura}")

# Create a reservation in 'pendente' status
reserva = Reserva.objects.create(
    pousada=pousada,
    quarto=quarto,
    data_checkin=date.today() + timedelta(days=1),
    data_checkout=date.today() + timedelta(days=3),
    status='pendente',
    valor_total=200
)

print(f"Reserva #{reserva.id} criada com status 'pendente'. Senha da fechadura: {reserva.senha_fechadura}")

# Confirm the reservation
reserva.status = 'confirmada'
reserva.save()

# Refresh from db
reserva.refresh_from_db()

print(f"Reserva #{reserva.id} atualizada para 'confirmada'. Senha da fechadura gerada: {reserva.senha_fechadura}")

# Clean up
reserva.delete()
if created:
    fechadura.delete()

# Assertions
assert reserva.senha_fechadura is not None
assert len(reserva.senha_fechadura) == 6
assert reserva.senha_fechadura.isdigit()
print("SUCESSO: A automação de senha de fechadura Tuya funcionou perfeitamente!")
