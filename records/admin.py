from django.contrib import admin

from .models import MedicalRecordAccessLog, MedicalRecordAmendment


@admin.register(MedicalRecordAmendment)
class MedicalRecordAmendmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'target_event_type', 'target_event_id', 'recorded_by', 'created_at')
    list_filter = ('target_event_type',)
    readonly_fields = (
        'id',
        'patient',
        'dependent',
        'target_event_type',
        'target_event_id',
        'recorded_by',
        'amendment_text',
        'created_at',
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MedicalRecordAccessLog)
class MedicalRecordAccessLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'actor', 'crm_snapshot', 'allowed', 'ip_address', 'accessed_at')
    list_filter = ('allowed',)
    readonly_fields = (
        'id',
        'actor',
        'crm_snapshot',
        'patient',
        'dependent',
        'allowed',
        'reason',
        'ip_address',
        'accessed_at',
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
