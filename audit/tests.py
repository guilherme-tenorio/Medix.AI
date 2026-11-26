from datetime import date

from django.test import TestCase
from django.urls import reverse

from audit.models import AdministrativeAction, AuditQuery, LoginAttempt
from audit.services import (
    AdminAccountService,
    AuditService,
    OperationalMonitoringService,
    PermissaoAuditoriaNegada,
    UltimoAdministradorAtivo,
)
from users.models import User


class AuditServiceAndViewTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin = User.objects.create_user(
            username='admin-audit',
            email='admin-audit@example.test',
            cpf='88888888888',
            role=User.Role.ADMINISTRATOR,
            is_staff=True,
            password='SenhaAdmin9!',
        )
        cls.paciente = User.objects.create_user(
            username='pac-audit',
            email='pac-audit@example.test',
            cpf='99999999999',
            role=User.Role.PATIENT,
            password='SenhaPaciente9!',
        )
        AuditService.registrar_tentativa_login(
            '99999999999',
            LoginAttempt.Result.SUCCESS,
            cls.paciente,
            User.Role.PATIENT,
        )
        AuditService.registrar_tentativa_login(
            '88888888888',
            LoginAttempt.Result.INVALID_CREDENTIALS,
            cls.admin,
            User.Role.ADMINISTRATOR,
        )

    def test_consulta_de_auditoria_filtra_por_identificador_e_registra_consulta(self) -> None:
        pagina = AuditService.listar_tentativas_acesso(
            actor_id=self.admin.pk,
            ip_address='127.0.0.1',
            occurred_from=None,
            occurred_until=None,
            identificador='999.999.999-99',
            papel=User.Role.PATIENT,
            resultado=LoginAttempt.Result.SUCCESS,
            pagina=1,
        )

        self.assertEqual(pagina.paginator.count, 1)
        consulta = AuditQuery.objects.get(actor=self.admin)
        self.assertEqual(consulta.ip_address, '127.0.0.1')
        self.assertNotEqual(consulta.identifier_fingerprint, '999.999.999-99')
        self.assertEqual(
            consulta.identifier_fingerprint,
            AuditService.fingerprint_identificador('999.999.999-99'),
        )

    def test_usuario_nao_administrador_nao_pode_consultar_auditoria(self) -> None:
        with self.assertRaises(PermissaoAuditoriaNegada):
            AuditService.listar_tentativas_acesso(
                actor_id=self.paciente.pk,
                ip_address=None,
                occurred_from=None,
                occurred_until=None,
                identificador='',
                papel='',
                resultado='',
                pagina=1,
            )

        self.client.force_login(self.paciente)
        resposta = self.client.get(reverse('audit:access_history'))
        self.assertEqual(resposta.status_code, 403)

    def test_admin_acessa_historico_de_acessos(self) -> None:
        self.client.force_login(self.admin)
        resposta = self.client.get(reverse('audit:access_history'))
        self.assertEqual(resposta.status_code, 200)

    def test_gestao_administradores_protege_ultimo_ativo_e_painel_operacional(self) -> None:
        # Não pode desativar o último administrador ativo
        with self.assertRaises(UltimoAdministradorAtivo):
            AdminAccountService.desativar_administrador(self.admin.pk, self.admin.pk, ip_address='127.0.0.1')

        # Cria segundo administrador com senha provisória e troca obrigatória
        novo_admin = AdminAccountService.criar_administrador(
            self.admin.pk,
            full_name='Mariana Admin Auxiliar',
            cpf='52998224725',
            email='mariana.admin@example.test',
            birth_date=date(1988, 5, 12),
            ip_address='127.0.0.1',
        )
        self.assertTrue(novo_admin.must_change_password)
        self.assertTrue(
            AdministrativeAction.objects.filter(
                actor=self.admin,
                target=novo_admin,
                action=AdministrativeAction.Action.ADMIN_CREATED,
            ).exists()
        )

        # Agora pode desativar o segundo administrador
        desativado = AdminAccountService.desativar_administrador(
            self.admin.pk,
            novo_admin.pk,
            ip_address='127.0.0.1',
        )
        self.assertFalse(desativado.is_active)

        # Métricas operacionais acessíveis só para administrador
        with self.assertRaises(PermissaoAuditoriaNegada):
            OperationalMonitoringService.obter_metricas_operacionais(self.paciente.pk)

        metricas = OperationalMonitoringService.obter_metricas_operacionais(self.admin.pk)
        self.assertEqual(metricas.chat_queue_waiting, 0)

        self.client.force_login(self.paciente)
        self.assertEqual(self.client.get(reverse('audit:monitoring')).status_code, 403)

        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('audit:monitoring')).status_code, 200)
        self.assertEqual(self.client.get(reverse('audit:admin_accounts')).status_code, 200)
