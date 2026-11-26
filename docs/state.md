# Estado atual

Atualizado em: 2026-11-26

## Em andamento
- A skill `.agents/skills/medix-figma-design/SKILL.md` orienta que todas as interfaces e portais do sistema sigam a linguagem visual comum derivada dos frames “Tela de Revisão Médica” (`1:3`) e “Cadastro de Paciente MEDIX.AI” (`2:3`), adaptada ao propósito de cada tela. Os metadados consultados não expuseram tokens visuais detalhados; conferir os frames no Figma durante refinamentos visuais.
- Fonte vigente: [`DocumentoRequisitoMEDIX.AI (4).md`](DocumentoRequisitoMEDIX.AI%20(4).md), atualizada em 2026-11-24. A cópia sem “(4)” é uma versão histórica substituída.
- Os cinco PRDs estão `Aceito`. As 15 specs foram aprovadas pelo responsável em 2026-11-25; mantêm `Status: Proposto` até revisão final de aceite sobre código e testes. RF001–RF022, RNF001–RNF014 e RS001–RS011 estão mapeados na [matriz de rastreabilidade](rastreabilidade-requisitos.md).
- Escopo confirmado: um único WebApp para todos os perfis, sem cliente nativo. Portais web segregados: paciente/responsável em `/login`, médico em `/medico/login` e administrador em `/admin/login`; tentativas de acesso cruzado recebem HTTP 403. Cadastro público apenas para paciente; médicos são provisionados/homologados por administrador; sem cadastro público de administrador ou seletor de papel.
- Divisão dos apps por domínio e autenticação por sessão Django server-side aprovadas nos ADRs 0004/0005. Banco PostgreSQL `medix_ai_webapp` em uso (SQLite removido do projeto).
- RNF009 permanece requisito do produto completo: o MVP WebApp não cumpre a exigência de aplicativo Android/iOS. Interfaces web responsivas não são equivalentes a clientes nativos.
- ADRs 0001–0005 estão aceitos. ADR 0003 aprova a estratégia de integração e anonimização; fornecedor, contrato, retenção e região ainda precisam ser definidos antes do tráfego clínico real.

## Implementação

