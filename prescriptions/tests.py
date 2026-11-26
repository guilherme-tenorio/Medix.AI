from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from care.models import ClinicalQueueItem
from patients.models import BloodType, Gender, SmsVerificationChallenge
from patients.services import PatientService
from professionals.services import ProfessionalService
from triage.models import EmergencyDispatch
from triage.services import TriageService

from .models import DigitalPrescription, PrescriptionReview
from .services import (
    ConflitoAlergiaCritico,
    DispensacaoRecusada,
    PermissaoReceitaNegada,
    PrescriptionReviewService,
    PrescriptionService,
)

User = get_user_model()


def _criar_paciente(cpf: str, email: str, full_name: str, phone: str, alergia: str = 'Dipirona'):
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
            'birth_date': date(1991, 6, 15),
            'gender': Gender.FEMALE,
            'password': 'SenhaForte!123',
            'consent_accepted': True,
            'has_disability': False,
            'disability_description': '',
            'blood_type': BloodType.A_POS,
            'has_allergy': bool(alergia),
            'allergy_description': alergia,
            'continuous_medications': '',
            'height_cm': 166,
            'weight_kg': Decimal('60.0'),
            'has_hypertension': False,
            'has_diabetes': False,
        },
        ip_address='127.0.0.1',
    )


class PrescriptionFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username='admin-rx',
            cpf='66677788800',
            email='admin.rx@example.com',
            password='AdminPassword!123',
            role=User.Role.ADMINISTRATOR,
            first_name='Admin',
            last_name='Rx',
        )
        cls.paciente_a = _criar_paciente('52998224725', 'rx.a@example.com', 'Fernanda Paciente', '11966661111', 'Dipirona')
        cls.paciente_b = _criar_paciente('11144477735', 'rx.b@example.com', 'Gabriel Outro', '11966662222', '')

        comprovante = SimpleUploadedFile('crm.pdf', b'%PDF-1.4 crm', content_type='application/pdf')
        cls.medico = ProfessionalService.cadastrar_profissional(
            cls.admin.id,
            {
                'full_name': 'Dr. Marcos Prescritor',
                'cpf': '39053344705',
                'email': 'marcos.rx@example.com',
                'birth_date': date(1982, 2, 10),
                'phone': '11955551111',
                'crm_number': '654321',
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

    def _criar_triagem_verde(self):
        sessao, _ = TriageService.iniciar_triagem(
            self.paciente_a.user_id,
            symptoms_description='Dor de cabeça leve desde cedo',
            symptom_onset='Hoje',
            pain_intensity=3,
            identity_confirmed=True,
        )
        sessao, _ = TriageService.concluir_triagem(
            self.paciente_a.user_id,
            sessao.pk,
            responses={'pergunta_1': 'Sem febre'},
        )
        return sessao

    def test_conflito_alergia_bloqueia_assinatura_de_receita(self):
        triagem = self._criar_triagem_verde()
        with self.assertRaises(ConflitoAlergiaCritico):
            PrescriptionReviewService.registrar_revisao(
                self.medico.user_id,
                triagem.pk,
                decision=PrescriptionReview.Decision.APPROVED,
                clinical_opinion='Tentativa de prescrever fármaco com alergia.',
                prescribed_medication='Dipirona 500mg',
                dosage_and_route='1 comprimido VO a cada 6h',
            )
        self.assertEqual(DigitalPrescription.objects.count(), 0)

    def test_aprovacao_emissao_pdf_sem_cpf_verificacao_publica_e_dispensacao_unica(self):
        triagem = self._criar_triagem_verde()
        revisao, receita, dispatch = PrescriptionReviewService.registrar_revisao(
            self.medico.user_id,
            triagem.pk,
            decision=PrescriptionReview.Decision.APPROVED_WITH_CHANGES,
            clinical_opinion='Substituído por paracetamol devido à alergia à dipirona.',
            prescribed_medication='Paracetamol 750mg',
            dosage_and_route='1 comprimido VO a cada 8h por 3 dias',
            instructions='Tomar após as refeições.',
        )
        self.assertIsNotNone(revisao)
        self.assertIsNotNone(receita)
        self.assertIsNone(dispatch)

        # PDF gerado não contém CPF do paciente
        pdf_bytes = PrescriptionService.gerar_pdf_receita(self.paciente_a.user_id, receita.pk)
        self.assertTrue(pdf_bytes.startswith(b'%PDF-1.4'))
        self.assertIn(b'Paracetamol 750mg', pdf_bytes)
        self.assertNotIn(b'52998224725', pdf_bytes)

        # Outro paciente não pode acessar receita alheia
        with self.assertRaises(PermissaoReceitaNegada):
            PrescriptionService.obter_receita_autorizada(self.paciente_b.user_id, receita.pk)

        # Página pública não revela CPF nem sintomas da triagem
        resp_pub = self.client.get(
            reverse('prescriptions:public_verify', kwargs={'token': receita.verification_token})
        )
        self.assertEqual(resp_pub.status_code, 200)
        self.assertNotContains(resp_pub, '52998224725')
        self.assertNotContains(resp_pub, 'Dor de cabeça leve desde cedo')
        self.assertContains(resp_pub, 'Paracetamol 750mg')

        # Primeira dispensação funciona
        disp = PrescriptionService.dispensar_receita(
            receita.verification_token,
            pharmacist_name='Luciana Farmacêutica',
            crf_number='98765',
            crf_uf='SP',
            pharmacy_cnpj='12.345.678/0001-90',
        )
        self.assertIsNotNone(disp.dispensed_at)

        # Segunda dispensação é recusada
        with self.assertRaises(DispensacaoRecusada):
            PrescriptionService.dispensar_receita(
                receita.verification_token,
                pharmacist_name='Outro Farmacêutico',
                crf_number='11111',
                crf_uf='SP',
                pharmacy_cnpj='12345678000190',
            )

    def test_rejeicao_encaminha_ao_chat_e_revogacao_impede_dispensacao(self):
        triagem = self._criar_triagem_verde()
        _, receita_rej, _ = PrescriptionReviewService.registrar_revisao(
            self.medico.user_id,
            triagem.pk,
            decision=PrescriptionReview.Decision.REJECTED_TO_CHAT,
            clinical_opinion='Necessita avaliação síncrona mais detalhada.',
        )
        self.assertIsNone(receita_rej)
        self.assertTrue(
            ClinicalQueueItem.objects.filter(
                triage_session=triagem,
                queue_type=ClinicalQueueItem.QueueType.SYNCHRONOUS_CHAT,
            ).exists()
        )

        # Aprovar outra e revogar antes da dispensação
        _, receita_2, _ = PrescriptionReviewService.registrar_revisao(
            self.medico.user_id,
            triagem.pk,
            decision=PrescriptionReview.Decision.APPROVED,
            clinical_opinion='Prescrição aprovada.',
            prescribed_medication='Paracetamol 500mg',
            dosage_and_route='1 comprimido VO se dor',
        )
        PrescriptionService.revogar_receita(
            self.medico.user_id,
            receita_2.pk,
            reason='Erro de posologia identificado após emissão.',
        )
        with self.assertRaises(DispensacaoRecusada):
            PrescriptionService.dispensar_receita(
                receita_2.verification_token,
                pharmacist_name='Farmacêutico Teste',
                crf_number='55555',
                crf_uf='SP',
                pharmacy_cnpj='12345678000190',
            )

    def test_reclassificacao_vermelha_na_revisao_dispara_emergencia(self):
        triagem = self._criar_triagem_verde()
        _, receita, dispatch = PrescriptionReviewService.registrar_revisao(
            self.medico.user_id,
            triagem.pk,
            decision=PrescriptionReview.Decision.RECLASSIFIED_TO_RED,
            clinical_opinion='Identificado sinal de alarme grave durante revisão.',
        )
        self.assertIsNone(receita)
        self.assertIsNotNone(dispatch)
        self.assertEqual(dispatch.trigger_source, EmergencyDispatch.TriggerSource.PRESCRIPTION_RECLASSIFICATION)
