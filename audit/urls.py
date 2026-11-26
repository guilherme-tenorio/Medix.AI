from django.urls import path

from .views import (
    DesativarAdministradorView,
    GestaoAdministradoresView,
    HistoricoAcessosView,
    PainelOperacionalView,
)

app_name = 'audit'

urlpatterns = [
    path('admin/auditoria/acessos/', HistoricoAcessosView.as_view(), name='access_history'),
    path('admin/operacao/monitoramento/', PainelOperacionalView.as_view(), name='monitoring'),
    path('admin/contas/administradores/', GestaoAdministradoresView.as_view(), name='admin_accounts'),
    path(
        'admin/contas/administradores/<int:admin_id>/desativar/',
        DesativarAdministradorView.as_view(),
        name='deactivate_admin',
    ),
]
