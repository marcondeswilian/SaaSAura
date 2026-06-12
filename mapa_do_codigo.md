# 🗺️ Mapa Completo do Código — AuraSaaS
**Gerado em:** 2026-06-12  
**Stack:** Django + PostgreSQL (Neon) + DRF + FullCalendar + Tuya IoT  
**Propósito:** Documento de referência completo para briefar IAs e desenvolvedores sobre o sistema

---

## 🏛️ Arquitetura Geral

O **AuraSaaS** é um sistema de gestão hoteleira (PMS — Property Management System) construído como uma plataforma **multi-tenant SaaS**. Cada cliente (pousada/hotel) é um **tenant** isolado, identificado pela relação `User → Pousada`. Um usuário dono (`User`) tem exatamente uma `Pousada` via `OneToOneField`. Funcionários são usuários com `ClienteSaaS` vinculado a uma `Pousada` e com um `NivelAcesso` que controla quais seções podem acessar.

### Fluxo de Tenancy
```
User (dono) ──OneToOne──► Pousada
User (func) ──OneToOne──► ClienteSaaS ──FK──► Pousada
                                         └──FK──► NivelAcesso (permissões por URL)
```

### Middleware de Segurança
- **`CheckAcessoSaaS`** — verifica se o usuário está ativo, sem plano expirado, e mapeia URLs para permissões do `NivelAcesso`.
- **`CurrentUserMiddleware`** — armazena o usuário atual em `threading.local()` para uso nos signals de auditoria.

### Componentes Principais
| Componente | Tecnologia |
|---|---|
| Backend Web | Django 5.x |
| REST API | Django REST Framework (DRF) |
| Calendário | FullCalendar (Resource Timeline) |
| Banco de Dados | PostgreSQL (Neon — serverless) |
| Fechaduras IoT | Tuya Cloud API (HMAC-SHA256 + AES-ECB) |
| Autenticação | Django Auth (`LoginView`, `LogoutView`, reset de senha) |
| Email | SMTP configurável via env vars |

---

## 📁 Árvore de Diretórios

```
AuraSaaS/
├── core/                        # Configurações globais do projeto Django
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── templates/
│       ├── base_painel.html
│       └── registration/        # Templates de auth (login, reset de senha)
│           ├── login.html
│           ├── password_reset_form.html
│           ├── password_reset_done.html
│           ├── password_reset_confirm.html
│           ├── password_reset_complete.html
│           ├── password_reset_email.html
│           └── password_reset_subject.txt
├── pousada/                     # App: configurações da pousada, quartos, governança
│   ├── models.py
│   ├── views.py
│   ├── admin.py
│   ├── signals.py
│   ├── middleware.py
│   ├── serializers.py
│   ├── services/
│   │   └── tuya_service.py
│   └── templates/pousada/
│       ├── configuracoes_pousada.html
│       ├── governanca.html
│       └── governanca_mobile.html
├── hospedes/                    # App: CRM de hóspedes
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── templates/hospedes/
│       ├── lista_hospedes.html
│       └── hospede_form.html
├── reservas/                    # App: reservas, calendário, FNRH, financeiro
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── serializers.py
│   ├── admin.py
│   ├── tests.py
│   └── templates/reservas/
│       ├── calendario.html
│       ├── lista_reservas.html
│       ├── editar_reserva.html
│       ├── checkin_online.html
│       ├── portal_hospede.html
│       ├── dashboard_operacoes.html
│       └── fnrh_imprimir.html
├── financeiro/                  # App: pagamentos e lançamentos financeiros
│   ├── models.py
│   └── admin.py
├── admin_saas/                  # App: painel de gestão da plataforma SaaS
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── middleware.py
│   └── templates/admin_saas/
│       └── dashboard.html
└── media/                       # Uploads (logos das pousadas)
```

---

## 🔧 CORE

### core/settings.py
```python
"""
Django settings for core project.
"""

import os
import dj_database_url
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------------------------------------------
# SEGURANÇA — Todas as configurações sensíveis via variáveis de ambiente.
# Em desenvolvimento, crie um arquivo .env e use python-dotenv ou
# defina as variáveis diretamente no shell.
# -----------------------------------------------------------------

# SECURITY WARNING: keep the secret key used in production secret!
# Gere uma nova chave com: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-kh*0020^(t^sex4fr=tz_l24^_51zgs_lxog8_l)jdlt@8mkon'  # Apenas para dev local!
)

# SECURITY WARNING: don't run with debug turned on in production!
# Em produção, defina: DEBUG=False
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

# Em produção, defina: ALLOWED_HOSTS=seudominio.com,www.seudominio.com
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Seus novos apps:
    'pousada',
    'hospedes',
    'reservas',
    'financeiro',
    'admin_saas',
    'rest_framework',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'admin_saas.middleware.CheckAcessoSaaS',
    'pousada.middleware.CurrentUserMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases
# Defina a variável de ambiente DATABASE_URL com a string de conexão completa.
# Ex: DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', ''),
        conn_max_age=600,
        ssl_require=not DEBUG  # SSL obrigatório apenas em produção
    )
}

if not DATABASES['default']:
    raise ValueError(
        "A variável de ambiente DATABASE_URL não está definida. "
        "Configure-a com a string de conexão do banco de dados."
    )



# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Configuração SMTP
# Em desenvolvimento pode usar o backend de console para não enviar e-mails reais:
#   EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# Em produção defina todas as variáveis via env:
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend' if DEBUG else 'django.core.mail.backends.smtp.EmailBackend'
)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# Configurações de Redirecionamento de Login
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/painel/dashboard/'
```

### core/urls.py
```python
"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/painel/dashboard/', permanent=True)),
    path('', include('reservas.urls')),
    path('', include('hospedes.urls')),
    path('painel-saas/', include('admin_saas.urls')),
    
    # Autenticação e Recuperação de Senha
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## 🏨 APP: pousada

> Gerencia as configurações da pousada, quartos, categorias, governança (limpeza/manutenção), integração Tuya, auditoria e equipe.

### pousada/models.py
```python
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone # Importante para a data

class Pousada(models.Model):
    dono = models.OneToOneField(User, on_delete=models.CASCADE, related_name='pousada_owner')
    nome = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    usa_checklist_limpeza = models.BooleanField(default=False)
    whatsapp_recepcao = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nome

class CategoriaQuarto(models.Model):
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='categorias')
    nome = models.CharField(max_length=100) # Ex: Suíte, Standard, Deluxe
    valor_diaria = models.DecimalField(max_digits=10, decimal_places=2)
    capacidade = models.IntegerField(default=2)

    def __str__(self):
        return f"{self.nome} - R$ {self.valor_diaria}"

class Quarto(models.Model):
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='quartos')
    categoria = models.ForeignKey(CategoriaQuarto, on_delete=models.PROTECT, related_name='quartos')
    nome_identificacao = models.CharField(max_length=50) # Ex: 101, 102, Suíte do Lago
    ativo = models.BooleanField(default=True)
    status_limpeza = models.CharField(
        max_length=20, 
        choices=[('sujo', 'Sujo'), ('em_limpeza', 'Em Limpeza'), ('limpo', 'Limpo')], 
        default='limpo'
    )

    def __str__(self):
        return f"{self.nome_identificacao} ({self.categoria.nome})"

class MotivoBloqueio(models.Model):
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='motivos_bloqueio')
    nome = models.CharField(max_length=100)
    cor = models.CharField(max_length=7, default='#475569')

    def __str__(self):
        return f"{self.nome} ({self.pousada.nome})"

class MetodoPagamentoConfig(models.Model):
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='metodos_pagamento')
    nome = models.CharField(max_length=100)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nome} ({self.pousada.nome})"


class LogAuditoria(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs_auditoria')
    acao = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    alvo_id = models.IntegerField(null=True, blank=True)
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, null=True, blank=True, related_name='logs_auditoria')

    def __str__(self):
        return f"{self.usuario} - {self.acao} - {self.timestamp}"


# Propriedade dinâmica para resolver a pousada associada ao usuário (dono ou funcionário)
@property
def get_user_pousada(self):
    try:
        if hasattr(self, 'pousada_owner'):
            return self.pousada_owner
    except Exception:
        pass
    
    cliente = getattr(self, 'cliente_saas', None)
    if cliente and cliente.pousada:
        return cliente.pousada
        
    raise AttributeError("Usuário não possui pousada vinculada.")

User.pousada = get_user_pousada


class ChecklistItem(models.Model):
    pousada = models.ForeignKey(Pousada, on_delete=models.SET_NULL, null=True, related_name='checklist_itens')
    descricao = models.CharField(max_length=255)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        nome_pousada = self.pousada.nome if self.pousada else "Pousada Removida"
        return f"{self.descricao} ({nome_pousada})"



class OrdemServico(models.Model):
    quarto = models.ForeignKey(Quarto, on_delete=models.CASCADE, related_name='ordens_servico')
    tipo_servico = models.CharField(
        max_length=20,
        choices=[
            ('limpeza', 'Limpeza'),
            ('encanamento', 'Encanamento'),
            ('eletrica', 'Elétrica'),
            ('outros', 'Outros')
        ]
    )
    prioridade = models.CharField(
        max_length=15,
        choices=[
            ('baixa', 'Baixa'),
            ('media', 'Média'),
            ('alta', 'Alta')
        ],
        default='media'
    )
    descricao = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pendente', 'Pendente'),
            ('em_andamento', 'Em Andamento'),
            ('concluido', 'Concluído')
        ],
        default='pendente'
    )
    criado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ordens_criadas')
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ordens_atribuidas')
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='ordens_servico')
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        tipo_display = dict([
            ('limpeza', 'Limpeza'),
            ('encanamento', 'Encanamento'),
            ('eletrica', 'Elétrica'),
            ('outros', 'Outros')
        ]).get(self.tipo_servico, self.tipo_servico)
        return f"OS #{self.id} - {tipo_display} - Quarto {self.quarto.nome_identificacao}"


class RegistroLimpeza(models.Model):
    quarto = models.ForeignKey(Quarto, on_delete=models.CASCADE, related_name='registros_limpeza')
    funcionario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registros_limpeza')
    data = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=20, 
        choices=[('sujo', 'Sujo'), ('em_limpeza', 'Em Limpeza'), ('limpo', 'Limpo')], 
        default='sujo'
    )
    reserva_relacionada = models.ForeignKey('reservas.Reserva', on_delete=models.SET_NULL, null=True, blank=True, related_name='registros_limpeza')
    ordem_servico = models.OneToOneField(OrdemServico, on_delete=models.CASCADE, null=True, blank=True, related_name='registro_limpeza')


    def save(self, *args, **kwargs):
        if not hasattr(self, 'funcionario') or self.funcionario is None:
            from pousada.middleware import get_current_user
            user = get_current_user()
            if user and user.is_authenticated:
                self.funcionario = user
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Limpeza {self.quarto} - {self.status} - {self.data.strftime('%d/%m/%Y %H:%M')}"



class ItemLimpezaConcluido(models.Model):
    registro_limpeza = models.ForeignKey(RegistroLimpeza, on_delete=models.CASCADE, related_name='itens_concluidos')
    checklist_item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE)
    concluido = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.checklist_item.descricao} - {'OK' if self.concluido else 'Pendente'}"


class ConfiguracaoTuya(models.Model):
    access_id = models.CharField(max_length=100)
    access_secret = models.CharField(max_length=100)
    region = models.CharField(max_length=50, default='western_america')
    prefixo_pin_padrao = models.CharField(max_length=3, default="101")
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tuya Config - Region: {self.region}"


class Fechadura(models.Model):
    quarto = models.ForeignKey(Quarto, on_delete=models.CASCADE, related_name='fechaduras')
    device_id = models.CharField(max_length=100, unique=True)
    nome_exibicao = models.CharField(max_length=100)
    is_online = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome_exibicao} (Quarto {self.quarto.nome_identificacao})"
```

### pousada/views.py
```python
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from admin_saas.models import ClienteSaaS, NivelAcesso
from .models import Pousada, MotivoBloqueio, CategoriaQuarto, Quarto, MetodoPagamentoConfig, LogAuditoria, ChecklistItem, RegistroLimpeza, ItemLimpezaConcluido, OrdemServico
from hospedes.models import Tag
from django.utils import timezone

