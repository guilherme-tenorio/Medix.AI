from django.contrib import admin
from django.http import HttpRequest

from .models import (
    ClinicalProfile,
    ClinicalProfileHistory,
    ConsentRecord,
    Dependent,
    PatientProfile,
)


class ReadOnlyAdminMixin:
    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


@admin.register(PatientProfile)
class PatientProfileAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ('user', 'birth_date', 'gender', 'phone_verified_at', 'created_at')
    list_select_related = ('user',)
    search_fields = ('user__email', 'user__cpf', 'user__first_name', 'user__last_name')


@admin.register(Dependent)
class DependentAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ('full_name', 'cpf', 'legal_relationship', 'guardian', 'is_active')
    list_filter = ('legal_relationship', 'is_active')
    list_select_related = ('guardian', 'guardian__user')
    search_fields = ('full_name', 'cpf')


@admin.register(ClinicalProfile)
class ClinicalProfileAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ('__str__', 'blood_type', 'has_allergy', 'has_hypertension', 'has_diabetes', 'updated_at')
    list_filter = ('blood_type', 'has_allergy', 'has_hypertension', 'has_diabetes')


@admin.register(ClinicalProfileHistory)
class ClinicalProfileHistoryAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ('clinical_profile', 'changed_by', 'change_reason', 'changed_at')
    list_select_related = ('clinical_profile', 'changed_by')


@admin.register(ConsentRecord)
class ConsentRecordAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ('patient', 'term_version', 'accepted', 'accepted_at')
    list_select_related = ('patient', 'patient__user')