- **Todas as Specs 0001–0015 implementadas e testadas no PostgreSQL (`medix_ai_webapp`), com 41 testes automatizados passando, `manage.py check` limpo e `makemigrations --check --dry-run` sem pendências:**
  - **Spec 0001 (Voz e acessibilidade):** Adaptador desacoplado `core/integrations/speech.py` (`DisabledSpeechAdapter` e `SandboxSpeechAdapter` sem retenção de áudio bruto) e alternância voz/digitação + TTS em pt-BR em `users/static/users/js/voice_input.js`.
  - **Spec 0002 (Cadastro de pacientes titulares):** `core/integrations/sms.py`, validação de CPF/celular em `users/identifiers.py`, models e services em `patients/` (consentimento LGPD, desafio SMS, perfil clínico com histórico imutável).
  - **Spec 0003 (Autenticação e sessão):** Portais segregados com HTTP 403 em acesso cruzado, bloqueio por tentativas, troca obrigatória de senha provisória, auditoria com HMAC e e-mail sandbox em `core/integrations/email.py`.
  - **Spec 0004 (Gestão de dependentes):** `Dependent` (vínculo legal, CPF único e imutável, desativação lógica) e `DependentService` em `patients/` com isolamento por responsável (18+).
  - **Spec 0005 (Gestão de profissionais):** `ProfessionalProfile`, `ShiftHistory` e `ProfessionalService` em `professionals/` (provisionamento restrito a admin, comprovante CRM, homologação, suspensão com revogação de sessões e disponibilidade exigindo CRM regular + ICP-Brasil ativo).
  - **Specs 0006 e 0007 (Triagem IA Manchester e Emergência):** `core/integrations/llm.py` (`GeminiLlmAdapter` via HTTPS REST com payload desidentificado sem nome/CPF conforme ADR 0003 + fallback `SandboxLlmAdapter`), `core/integrations/geolocation.py`, models `TriageSession` e `EmergencyDispatch`, `ManchesterClassifierService` (5 cores determinísticas + red flags com prioridade absoluta), `TriageService` (imutabilidade pós-conclusão e enfileiramento automático para `care`) e `EmergencyService` (alerta imediato com ficha resumida, GPS ou busca manual).
  - **Specs 0008 e 0009 (Fila clínica e Chat médico síncrono):** `care/` com filas separadas (`SYNCHRONOUS_CHAT` e `PRESCRIPTION_REVIEW`), ordenação por cor (Laranja > Amarela > Verde > Branca) e tempo de espera, resumo anonimizado pré-aceite, proibição de casos Vermelhos na fila, `ChatSession`, `ChatMessage` (até 1000 chars, entrega/leitura, polling JSON em tempo real, copiloto clínico IA desidentificado, STT sem reter áudio bruto), `ChatAttachment` (PDF/PNG/JPEG até 10 MB), `ClinicalOutcome` obrigatório, imutabilidade pós-encerramento, notificações automáticas e reclassificação Vermelha disparando `EmergencyService`.
  - **Specs 0010, 0011 e 0014 (Revisão de prescrição, Emissão de receita digital e Dispensação):** `core/integrations/pdf.py` (PDF 1.4 sem CPF do paciente), `prescriptions/` com `PrescriptionReview`, `DigitalPrescription` (hash ICP-Brasil, token QR, revogação com justificativa) e `PrescriptionDispensation` (baixa atômica única com CRF e CNPJ), bloqueio automático por conflito de alergia e página pública de verificação limitada.
  - **Spec 0012 (Prontuário e histórico):** `records/` com `MedicalRecordAmendment` (retificações preservando o original), `MedicalRecordAccessLog` (trilha imutável com CRM e tentativas negadas) e `MedicalRecordService` (linha do tempo decrescente agregando triagens, pareceres, chats, receitas e emergências com filtros combináveis e isolamento por vínculo).
  - **Spec 0013 (Notificações e alertas):** Expansão de `notifications/` com canais Push/SMS/E-mail/WhatsApp, `NotificationPreference`, prioridades (sem supressão de urgentes), fallback automático de Push sem confirmação após 30s para SMS, conteúdo mascarado, central do usuário e limpeza apenas de informativas lidas preservando auditoria.
  - **Spec 0015 (Gestão de administradores e monitoramento operacional):** Expansão de `audit/` com `AdminAccountService` (criação com senha provisória e bloqueio contra desativação do último administrador ativo) e `OperationalMonitoringService` (métricas ao vivo de fila, espera média, emergências 24h, pareceres, médicos Online e alertas de gargalo).
- Todas as migrações foram geradas e aplicadas no PostgreSQL local (`medix_ai_webapp`): `users.0001`–`0003`, `audit.0001`–`0006`, `notifications.0001`–`0002`, `patients.0001`, `professionals.0001`, `triage.0001`, `care.0001`–`0002`, `prescriptions.0001`–`0002`, `records.0001`.

## Próximos passos

1. Revisão funcional manual das telas no navegador e refinamento visual conforme frames do Figma (`medix-figma-design`).
2. Definição operacional dos provedores externos reais (LLM, STT/TTS, SMS, e-mail, ICP-Brasil, geolocalização/diretório hospitalar) antes de tráfego clínico real.

## Pendências de produto e operação

- Limites clínicos/etários de altura e peso, texto e retirada de consentimento, verificação de SMS e processo para menores.
- Provedor, região, retenção e contrato de processamento do LLM; integração de STT/TTS e tratamento de áudio de chat (RF010 versus descarte RF015).
- Validar versão do Protocolo de Manchester, red flags, algoritmos de compatibilidade e critérios de alerta de alergia com responsáveis clínicos.
- Provedores e contratos para e-mail, SMS, notificações multicanal, geolocalização/diretório hospitalar, ICP-Brasil, CRM e CRF/CNPJ.
- Confirmação de entrega, métricas de disponibilidade/latência e limites de gargalo; links de redefinição seguem validade de 30 minutos da Spec 0003.
- Bootstrap do primeiro administrador, autorização do farmacêutico para baixa e retenção/regra de expurgo por tipo de registro.
- Definição operacional de ambientes segregados, backup diário criptografado, monitoramento/alertas, arquivamento em camadas e proteção de imutabilidade/não-repúdio da auditoria (RNF011, RNF014 e RS011).
