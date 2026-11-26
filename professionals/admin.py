from django.contrib import admin
from django.http import HttpRequest

from .models import ProfessionalProfile, ShiftHistory


class ReadOnlyAdminMixin:
    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


@admin.register(ProfessionalProfile)
class ProfessionalProfileAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        'user',
        'crm_number',
        'crm_uf',
        'homologation_status',
        'availability',
        'crm_regular',
        'icp_brasil_active',
    )
    list_filter = ('homologation_status', 'availability', 'crm_uf', 'crm_regular', 'icp_brasil_active')
    list_select_related = ('user',)
    search_fields = ('user__email', 'user__cpf', 'crm_number')


@admin.register(ShiftHistory)
class ShiftHistoryAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ('professional', 'status', 'changed_at')
    list_filter = ('status',)
    list_select_related = ('professional', 'professional__user')
