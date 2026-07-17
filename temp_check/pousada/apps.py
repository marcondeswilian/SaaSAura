from django.apps import AppConfig


class PousadaConfig(AppConfig):
    name = 'pousada'

    def ready(self):
        import pousada.signals