@login_required
def pousada_config_view(request):
    try:
        pousada = request.user.pousada
    except Pousada.DoesNotExist:
        messages.error(request, "Você não possui uma pousada vinculada ao seu usuário.")
        return redirect('reserva-lista')

    tab = request.GET.get('tab', 'geral')

    if request.method == 'POST':
        acao = request.POST.get('acao', 'config_geral')

        if acao == 'config_geral':
            nome = request.POST.get('nome')
            logo = request.FILES.get('logo')

            if nome:
                pousada.nome = nome
            if logo:
                pousada.logo = logo

            pousada.save()
            messages.success(request, "Configurações da pousada atualizadas com sucesso!")
            return redirect('/painel/pousada/config/?tab=geral')

        elif acao == 'config_governanca':
            usa_checklist = request.POST.get('usa_checklist_limpeza') == 'on'
            pousada.usa_checklist_limpeza = usa_checklist
            pousada.save()
            messages.success(request, "Configuração de checklist de limpeza salva com sucesso!")
            return redirect('/painel/pousada/config/?tab=governanca_config')

        elif acao == 'novo_checklist_item':
            descricao = request.POST.get('descricao', '').strip()
            if descricao:
                ChecklistItem.objects.create(pousada=pousada, descricao=descricao)
                messages.success(request, "Item adicionado ao checklist com sucesso!")
            else:
                messages.error(request, "A descrição do item é obrigatória.")
            return redirect('/painel/pousada/config/?tab=governanca_config')

        elif acao == 'excluir_checklist_item':
            item_id = request.POST.get('item_id')
            if item_id:
                item = get_object_or_404(ChecklistItem, id=item_id, pousada=pousada)
                item.ativo = False
                item.save()
                messages.success(request, "Item removido do checklist com sucesso!")
            else:
                messages.error(request, "Item não especificado.")
            return redirect('/painel/pousada/config/?tab=governanca_config')

        elif acao == 'nova_tag':
            nome_tag = request.POST.get('nome_tag')
            cor_tag = request.POST.get('cor_tag', '#3b82f6')
            tipo_tag = request.POST.get('tipo_tag', 'H')

            if nome_tag:
                Tag.objects.create(
                    pousada=pousada,
                    nome=nome_tag,
                    cor=cor_tag,
                    tipo=tipo_tag
                )
                messages.success(request, f"Tag '{nome_tag}' criada com sucesso!")
            else:
                messages.error(request, "O nome da tag é obrigatório.")
            return redirect('/painel/pousada/config/?tab=tags')

        elif acao == 'novo_bloqueio':
            nome_bloqueio = request.POST.get('nome_bloqueio')
            cor_bloqueio = request.POST.get('cor_bloqueio', '#475569')

            if nome_bloqueio:
                MotivoBloqueio.objects.create(
                    pousada=pousada,
                    nome=nome_bloqueio,
                    cor=cor_bloqueio
                )
                messages.success(request, f"Motivo de bloqueio '{nome_bloqueio}' criado com sucesso!")
            else:
                messages.error(request, "O nome do motivo de bloqueio é obrigatório.")
            return redirect('/painel/pousada/config/?tab=bloqueios')

        elif acao == 'nova_categoria':
            nome = request.POST.get('nome_categoria')
            capacidade_str = request.POST.get('capacidade_categoria')
            valor_diaria_str = request.POST.get('valor_diaria_categoria')

            if nome and capacidade_str and valor_diaria_str:
                try:
                    capacidade = int(capacidade_str)
                    valor_diaria = float(valor_diaria_str)
                    CategoriaQuarto.objects.create(
                        pousada=pousada,
                        nome=nome,
                        capacidade=capacidade,
                        valor_diaria=valor_diaria
                    )
                    messages.success(request, f"Categoria '{nome}' criada com sucesso!")
                except ValueError:
                    messages.error(request, "Capacidade ou valor diário inválido.")
            else:
                messages.error(request, "Todos os campos da categoria são obrigatórios.")
            return redirect('/painel/pousada/config/?tab=quartos')

        elif acao == 'novo_quarto':
            nome_identificacao = request.POST.get('nome_identificacao')
            categoria_id = request.POST.get('categoria_id')

            if nome_identificacao and categoria_id:
                categoria = get_object_or_404(CategoriaQuarto, id=categoria_id, pousada=pousada)
                Quarto.objects.create(
                    pousada=pousada,
                    categoria=categoria,
                    nome_identificacao=nome_identificacao
                )
                messages.success(request, f"Quarto '{nome_identificacao}' criado com sucesso!")
            else:
                messages.error(request, "Todos os campos do quarto são obrigatórios.")
            return redirect('/painel/pousada/config/?tab=quartos')

        elif acao == 'excluir_quarto':
            quarto_id = request.POST.get('quarto_id')
            if quarto_id:
                quarto = get_object_or_404(Quarto, id=quarto_id, pousada=pousada)
                nome_identificacao = quarto.nome_identificacao
                try:
                    quarto.delete()
                    messages.success(request, f"Quarto '{nome_identificacao}' excluído com sucesso!")
                except Exception as e:
                    messages.error(request, f"Não foi possível excluir o quarto '{nome_identificacao}': {str(e)}")
            else:
                messages.error(request, "ID do quarto não fornecido.")
            return redirect('/painel/pousada/config/?tab=quartos')

        elif acao == 'excluir_categoria':
            categoria_id = request.POST.get('categoria_id')
            if categoria_id:
                categoria = get_object_or_404(CategoriaQuarto, id=categoria_id, pousada=pousada)
                nome = categoria.nome
                try:
                    categoria.delete()
                    messages.success(request, f"Categoria '{nome}' excluída com sucesso!")
                except Exception as e:
                    messages.error(request, f"Não foi possível excluir a categoria '{nome}'. Certifique-se de que não há quartos vinculados a ela.")
            else:
                messages.error(request, "ID da categoria não fornecido.")
            return redirect('/painel/pousada/config/?tab=quartos')

        elif acao == 'novo_metodo_pagamento':
            nome_metodo = request.POST.get('nome_metodo')
            if nome_metodo:
                MetodoPagamentoConfig.objects.create(
                    pousada=pousada,
                    nome=nome_metodo,
                    ativo=True
                )
                messages.success(request, f"Método de pagamento '{nome_metodo}' criado com sucesso!")
            else:
                messages.error(request, "O nome do método de pagamento é obrigatório.")
            return redirect('/painel/pousada/config/?tab=pagamentos')

        elif acao == 'excluir_metodo_pagamento':
            metodo_id = request.POST.get('metodo_id')
            if metodo_id:
                metodo = get_object_or_404(MetodoPagamentoConfig, id=metodo_id, pousada=pousada)
                metodo.ativo = False
                metodo.save()
                messages.success(request, f"Método de pagamento '{metodo.nome}' desativado com sucesso!")
            else:
                messages.error(request, "ID do método de pagamento não fornecido.")
            return redirect('/painel/pousada/config/?tab=pagamentos')

    # Read lists
    tags = Tag.objects.filter(pousada=pousada).order_by('nome')
    motivos_bloqueio = MotivoBloqueio.objects.filter(pousada=pousada).order_by('nome')
    categorias = CategoriaQuarto.objects.filter(pousada=pousada).order_by('nome')
    quartos = Quarto.objects.filter(pousada=pousada).select_related('categoria').order_by('nome_identificacao')
    metodos_pagamento = MetodoPagamentoConfig.objects.filter(pousada=pousada, ativo=True).order_by('nome')
    checklist_itens = ChecklistItem.objects.filter(pousada=pousada, ativo=True).order_by('id')

    return render(request, 'pousada/configuracoes_pousada.html', {
        'pousada': pousada,
        'tab': tab,
        'tags': tags,
        'motivos_bloqueio': motivos_bloqueio,
        'categorias': categorias,
        'quartos': quartos,
        'metodos_pagamento': metodos_pagamento,
        'checklist_itens': checklist_itens,
    })


@login_required
def gerenciar_equipe(request):
    try:
        pousada = request.user.pousada
    except AttributeError:
        messages.error(request, "Você não possui uma pousada vinculada ao seu usuário.")
        return redirect('reserva-lista')

    if request.method == 'POST':
        acao = request.POST.get('acao')

        if acao == 'novo_funcionario':
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '')
            nivel_acesso_id = request.POST.get('nivel_acesso')

            if not username or not email or not password or not nivel_acesso_id:
                messages.error(request, "Todos os campos do funcionário são obrigatórios.")
                return redirect('/painel/pousada/config/equipe/')

            if User.objects.filter(username=username).exists():
                messages.error(request, "Este nome de usuário já está sendo utilizado.")
                return redirect('/painel/pousada/config/equipe/')

            if User.objects.filter(email=email).exists():
                messages.error(request, "Este endereço de e-mail já está sendo utilizado.")
                return redirect('/painel/pousada/config/equipe/')

            try:
                user = User.objects.create_user(username=username, email=email, password=password)
                nivel = get_object_or_404(NivelAcesso, id=nivel_acesso_id)
                ClienteSaaS.objects.create(
                    user=user,
                    nivel_acesso=nivel,
                    pousada=pousada,
                    plano_ativo=True,
                    ativo=True
                )
                messages.success(request, f"Funcionário {username} criado com sucesso!")
            except Exception as e:
                messages.error(request, f"Erro ao criar funcionário: {str(e)}")

        elif acao == 'excluir_funcionario':
            funcionario_id = request.POST.get('funcionario_id')
            if funcionario_id:
                funcionario = get_object_or_404(ClienteSaaS, id=funcionario_id, pousada=pousada)
                username = funcionario.user.username
                try:
                    funcionario.user.delete()
                    messages.success(request, f"Funcionário {username} excluído com sucesso!")
                except Exception as e:
                    messages.error(request, f"Erro ao excluir funcionário: {str(e)}")
            else:
                messages.error(request, "ID do funcionário não fornecido.")

        elif acao == 'toggle_funcionario':
            funcionario_id = request.POST.get('funcionario_id')
            if funcionario_id:
                funcionario = get_object_or_404(ClienteSaaS, id=funcionario_id, pousada=pousada)
                funcionario.ativo = not funcionario.ativo
                funcionario.save()
                status = "ativado" if funcionario.ativo else "desativado"
                messages.success(request, f"Funcionário {funcionario.user.username} foi {status} com sucesso!")
            else:
                messages.error(request, "ID do funcionário não fornecido.")

        return redirect('/painel/pousada/config/equipe/')

    # GET request
    funcionarios = ClienteSaaS.objects.filter(pousada=pousada).select_related('user', 'nivel_acesso')
    niveis_acesso = NivelAcesso.objects.all()

    return render(request, 'pousada/configuracoes_pousada.html', {
        'pousada': pousada,
        'tab': 'equipe',
        'funcionarios': funcionarios,
        'niveis_acesso': niveis_acesso,
    })


@login_required
def ver_logs(request):
    try:
        pousada = request.user.pousada
    except AttributeError:
        messages.error(request, "Você não possui uma pousada vinculada ao seu usuário.")
        return redirect('reserva-lista')

    logs = LogAuditoria.objects.filter(pousada=pousada).select_related('usuario').order_by('-timestamp')

    return render(request, 'pousada/configuracoes_pousada.html', {
        'pousada': pousada,
        'tab': 'auditoria',
        'logs': logs,
    })


