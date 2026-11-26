from django.urls import path

from .views import (
    CadastrarDependenteView,
    CadastroPacienteView,
    DesativarDependenteView,
    EditarDependenteView,
    ListaDependentesView,
    PerfilPacienteView,
    SolicitarCodigoSmsView,
)

app_name = 'patients'

urlpatterns = [
    path('cadastro/', CadastroPacienteView.as_view(), name='register'),
    path('cadastro/sms/', SolicitarCodigoSmsView.as_view(), name='request_sms_code'),
    path('paciente/perfil/', PerfilPacienteView.as_view(), name='profile'),
    path('paciente/dependentes/', ListaDependentesView.as_view(), name='dependents_list'),
    path('paciente/dependentes/novo/', CadastrarDependenteView.as_view(), name='dependent_create'),
    path(
        'paciente/dependentes/<int:dependent_id>/editar/',
        EditarDependenteView.as_view(),
        name='dependent_edit',
    ),
    path(
        'paciente/dependentes/<int:dependent_id>/desativar/',
        DesativarDependenteView.as_view(),
        name='dependent_deactivate',
    ),
]
