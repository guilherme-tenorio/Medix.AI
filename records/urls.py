from django.urls import path

from .views import MedicalRecordTimelineView

app_name = 'records'

urlpatterns = [
    path('prontuario/', MedicalRecordTimelineView.as_view(), name='timeline'),
]
