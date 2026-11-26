from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from patients.models import BloodType, Dependent, Gender
from patients.services import DependentService, PatientService, SmsVerificationService

from .models import EmergencyDispatch, TriageSession
from .services import (
    EmergencyService,
    ManchesterClassifierService,
    PermissaoTriagemNegada,
    TriageService,
    TriagemImutavel,
    TriagemIndisponivel,
)


def _criar_paciente_completo(cpf: str, email: str, full_name: str, phone: str):
    SmsVerificationService.enviar_codigo(phone)
    from patients.models import SmsVerificationChallenge

    SmsVerificationChallenge.objects.filter(phone=phone).delete()
    from django.contrib.auth.hashers import make_password
    from django.utils import timezone
    from datetime import timedelta

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
            'birth_date': date(1990, 5, 10),
            'gender': Gender.FEMALE,
            'password': 'SenhaForte!123',
            'consent_accepted': True,
            'has_disability': False,
            'disability_description': '',
            'blood_type': BloodType.O_POS,
            'has_allergy': True,
            'allergy_description': 'Dipirona',
            'continuous_medications': '',
            'height_cm': 165,
            'weight_kg': Decimal('62.0'),
            'has_hypertension': False,
            'has_diabetes': False,
        },
        ip_address='127.0.0.1',
    )


class TriageAndEmergencyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.paciente_a = _criar_paciente_completo(
            cpf='52998224725',
            email='triagem.a@example.com',
            full_name='Ana Triagem',
            phone='11999991111',
        )
        cls.paciente_b = _criar_paciente_completo(
            cpf='11144477735',
            email='triagem.b@example.com',
            full_name='Bruno Outro',
            phone='11999992222',
        )
        cls.dependente_a = DependentService.cadastrar_dependente(
            cls.paciente_a.user_id,
            {
                'full_name': 'Lucas Dependente',
                'cpf': '39053344705',
                'birth_date': date(2016, 3, 15),
                'gender': Gender.MALE,
                'legal_relationship': Dependent.LegalRelationship.CHILD,
                'has_disability': False,
                'disability_description': '',
                'blood_type': BloodType.A_POS,
                'has_allergy': False,
                'allergy_description': '',
                'continuous_medications': '',
                'height_cm': 130,
                'weight_kg': Decimal('30.0'),
                'has_hypertension': False,
                'has_diabetes': False,
            },
        )

    def test_payload_desidentificado_nao_contem_nome_nem_cpf(self):
        sujeito = TriageService.obter_alvo_autorizado(self.paciente_a.user_id)
        payload = TriageService.montar_payload_desidentificado(
            sujeito,
            symptoms_description='Dor leve na garganta',
            symptom_onset='Ontem',
            pain_intensity=2,
        )
        dados = payload.to_dict()
        texto_json = str(dados)
        self.assertNotIn('Ana Triagem', texto_json)
        self.assertNotIn('52998224725', texto_json)
        self.assertEqual(dados['age_group'], 'adulto (18-59 anos)')

    def test_confirmacao_identidade_obrigatoria_e_isolamento_dependente(self):
        with self.assertRaises(ValidationError):
            TriageService.iniciar_triagem(
                self.paciente_a.user_id,
                symptoms_description='Coriza leve há 1 dia',
                symptom_onset='1 dia',
                pain_intensity=1,
                identity_confirmed=False,
            )

        with self.assertRaises(PermissaoTriagemNegada):
            TriageService.iniciar_triagem(
                self.paciente_b.user_id,
                symptoms_description='Febre no dependente alheio',
                symptom_onset='Hoje',
                pain_intensity=4,
                dependent_id=self.dependente_a.pk,
                identity_confirmed=True,
            )

    def test_cinco_cores_manchester_e_encaminhamentos_e_imutabilidade(self):
        # Branca sem medicação -> orientação da IA
        r_branca = ManchesterClassifierService.classificar(
            symptoms_description='Coriza leve sem febre',
            answers={},
            pain_intensity=1,
            suggested_medication='',
        )
        self.assertEqual(r_branca.risk_color, TriageSession.RiskColor.WHITE)
        self.assertEqual(r_branca.routing_destination, TriageSession.RoutingDestination.AI_GUIDANCE)

        # Verde com sugestão medicamentosa -> fila de revisão médica
        r_verde = ManchesterClassifierService.classificar(
            symptoms_description='Dor de cabeça leve',
            answers={},
            pain_intensity=3,
            suggested_medication='Analgésico simples',
        )
        self.assertEqual(r_verde.risk_color, TriageSession.RiskColor.GREEN)
        self.assertEqual(r_verde.routing_destination, TriageSession.RoutingDestination.PRESCRIPTION_REVIEW)

        # Amarela -> chat síncrono
        r_amarela = ManchesterClassifierService.classificar(
            symptoms_description='Febre moderada e dor persistente',
            answers={},
            pain_intensity=5,
        )
        self.assertEqual(r_amarela.risk_color, TriageSession.RiskColor.YELLOW)
        self.assertEqual(r_amarela.routing_destination, TriageSession.RoutingDestination.SYNCHRONOUS_CHAT)

        # Laranja -> chat síncrono
        r_laranja = ManchesterClassifierService.classificar(
            symptoms_description='Dor abdominal forte',
            answers={},
            pain_intensity=8,
        )
        self.assertEqual(r_laranja.risk_color, TriageSession.RiskColor.ORANGE)
        self.assertEqual(r_laranja.routing_destination, TriageSession.RoutingDestination.SYNCHRONOUS_CHAT)

        # Fluxo completo e imutabilidade após conclusão
        sessao, dispatch = TriageService.iniciar_triagem(
            self.paciente_a.user_id,
            symptoms_description='Dor de cabeça leve desde cedo',
            symptom_onset='Hoje de manhã',
            pain_intensity=3,
            identity_confirmed=True,
        )
        self.assertIsNone(dispatch)
        sessao, dispatch = TriageService.concluir_triagem(
            self.paciente_a.user_id,
            sessao.pk,
            responses={'pergunta_1': 'Sem piora ao esforço'},
        )
        self.assertTrue(sessao.is_completed)
        self.assertEqual(sessao.risk_color, TriageSession.RiskColor.GREEN)
        self.assertEqual(sessao.routing_destination, TriageSession.RoutingDestination.PRESCRIPTION_REVIEW)

        with self.assertRaises(TriagemImutavel):
            TriageService.concluir_triagem(
                self.paciente_a.user_id,
                sessao.pk,
                responses={'pergunta_1': 'Tentativa de alteração'},
            )

    def test_red_flag_dispara_emergencia_imediata_com_gps_e_busca_manual(self):
        sessao, dispatch = TriageService.iniciar_triagem(
            self.paciente_a.user_id,
            symptoms_description='Estou com dor no peito muito forte e suor frio',
            symptom_onset='Agora há 10 minutos',
            pain_intensity=9,
            identity_confirmed=True,
        )
        self.assertTrue(sessao.is_completed)
        self.assertEqual(sessao.risk_color, TriageSession.RiskColor.RED)
        self.assertEqual(sessao.routing_destination, TriageSession.RoutingDestination.EMERGENCY)
        self.assertIsNotNone(dispatch)
        self.assertEqual(dispatch.trigger_source, EmergencyDispatch.TriggerSource.TRIAGE)
        self.assertEqual(dispatch.patient_summary['alergias'], 'Dipirona')

        # Com GPS ativado, retorna ordenado por distância
        dispatch, unidades_gps = EmergencyService.atualizar_localizacao(
            self.paciente_a.user_id,
            dispatch.pk,
            latitude=Decimal('-23.589000'),
            longitude=Decimal('-46.634700'),
        )
        self.assertTrue(unidades_gps[0].distance_km <= unidades_gps[-1].distance_km)

        # Sem GPS (busca manual por bairro), alerta permanece e filtra unidades
        dispatch, unidades_manuais = EmergencyService.atualizar_localizacao(
            self.paciente_a.user_id,
            dispatch.pk,
            latitude=None,
            longitude=None,
            manual_location_query='Santana',
        )
        self.assertEqual(unidades_manuais[0].neighborhood, 'Santana')

    @override_settings(MEDIX_LLM_BACKEND='core.integrations.llm.DisabledLlmAdapter')
    def test_indisponibilidade_llm_nao_cria_classificacao_inventada(self):
        with self.assertRaises(TriagemIndisponivel):
            TriageService.iniciar_triagem(
                self.paciente_a.user_id,
                symptoms_description='Tosse leve há 2 dias',
                symptom_onset='2 dias',
                pain_intensity=2,
                identity_confirmed=True,
            )
        self.assertEqual(TriageSession.objects.count(), 0)

    def test_rotas_protegidas_triagem_e_emergencia(self):
        # Visitante redireciona para login
        resp = self.client.get(reverse('triage:list'))
        self.assertEqual(resp.status_code, 302)

        # Titular autenticado inicia triagem Vermelha e acessa tela de emergência
        self.client.force_login(self.paciente_a.user)
        resp_post = self.client.post(
            reverse('triage:start'),
            {
                'identity_confirmed': 'on',
                'symptoms_description': 'Senti um desmaio súbito agora',
                'symptom_onset': 'Agora',
                'pain_intensity': 9,
            },
        )
        self.assertEqual(resp_post.status_code, 302)
        dispatch = EmergencyDispatch.objects.first()
        self.assertIsNotNone(dispatch)

        resp_em = self.client.get(reverse('triage:emergency', kwargs={'dispatch_id': dispatch.pk}))
        self.assertEqual(resp_em.status_code, 200)

        # Outro paciente não pode acessar emergência alheia (403)
        self.client.force_login(self.paciente_b.user)
        resp_outro = self.client.get(reverse('triage:emergency', kwargs={'dispatch_id': dispatch.pk}))
        self.assertEqual(resp_outro.status_code, 403)
