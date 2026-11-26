from django.urls import path

from .views import (
    NotificationCenterView,
    NotificationClearInformativeView,
    NotificationMarkReadView,
    NotificationPreferencesUpdateView,
)

app_name = 'notifications'

urlpatterns = [
    path('notificacoes/', NotificationCenterView.as_view(), name='center'),
    path('notificacoes/preferencias/', NotificationPreferencesUpdateView.as_view(), name='preferences'),
    path('notificacoes/<uuid:notification_id>/lida/', NotificationMarkReadView.as_view(), name='mark_read'),
    path('notificacoes/limpar/', NotificationClearInformativeView.as_view(), name='clear_informative'),
]
