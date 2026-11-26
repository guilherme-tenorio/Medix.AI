from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from patients.models import BloodType, Gender, SmsVerificationChallenge
from patients.services import PatientService
from professionals.models import ProfessionalProfile
from professionals.services import ProfessionalService
from triage.models import EmergencyDispatch, TriageSession
from triage.services import TriageService

from .models import ChatAttachment, ClinicalOutcome, ClinicalQueueItem
from .services import (
    ChatEncerrado,
    ChatService,
    PermissaoAtendimentoNegada,
    QueueService,
)

User = get_user_model()


def _criar_paciente(cpf: str, email: str, full_name: str, phone: str):
    SmsVerificationChallenge.objects.create(
        phone=phone,
        code_hash=make_password('123456'),
        expires_at=timezone.now() + timedelta(minutes=10),
    )
    return PatientService.cadastrar_titular(
        {
            'full_name': full_name,
            'cpf': cpf,
            'email': email,
            'phone': phone,
            'sms_code': '123456',
            'birth_date': date(1992, 4, 20),
            'gender': Gender.MALE,
            'password': 'SenhaForte!123',
            'consent_accepted': True,
            'has_disability': False,
            'disability_description': '',
            'blood_type': BloodType.B_POS,
            'has_allergy': True,
            'allergy_description': 'Penicilina',
            'continuous_medications': '',
            'height_cm': 178,
            'weight_kg': Decimal('75.0'),
            'has_hypertension': False,
            'has_diabetes': False,
        },
        ip_address='127.0.0.1',
    )


class ClinicalQueueAndChatTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username='admin-care',
            cpf='77788899900',
            email='admin.care@example.com',
            password='AdminPassword!123',
            role=User.Role.ADMINISTRATOR,
            first_name='Admin',
            last_name='Care',
        )
        cls.paciente_a = _criar_paciente('52998224725', 'care.a@example.com', 'Carlos Paciente', '11988881111')
        cls.paciente_b = _criar_paciente('11144477735', 'care.b@example.com', 'Daniela Outra', '11988882222')

        comprovante = SimpleUploadedFile('crm.pdf', b'%PDF-1.4 crm', content_type='application/pdf')
        cls.medico = ProfessionalService.cadastrar_profissional(
            cls.admin.id,
            {
                'full_name': 'Dra. Helena Clinica',
                'cpf': '39053344705',
                'email': 'helena.medico@example.com',
                'birth_date': date(1985, 8, 12),
                'phone': '11977771111',
                'crm_number': '123456',
                'crm_uf': 'SP',
            },
            crm_document=comprovante,
        )
        ProfessionalService.homologar_profissional(
            cls.admin.id,
            cls.medico.pk,
            crm_regular=True,
            icp_brasil_active=True,
        )
        cls.medico.refresh_from_db()
        cls.medico.user.must_change_password = False
        cls.medico.user.save(update_fields=('must_change_password',))
        ProfessionalService.alterar_disponibilidade(
            cls.medico.user_id,
            ProfessionalProfile.Availability.ONLINE,
        )

    def _criar_triagem_concluida(self, paciente, sintomas: str, intensidade: int):
        sessao, _ = TriageService.iniciar_triagem(
            paciente.user_id,
            symptoms_description=sintomas,
            symptom_onset='Hoje',
            pain_intensity=intensidade,
            identity_confirmed=True,
        )
        sessao, _ = TriageService.concluir_triagem(
            paciente.user_id,
            sessao.pk,
            responses={'pergunta_1': 'Sem melhora'},
        )
        return sessao

    def test_fila_ordena_por_gravidade_e_tempo_e_anonimiza_pre_aceite(self):
        t_amarela_1 = self._criar_triagem_concluida(self.paciente_a, 'Febre persistente moderada', 5)
        t_laranja = self._criar_triagem_concluida(self.paciente_b, 'Dor abdominal forte agora', 8)
        t_amarela_2 = self._criar_triagem_concluida(self.paciente_a, 'Tosse persistente com febre', 5)

        q1 = QueueService.enfileirar_triagem(t_amarela_1)
        q2 = QueueService.enfileirar_triagem(t_laranja)
        q3 = QueueService.enfileirar_triagem(t_amarela_2)

        # Ajustar enqueued_at para testar desempate dentro da mesma cor
        ClinicalQueueItem.objects.filter(pk=q1.pk).update(enqueued_at=timezone.now() - timedelta(minutes=20))
        ClinicalQueueItem.objects.filter(pk=q3.pk).update(enqueued_at=timezone.now() - timedelta(minutes=5))

        lista = QueueService.listar_fila_anonimizada(
            self.medico.user_id,
            queue_type=ClinicalQueueItem.QueueType.SYNCHRONOUS_CHAT,
        )
        self.assertEqual([e.queue_item_id for e in lista], [q2.pk, q1.pk, q3.pk])
        # Nome completo não é exposto antes do aceite
        self.assertEqual(lista[0].abbreviated_name, 'D. O.')
        self.assertNotIn('Daniela', lista[0].abbreviated_name)

    def test_caso_vermelho_nunca_entra_em_fila_virtual(self):
        t_vermelha, _ = TriageService.iniciar_triagem(
            self.paciente_a.user_id,
            symptoms_description='Dor no peito intensa',
            symptom_onset='Agora',
            pain_intensity=9,
            identity_confirmed=True,
        )
        with self.assertRaises(ValidationError):
            QueueService.enfileirar_triagem(t_vermelha)

    def test_fluxo_chat_anexo_audio_stt_isolamento_e_reclassificacao_vermelha(self):
        t_laranja = self._criar_triagem_concluida(self.paciente_a, 'Dor abdominal forte', 8)
        item = QueueService.enfileirar_triagem(t_laranja)
        item, sessao = QueueService.aceitar_chamado(self.medico.user_id, item.pk)
        self.assertEqual(item.status, ClinicalQueueItem.Status.IN_PROGRESS)
        self.assertIsNotNone(sessao)

        # Outro paciente não pode acessar o chat
        with self.assertRaises(PermissaoAtendimentoNegada):
            ChatService.obter_sessao_autorizada(self.paciente_b.user_id, sessao.pk)

        # Resumo clínico inclui alergia
        resumo = ChatService.obter_resumo_clinico_para_chat(self.medico.user_id, sessao.pk)
        self.assertEqual(resumo['alergias'], 'Penicilina')

        # Anexo inválido recusado
        arquivo_invalido = SimpleUploadedFile('script.exe', b'MZ', content_type='application/octet-stream')
        with self.assertRaises(ValidationError):
            ChatService.enviar_mensagem(
                self.paciente_a.user_id,
                sessao.pk,
                content='Segue arquivo',
                attachment=arquivo_invalido,
            )

        # Anexo PDF válido aceito
        pdf_valido = SimpleUploadedFile('exame.pdf', b'%PDF-1.4 exame', content_type='application/pdf')
        msg_anexo = ChatService.enviar_mensagem(
            self.paciente_a.user_id,
            sessao.pk,
            content='Segue exame em PDF',
            attachment=pdf_valido,
        )
        self.assertEqual(ChatAttachment.objects.filter(message=msg_anexo).count(), 1)

        # Áudio transcrito via STT sem persistir áudio bruto
        msg_audio = ChatService.enviar_mensagem(
            self.paciente_a.user_id,
            sessao.pk,
            audio_bytes=b'fake-audio-pcm',
            audio_duration_seconds=30,
        )
        self.assertTrue(msg_audio.is_from_audio_transcription)

        # Reclassificação para Vermelho dispara EmergencyDispatch imediatamente e torna chat imutável
        desfecho, dispatch = ChatService.encerrar_sessao(
            self.medico.user_id,
            sessao.pk,
            outcome_type=ClinicalOutcome.OutcomeType.EMERGENCY_RECLASSIFICATION,
            summary_and_conduct='Paciente evoluiu com sinais de alarme. Encaminhado imediatamente.',
            reclassified_to_red=True,
        )
        self.assertTrue(desfecho.reclassified_to_red)
        self.assertIsNotNone(dispatch)
        self.assertEqual(dispatch.trigger_source, EmergencyDispatch.TriggerSource.CHAT_RECLASSIFICATION)

        with self.assertRaises(ChatEncerrado):
            ChatService.enviar_mensagem(self.paciente_a.user_id, sessao.pk, content='Nova mensagem')

    def test_rotas_fila_e_chat_protegidas(self):
        resp_anon = self.client.get(reverse('care:queue_dashboard'))
        self.assertEqual(resp_anon.status_code, 302)

        self.client.force_login(self.paciente_a.user)
        resp_pac = self.client.get(reverse('care:queue_dashboard'))
        self.assertEqual(resp_pac.status_code, 403)

        self.client.force_login(self.medico.user)
        resp_med = self.client.get(reverse('care:queue_dashboard'))
        self.assertEqual(resp_med.status_code, 200)