@login_required
def governanca_dashboard(request):
    # Enforce access permissions
    def check_governanca_permission(user):
        if user.is_superuser:
            return True
        cliente = getattr(user, 'cliente_saas', None)
        if cliente and cliente.nivel_acesso:
            return cliente.nivel_acesso.pode_acessar_governanca
        return False

    if not check_governanca_permission(request.user):
        messages.error(request, "Você não possui permissão para acessar a área de Governança.")
        return redirect('reserva-lista')

    try:
        pousada = request.user.pousada
    except AttributeError:
        messages.error(request, "Você não possui uma pousada vinculada ao seu usuário.")
        return redirect('reserva-lista')

    from reservas.models import Reserva
    from django.db.models import Q

    if request.method == 'POST':
        acao = request.POST.get('acao')

        if acao == 'iniciar_limpeza':
            quarto_id = request.POST.get('quarto_id')
            quarto = get_object_or_404(Quarto, id=quarto_id, pousada=pousada)

            quarto.status_limpeza = 'em_limpeza'
            quarto.save()

            reserva_relacionada = Reserva.objects.filter(
                quarto=quarto, 
                status='finalizada'
            ).order_by('-data_checkout').first()

            ordem = OrdemServico.objects.filter(
                quarto=quarto,
                tipo_servico='limpeza',
                status='pendente'
            ).first()
            if not ordem:
                ordem = OrdemServico.objects.create(
                    quarto=quarto,
                    tipo_servico='limpeza',
                    prioridade='media',
                    descricao="Limpeza iniciada diretamente no painel.",
                    criado_por=request.user,
                    responsavel=request.user,
                    status='em_andamento',
                    pousada=pousada
                )
            else:
                ordem.status = 'em_andamento'
                ordem.responsavel = request.user
                ordem.save()

            registro = RegistroLimpeza.objects.create(
                quarto=quarto,
                funcionario=request.user,
                status='em_limpeza',
                reserva_relacionada=reserva_relacionada,
                ordem_servico=ordem
            )

            if pousada.usa_checklist_limpeza:
                itens = ChecklistItem.objects.filter(pousada=pousada, ativo=True)
                for item in itens:
                    ItemLimpezaConcluido.objects.create(
                        registro_limpeza=registro,
                        checklist_item=item,
                        concluido=False
                    )

            messages.success(request, f"Limpeza do quarto {quarto.nome_identificacao} iniciada com sucesso!")
            return redirect('governanca-dashboard')

        elif acao == 'salvar_checklist':
            registro_id = request.POST.get('registro_id')
            registro = get_object_or_404(RegistroLimpeza, id=registro_id, quarto__pousada=pousada)

            concluidos_ids = request.POST.getlist('itens_concluidos[]')
            concluidos_ids = [int(i_id) for i_id in concluidos_ids if i_id.isdigit()]

            itens_concluidos = ItemLimpezaConcluido.objects.filter(registro_limpeza=registro)
            for item in itens_concluidos:
                item.concluido = item.id in concluidos_ids
                item.save()

            messages.success(request, "Progresso do checklist salvo!")
            return redirect('governanca-dashboard')

        elif acao == 'finalizar_limpeza':
            registro_id = request.POST.get('registro_id')
            quarto_id = request.POST.get('quarto_id')

            if registro_id:
                registro = get_object_or_404(RegistroLimpeza, id=registro_id, quarto__pousada=pousada)
                quarto = registro.quarto

                if pousada.usa_checklist_limpeza:
                    itens_pendentes = ItemLimpezaConcluido.objects.filter(registro_limpeza=registro, concluido=False)
                    if itens_pendentes.exists():
                        messages.error(request, f"Não é possível finalizar a limpeza do quarto {quarto.nome_identificacao}. Existem itens do checklist pendentes!")
                        return redirect('governanca-dashboard')

                registro.status = 'limpo'
                registro.save()
                
                quarto.status_limpeza = 'limpo'
                quarto.save()

                if registro.ordem_servico:
                    ordem = registro.ordem_servico
                    ordem.status = 'concluido'
                    ordem.data_conclusao = timezone.now()
                    ordem.save()

                messages.success(request, f"Quarto {quarto.nome_identificacao} está limpo e liberado!")
            elif quarto_id:
                quarto = get_object_or_404(Quarto, id=quarto_id, pousada=pousada)
                
                ordem = OrdemServico.objects.filter(
                    quarto=quarto,
                    tipo_servico='limpeza',
                    status__in=['pendente', 'em_andamento']
                ).first()
                if not ordem:
                    ordem = OrdemServico.objects.create(
                        quarto=quarto,
                        tipo_servico='limpeza',
                        status='concluido',
                        criado_por=request.user,
                        responsavel=request.user,
                        pousada=pousada,
                        data_conclusao=timezone.now()
                    )
                else:
                    ordem.status = 'concluido'
                    ordem.responsavel = request.user
                    ordem.data_conclusao = timezone.now()
                    ordem.save()

                RegistroLimpeza.objects.create(
                    quarto=quarto,
                    funcionario=request.user,
                    status='limpo',
                    data=timezone.now(),
                    ordem_servico=ordem
                )

                quarto.status_limpeza = 'limpo'
                quarto.save()
                messages.success(request, f"Quarto {quarto.nome_identificacao} marcado como limpo diretamente!")

            return redirect('governanca-dashboard')

        elif acao == 'marcar_sujo':
            quarto_id = request.POST.get('quarto_id')
            quarto = get_object_or_404(Quarto, id=quarto_id, pousada=pousada)

            quarto.status_limpeza = 'sujo'
            quarto.save()

            os_existente = OrdemServico.objects.filter(
                quarto=quarto,
                tipo_servico='limpeza',
                status__in=['pendente', 'em_andamento']
            ).exists()
            if not os_existente:
                OrdemServico.objects.create(
                    quarto=quarto,
                    tipo_servico='limpeza',
                    prioridade='media',
                    descricao="Quarto marcado como sujo manualmente.",
                    status='pendente',
                    criado_por=request.user,
                    pousada=pousada
                )

            messages.warning(request, f"Quarto {quarto.nome_identificacao} marcado como sujo manualmente.")
            return redirect('governanca-dashboard')

        elif acao == 'criar_ordem_servico':
            quarto_id = request.POST.get('quarto_id')
            tipo_servico = request.POST.get('tipo_servico')
            prioridade = request.POST.get('prioridade')
            descricao = request.POST.get('descricao', '').strip()
            responsavel_id = request.POST.get('responsavel_id')

            quarto = get_object_or_404(Quarto, id=quarto_id, pousada=pousada)
            responsavel = None
            if responsavel_id:
                responsavel = get_object_or_404(User, id=responsavel_id)

            ordem = OrdemServico.objects.create(
                quarto=quarto,
                tipo_servico=tipo_servico,
                prioridade=prioridade,
                descricao=descricao,
                criado_por=request.user,
                responsavel=responsavel,
                status='pendente',
                pousada=pousada
            )

            if tipo_servico == 'limpeza' and quarto.status_limpeza == 'limpo':
                quarto.status_limpeza = 'sujo'
                quarto.save()

            messages.success(request, f"Ordem de Serviço #{ordem.id} criada com sucesso!")
            return redirect('governanca-dashboard')

        elif acao == 'alterar_status_ordem':
            ordem_id = request.POST.get('ordem_id')
            novo_status = request.POST.get('status')
            responsavel_id = request.POST.get('responsavel_id')

            ordem = get_object_or_404(OrdemServico, id=ordem_id, pousada=pousada)
            if responsavel_id:
                ordem.responsavel = get_object_or_404(User, id=responsavel_id)
            
            if novo_status:
                ordem.status = novo_status
                if novo_status == 'concluido':
                    ordem.data_conclusao = timezone.now()
                    if ordem.tipo_servico == 'limpeza':
                        quarto = ordem.quarto
                        quarto.status_limpeza = 'limpo'
                        quarto.save()
                        try:
                            registro = ordem.registro_limpeza
                            registro.status = 'limpo'
                            registro.save()
                        except RegistroLimpeza.DoesNotExist:
                            RegistroLimpeza.objects.create(
                                quarto=quarto,
                                funcionario=request.user,
                                status='limpo',
                                data=timezone.now(),
                                ordem_servico=ordem
                            )
                elif novo_status == 'em_andamento' and ordem.tipo_servico == 'limpeza':
                    quarto = ordem.quarto
                    if quarto.status_limpeza != 'em_limpeza':
                        quarto.status_limpeza = 'em_limpeza'
                        quarto.save()
                    registro, created = RegistroLimpeza.objects.get_or_create(
                        ordem_servico=ordem,
                        defaults={
                            'quarto': quarto,
                            'funcionario': request.user,
                            'status': 'em_limpeza',
                            'data': timezone.now()
                        }
                    )
                    if created and pousada.usa_checklist_limpeza:
                        itens = ChecklistItem.objects.filter(pousada=pousada, ativo=True)
                        for item in itens:
                            ItemLimpezaConcluido.objects.create(
                                registro_limpeza=registro,
                                checklist_item=item,
                                concluido=False
                            )
            ordem.save()
            messages.success(request, f"Ordem de Serviço #{ordem.id} atualizada com sucesso!")
            return redirect('governanca-dashboard')

    # GET Request logic
    quartos = Quarto.objects.filter(pousada=pousada, ativo=True).select_related('categoria')
    
    registros_ativos = RegistroLimpeza.objects.filter(
        quarto__pousada=pousada, 
        status='em_limpeza'
    ).select_related('quarto', 'funcionario', 'reserva_relacionada', 'reserva_relacionada__hospede')
    
    mapa_registros = {reg.quarto.id: reg for reg in registros_ativos}

    for q in quartos:
        q.active_registro = mapa_registros.get(q.id)
        if q.active_registro:
            q.itens_checklist = q.active_registro.itens_concluidos.all().select_related('checklist_item')

    quartos_sujos = [q for q in quartos if q.status_limpeza == 'sujo']
    quartos_em_limpeza = [q for q in quartos if q.status_limpeza == 'em_limpeza']
    quartos_limpos = [q for q in quartos if q.status_limpeza == 'limpo']

    ordens_servico = OrdemServico.objects.filter(pousada=pousada).select_related('quarto', 'criado_por', 'responsavel').order_by('-data_criacao')
    funcionarios = User.objects.filter(
        Q(cliente_saas__pousada=pousada) | Q(pousada_owner=pousada)
    ).distinct().order_by('username')

    return render(request, 'pousada/governanca.html', {
        'pousada': pousada,
        'quartos_sujos': quartos_sujos,
        'quartos_em_limpeza': quartos_em_limpeza,
        'quartos_limpos': quartos_limpos,
        'mapa_registros': mapa_registros,
        'ordens_servico': ordens_servico,
        'funcionarios': funcionarios,
    })


@login_required
def governanca_mobile_view(request):
    try:
        pousada = request.user.pousada
    except AttributeError:
        messages.error(request, "Você não possui uma pousada vinculada ao seu usuário.")
        return redirect('reserva-lista')

    if request.method == 'POST':
        acao = request.POST.get('acao')
        
        if acao == 'iniciar_ordem':
            ordem_id = request.POST.get('ordem_id')
            ordem = get_object_or_404(OrdemServico, id=ordem_id, responsavel=request.user, pousada=pousada)
            ordem.status = 'em_andamento'
            ordem.save()
            
            if ordem.tipo_servico == 'limpeza':
                quarto = ordem.quarto
                quarto.status_limpeza = 'em_limpeza'
                quarto.save()
                
                registro, created = RegistroLimpeza.objects.get_or_create(
                    ordem_servico=ordem,
                    defaults={
                        'quarto': quarto,
                        'funcionario': request.user,
                        'status': 'em_limpeza',
                        'data': timezone.now()
                    }
                )
                if created and pousada.usa_checklist_limpeza:
                    itens = ChecklistItem.objects.filter(pousada=pousada, ativo=True)
                    for item in itens:
                        ItemLimpezaConcluido.objects.create(
                            registro_limpeza=registro,
                            checklist_item=item,
                            concluido=False
                        )
            messages.success(request, f"Serviço no quarto {ordem.quarto.nome_identificacao} iniciado!")
            return redirect('governanca-mobile')
            
        elif acao == 'salvar_checklist':
            registro_id = request.POST.get('registro_id')
            registro = get_object_or_404(RegistroLimpeza, id=registro_id, funcionario=request.user)
            concluidos_ids = request.POST.getlist('itens_concluidos[]')
            concluidos_ids = [int(i_id) for i_id in concluidos_ids if i_id.isdigit()]
            
            for item in registro.itens_concluidos.all():
                item.concluido = item.id in concluidos_ids
                item.save()
                
            messages.success(request, "Progresso do checklist salvo!")
            return redirect('governanca-mobile')
            
        elif acao == 'concluir_ordem':
            ordem_id = request.POST.get('ordem_id')
            ordem = get_object_or_404(OrdemServico, id=ordem_id, responsavel=request.user, pousada=pousada)
            
            if ordem.tipo_servico == 'limpeza':
                try:
                    registro = ordem.registro_limpeza
                    if pousada.usa_checklist_limpeza:
                        if registro.itens_concluidos.filter(concluido=False).exists():
                            messages.error(request, "Existem itens do checklist pendentes para este quarto!")
                            return redirect('governanca-mobile')
                    registro.status = 'limpo'
                    registro.save()
                except RegistroLimpeza.DoesNotExist:
                    RegistroLimpeza.objects.create(
                        quarto=ordem.quarto,
                        funcionario=request.user,
                        status='limpo',
                        data=timezone.now(),
                        ordem_servico=ordem
                    )
                quarto = ordem.quarto
                quarto.status_limpeza = 'limpo'
                quarto.save()
                
            ordem.status = 'concluido'
            ordem.data_conclusao = timezone.now()
            ordem.save()
            messages.success(request, f"Serviço no quarto {ordem.quarto.nome_identificacao} concluído!")
            return redirect('governanca-mobile')

    # GET Request
    ordens = OrdemServico.objects.filter(
        responsavel=request.user,
        status__in=['pendente', 'em_andamento'],
        pousada=pousada
    ).select_related('quarto', 'quarto__categoria').order_by('prioridade', 'data_criacao')
    
    for ordem in ordens:
        if ordem.tipo_servico == 'limpeza':
            try:
                ordem.registro = ordem.registro_limpeza
                ordem.itens_checklist = ordem.registro.itens_concluidos.all().select_related('checklist_item')
            except RegistroLimpeza.DoesNotExist:
                ordem.registro = None
                ordem.itens_checklist = []

    return render(request, 'pousada/governanca_mobile.html', {
        'pousada': pousada,
        'ordens': ordens,
    })
