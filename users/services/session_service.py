from django.contrib.auth import SESSION_KEY
from django.contrib.sessions.models import Session
from django.utils import timezone


class SessaoService:
    @staticmethod
    def revogar_sessoes_usuario(
        usuario_id: int,
        preservar_chave: str | None = None,
    ) -> int:
        chaves_revogadas = []
        sessoes = Session.objects.filter(expire_date__gt=timezone.now()).only(
            'session_key',
            'session_data',
        )
        for sessao in sessoes.iterator(chunk_size=500):
            dados = sessao.get_decoded()
            if (
                str(dados.get(SESSION_KEY, '')) == str(usuario_id)
                and sessao.session_key != preservar_chave
            ):
                chaves_revogadas.append(sessao.session_key)

        if not chaves_revogadas:
            return 0
        quantidade, _ = Session.objects.filter(session_key__in=chaves_revogadas).delete()
        return quantidade
