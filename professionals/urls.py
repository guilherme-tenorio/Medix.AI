from django.urls import path

from .views import (
    AdminGestaoMedicosView,
    AdminHomologarMedicoView,
    AdminSuspenderMedicoView,
    DisponibilidadeMedicoView,
)

app_name = 'professionals'

urlpatterns = [
    path('admin/medicos/', AdminGestaoMedicosView.as_view(), name='admin_list'),
    path(
        'admin/medicos/<int:professional_id>/homologar/',
        AdminHomologarMedicoView.as_view(),
        name='admin_homologate',
    ),
    path(
        'admin/medicos/<int:professional_id>/suspender/',
        AdminSuspenderMedicoView.as_view(),
        name='admin_suspend',
    ),
    path('medico/disponibilidade/', DisponibilidadeMedicoView.as_view(), name='availability'),
]
