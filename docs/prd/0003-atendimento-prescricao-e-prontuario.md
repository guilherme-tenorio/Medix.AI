# PRD 0003: Atendimento médico, prescrição e prontuário

- **Status:** Proposto
- **Data:** 2026-11-23
- **Especificações:** [Spec 0009](../specs/0009-chat-medico.md), [Spec 0010](../specs/0010-validacao-medica-de-prescricao.md), [Spec 0011](../specs/0011-emissao-e-consulta-de-receita.md), [Spec 0012](../specs/0012-prontuario-e-historico.md) e [Spec 0014](../specs/0014-verificacao-e-dispensacao-de-receita.md)
- **Fonte:** `docs/Cópia de DocumentoRequisitoMEDIX.AI.md`

## Objetivo

Dar continuidade aos casos encaminhados para avaliação de um médico, permitir a comunicação clínica prevista e manter as prescrições e os atendimentos disponíveis em um histórico associado ao paciente correto.

## Perfis de uso

| Perfil | Quem é | O que precisa fazer |
|---|---|---|
| Paciente ou responsável | Pessoa que iniciou ou acompanha a triagem | Conversar com o médico, consultar prescrições e histórico autorizado |
| Médico credenciado | Profissional homologado | Avaliar recomendações, atender pacientes e registrar pareceres |
| Farmácia | Destinatário previsto da receita digital | Conferir a autenticidade da receita apresentada pelo paciente |

## Requisitos funcionais

### Avaliação e receita

- **RF-01:** Para casos Brancos/Verdes, o médico credenciado pode revisar a anamnese, classificação, perfil clínico e alergias, registrar parecer obrigatório e aprovar, ajustar, rejeitar ou reclassificar a conduta. (Fonte: RF006)
- **RF-02:** Após aprovação e assinatura digital válida, o paciente pode visualizar e baixar a receita em PDF imutável, sem CPF impresso, com nome do paciente, dados do prescritor, itens aprovados, validade e QR Code. (Fonte: RF007, RF008)
- **RF-03:** A receita permite conferência pública de autenticidade e status pelo QR Code/código identificador, sem expor dados além dos necessários à validação. (Fonte: RF008, RF009)
- **RF-04:** A sugestão de prescrição é comparada com alergias e comorbidades do perfil; conflito com alergia gera bloqueio visual antes da assinatura. (Fonte: RF003, RF006, RS006)

### Atendimento e histórico

- **RF-05:** Pacientes ou responsáveis de casos Amarelos/Laranjas ou reclassificados podem participar de chat síncrono com médico credenciado, com mensagens e confirmações de entrega/leitura registradas. (Fonte: RF010)
- **RF-06:** O sistema mantém linha do tempo cronológica imutável de triagens, pareceres, receitas, chats e emergências do paciente e dependentes. (Fonte: RF014)
- **RF-07:** O paciente/responsável consulta registros vinculados; profissionais acessam prontuário conforme vínculo autorizado, com auditoria de acessos médicos. (Fonte: RF014, RS003)
- **RF-08:** Farmacêutico pode registrar dispensação única da receita informando CRF e CNPJ da farmácia; o sistema grava data/hora e bloqueia nova baixa de receita dispensada ou revogada. (Fonte: RF009, RS002)
- **RF-09:** Médico registra obrigatoriamente desfecho e conduta antes de encerrar consulta e voltar à fila; red flags ou reclassificação Vermelha acionam emergência. (Fonte: RF011)
- **RF-10:** Médico pode revogar receita ativa com justificativa formal; a revogação desativa imediatamente seu QR Code de dispensação e fica auditada. (Fonte: RF007)

## Requisitos não funcionais

- **RNF-01 (tempo real):** Mensagens de texto do chat devem sincronizar entre paciente e médico com latência máxima de 1 segundo. (Fonte: RNF004)
- **RNF-02 (privacidade):** Dados pessoais e clínicos devem ser protegidos durante transmissão e armazenamento, conforme TLS 1.3 e AES-256 indicados pela fonte. (Fonte: RNF006)
- **RNF-03 (acesso e auditoria):** O acesso a prontuários deve respeitar os papéis definidos e manter trilha de auditoria imutável dos acessos e emissões de receitas, com autor e data/hora. (Fonte: RNF007)
- **RNF-04 (conformidade e retenção):** Prontuários devem obedecer às normas e ao prazo mínimo de guarda de 20 anos citados na fonte; receitas devem observar as regras de validade jurídica e assinatura digital ali especificadas. (Fonte: RNF008)
- **RNF-05 (compatibilidade):** O painel clínico deve operar nos navegadores e telas responsivas descritos na fonte. (Fonte: RNF009)

## Requisitos de segurança

- **RS-01:** O sistema não libera uma receita sem revisão médica e assinatura digital ICP-Brasil válida de médico com CRM ativo; deve permitir verificação pública de autenticidade conforme a fonte. (Fonte: RS002)
- **RS-02:** Prontuários, exames e históricos só podem ser acessados por pessoas autorizadas e vinculadas ao paciente ou ao atendimento, com registro de auditoria. (Fonte: RS003)
- **RS-03:** Incompatibilidades entre uma sugestão farmacológica e alergias ou comorbidades graves registradas devem gerar o bloqueio visual crítico descrito na fonte antes da assinatura médica. (Fonte: RS006)
- **RS-04:** Nenhuma receita pode ser emitida sem assinatura ICP-Brasil válida de médico com CRM ativo; dispensação registrada não pode ser repetida e receita revogada não pode ser dispensada. (Fonte: RS002)

## Fora do escopo desta versão

Não se define neste PRD a lista de medicamentos, a decisão clínica de prescrever, os critérios legais de validade da receita ou a integração operacional com farmácias. O PRD registra somente os comportamentos da fonte, incluindo revisão humana e baixa única por farmacêutico.

## Critérios de conclusão

- A separação entre sugestão da IA, revisão do médico e liberação da receita está explícita.
- Os casos Amarelos/Laranjas, a consulta ao prontuário e a proteção de seus registros estão rastreáveis às fontes.
- As dúvidas de validade, retenção e verificação da receita estão identificadas para validação antes da especificação.

## Dependências, restrições e questões em aberto

- A fonte cita regras do CFM, Anvisa, guarda mínima de 20 anos e validade de receita calculada conforme regulamentação; confirmar aplicabilidade atual e cálculo de validade com responsáveis competentes antes das specs finais.
- A fonte exige assinatura ICP-Brasil e validação de certificado/CRM, mas não define integração, revogação de certificado nem fluxo de indisponibilidade do token.
- A página pública de verificação deve expor apenas dados necessários à autenticidade; a fonte não define o conjunto mínimo de campos públicos nem proteção contra enumeração.
- A fonte exige CRF e CNPJ no registro de dispensação, mas não define como a identidade e regularidade desses dados serão verificadas.
- A fonte torna o parecer e desfecho imutáveis, mas não define procedimento para corrigir erro material após encerramento.
