from django.urls import path

from .views import (
    PatientPrescriptionListView,
    PrescriptionDetailView,
    PrescriptionPdfDownloadView,
    PrescriptionReviewView,
    PrescriptionRevokeView,
    PublicPrescriptionVerifyView,
)

app_name = 'prescriptions'

urlpatterns = [
    path('receitas/', PatientPrescriptionListView.as_view(), name='list'),
    path('receitas/<uuid:prescription_id>/', PrescriptionDetailView.as_view(), name='detail'),
    path('receitas/<uuid:prescription_id>/pdf/', PrescriptionPdfDownloadView.as_view(), name='pdf'),
    path('receitas/<uuid:prescription_id>/revogar/', PrescriptionRevokeView.as_view(), name='revoke'),
    path('medico/revisao/<uuid:triage_id>/', PrescriptionReviewView.as_view(), name='review'),
    path('receitas/verificar/<str:token>/', PublicPrescriptionVerifyView.as_view(), name='public_verify'),
]
