from django.urls import path

from .views import (
    AdministratorLoginView,
    EmitirSenhaProvisoriaMedicoView,
    LogoutView,
    PatientLoginView,
    PatientPortalView,
    ProfessionalLoginView,
    ProfessionalPortalView,
    RedefinirSenhaConcluidoView,
    RedefinirSenhaEnviadoView,
    RedefinirSenhaView,
    RedefinicaoAdministradorEnviadaView,
    RedirecionarTrocaSenhaAdminView,
    SolicitarRedefinicaoAdministradorView,
    SolicitarRedefinicaoSenhaView,
    SenhaProvisoriaMedicoEnviadaView,
    TrocarSenhaView,
)

app_name = 'users'

urlpatterns = [
    path('login/', PatientLoginView.as_view(), name='patient_login'),
    path('paciente/', PatientPortalView.as_view(), name='patient_portal'),
    path('medico/login/', ProfessionalLoginView.as_view(), name='professional_login'),
    path('medico/', ProfessionalPortalView.as_view(), name='professional_portal'),
    path('admin/login/', AdministratorLoginView.as_view(), name='administrator_login'),
    path('admin/password_change/', RedirecionarTrocaSenhaAdminView.as_view(), name='admin_password_change'),
    path(
        'admin/seguranca/redefinir-senha/',
        SolicitarRedefinicaoAdministradorView.as_view(),
        name='admin_password_reset_request',
    ),
    path(
        'admin/seguranca/redefinir-senha/enviado/',
        RedefinicaoAdministradorEnviadaView.as_view(),
        name='admin_password_reset_sent',
    ),
    path(
        'admin/seguranca/senha-provisoria-medico/',
        EmitirSenhaProvisoriaMedicoView.as_view(),
        name='professional_temporary_password',
    ),
    path(
        'admin/seguranca/senha-provisoria-medico/enviada/',
        SenhaProvisoriaMedicoEnviadaView.as_view(),
        name='professional_temporary_password_sent',
    ),
    path('sair/', LogoutView.as_view(), name='logout'),
    path('senha/alterar/', TrocarSenhaView.as_view(), name='password_change'),
    path('senha/esqueci/', SolicitarRedefinicaoSenhaView.as_view(), name='password_reset_request'),
    path('senha/enviada/', RedefinirSenhaEnviadoView.as_view(), name='password_reset_sent'),
    path(
        'senha/redefinir/<uidb64>/<token>/',
        RedefinirSenhaView.as_view(),
        name='password_reset_confirm',
    ),
    path('senha/redefinida/', RedefinirSenhaConcluidoView.as_view(), name='password_reset_complete'),
]
