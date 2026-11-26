from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q

from users.services.session_service import SessaoService

if TYPE_CHECKING:
    from users.models import User


class UserService:
    @staticmethod
    def inativar_usuario(
        usuario_id: int,
        actor_id: int,
        ip_address: str | None = None,
    ) -> User:
        from audit.models import AdministrativeAction
        from audit.services import AuditService

        usuario_model = get_user_model()
        with transaction.atomic():
            administradores_ativos = list(
                usuario_model.objects.select_for_update().filter(
                    role='administrator',
                    is_active=True,
                    is_staff=True,
                ).order_by('pk')
            )
            usuario = usuario_model.objects.select_for_update().filter(
                pk=usuario_id,
                is_active=True,
            ).first()
            if not any(
                administrador.pk == actor_id
                for administrador in administradores_ativos
            ):
                raise PermissaoGestaoUsuariosNegada
            if usuario is None:
                raise UsuarioNaoEncontrado

            if usuario.role == 'administrator' and len(administradores_ativos) <= 1:
                raise UltimoAdministradorAtivo

            AuditService.registrar_acao_administrativa(
                actor_id,
                usuario.pk,
                AdministrativeAction.Action.USER_INACTIVATED,
                ip_address,
            )
            usuario.is_active = False
            usuario.save(update_fields=('is_active',))
            SessaoService.revogar_sessoes_usuario(usuario.pk)
            return usuario

    @staticmethod
    def buscar_bloqueado_para_atualizacao(identificador: str) -> User | None:
        if not transaction.get_connection().in_atomic_block:
            raise RuntimeError('A busca bloqueada exige uma transaÃ§Ã£o ativa.')
        usuario_model = get_user_model()
        return usuario_model.objects.select_for_update().filter(
            Q(cpf=identificador) | Q(email__iexact=identificador)
        ).first()

    @staticmethod
    def obter_ativo_por_id(usuario_id: int) -> User | None:
        usuario_model = get_user_model()
        return usuario_model.objects.filter(pk=usuario_id, is_active=True).first()

    @staticmethod
    def obter_por_id(usuario_id: int) -> User | None:
        usuario_model = get_user_model()
        return usuario_model.objects.filter(pk=usuario_id).first()

    @staticmethod
    def obter_para_atualizacao(usuario_id: int) -> User | None:
        usuario_model = get_user_model()
        return usuario_model.objects.select_for_update().filter(
            pk=usuario_id,
            is_active=True,
        ).first()

    @staticmethod
    def obter_paciente_ativo_por_email(email: str) -> User | None:
        usuario_model = get_user_model()
        return usuario_model.objects.filter(
            email__iexact=email,
            role='patient',
            is_active=True,
        ).first()


    @staticmethod
    def obter_paciente_ativo_por_id(usuario_id: int, *, bloquear: bool = False) -> User | None:
        usuario_model = get_user_model()
        consulta = usuario_model.objects.filter(
            pk=usuario_id,
            role='patient',
            is_active=True,
        )
        if bloquear:
            if not transaction.get_connection().in_atomic_block:
                raise RuntimeError('A busca bloqueada exige transacao ativa.')
            consulta = consulta.select_for_update()
        return consulta.first()

    @staticmethod
    def obter_admin_ativo_por_id(usuario_id: int) -> User | None:
        usuario_model = get_user_model()
        return usuario_model.objects.filter(
            pk=usuario_id,
            role='administrator',
            is_active=True,
            is_staff=True,
        ).first()

    @staticmethod
    def listar_administradores_para_redefinicao(actor_id: int) -> list[tuple[str, str]]:
        usuario_model = get_user_model()
        if UserService.obter_admin_ativo_por_id(actor_id) is None:
            raise PermissaoGestaoUsuariosNegada

        administradores = usuario_model.objects.filter(
            role='administrator',
            is_active=True,
            is_staff=True,
        ).exclude(pk=actor_id).order_by('last_name', 'first_name', 'email')
        escolhas = []
        for pk, primeiro_nome, sobrenome, email in administradores.values_list(
            'pk', 'first_name', 'last_name', 'email'
        ):
            nome_completo = f'{primeiro_nome} {sobrenome}'.strip()
            escolhas.append((str(pk), f'{nome_completo or email} — {email}'))
        return escolhas

    @staticmethod
    def listar_profissionais_para_senha_provisoria(actor_id: int) -> list[tuple[str, str]]:
        usuario_model = get_user_model()
        if UserService.obter_admin_ativo_por_id(actor_id) is None:
            raise PermissaoGestaoUsuariosNegada

        profissionais = usuario_model.objects.filter(
            role='professional',
            is_active=True,
        ).order_by('last_name', 'first_name', 'email')
        escolhas = []
        for pk, primeiro_nome, sobrenome, email in profissionais.values_list(
            'pk', 'first_name', 'last_name', 'email'
        ):
            nome_completo = f'{primeiro_nome} {sobrenome}'.strip()
            escolhas.append((str(pk), f'{nome_completo or email} — {email}'))
        return escolhas

    @staticmethod
    def obter_profissional_ativo_por_id(
        usuario_id: int,
        *,
        bloquear: bool = False,
    ) -> User | None:
        usuario_model = get_user_model()
        consulta = usuario_model.objects.filter(
            pk=usuario_id,
            role='professional',
            is_active=True,
        )
        if bloquear:
            if not transaction.get_connection().in_atomic_block:
                raise RuntimeError('A busca bloqueada exige transação ativa.')
            consulta = consulta.select_for_update()
        return consulta.first()

    @staticmethod
    def cpf_existe(cpf: str) -> bool:
        usuario_model = get_user_model()
        return usuario_model.objects.filter(cpf=cpf).exists()

    @staticmethod
    def email_existe(email: str) -> bool:
        usuario_model = get_user_model()
        return usuario_model.objects.filter(email__iexact=email).exists()

    @staticmethod
    def criar_usuario_paciente(
        *,
        cpf: str,
        email: str,
        full_name: str,
        password: str,
    ) -> User:
        from django.contrib.auth.password_validation import validate_password

        usuario_model = get_user_model()
        partes = full_name.strip().split(None, 1)
        first_name = partes[0]
        last_name = partes[1] if len(partes) > 1 else ''
        usuario = usuario_model(
            username=cpf,
            email=email.strip().casefold(),
            cpf=cpf,
            role='patient',
            first_name=first_name,
            last_name=last_name,
            is_active=True,
        )
        validate_password(password, usuario)
        usuario.set_password(password)
        usuario.save()
        return usuario

    @staticmethod
    def criar_usuario_profissional(
        *,
        cpf: str,
        email: str,
        full_name: str,
        password: str,
        is_active: bool = False,
        must_change_password: bool = True,
    ) -> User:
        usuario_model = get_user_model()
        partes = full_name.strip().split(None, 1)
        first_name = partes[0]
        last_name = partes[1] if len(partes) > 1 else ''
        usuario = usuario_model(
            username=cpf,
            email=email.strip().casefold(),
            cpf=cpf,
            role='professional',
            first_name=first_name,
            last_name=last_name,
            is_active=is_active,
            must_change_password=must_change_password,
        )
        usuario.set_password(password)
        usuario.save()
        return usuario

    @staticmethod
    def ativar_usuario(usuario_id: int) -> User:
        usuario_model = get_user_model()
        usuario = usuario_model.objects.filter(pk=usuario_id).first()
        if usuario is None:
            raise UsuarioNaoEncontrado
        if not usuario.is_active:
            usuario.is_active = True
            usuario.save(update_fields=('is_active',))
        return usuario

    @staticmethod
    def obter_conta_para_redefinicao(
        usuario_id: int,
        *,
        bloquear: bool = False,
    ) -> User | None:
        usuario_model = get_user_model()
        consulta = usuario_model.objects.filter(pk=usuario_id, is_active=True).filter(
            Q(role='patient') | Q(role='administrator', is_staff=True)
        )
        if bloquear:
            if not transaction.get_connection().in_atomic_block:
                raise RuntimeError('A busca bloqueada exige transação ativa.')
            consulta = consulta.select_for_update()
        return consulta.first()

    @staticmethod
    def cpf_existe(cpf: str) -> bool:
        usuario_model = get_user_model()
        return usuario_model.objects.filter(cpf=cpf).exists()

    @staticmethod
    def email_existe(email: str) -> bool:
        usuario_model = get_user_model()
        return usuario_model.objects.filter(email__iexact=email).exists()

    @staticmethod
    def criar_usuario_paciente(
        *,
        cpf: str,
        email: str,
        full_name: str,
        password: str,
    ) -> User:
        from django.contrib.auth.password_validation import validate_password

        usuario_model = get_user_model()
        partes = full_name.strip().split(None, 1)
        first_name = partes[0]
        last_name = partes[1] if len(partes) > 1 else ''
        usuario = usuario_model(
            username=cpf,
            email=email.strip().casefold(),
            cpf=cpf,
            role='patient',
            first_name=first_name,
            last_name=last_name,
            is_active=True,
        )
        validate_password(password, usuario)
        usuario.set_password(password)
        usuario.save()
        return usuario

    @staticmethod
    def criar_usuario_profissional(
        *,
        cpf: str,
        email: str,
        full_name: str,
        password: str,
        is_active: bool = False,
        must_change_password: bool = True,
    ) -> User:
        usuario_model = get_user_model()
        partes = full_name.strip().split(None, 1)
        first_name = partes[0]
        last_name = partes[1] if len(partes) > 1 else ''
        usuario = usuario_model(
            username=cpf,
            email=email.strip().casefold(),
            cpf=cpf,
            role='professional',
            first_name=first_name,
            last_name=last_name,
            is_active=is_active,
            must_change_password=must_change_password,
        )
        usuario.set_password(password)
        usuario.save()
        return usuario

    @staticmethod
    def ativar_usuario(usuario_id: int) -> User:
        usuario_model = get_user_model()
        usuario = usuario_model.objects.filter(pk=usuario_id).first()
        if usuario is None:
            raise UsuarioNaoEncontrado
        if not usuario.is_active:
            usuario.is_active = True
            usuario.save(update_fields=('is_active',))
        return usuario


class UsuarioNaoEncontrado(Exception):
    pass


class UltimoAdministradorAtivo(Exception):
    pass


class PermissaoGestaoUsuariosNegada(Exception):
    pass
