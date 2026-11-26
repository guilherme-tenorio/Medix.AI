from django.contrib import admin

from .models import EmergencyDispatch, TriageSession


@admin.register(TriageSession)
class TriageSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'dependent', 'risk_color', 'routing_destination', 'is_completed', 'created_at')
    list_filter = ('risk_color', 'routing_destination', 'is_completed')
    readonly_fields = (
        'id',
        'patient',
        'dependent',
        'initiated_by',
        'symptoms_description',
        'symptom_onset',
        'pain_intensity',
        'answers',
        'ai_summary',
        'ai_guidance_text',
        'suggested_medication',
        'red_flags_detected',
        'risk_color',
        'routing_destination',
        'is_completed',
        'completed_at',
        'created_at',
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EmergencyDispatch)
class EmergencyDispatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'triage_session', 'trigger_source', 'created_at')
    list_filter = ('trigger_source',)
    readonly_fields = (
        'id',
        'triage_session',
        'trigger_source',
        'alert_message',
        'patient_summary',
        'latitude',
        'longitude',
        'manual_location_query',
        'created_at',
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
