from django.urls import path

from .views import (
    EmergencyDispatchView,
    TriageDetailView,
    TriageListView,
    TriageStartView,
)

app_name = 'triage'

urlpatterns = [
    path('triagem/', TriageListView.as_view(), name='list'),
    path('triagem/nova/', TriageStartView.as_view(), name='start'),
    path('triagem/<uuid:triage_id>/', TriageDetailView.as_view(), name='detail'),
    path('emergencia/<uuid:dispatch_id>/', EmergencyDispatchView.as_view(), name='emergency'),
]