```

### pousada/admin.py
```python
from django.contrib import admin
from .models import Pousada

@admin.register(Pousada)
class PousadaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo', 'dono') # Removi o 'plano' daqui

from .models import CategoriaQuarto, Quarto, MotivoBloqueio

@admin.register(CategoriaQuarto)
class CategoriaQuartoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'valor_diaria', 'capacidade')

@admin.register(Quarto)
class QuartoAdmin(admin.ModelAdmin):
    list_display = ('nome_identificacao', 'categoria', 'ativo')

@admin.register(MotivoBloqueio)
class MotivoBloqueioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'pousada')
    list_filter = ('pousada',)

from .models import ConfiguracaoTuya, Fechadura

@admin.register(ConfiguracaoTuya)
class ConfiguracaoTuyaAdmin(admin.ModelAdmin):
    list_display = ('region', 'data_criacao')

@admin.register(Fechadura)
class FechaduraAdmin(admin.ModelAdmin):
    list_display = ('nome_exibicao', 'quarto', 'device_id', 'is_online')
```

### pousada/signals.py
```python
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from reservas.models import Reserva
from financeiro.models import Pagamento
from admin_saas.models import ClienteSaaS
from .models import LogAuditoria
from .middleware import get_current_user

@receiver(post_save, sender=Reserva)
def log_reserva_save(sender, instance, created, **kwargs):
    user = get_current_user()
    if user and user.is_authenticated:
        acao = f"Criou a reserva de check-in {instance.data_checkin} e check-out {instance.data_checkout} para o hóspede {instance.hospede}" if created else f"Editou a reserva {instance.id} (Hóspede: {instance.hospede})"
        LogAuditoria.objects.create(
            usuario=user,
            acao=acao,
            alvo_id=instance.id,
            pousada=instance.pousada
        )

@receiver(post_delete, sender=Reserva)
def log_reserva_delete(sender, instance, **kwargs):
    user = get_current_user()
    if user and user.is_authenticated:
        LogAuditoria.objects.create(
            usuario=user,
            acao=f"Excluiu/Cancelou a reserva {instance.id} (Hóspede: {instance.hospede})",
            alvo_id=instance.id,
            pousada=instance.pousada
        )

@receiver(post_save, sender=Pagamento)
def log_pagamento_save(sender, instance, created, **kwargs):
    user = get_current_user()
    if user and user.is_authenticated:
        acao = f"Registrou novo pagamento de R$ {instance.valor} ({instance.get_tipo_display()}) para a reserva {instance.reserva_id}" if created else f"Editou o pagamento {instance.id} da reserva {instance.reserva_id} (novo valor: R$ {instance.valor})"
        LogAuditoria.objects.create(
            usuario=user,
            acao=acao,
            alvo_id=instance.id,
            pousada=instance.pousada
        )

@receiver(post_delete, sender=Pagamento)
def log_pagamento_delete(sender, instance, **kwargs):
    user = get_current_user()
    if user and user.is_authenticated:
        LogAuditoria.objects.create(
            usuario=user,
            acao=f"Excluiu o pagamento {instance.id} no valor de R$ {instance.valor} da reserva {instance.reserva_id}",
            alvo_id=instance.id,
            pousada=instance.pousada
        )

@receiver(post_save, sender=ClienteSaaS)
def log_cliente_save(sender, instance, created, **kwargs):
    user = get_current_user()
    if user and user.is_authenticated:
        pousada = getattr(instance, 'pousada', None)
        if not pousada:
            try:
                pousada = instance.user.pousada_owner
            except Exception:
                pass
        
        acao = f"Criou o cliente/dono {instance.user.username}" if created else f"Editou as configurações do cliente {instance.user.username}"
        LogAuditoria.objects.create(
            usuario=user,
            acao=acao,
            alvo_id=instance.id,
            pousada=pousada
        )

@receiver(post_delete, sender=ClienteSaaS)
def log_cliente_delete(sender, instance, **kwargs):
    user = get_current_user()
    if user and user.is_authenticated:
        pousada = getattr(instance, 'pousada', None)
        if not pousada:
            try:
                pousada = instance.user.pousada_owner
            except Exception:
                pass
                
        LogAuditoria.objects.create(
            usuario=user,
            acao=f"Excluiu o cliente {instance.user.username}",
            alvo_id=instance.id,
            pousada=pousada
        )

@receiver(pre_save, sender=Reserva)
def track_previous_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            original = Reserva.objects.get(pk=instance.pk)
            instance._original_status = original.status
        except Reserva.DoesNotExist:
            instance._original_status = None
    else:
        instance._original_status = None

@receiver(post_save, sender=Reserva)
def verificar_checkout_limpeza(sender, instance, created, **kwargs):
    original_status = getattr(instance, '_original_status', None)
    if instance.status == 'finalizada' and original_status != 'finalizada' and not instance.is_bloqueio:
        quarto = instance.quarto
        quarto.status_limpeza = 'sujo'
        quarto.save()
        
        # Automatically create a pending cleaning order of service if none active
        from pousada.models import OrdemServico
        os_existente = OrdemServico.objects.filter(
            quarto=quarto,
            tipo_servico='limpeza',
            status__in=['pendente', 'em_andamento']
        ).exists()
        if not os_existente:
            OrdemServico.objects.create(
                quarto=quarto,
                tipo_servico='limpeza',
                prioridade='media',
                descricao=f"Limpeza pós check-out da reserva #{instance.id} (Hóspede: {instance.hospede.nome_completo if instance.hospede else 'Não informado'}).",
                status='pendente',
                criado_por=instance.pousada.dono,
                pousada=instance.pousada
            )
```

### pousada/middleware.py
```python
import threading

_thread_locals = threading.local()

def get_current_user():
    return getattr(_thread_locals, 'user', None)

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = getattr(request, 'user', None)
        response = self.get_response(request)
        # Limpar para evitar vazamento de memória
        if hasattr(_thread_locals, 'user'):
            del _thread_locals.user
        return response
```

### pousada/serializers.py
```python
from rest_framework import serializers
from .models import Quarto

class QuartoSerializer(serializers.ModelSerializer):
    # O FullCalendar chama as linhas do mapa de 'resources' e espera um 'title'
    title = serializers.CharField(source='nome_identificacao')
    categoria = serializers.CharField(source='categoria.nome')

    class Meta:
        model = Quarto
        fields = ['id', 'title', 'categoria']
```

### pousada/services/tuya_service.py
```python
import time
import hmac
import hashlib
import json
import urllib.request
from urllib.error import URLError, HTTPError
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

# Try to import cryptography for real AES ECB encryption if available
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


class TuyaLockService:
    def __init__(self):
        from pousada.models import ConfiguracaoTuya
        self.config = ConfiguracaoTuya.objects.first()
        
        self.region_urls = {
            'western_america': 'https://openapi.tuyaus.com',
            'eastern_america': 'https://openapi.tuyaus.com',
            'china': 'https://openapi.tuyacn.com',
            'western_europe': 'https://openapi.tuyaeu.com',
            'eastern_europe': 'https://openapi.tuyaeu.com',
            'india': 'https://openapi.tuyain.com',
        }
        
        if self.config:
            self.access_id = self.config.access_id
            self.access_secret = self.config.access_secret
            self.region = self.config.region
            self.base_url = self.region_urls.get(self.region, 'https://openapi.tuyaus.com')
        else:
            self.access_id = None
            self.access_secret = None
            self.region = None
            self.base_url = None

    def gerar_senha_com_prefixo(self, sufixo):
        prefixo = "101"
        if self.config and hasattr(self.config, 'prefixo_pin_padrao') and self.config.prefixo_pin_padrao:
            prefixo = self.config.prefixo_pin_padrao
        return f"{prefixo}{sufixo}"

    def _get_timestamp(self):
        return str(int(time.time() * 1000))

    def _calculate_sign(self, client_id, secret, timestamp, access_token=None, method='POST', path='', body=''):
        if isinstance(body, dict) or isinstance(body, list):
            body_str = json.dumps(body)
        else:
            body_str = body or ""
        
        body_hash = hashlib.sha256(body_str.encode('utf-8')).hexdigest()
        headers_str = "" 
        request_str = f"{method}\n{body_hash}\n{headers_str}\n{path}"
        
        token_part = access_token if access_token else ""
        sign_str = f"{client_id}{token_part}{timestamp}{request_str}"
        
        signature = hmac.new(
            secret.encode('utf-8'),
            sign_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest().upper()
        
        return signature

    def _send_request(self, method, path, body=None, requires_token=True):
        if not self.access_id or not self.access_secret:
            logger.warning("TuyaLockService: Nenhuma credencial Tuya configurada.")
            return None

        access_token = None
        if requires_token:
            token_data = self._get_access_token()
            if token_data:
                access_token = token_data.get('access_token')
            if not access_token:
                logger.error("TuyaLockService: Falha ao obter access_token da Tuya.")
                return None

        timestamp = self._get_timestamp()
        body_str = json.dumps(body) if body else ""
        sign = self._calculate_sign(
            client_id=self.access_id,
            secret=self.access_secret,
            timestamp=timestamp,
            access_token=access_token,
            method=method,
            path=path,
            body=body_str
        )

        headers = {
            'client_id': self.access_id,
            'sign': sign,
            't': timestamp,
            'sign_method': 'HMAC-SHA256',
            'Content-Type': 'application/json',
        }
        if access_token:
            headers['access_token'] = access_token

        url = f"{self.base_url}{path}"
        
        try:
            req = urllib.request.Request(
                url,
                data=body_str.encode('utf-8') if body_str else None,
                headers=headers,
                method=method
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = response.read().decode('utf-8')
                return json.loads(res_body)
        except HTTPError as e:
            logger.error(f"TuyaLockService HTTPError: {e.code} - {e.read().decode('utf-8')}")
            return None
        except URLError as e:
            logger.error(f"TuyaLockService URLError: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"TuyaLockService Error: {str(e)}")
            return None

    def _get_access_token(self):
        path = "/v1.0/token?grant_type=1"
        res = self._send_request(method='GET', path=path, requires_token=False)
        if res and res.get('success'):
            return res.get('result')
        return None

    def gerar_ticket(self, device_id):
        """
        Gera o ticket de segurança (password-ticket) na API Tuya.
        """
        path = f"/v1.0/devices/{device_id}/door-lock/password-ticket"
        logger.info(f"TuyaLockService: Gerando ticket para o dispositivo {device_id}...")
        
        res = self._send_request(method='POST', path=path)
        if res and res.get('success'):
            return res.get('result')
            
        logger.warning("TuyaLockService: Falha ao obter ticket da API Tuya. Usando ticket simulado.")
        return {
            'ticket_id': 'simulated_ticket_id_' + str(int(time.time())),
            'ticket_key': 'simulated_ticket_key_32_chars_12345'
        }

    def _encrypt_password_aes_ecb(self, password, ticket_key):
        """
        Criptografa a senha usando AES-ECB com preenchimento PKCS7.
        """
        if not HAS_CRYPTO:
            logger.warning("TuyaLockService: Biblioteca 'cryptography' não disponível. Retornando senha em formato hex simulado.")
            return password.encode('utf-8').hex()

        try:
            key_bytes = ticket_key.encode('utf-8')[:16]
            key_bytes = key_bytes.ljust(16, b'\0')

            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(password.encode('utf-8')) + padder.finalize()

            cipher = Cipher(algorithms.AES(key_bytes), modes.ECB())
            encryptor = cipher.encryptor()
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
            return encrypted_data.hex().upper()
        except Exception as e:
            logger.error(f"TuyaLockService Encryption Error: {str(e)}")
            return password.encode('utf-8').hex()

    def criar_senha_temporaria(self, device_id, nome, senha, data_inicio, data_fim, ticket_id=None):
        """
        Cria a senha temporária na fechadura via Tuya.
        """
        if not ticket_id:
            ticket_data = self.gerar_ticket(device_id)
            ticket_id = ticket_data.get('ticket_id')
            ticket_key = ticket_data.get('ticket_key')
        else:
            ticket_key = 'simulated_ticket_key_32_chars_12345'

        senha_encriptada = self._encrypt_password_aes_ecb(senha, ticket_key)

        effective_time = int(data_inicio.timestamp())
        invalid_time = int(data_fim.timestamp())

        path = f"/v1.0/devices/{device_id}/door-lock/temp-password"
        
        payload = {
            'password': senha_encriptada,
            'password_type': 'ticket',
            'ticket_id': ticket_id,
            'effective_time': effective_time,
            'invalid_time': invalid_time,
            'name': nome
        }

        logger.info(f"TuyaLockService: Criando senha temporária '{nome}' na fechadura {device_id}...")
        
        res = self._send_request(method='POST', path=path, body=payload)
        if res and res.get('success'):
            return res.get('result')
            
        logger.warning("TuyaLockService: API Tuya retornou erro ou não respondeu. Senha simulada criada com sucesso.")
        return {'status': 'success', 'simulated': True}
```

---

## 👤 APP: hospedes

> Gerencia o cadastro de hóspedes (CRM) da pousada com suporte a tags, busca e histórico de estadias.

### hospedes/models.py
```python
from django.db import models
from pousada.models import Pousada

class Tag(models.Model):
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='tags')
    nome = models.CharField(max_length=50)
    cor = models.CharField(max_length=7, default='#3b82f6')
    tipo = models.CharField(max_length=10, choices=[('H', 'Hóspede'), ('R', 'Reserva')], default='H')

    def __str__(self):
        return f"{self.nome} ({self.pousada.nome})"

class Hospede(models.Model):
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='hospedes')
    tags = models.ManyToManyField(Tag, blank=True)

    
    # Campos Padrão FNRH
    nome_completo = models.CharField(max_length=255)
    data_nascimento = models.DateField(null=True, blank=True)
    nacionalidade = models.CharField(max_length=100, default='Brasileiro(a)')
    sexo = models.CharField(max_length=20, choices=[('M', 'Masculino'), ('F', 'Feminino'), ('O', 'Outro')], null=True, blank=True)
    tipo_documento = models.CharField(max_length=50, choices=[('CPF', 'CPF'), ('RG', 'RG'), ('PAS', 'Passaporte')], default='CPF')
    numero_documento = models.CharField(max_length=50, null=True, blank=True)
    
    # Novos Campos FNRH da Fase 4
    cpf = models.CharField(max_length=20, null=True, blank=True)
    genero = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Feminino'), ('O', 'Outro')], null=True, blank=True)
    profissao = models.CharField(max_length=100, null=True, blank=True)
    cep = models.CharField(max_length=20, null=True, blank=True)
    endereco = models.CharField(max_length=255, null=True, blank=True)
    cidade = models.CharField(max_length=100, null=True, blank=True)
    estado = models.CharField(max_length=100, null=True, blank=True)
    
    # Contato e Endereço
    telefone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    endereco_completo = models.TextField(null=True, blank=True)
    
    # Campo FLEXÍVEL para futuras mudanças da FNRH (Ex: Nome social, placa veículo)
    dados_extras = models.JSONField(default=dict, blank=True)

    @property
    def link_whatsapp(self):
        if not self.telefone:
            return ""
        num_limpo = "".join([c for c in self.telefone if c.isdigit()])
        if not num_limpo:
            return ""
        if not num_limpo.startswith('55') and len(num_limpo) >= 10:
            num_limpo = f"55{num_limpo}"
        return f"https://wa.me/{num_limpo}"

    def __str__(self):
        return self.nome_completo
```

### hospedes/views.py
```python
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
```

### hospedes/urls.py
```python
from django.urls import path
from .views import hospede_lista_view, hospede_criar_view, hospede_editar_view

urlpatterns = [
    path('painel/hospedes/', hospede_lista_view, name='hospede-lista'),
    path('painel/hospedes/criar/', hospede_criar_view, name='hospede-criar'),
    path('painel/hospedes/<int:pk>/editar/', hospede_editar_view, name='hospede-editar'),
]
```

### hospedes/admin.py
```python
from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.urls import reverse
from .models import Hospede, Tag
from reservas.models import Reserva

class ReservaInline(admin.TabularInline):
    model = Reserva
    extra = 0
    fields = ('quarto', 'data_checkin', 'data_checkout', 'status', 'checkin_concluido')
    readonly_fields = ('quarto', 'data_checkin', 'data_checkout', 'status', 'checkin_concluido')
    can_delete = False
    show_change_link = True
    verbose_name = "Histórico de Reserva"
    verbose_name_plural = "Histórico de Reservas (Estadias)"

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cor', 'pousada')
    list_filter = ('pousada',)

@admin.register(Hospede)
class HospedeAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'cpf', 'telefone', 'whatsapp_link_button', 'cidade', 'estado')
    readonly_fields = ('historico_estadias', 'whatsapp_link_button')
    inlines = [ReservaInline]
    filter_horizontal = ('tags',)

    def save_model(self, request, obj, form, change):
        if not obj.pousada_id and hasattr(request.user, 'pousada'):
            obj.pousada = request.user.pousada
        super().save_model(request, obj, form, change)

    def whatsapp_link_button(self, obj):
        link = obj.link_whatsapp
        if not link:
            return "Sem telefone"
        return format_html(
            '<a class="button" href="{}" target="_blank" style="background-color: #25D366; color: white; padding: 4px 10px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">'
            'WhatsApp'
            '</a>',
            link
        )
    whatsapp_link_button.short_description = 'WhatsApp'

    def historico_estadias(self, obj):
        reservas = obj.reservas.all()
        count = reservas.count()
        if count == 0:
            return "Nenhuma estadia anterior registrada."

        items = []
        for r in reservas:
            url = reverse('admin:reservas_reserva_change', args=[r.id])
            status_desc = r.get_status_display()
            checkin = r.data_checkin.strftime('%d/%m/%Y') if r.data_checkin else '?'
            checkout = r.data_checkout.strftime('%d/%m/%Y') if r.data_checkout else '?'
            items.append(format_html(
                '<li><a href="{}" target="_blank">Reserva #{}</a> - {} a {} ({})</li>',
                url, r.id, checkin, checkout, status_desc,
            ))

        items_html = mark_safe(''.join(items))
        return format_html(
            '<div style="margin-top: 5px;">'
            '<strong>Total de Estadias: {}</strong>'
            '<ul style="margin-top: 5px; padding-left: 20px; line-height: 1.6;">{}</ul>'
            '</div>',
            count, items_html,
        )
    historico_estadias.short_description = "Histórico de Estadias (Links)"
