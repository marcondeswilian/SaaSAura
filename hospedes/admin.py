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
                url,
                r.id,
                checkin,
                checkout,
                status_desc,
            ))

        items_html = mark_safe(''.join(items))
        return format_html(
            '<div style="margin-top: 5px;">'
            '<strong>Total de Estadias: {}</strong>'
            '<ul style="margin-top: 5px; padding-left: 20px; line-height: 1.6;">{}</ul>'
            '</div>',
            count,
            items_html,
        )
    historico_estadias.short_description = "Histórico de Estadias (Links)"