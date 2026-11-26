from django.contrib import admin

from .models import DigitalPrescription, PrescriptionDispensation, PrescriptionReview


@admin.register(PrescriptionReview)
class PrescriptionReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'triage_session', 'professional', 'decision', 'allergy_conflict_detected', 'created_at')
    list_filter = ('decision', 'allergy_conflict_detected')
    readonly_fields = (
        'id',
        'triage_session',
        'queue_item',
        'professional',
        'decision',
        'clinical_opinion',
        'allergy_conflict_detected',
        'allergy_conflict_details',
        'prescribed_medication',
        'dosage_and_route',
        'instructions',
        'created_at',
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DigitalPrescription)
class DigitalPrescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'medication_name', 'prescriber', 'status', 'issued_at', 'valid_until')
    list_filter = ('status', 'icp_signature_valid')
    readonly_fields = (
        'id',
        'review',
        'triage_session',
        'patient',
        'dependent',
        'prescriber',
        'medication_name',
        'dosage_and_route',
        'instructions',
        'icp_signature_hash',
        'icp_signature_valid',
        'verification_token',
        'status',
        'issued_at',
        'valid_until',
        'revoked_at',
        'revocation_reason',
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PrescriptionDispensation)
class PrescriptionDispensationAdmin(admin.ModelAdmin):
    list_display = ('id', 'prescription', 'pharmacist_name', 'crf_number', 'crf_uf', 'pharmacy_cnpj', 'dispensed_at')
    readonly_fields = ('id', 'prescription', 'pharmacist_name', 'crf_number', 'crf_uf', 'pharmacy_cnpj', 'dispensed_at')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
