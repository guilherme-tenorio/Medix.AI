from django.contrib.auth.backends import ModelBackend

from .models import User
from .services.authentication_service import AutenticacaoService


class CpfEmailBackend(ModelBackend):
    def authenticate(
        self,
        request,
        username: str | None = None,
        password: str | None = None,
        **kwargs,
    ) -> User | None:
        identificador = kwargs.get('identifier', username)
        if identificador is None or password is None:
            return None
        return AutenticacaoService.autenticar(identificador, password)

    def get_user(self, user_id: int) -> User | None:
        return AutenticacaoService.obter_usuario_por_id(user_id)
