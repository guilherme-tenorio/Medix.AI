from uuid import UUID

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from .services import NotificacaoService, PermissaoNotificacaoNegada


class NotificationCenterView(LoginRequiredMixin, View):
    template_name = 'notifications/center.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        notificacoes = NotificacaoService.listar_central_usuario(request.user.id)
        preferencias = NotificacaoService.obter_ou_criar_preferencias(request.user.id)
        return render(
            request,
            self.template_name,
            {
                'notificacoes': notificacoes,
                'preferencias': preferencias,
            },
        )


class NotificationPreferencesUpdateView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest) -> HttpResponse:
        NotificacaoService.atualizar_preferencias(
            request.user.id,
            {
                'allow_push': 'allow_push' in request.POST,
                'allow_sms': 'allow_sms' in request.POST,
                'allow_email': 'allow_email' in request.POST,
                'allow_whatsapp': 'allow_whatsapp' in request.POST,
                'allow_informative': 'allow_informative' in request.POST,
            },
        )
        messages.success(request, 'Preferências de notificação atualizadas.')
        return redirect(reverse('notifications:center'))


class NotificationMarkReadView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, notification_id: UUID) -> HttpResponse:
        try:
            NotificacaoService.marcar_como_lida(request.user.id, notification_id)
        except PermissaoNotificacaoNegada:
            raise PermissionDenied from None
        return redirect(reverse('notifications:center'))


class NotificationClearInformativeView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest) -> HttpResponse:
        NotificacaoService.limpar_informativas_lidas(request.user.id)
        messages.success(request, 'Notificações informativas lidas removidas da central.')
        return redirect(reverse('notifications:center'))
