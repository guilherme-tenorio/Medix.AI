# PRD 0003: Atendimento médico, prescrição e prontuário

- **Status:** Proposto
- **Data:** 2026-11-19
- **Especificações:** [Spec 0009](../specs/0009-chat-medico.md), [Spec 0010](../specs/0010-validacao-medica-de-prescricao.md), [Spec 0011](../specs/0011-emissao-e-consulta-de-receita.md) e [Spec 0012](../specs/0012-prontuario-e-historico.md)
- **Fonte:** `docs/DocumentoRequisitoMEDIX.AI (3).md`

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

- **RF-01:** Para casos Brancos/Verdes, o médico credenciado pode revisar a anamnese e a prescrição sugerida pela IA, editar a sugestão e aprová-la formalmente antes da liberação. (Fonte: RF004)
- **RF-02:** Após aprovação médica, o paciente pode consultar e baixar a receita digital e apresentar seu código de validação na farmácia. (Fonte: RF005)
- **RF-03:** A receita deve permitir verificação de autenticidade por QR Code e assinatura digital, conforme os requisitos legais e de segurança registrados na fonte. (Fonte: RF005, RNF008, RS002)
- **RF-04:** A sugestão de prescrição deve ser comparada com alergias e comorbidades registradas, e o médico deve receber o alerta crítico descrito na fonte antes de assinar quando houver incompatibilidade. (Fonte: RS006)

### Atendimento e histórico

- **RF-05:** Pacientes ou responsáveis de casos Amarelos/Laranjas podem participar de atendimento síncrono por chat com médico credenciado. (Fonte: RF006)
- **RF-06:** O sistema mantém uma linha do tempo cronológica com triagens, pareceres, receitas e atendimentos do paciente e de seus dependentes, conforme os registros previstos na fonte. (Fonte: RF008)
- **RF-07:** O paciente ou responsável pode consultar os registros vinculados ao seu perfil; o acesso profissional deve estar limitado às relações de atendimento autorizadas descritas na fonte. (Fonte: RF008, RS003)

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

## Fora do escopo desta versão

Não se define neste PRD a lista de medicamentos, a decisão clínica de prescrever ou os detalhes de comunicação com farmácias. O PRD registra somente os comportamentos presentes na fonte, incluindo a revisão humana obrigatória.

## Critérios de conclusão

- A separação entre sugestão da IA, revisão do médico e liberação da receita está explícita.
- Os casos Amarelos/Laranjas, a consulta ao prontuário e a proteção de seus registros estão rastreáveis às fontes.
- As dúvidas de validade, retenção e verificação da receita estão identificadas para validação antes da especificação.

## Dependências, restrições e questões em aberto

- A fonte explica as categorias de prioridade, mas não atribui prioridade aos RFs; este PRD não inventa essa classificação.
- A fonte cita regras do CFM, Anvisa, guarda mínima de 20 anos e assinatura ICP-Brasil. Confirmar a aplicabilidade atual e o escopo de cada regra com responsáveis competentes antes de fechar as specs; este PRD apenas registra o que consta na fonte.
- A fonte descreve receita sugerida pela IA e aprovação/edição obrigatória pelo médico. Confirmar se há qualquer cenário de emissão sem sugestão da IA; nenhum foi presumido aqui.
- A fonte exige envio da receita à farmácia, mas não define integração, destinatário, consentimento ou o que acontece se o envio falhar.
- Confirmar se o documento-fonte correto é a versão `(3)` utilizada neste PRD; o caminho indicado no pedido, `docs/DocumentoRequisitoMEDIX.AI.md`, não foi encontrado.
