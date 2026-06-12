from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from pousada.models import Pousada, CategoriaQuarto, Quarto
from hospedes.models import Hospede
from reservas.models import Reserva, FichaFNRH
import datetime

class ImprimirFNRHViewTests(TestCase):
    def setUp(self):
        # Create user and their pousada
        self.user = User.objects.create_superuser(username='dono', password='password123')
        self.pousada = Pousada.objects.create(
            dono=self.user,
            nome='Pousada Teste',
            slug='pousada-teste'
        )
        
        # Create category and room
        self.categoria = CategoriaQuarto.objects.create(
            pousada=self.pousada,
            nome='Standard',
            valor_diaria=150.00,
            capacidade=2
        )
        self.quarto = Quarto.objects.create(
            pousada=self.pousada,
            categoria=self.categoria,
            nome_identificacao='101'
        )
        
        # Create guest
        self.hospede = Hospede.objects.create(
            pousada=self.pousada,
            nome_completo='Hóspede Teste'
        )
        
        # Create reservation
        self.reserva = Reserva.objects.create(
            pousada=self.pousada,
            quarto=self.quarto,
            hospede=self.hospede,
            data_checkin=datetime.date(2026, 6, 12),
            data_checkout=datetime.date(2026, 6, 15),
            valor_total=450.00,
            status='confirmada'
        )
        
        self.client = Client()

    def test_imprimir_fnrh_requires_login(self):
        url = reverse('imprimir_fnrh', kwargs={'pk': self.reserva.id})
        response = self.client.get(url)
        # Should redirect to login since not logged in
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_imprimir_fnrh_pousada_check(self):
        # Create another user and reservation
        other_user = User.objects.create_superuser(username='dono2', password='password123')
        other_pousada = Pousada.objects.create(
            dono=other_user,
            nome='Outra Pousada',
            slug='outra-pousada'
        )
        other_categoria = CategoriaQuarto.objects.create(
            pousada=other_pousada,
            nome='Luxury',
            valor_diaria=300.00
        )
        other_quarto = Quarto.objects.create(
            pousada=other_pousada,
            categoria=other_categoria,
            nome_identificacao='202'
        )
        other_reserva = Reserva.objects.create(
            pousada=other_pousada,
            quarto=other_quarto,
            data_checkin=datetime.date(2026, 6, 12),
            data_checkout=datetime.date(2026, 6, 15),
            valor_total=900.00,
            status='confirmada'
        )
        
        # Login as 'dono'
        self.client.login(username='dono', password='password123')
        
        # Try to access reservation belonging to another pousada
        url = reverse('imprimir_fnrh', kwargs={'pk': other_reserva.id})
        response = self.client.get(url)
        # Should return 404 (Not Found)
        self.assertEqual(response.status_code, 404)

    def test_imprimir_fnrh_no_ficha_renders_blank_lines(self):
        self.client.login(username='dono', password='password123')
        
        url = reverse('imprimir_fnrh', kwargs={'pk': self.reserva.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reservas/fnrh_imprimir.html')
        
        # Ficha should be None in the context
        self.assertIsNone(response.context['ficha'])
        # Check standard fields are present but value is empty / blank line border is rendered
        self.assertContains(response, 'Nome Completo:')
        # Check window.print() script is loaded
        self.assertContains(response, 'window.print()')

    def test_imprimir_fnrh_with_ficha_renders_filled_data(self):
        # Create FichaFNRH
        ficha = FichaFNRH.objects.create(
            reserva=self.reserva,
            nome_completo='Hóspede FNRH Preenchido',
            email='hospede@example.com',
            telefone='11999999999',
            data_nascimento=datetime.date(1990, 1, 1),
            nacionalidade='Brasileira',
            cpf_passaporte='123.456.789-00',
            documento_identidade='12345678-9',
            cep='01001-000',
            logradouro='Praça da Sé',
            numero='100',
            bairro='Centro',
            cidade='São Paulo',
            estado='SP',
            pais='Brasil',
            motivo_viagem='lazer'
        )
        
        self.client.login(username='dono', password='password123')
        
        url = reverse('imprimir_fnrh', kwargs={'pk': self.reserva.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reservas/fnrh_imprimir.html')
        
        # Check context
        self.assertEqual(response.context['ficha'], ficha)
        
        # Check rendered values
        self.assertContains(response, 'Hóspede FNRH Preenchido')
        self.assertContains(response, 'hospede@example.com')
        self.assertContains(response, '11999999999')
        self.assertContains(response, '123.456.789-00')
        self.assertContains(response, 'Praça da Sé')
        self.assertContains(response, 'São Paulo')