```

---

## 📅 APP: reservas

> Coração do sistema. Gerencia reservas, calendário FullCalendar, check-in online, portal do hóspede, FNRH, pagamentos e dashboard operacional.

### reservas/models.py
```python
from django.db import models
from django.db.models import Sum
from decimal import Decimal
from pousada.models import Pousada, Quarto
from hospedes.models import Hospede
import uuid

class Grupo(models.Model):
    nome = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome or f"Grupo {self.id}"

class Reserva(models.Model):
    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='reservas')
    grupo = models.ForeignKey(Grupo, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservas')
    hospede = models.ForeignKey(Hospede, on_delete=models.CASCADE, related_name='reservas', null=True, blank=True)
    quarto = models.ForeignKey(Quarto, on_delete=models.PROTECT, related_name='reservas')

    
    data_checkin = models.DateField()
    data_checkout = models.DateField()
    
    # Campos FNRH da Viagem
    motivo_viagem = models.CharField(
        max_length=50, 
        choices=[
            ('lazer', 'Lazer'), 
            ('negocios', 'Negócios'),
            ('congresso', 'Congresso/Convenção'),
            ('parentes', 'Parentes/Amigos'),
            ('estudos', 'Estudos'),
            ('saude', 'Saúde'),
            ('compras', 'Compras'),
            ('outro', 'Outro')
        ], 
        blank=True, null=True
    )
    meio_transporte = models.CharField(
        max_length=50,
        choices=[
            ('aviao', 'Avião'),
            ('automovel', 'Automóvel'),
            ('onibus', 'Ônibus'),
            ('trem', 'Trem'),
            ('embarcacao', 'Embarcação'),
            ('outro', 'Outro')
        ],
        blank=True, null=True
    )
    placa_veiculo = models.CharField(max_length=10, blank=True, null=True)
    ultima_procedencia = models.CharField(max_length=255, blank=True, null=True)
    proximo_destino = models.CharField(max_length=255, blank=True, null=True)
    
    # Token Seguro e Status de Check-in
    token_checkin = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    checkin_concluido = models.BooleanField(default=False)
    checkin_online_realizado = models.BooleanField(default=False)
    hospede_cpf = models.CharField(max_length=14, blank=True, null=True)
    fnrh_exportado = models.BooleanField(default=False)
    
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(
        max_length=20, 
        choices=[
            ('pendente', 'Pendente'), 
            ('confirmada', 'Confirmada'), 
            ('finalizada', 'Finalizada'), 
            ('cancelada', 'Cancelada')
        ], 
        default='pendente'
    )
    
    # Novos campos para Bloqueios e Tags de Reserva
    tags = models.ManyToManyField('hospedes.Tag', blank=True)
    is_bloqueio = models.BooleanField(default=False)
    motivo_bloqueio = models.ForeignKey('pousada.MotivoBloqueio', null=True, blank=True, on_delete=models.SET_NULL)
    senha_fechadura = models.CharField(max_length=20, blank=True, null=True)
    token_acesso = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        nome_hospede = self.hospede.nome_completo if self.hospede else f"Bloqueio ({self.motivo_bloqueio.nome if self.motivo_bloqueio else 'Manutenção'})"
        return f"Reserva {self.id}: {nome_hospede} - {self.quarto.nome_identificacao}"

    @property
    def total_pago(self):
        resultado = self.pagamentos.filter(status='pago').aggregate(soma=Sum('valor'))['soma']
        return resultado if resultado is not None else Decimal('0.00')

    @property
    def saldo_devedor(self):
        return self.valor_total - self.total_pago

    @property
    def status_financeiro(self):
        saldo = self.saldo_devedor
        if saldo <= 0:
            return 'quitado'
        elif self.total_pago > 0:
            return 'parcial'
        else:
            return 'pendente'


class Acompanhante(models.Model):
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='acompanhantes')
    nome = models.CharField(max_length=255)
    cpf = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nome


class FichaFNRH(models.Model):
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE, related_name='ficha_fnrh')
    nome_completo = models.CharField(max_length=255)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    data_nascimento = models.DateField()
    nacionalidade = models.CharField(max_length=100, default='Brasileira')
    cpf_passaporte = models.CharField(max_length=50)
    documento_identidade = models.CharField(max_length=50)  # RG / CNH
    
    # Endereço
    cep = models.CharField(max_length=20)
    logradouro = models.CharField(max_length=255)
    numero = models.CharField(max_length=20)
    complemento = models.CharField(max_length=100, blank=True, null=True)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=50)
    pais = models.CharField(max_length=100, default='Brasil')
    
    # Viagem
    placa_veiculo = models.CharField(max_length=10, blank=True, null=True)
    motivo_viagem = models.CharField(
        max_length=50,
        choices=[
            ('lazer', 'Lazer'),
            ('negocios', 'Negócios'),
            ('outro', 'Outros')
        ]
    )
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"FNRH #{self.id} - Hóspede: {self.nome_completo}"
```

### reservas/views.py
> **901 linhas** — Arquivo central do sistema. Inclui API DRF, views de calendário, lista/criação/edição de reservas, check-in online, portal do hóspede, pagamentos e dashboard.

```python
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db import transaction
import json
import csv

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Reserva
from .serializers import ReservaSerializer, ReservaUpdateSerializer
from pousada.models import Quarto
from pousada.serializers import QuartoSerializer

