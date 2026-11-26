from django.contrib.auth import logout
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse


class PasswordChangeRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        usuario = request.user
        if not usuario.is_authenticated:
            return None

        if not usuario.is_active:
            logout(request)
            return HttpResponseForbidden('Esta conta está inativa.')

        if not usuario.must_change_password:
            return None

        nomes_permitidos = {'password_change', 'logout'}
        if request.resolver_match and request.resolver_match.url_name in nomes_permitidos:
            return None

        return redirect(reverse('users:password_change'))