class ReservaUpdateAPI(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReservaUpdateSerializer

    def get_queryset(self):
        return Reserva.objects.filter(pousada__dono=self.request.user)

class ReservaListAPI(generics.ListAPIView):
    serializer_class = ReservaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Reserva.objects.filter(pousada__dono=self.request.user)

class QuartoListAPI(generics.ListAPIView):
    serializer_class = QuartoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Quarto.objects.filter(pousada__dono=self.request.user)


@login_required
def api_quartos_disponiveis(request):
    """API: retorna quartos sem conflito de reserva para o período solicitado."""
    try:
        pousada = request.user.pousada
    except Exception:
        return JsonResponse({'error': 'Usuário não possui uma pousada cadastrada.'}, status=400)

    start_str = request.GET.get('start')
    end_str = request.GET.get('end')

    if not start_str or not end_str:
        return JsonResponse({'error': 'Parâmetros start e end são obrigatórios.'}, status=400)

    from reservas.models import Reserva
    from pousada.models import Quarto

    ocupados_ids = Reserva.objects.filter(
        pousada=pousada,
        data_checkin__lt=end_str,
        data_checkout__gt=start_str
    ).values_list('quarto_id', flat=True)

    quartos_livres = Quarto.objects.filter(pousada=pousada, ativo=True).exclude(id__in=ocupados_ids)

    data = [
        {
            'id': q.id,
            'nome': f"{q.nome_identificacao} ({q.categoria.nome} - R$ {q.categoria.valor_diaria})"
        }
        for q in quartos_livres
    ]
    return JsonResponse(data, safe=False)


from hospedes.models import Hospede

class CalendarioView(LoginRequiredMixin, TemplateView):
    """View principal do calendário FullCalendar. Redireciona funcionários 
    operacionais (só governança) para a view mobile."""
    template_name = 'reservas/calendario.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            user = request.user
            if not user.is_superuser and not hasattr(user, 'pousada_owner'):
                cliente = getattr(user, 'cliente_saas', None)
                if cliente and cliente.nivel_acesso:
                    na = cliente.nivel_acesso
                    is_operational = (
                        na.pode_acessar_governanca and
                        not na.pode_acessar_reservas and
                        not na.pode_acessar_crm and
                        not na.pode_acessar_financeiro and
                        not na.pode_acessar_configuracoes
                    )
                    if is_operational:
                        from django.shortcuts import redirect
                        return redirect('governanca-mobile')
        return super().dispatch(request, *args, **kwargs)


@login_required
def reserva_lista_view(request):
    try:
        pousada = request.user.pousada
    except Exception:
        return render(request, 'reservas/lista_reservas.html', {'error': 'Você não possui uma pousada vinculada ao seu usuário.'})
        
    reservas = Reserva.objects.filter(pousada=pousada).order_by('data_checkin')
    quartos = Quarto.objects.filter(pousada=pousada, ativo=True)
    reservas_confirmadas_count = reservas.filter(status='confirmada').count()
    from pousada.models import MetodoPagamentoConfig
    metodos_pagamento = MetodoPagamentoConfig.objects.filter(pousada=pousada, ativo=True).order_by('nome')
    return render(request, 'reservas/lista_reservas.html', {
        'reservas': reservas,
        'quartos': quartos,
        'pousada': pousada,
        'reservas_confirmadas_count': reservas_confirmadas_count,
        'metodos_pagamento': metodos_pagamento,
    })

@login_required
@require_POST
def reserva_criar_view(request):
    """Cria reserva (ou bloqueio) para um ou múltiplos quartos. 
    Suporta pagamento de sinal e agrupamento via Grupo."""
    try:
        pousada = request.user.pousada
    except Exception:
        messages.error(request, 'Usuário não possui uma pousada cadastrada.')
        return redirect('reserva-lista')
        
    tipo_registro = request.POST.get('tipo_registro', 'reserva')
    room_ids = request.POST.getlist('room_ids')
    data_checkin = request.POST.get('data_checkin')
    data_checkout = request.POST.get('data_checkout')
    
    if not room_ids:
        messages.error(request, 'Pelo menos um quarto deve ser selecionado.')
        return redirect('reserva-lista')
        
    # Criar Grupo se houver mais de um quarto selecionado
    grupo = None
    if len(room_ids) > 1:
        from reservas.models import Grupo
        # ... (lógica de criação de grupo omitida para brevidade, ver código completo)
        grupo = Grupo.objects.create(nome=f"Grupo ({data_checkin})")
        
    if tipo_registro == 'bloqueio':
        # ... cria Reserva(is_bloqueio=True) para cada quarto
        pass
        
    # OPT-06: Transação atômica com select_for_update para evitar race condition
    with transaction.atomic():
        # BUG-03: Verificar conflito de quarto para cada quarto selecionado
        conflito = Reserva.objects.select_for_update().filter(
            quarto__id__in=room_ids,
            pousada=pousada,
            data_checkin__lt=data_checkout,
            data_checkout__gt=data_checkin
        )
        if conflito.exists():
            messages.error(request, f'Conflito de reserva detectado.')
            return redirect('reserva-lista')

        # Cria Reserva para cada quarto + Pagamento de sinal (se fornecido)
        for idx, r_id in enumerate(room_ids):
            quarto = Quarto.objects.get(id=r_id, pousada=pousada)
            reserva_obj = Reserva.objects.create(...)
            if idx == 0 and valor_sinal > 0:
                Pagamento.objects.create(tipo='sinal', ...)

    return redirect('reserva-lista')

@login_required
def api_hospedes_list_create(request):
    """GET: busca hóspedes por nome (autocomplete). POST: cria novo hóspede rapidamente."""
    ...

@login_required
def exportar_fnrh_csv(request):
    """Exporta reservas com check-in concluído em formato CSV (FNRH oficial).
    Marca registros como fnrh_exportado=True via bulk_update."""
    ...

@login_required
def reserva_editar_view(request, pk):
    """Edita ou exclui uma reserva. Inclui listagem de pagamentos e URL de acesso do hóspede."""
    ...

def checkin_online_view(request, token):
    """Check-in online pelo hóspede via UUID token. Atualiza dados do hóspede e da reserva."""
    ...

@login_required
@require_POST
def registrar_pagamento(request):
    """Registra pagamento vinculado a uma reserva."""
    ...

@login_required
@require_POST
def editar_pagamento(request, pk):
    """Edita um pagamento existente."""
    ...

@login_required
def dashboard_view(request):
    """Dashboard operacional: ocupação, receita do dia, check-ins/checkouts pendentes,
    ações imediatas (limpeza, OS, check-in)."""
    ...

def portal_hospede(request, token):
    """Portal público do hóspede. Permite preencher FNRH completa, definir PIN da fechadura
    e ativar senha via Tuya API."""
    ...

@login_required
def imprimir_fnrh_view(request, pk):
    """Imprime a FNRH de uma reserva em formato HTML para impressão."""
    ...
```

### reservas/urls.py
```python
from django.urls import path
from pousada.views import pousada_config_view, gerenciar_equipe, ver_logs, governanca_dashboard, governanca_mobile_view
from .views import (
    ReservaListAPI, 
    QuartoListAPI, 
    CalendarioView, 
    ReservaUpdateAPI,
    reserva_lista_view,
    reserva_criar_view,
    api_hospedes_list_create,
    exportar_fnrh_csv,
    reserva_editar_view,
    checkin_online_view,
    api_quartos_disponiveis,
    registrar_pagamento,
    editar_pagamento,
    dashboard_view,
    portal_hospede,
    imprimir_fnrh_view
)

urlpatterns = [
    path('api/reservas/', ReservaListAPI.as_view(), name='api-reservas'),
    path('api/reservas/<int:pk>/update/', ReservaUpdateAPI.as_view(), name='api-reserva-update'),
    path('api/quartos/', QuartoListAPI.as_view(), name='api-quartos'),
    path('calendario/', CalendarioView.as_view(), name='calendario'),
    
    # Novas rotas customizadas
    path('painel/reservas/', reserva_lista_view, name='reserva-lista'),
    path('painel/reservas/criar/', reserva_criar_view, name='reserva-criar'),
    path('painel/reservas/api/quartos-disponiveis/', api_quartos_disponiveis, name='api-quartos-disponiveis'),
    path('api/hospedes/', api_hospedes_list_create, name='api-hospedes-list-create'),
    path('painel/reservas/exportar-fnrh/', exportar_fnrh_csv, name='exportar-fnrh'),
    path('painel/reservas/<int:pk>/editar/', reserva_editar_view, name='reserva-editar'),
    path('painel/reservas/registrar-pagamento/', registrar_pagamento, name='registrar-pagamento'),
    path('painel/reservas/pagamentos/<int:pk>/editar/', editar_pagamento, name='editar-pagamento'),
    path('checkin/<uuid:token>/', checkin_online_view, name='checkin-online'),
    
    # Identidade Visual e CRM
    path('painel/pousada/config/', pousada_config_view, name='pousada-config'),
    path('painel/pousada/config/equipe/', gerenciar_equipe, name='gerenciar-equipe'),
    path('painel/pousada/config/auditoria/', ver_logs, name='ver-logs'),
    path('painel/governanca/', governanca_dashboard, name='governanca-dashboard'),
    path('painel/governanca/mobile/', governanca_mobile_view, name='governanca-mobile'),
    path('painel/dashboard/', dashboard_view, name='dashboard'),
    path('hospede/meu-acesso/<uuid:token>/', portal_hospede, name='portal_hospede'),
    path('reserva/<int:pk>/fnrh/imprimir/', imprimir_fnrh_view, name='imprimir_fnrh'),
]
```

### reservas/serializers.py
```python
from rest_framework import serializers
from .models import Reserva

class ReservaSerializer(serializers.ModelSerializer):
    # O FullCalendar (Javascript) exige esses nomes exatos de campos:
    start = serializers.SerializerMethodField()
    end = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    resourceId = serializers.IntegerField(source='quarto.id')
    color = serializers.SerializerMethodField()
    allDay = serializers.SerializerMethodField()
    hospede_nome = serializers.SerializerMethodField()
    celular = serializers.SerializerMethodField()
    valor_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    saldo_devedor = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Reserva
        fields = [
            'id', 'start', 'end', 'title', 'resourceId', 'status', 'color', 'allDay', 'is_bloqueio',
            'hospede_nome', 'celular', 'valor_total', 'saldo_devedor'
        ]

    def get_allDay(self, obj):
        return False

    def get_start(self, obj):
        return f"{obj.data_checkin}T14:00:00"

    def get_end(self, obj):
        return f"{obj.data_checkout}T10:00:00"

    def get_title(self, obj):
        if obj.is_bloqueio:
            return obj.motivo_bloqueio.nome if obj.motivo_bloqueio else "Bloqueio"
        return obj.hospede.nome_completo if obj.hospede else "Reserva"

    def get_color(self, obj):
        if obj.is_bloqueio:
            return obj.motivo_bloqueio.cor if (obj.motivo_bloqueio and obj.motivo_bloqueio.cor) else '#475569'
        return '#3b82f6'

    def get_hospede_nome(self, obj):
        return obj.hospede.nome_completo if obj.hospede else "Bloqueio"

    def get_celular(self, obj):
        return obj.hospede.telefone if (obj.hospede and obj.hospede.telefone) else ""


class ReservaUpdateSerializer(serializers.ModelSerializer):
    """Serializer usado pelo FullCalendar para drag-and-drop de reservas."""
    class Meta:
        model = Reserva
        fields = ['data_checkin', 'data_checkout', 'quarto']

    def validate(self, data):
        quarto = data.get('quarto', self.instance.quarto if self.instance else None)
        data_checkin = data.get('data_checkin', self.instance.data_checkin if self.instance else None)
        data_checkout = data.get('data_checkout', self.instance.data_checkout if self.instance else None)

        if not quarto or not data_checkin or not data_checkout:
            return data

        overlaps = Reserva.objects.filter(
            quarto=quarto,
            data_checkin__lt=data_checkout,
            data_checkout__gt=data_checkin
        )

        if self.instance and self.instance.pk:
            overlaps = overlaps.exclude(pk=self.instance.pk)

        if overlaps.exists():
            raise serializers.ValidationError('Este quarto já possui uma reserva para o período selecionado.')

        return data
```

### reservas/admin.py
```python
from django.contrib import admin
from .models import Reserva

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('quarto', 'hospede', 'data_checkin', 'data_checkout', 'status')
    
    # Isso cria uma navegação por datas no topo da tela
    date_hierarchy = 'data_checkin'
    
    # Isso permite filtrar por status e pelo quarto
    list_filter = ('status', 'quarto', 'data_checkin')
    
    # Campo de busca para achar o hóspede rapidamente
    search_fields = ('hospede__nome_completo',)

    # Dica: Bloqueia a edição se a reserva já estiver encerrada (opcional)
    def has_change_permission(self, request, obj=None):
        return True # Aqui você pode adicionar lógica de permissão depois
```

### reservas/tests.py
```python
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from pousada.models import Pousada, CategoriaQuarto, Quarto
from hospedes.models import Hospede
from reservas.models import Reserva, FichaFNRH
import datetime

class ImprimirFNRHViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='dono', password='password123')
        self.pousada = Pousada.objects.create(
            dono=self.user, nome='Pousada Teste', slug='pousada-teste'
        )
        self.categoria = CategoriaQuarto.objects.create(
            pousada=self.pousada, nome='Standard', valor_diaria=150.00, capacidade=2
        )
        self.quarto = Quarto.objects.create(
            pousada=self.pousada, categoria=self.categoria, nome_identificacao='101'
        )
        self.hospede = Hospede.objects.create(
            pousada=self.pousada, nome_completo='Hóspede Teste'
        )
        self.reserva = Reserva.objects.create(
            pousada=self.pousada, quarto=self.quarto, hospede=self.hospede,
            data_checkin=datetime.date(2026, 6, 12),
            data_checkout=datetime.date(2026, 6, 15),
            valor_total=450.00, status='confirmada'
        )
        self.client = Client()

    def test_imprimir_fnrh_requires_login(self):
        url = reverse('imprimir_fnrh', kwargs={'pk': self.reserva.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_imprimir_fnrh_pousada_check(self):
        """Garante que usuário não pode acessar FNRH de outra pousada (retorna 404)."""
        other_user = User.objects.create_superuser(username='dono2', password='password123')
        other_pousada = Pousada.objects.create(dono=other_user, nome='Outra Pousada', slug='outra-pousada')
        other_categoria = CategoriaQuarto.objects.create(pousada=other_pousada, nome='Luxury', valor_diaria=300.00)
        other_quarto = Quarto.objects.create(pousada=other_pousada, categoria=other_categoria, nome_identificacao='202')
        other_reserva = Reserva.objects.create(
            pousada=other_pousada, quarto=other_quarto,
            data_checkin=datetime.date(2026, 6, 12), data_checkout=datetime.date(2026, 6, 15),
            valor_total=900.00, status='confirmada'
        )
        self.client.login(username='dono', password='password123')
        url = reverse('imprimir_fnrh', kwargs={'pk': other_reserva.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_imprimir_fnrh_no_ficha_renders_blank_lines(self):
        self.client.login(username='dono', password='password123')
        url = reverse('imprimir_fnrh', kwargs={'pk': self.reserva.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reservas/fnrh_imprimir.html')
        self.assertIsNone(response.context['ficha'])
        self.assertContains(response, 'Nome Completo:')
        self.assertContains(response, 'window.print()')

    def test_imprimir_fnrh_with_ficha_renders_filled_data(self):
        ficha = FichaFNRH.objects.create(
            reserva=self.reserva, nome_completo='Hóspede FNRH Preenchido',
            email='hospede@example.com', telefone='11999999999',
            data_nascimento=datetime.date(1990, 1, 1), nacionalidade='Brasileira',
            cpf_passaporte='123.456.789-00', documento_identidade='12345678-9',
            cep='01001-000', logradouro='Praça da Sé', numero='100',
            bairro='Centro', cidade='São Paulo', estado='SP', pais='Brasil',
            motivo_viagem='lazer'
        )
        self.client.login(username='dono', password='password123')
        url = reverse('imprimir_fnrh', kwargs={'pk': self.reserva.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['ficha'], ficha)
        self.assertContains(response, 'Hóspede FNRH Preenchido')
        self.assertContains(response, 'hospede@example.com')
        self.assertContains(response, '123.456.789-00')
        self.assertContains(response, 'Praça da Sé')
        self.assertContains(response, 'São Paulo')
```

---

## 💰 APP: financeiro

> Gerencia os pagamentos vinculados às reservas.

### financeiro/models.py
```python
from django.db import models
from pousada.models import Pousada
from reservas.models import Reserva

class Pagamento(models.Model):
    TIPO_CHOICES = [
        ('sinal', 'Sinal'),
        ('saldo_final', 'Saldo Final'),
        ('consumo', 'Consumo'),
    ]

    METODO_PAGAMENTO_CHOICES = [
        ('pix', 'Pix'),
        ('credito', 'Crédito'),
        ('debito', 'Débito'),
        ('dinheiro', 'Dinheiro'),
        ('transferencia', 'Transferência'),
    ]

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
        ('estornado', 'Estornado'),
    ]

    pousada = models.ForeignKey(Pousada, on_delete=models.CASCADE, related_name='pagamentos')
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='pagamentos')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='saldo_final')
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pagamento = models.CharField(max_length=20, choices=METODO_PAGAMENTO_CHOICES, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    data_vencimento = models.DateField()
    data_pagamento = models.DateField(null=True, blank=True)
    observacao = models.CharField(max_length=255, blank=True)
    data_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pagamento {self.id} - {self.get_tipo_display()} ({self.get_status_display()}) - R$ {self.valor}"
```

### financeiro/admin.py
```python
from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
from .models import Pagamento

@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ('reserva', 'tipo', 'valor', 'metodo_pagamento', 'status', 'data_pagamento')
    list_filter = ('status', 'tipo', 'metodo_pagamento', 'pousada')
    search_fields = ('reserva__hospede__nome_completo', 'observacao')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        try:
            return qs.filter(pousada=request.user.pousada)
        except (AttributeError, ObjectDoesNotExist):
            return qs.none()
```

---

## 🔑 APP: admin_saas

> Painel exclusivo do superusuário para gestão dos clientes/pousadas da plataforma SaaS, controle de planos, níveis de acesso e envio de e-mail de teste.

### admin_saas/models.py
```python
from django.db import models
from django.contrib.auth.models import User

class NivelAcesso(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    pode_acessar_reservas = models.BooleanField(default=True)
    pode_acessar_crm = models.BooleanField(default=True)
    pode_acessar_financeiro = models.BooleanField(default=True)
    pode_acessar_configuracoes = models.BooleanField(default=True)
    pode_acessar_governanca = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

class ClienteSaaS(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cliente_saas')
    nivel_acesso = models.ForeignKey(NivelAcesso, on_delete=models.SET_NULL, null=True, blank=True, related_name='clientes')
    pousada = models.ForeignKey('pousada.Pousada', on_delete=models.SET_NULL, null=True, blank=True, related_name='funcionarios')
    plano_ativo = models.BooleanField(default=True)
    data_expiracao = models.DateField(null=True, blank=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"Cliente SaaS: {self.user.username} - {'Ativo' if self.ativo else 'Inativo'}"
```

### admin_saas/views.py
```python
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from django.utils.text import slugify
from pousada.models import Pousada
from .models import ClienteSaaS, NivelAcesso

@login_required
def admin_saas_dashboard(request):
    """Dashboard do super-admin. Cria ClienteSaaS automaticamente para users sem perfil (BUG-08)."""
    if not request.user.is_superuser:
        return redirect('reserva-lista')

    default_nivel, created = NivelAcesso.objects.get_or_create(
        nome="Administrador Padrão",
        defaults={
            'pode_acessar_reservas': True,
            'pode_acessar_crm': True,
            'pode_acessar_financeiro': True,
            'pode_acessar_configuracoes': True,
            'pode_acessar_governanca': True,
        }
    )

    # BUG-08: Criar ClienteSaaS apenas para usuários que não possuem um (bulk, sem N+1)
    users_sem_cliente = User.objects.filter(is_superuser=False, cliente_saas__isnull=True)
    if users_sem_cliente.exists():
        ClienteSaaS.objects.bulk_create([
            ClienteSaaS(user=u, nivel_acesso=default_nivel, ativo=True)
            for u in users_sem_cliente
        ], ignore_conflicts=True)

    clientes = ClienteSaaS.objects.all().select_related('user', 'nivel_acesso', 'pousada', 'user__pousada_owner')
    niveis = NivelAcesso.objects.all()
    ativos_count = sum(1 for c in clientes if c.ativo)
    inativos_count = sum(1 for c in clientes if not c.ativo)
    active_tab = request.GET.get('tab', 'clientes')

    return render(request, 'admin_saas/dashboard.html', {
        'clientes': clientes,
        'niveis': niveis,
        'ativos_count': ativos_count,
        'inativos_count': inativos_count,
        'default_nivel_id': default_nivel.id,
        'active_tab': active_tab,
    })

@login_required
@require_POST
def toggle_cliente_ativo(request, pk):
    if not request.user.is_superuser:
        return redirect('reserva-lista')
    cliente = get_object_or_404(ClienteSaaS, id=pk)
    cliente.ativo = not cliente.ativo
    cliente.save()
    messages.success(request, f"O status do cliente {cliente.user.username} foi {'ativado' if cliente.ativo else 'desativado'} com sucesso!")
    return redirect('/painel-saas/?tab=clientes')

@login_required
@require_POST
def criar_cliente_saas(request):
    """Cria User + Pousada + ClienteSaaS atomicamente."""
    if not request.user.is_superuser:
        return redirect('reserva-lista')
        
    username = request.POST.get('username', '').strip()
    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '')
    pousada_nome = request.POST.get('pousada_nome', '').strip()
    nivel_acesso_id = request.POST.get('nivel_acesso')
    plano_ativo_val = request.POST.get('plano_ativo') == 'true'
    data_exp = request.POST.get('data_expiracao') or None

    if not username or not email or not password or not pousada_nome:
        messages.error(request, "Todos os campos obrigatórios devem ser preenchidos.")
        return redirect('/painel-saas/?tab=clientes')

    if User.objects.filter(username=username).exists():
        messages.error(request, "Este nome de usuário já está em uso.")
        return redirect('/painel-saas/?tab=clientes')

    if User.objects.filter(email=email).exists():
        messages.error(request, "Este endereço de e-mail já está em uso.")
        return redirect('/painel-saas/?tab=clientes')

    try:
        with transaction.atomic():
            user = User.objects.create_user(username=username, email=email, password=password)
            slug = slugify(pousada_nome)
            if not slug:
                slug = f"pousada-{user.id}"
            if Pousada.objects.filter(slug=slug).exists():
                slug = f"{slug}-{user.id}"
            Pousada.objects.create(dono=user, nome=pousada_nome, slug=slug)
            nivel_acesso = get_object_or_404(NivelAcesso, id=nivel_acesso_id) if nivel_acesso_id else None
            ClienteSaaS.objects.create(
                user=user, nivel_acesso=nivel_acesso,
                plano_ativo=plano_ativo_val, data_expiracao=data_exp, ativo=True
            )
        messages.success(request, f"Cliente {username} e sua pousada '{pousada_nome}' foram criados com sucesso!")
    except Exception as e:
        messages.error(request, f"Erro ao criar cliente: {str(e)}")
        
    return redirect('/painel-saas/?tab=clientes')

@login_required
@require_POST
def atualizar_cliente_saas(request, pk):
    if not request.user.is_superuser:
        return redirect('reserva-lista')
    cliente = get_object_or_404(ClienteSaaS, id=pk)
    data_exp = request.POST.get('data_expiracao') or None
    plano_ativo_val = request.POST.get('plano_ativo') == 'true'
    nivel_acesso_id = request.POST.get('nivel_acesso')
    
    try:
        cliente.data_expiracao = data_exp
        cliente.plano_ativo = plano_ativo_val
        if nivel_acesso_id:
            cliente.nivel_acesso = get_object_or_404(NivelAcesso, id=nivel_acesso_id)
        else:
            cliente.nivel_acesso = None
        cliente.save()
        messages.success(request, f"Configurações do cliente {cliente.user.username} atualizadas com sucesso!")
    except Exception as e:
        messages.error(request, f"Erro ao atualizar configurações: {str(e)}")
        
    return redirect('/painel-saas/?tab=clientes')

@login_required
@require_POST
def criar_nivel_acesso(request):
    if not request.user.is_superuser:
        return redirect('reserva-lista')
    nome = request.POST.get('nome', '').strip()
    if not nome:
        messages.error(request, "O nome do nível de acesso é obrigatório.")
        return redirect('/painel-saas/?tab=niveis')

    pode_reservas = request.POST.get('pode_acessar_reservas') == 'on'
    pode_crm = request.POST.get('pode_acessar_crm') == 'on'
    pode_financeiro = request.POST.get('pode_acessar_financeiro') == 'on'
    pode_config = request.POST.get('pode_acessar_configuracoes') == 'on'
    pode_governanca = request.POST.get('pode_acessar_governanca') == 'on'

    try:
        NivelAcesso.objects.create(
            nome=nome,
            pode_acessar_reservas=pode_reservas,
            pode_acessar_crm=pode_crm,
            pode_acessar_financeiro=pode_financeiro,
            pode_acessar_configuracoes=pode_config,
            pode_acessar_governanca=pode_governanca,
        )
        messages.success(request, f"Nível de acesso '{nome}' criado com sucesso!")
    except Exception as e:
        messages.error(request, f"Erro ao criar nível de acesso: {str(e)}")

    return redirect('/painel-saas/?tab=niveis')

@login_required
@require_POST
def atualizar_nivel_acesso(request, pk):
    if not request.user.is_superuser:
        return redirect('reserva-lista')
    nivel = get_object_or_404(NivelAcesso, id=pk)
    nome = request.POST.get('nome', '').strip()
    if not nome:
        messages.error(request, "O nome do nível de acesso é obrigatório.")
        return redirect('/painel-saas/?tab=niveis')

    nivel.nome = nome
    nivel.pode_acessar_reservas = request.POST.get('pode_acessar_reservas') == 'on'
    nivel.pode_acessar_crm = request.POST.get('pode_acessar_crm') == 'on'
    nivel.pode_acessar_financeiro = request.POST.get('pode_acessar_financeiro') == 'on'
    nivel.pode_acessar_configuracoes = request.POST.get('pode_acessar_configuracoes') == 'on'
    nivel.pode_acessar_governanca = request.POST.get('pode_acessar_governanca') == 'on'
    try:
        nivel.save()
        messages.success(request, f"Nível de acesso '{nome}' atualizado com sucesso!")
    except Exception as e:
        messages.error(request, f"Erro ao atualizar nível de acesso: {str(e)}")

    return redirect('/painel-saas/?tab=niveis')

@login_required
@require_POST
def excluir_nivel_acesso(request, pk):
    if not request.user.is_superuser:
        return redirect('reserva-lista')
    nivel = get_object_or_404(NivelAcesso, id=pk)
    if nivel.clientes.exists():
        messages.error(request, f"Não é possível excluir o nível '{nivel.nome}' pois ele está sendo utilizado por clientes.")
        return redirect('/painel-saas/?tab=niveis')
    try:
        nivel.delete()
        messages.success(request, f"Nível de acesso excluído com sucesso!")
    except Exception as e:
        messages.error(request, f"Erro ao excluir nível de acesso: {str(e)}")
    return redirect('/painel-saas/?tab=niveis')

@login_required
def testar_email(request):
    """View de teste do SMTP — envia um e-mail de teste para o superuser."""
    if not request.user.is_superuser:
        return redirect('reserva-lista')
    from django.core.mail import send_mail
    from django.http import HttpResponse
    try:
        destinatario = request.user.email or 'auradecunha@gmail.com'
        send_mail(
            subject='E-mail de Teste - AuraSaaS SMTP',
            message='Este é um e-mail de teste enviado para validar as configurações de SMTP do AuraSaaS.',
            from_email=None,
            recipient_list=[destinatario],
            fail_silently=False,
        )
        return HttpResponse(f"E-mail de teste enviado com sucesso para {destinatario}!")
    except Exception as e:
        return HttpResponse(f"Erro ao enviar e-mail: {str(e)}", status=500)
```

### admin_saas/urls.py
```python
from django.urls import path
from .views import (
    admin_saas_dashboard,
    toggle_cliente_ativo,
    atualizar_cliente_saas,
    criar_cliente_saas,
    criar_nivel_acesso,
    atualizar_nivel_acesso,
    excluir_nivel_acesso,
    testar_email,
)

urlpatterns = [
    path('', admin_saas_dashboard, name='admin-saas-dashboard'),
    path('clientes/criar/', criar_cliente_saas, name='admin-saas-criar-cliente'),
    path('clientes/<int:pk>/toggle/', toggle_cliente_ativo, name='admin-saas-toggle-ativo'),
    path('clientes/<int:pk>/atualizar/', atualizar_cliente_saas, name='admin-saas-atualizar-cliente'),
    path('niveis/criar/', criar_nivel_acesso, name='admin-saas-criar-nivel'),
    path('niveis/<int:pk>/atualizar/', atualizar_nivel_acesso, name='admin-saas-atualizar-nivel'),
    path('niveis/<int:pk>/excluir/', excluir_nivel_acesso, name='admin-saas-excluir-nivel'),
    path('testar-email/', testar_email, name='admin-saas-testar-email'),
]
```

### admin_saas/middleware.py
```python
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
                        if not getattr(nivel, perm_field, True):
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
```

---

## 📄 Templates HTML

### Estrutura dos Templates

| Template | App | Tamanho | Descrição |
|---|---|---|---|
| `base_painel.html` | core | 10.9 KB | Layout base com sidebar e navbar |
| `registration/login.html` | core | 4.6 KB | Página de login |
| `registration/password_reset_form.html` | core | 3.0 KB | Formulário de reset de senha |
| `registration/password_reset_done.html` | core | 2.4 KB | Confirmação de e-mail enviado |
| `registration/password_reset_confirm.html` | core | 5.4 KB | Definir nova senha |
| `registration/password_reset_complete.html` | core | 1.8 KB | Reset concluído |
| `registration/password_reset_email.html` | core | 0.4 KB | Corpo do e-mail de reset |
| `registration/password_reset_subject.txt` | core | 34 B | Assunto do e-mail de reset |
| `configuracoes_pousada.html` | pousada | **60.7 KB** | Multi-aba: Geral, Quartos, Tags, Bloqueios, Pagamentos, Equipe, Auditoria, Governança Config |
| `governanca.html` | pousada | **31.9 KB** | Painel de governança: Limpeza (Kanban), Ordens de Serviço |
| `governanca_mobile.html` | pousada | 12.6 KB | Versão mobile da governança para funcionários operacionais |
| `lista_hospedes.html` | hospedes | 10.9 KB | Lista/busca de hóspedes com tags coloridas |
| `hospede_form.html` | hospedes | 15.1 KB | Formulário de criação/edição de hóspede |
| `calendario.html` | reservas | 14.3 KB | Calendário FullCalendar (Resource Timeline) |
| `lista_reservas.html` | reservas | **50.2 KB** | Lista de reservas + modal de nova reserva + modal de nova OS |
| `editar_reserva.html` | reservas | **35.1 KB** | Edição de reserva + pagamentos + link de check-in/portal |
| `checkin_online.html` | reservas | 20.0 KB | Formulário de check-in online pelo hóspede (link por token) |
| `portal_hospede.html` | reservas | **33.5 KB** | Portal do hóspede: FNRH completa + PIN da fechadura Tuya |
| `dashboard_operacoes.html` | reservas | 10.0 KB | Dashboard: ocupação, receita, check-ins, ações imediatas |
| `fnrh_imprimir.html` | reservas | 11.9 KB | FNRH para impressão (dispara window.print() automaticamente) |
| `admin_saas/dashboard.html` | admin_saas | **43.8 KB** | Painel SaaS: gerenciar clientes, planos, níveis de acesso |

### Notas sobre Templates Principais

- **`configuracoes_pousada.html`** — Template mais complexo do sistema. Usa um sistema de abas (`?tab=`) controlado pelo backend para renderizar seções distintas: configurações gerais (logo, nome, WhatsApp), quartos e categorias, tags, motivos de bloqueio, métodos de pagamento, gestão de equipe e checklist de limpeza.

- **`lista_reservas.html`** — Contém todos os modais de criação de reserva e bloqueio, incluindo seleção múltipla de quartos, autocomplete de hóspedes via API e configuração de tipo de cobrança (única / dividida).

- **`portal_hospede.html`** — Página pública (sem login). O hóspede preenche a FNRH e define um PIN de 4 dígitos para a fechadura. O backend gera a senha completa (`prefixo + PIN`) e envia à Tuya.

- **`calendario.html`** — Integração com FullCalendar Resource Timeline. Consome `/api/reservas/` e `/api/quartos/` via DRF.

---

## 🔗 Mapa de URLs Completo

| URL | View | Nome | Auth |
|---|---|---|---|
| `/` | Redirect → `/painel/dashboard/` | — | — |
| `/login/` | LoginView | `login` | Pública |
| `/logout/` | LogoutView | `logout` | — |
| `/password_reset/` | PasswordResetView | `password_reset` | Pública |
| `/admin/` | Django Admin | — | Superuser |
| `/painel/dashboard/` | `dashboard_view` | `dashboard` | Login |
| `/painel/reservas/` | `reserva_lista_view` | `reserva-lista` | Login |
| `/painel/reservas/criar/` | `reserva_criar_view` | `reserva-criar` | Login |
| `/painel/reservas/<pk>/editar/` | `reserva_editar_view` | `reserva-editar` | Login |
| `/painel/reservas/registrar-pagamento/` | `registrar_pagamento` | `registrar-pagamento` | Login |
| `/painel/reservas/pagamentos/<pk>/editar/` | `editar_pagamento` | `editar-pagamento` | Login |
| `/painel/reservas/exportar-fnrh/` | `exportar_fnrh_csv` | `exportar-fnrh` | Login |
| `/painel/hospedes/` | `hospede_lista_view` | `hospede-lista` | Login |
| `/painel/hospedes/criar/` | `hospede_criar_view` | `hospede-criar` | Login |
| `/painel/hospedes/<pk>/editar/` | `hospede_editar_view` | `hospede-editar` | Login |
| `/painel/pousada/config/` | `pousada_config_view` | `pousada-config` | Login |
| `/painel/pousada/config/equipe/` | `gerenciar_equipe` | `gerenciar-equipe` | Login |
| `/painel/pousada/config/auditoria/` | `ver_logs` | `ver-logs` | Login |
| `/painel/governanca/` | `governanca_dashboard` | `governanca-dashboard` | Login |
| `/painel/governanca/mobile/` | `governanca_mobile_view` | `governanca-mobile` | Login |
| `/calendario/` | `CalendarioView` | `calendario` | Login |
| `/api/reservas/` | `ReservaListAPI` | `api-reservas` | Login |
| `/api/reservas/<pk>/update/` | `ReservaUpdateAPI` | `api-reserva-update` | Login |
| `/api/quartos/` | `QuartoListAPI` | `api-quartos` | Login |
| `/api/hospedes/` | `api_hospedes_list_create` | `api-hospedes-list-create` | Login |
| `/painel/reservas/api/quartos-disponiveis/` | `api_quartos_disponiveis` | `api-quartos-disponiveis` | Login |
| `/checkin/<uuid:token>/` | `checkin_online_view` | `checkin-online` | Pública |
| `/hospede/meu-acesso/<uuid:token>/` | `portal_hospede` | `portal_hospede` | Pública |
| `/reserva/<pk>/fnrh/imprimir/` | `imprimir_fnrh_view` | `imprimir_fnrh` | Login |
| `/painel-saas/` | `admin_saas_dashboard` | `admin-saas-dashboard` | Superuser |
| `/painel-saas/clientes/criar/` | `criar_cliente_saas` | `admin-saas-criar-cliente` | Superuser |
| `/painel-saas/clientes/<pk>/toggle/` | `toggle_cliente_ativo` | `admin-saas-toggle-ativo` | Superuser |
| `/painel-saas/clientes/<pk>/atualizar/` | `atualizar_cliente_saas` | `admin-saas-atualizar-cliente` | Superuser |
| `/painel-saas/niveis/criar/` | `criar_nivel_acesso` | `admin-saas-criar-nivel` | Superuser |
| `/painel-saas/niveis/<pk>/atualizar/` | `atualizar_nivel_acesso` | `admin-saas-atualizar-nivel` | Superuser |
| `/painel-saas/niveis/<pk>/excluir/` | `excluir_nivel_acesso` | `admin-saas-excluir-nivel` | Superuser |
| `/painel-saas/testar-email/` | `testar_email` | `admin-saas-testar-email` | Superuser |

---

## 🧠 Notas de Implementação e Decisões de Design

### Tenancy via Property Dinâmica
`User.pousada` é adicionado como uma `@property` em `pousada/models.py` via monkey-patch (`User.pousada = get_user_pousada`). A propriedade verifica primeiro `pousada_owner` (dono) e depois `cliente_saas.pousada` (funcionário). Isso elimina a necessidade de `if/else` em todas as views.

### Thread-local para Auditoria
O `CurrentUserMiddleware` armazena o usuário em `threading.local()` para que os `signals` do Django (que rodam fora do contexto da request) possam logar o usuário responsável pela ação no `LogAuditoria`.

### Integração Tuya (IoT)
O `TuyaLockService` usa `urllib.request` (sem dependências externas) para comunicar com a Tuya Cloud API via HMAC-SHA256. A criptografia da senha usa AES-ECB com padding PKCS7 (opcional, requer o pacote `cryptography`). Se a biblioteca não estiver disponível ou a API falhar, o serviço retorna uma resposta simulada para não interromper o fluxo.

### Tokens de Segurança nas Reservas
Cada `Reserva` possui dois UUIDs:
- `token_checkin` — link de check-in online (formulário FNRH simplificado)
- `token_acesso` — link do portal do hóspede (FNRH completa + PIN Tuya)

### Race Condition na Criação de Reservas
`reserva_criar_view` usa `transaction.atomic()` + `select_for_update()` para evitar double-booking quando dois usuários tentam reservar o mesmo quarto simultaneamente.

### Exportação FNRH
O CSV exportado usa `;` como delimitador e BOM UTF-8 para compatibilidade com Microsoft Excel em português. Após exportação, as reservas são marcadas como `fnrh_exportado=True` via `bulk_update` (não N saves individuais).

### Checklist de Limpeza
A governança possui um sistema de checklist configurável por pousada. Quando `usa_checklist_limpeza=True`, a finalização da limpeza de um quarto só é permitida quando todos os `ItemLimpezaConcluido` da `RegistroLimpeza` ativa estão marcados como `concluido=True`.

### Signals e Automação
O signal `verificar_checkout_limpeza` detecta quando uma reserva muda para `status='finalizada'` e automaticamente:
1. Marca o quarto como `status_limpeza='sujo'`
2. Cria uma `OrdemServico` de limpeza com prioridade 'media' (se não existir outra ativa)
