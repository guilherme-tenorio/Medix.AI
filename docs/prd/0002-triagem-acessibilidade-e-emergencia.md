# PRD 0002: Triagem acessível e encaminhamento de emergência

- **Status:** Proposto
- **Data:** 2026-11-23
- **Especificações:** [Spec 0001](../specs/0001-interacao-por-voz-e-acessibilidade.md), [Spec 0006](../specs/0006-triagem-e-classificacao-de-risco.md), [Spec 0007](../specs/0007-encaminhamento-de-emergencia.md), [Spec 0002](../specs/0002-cadastro-de-pacientes.md) e [Spec 0004](../specs/0004-gestao-de-dependentes.md)
- **Fonte:** `docs/Cópia de DocumentoRequisitoMEDIX.AI.md`

## Objetivo

Permitir que um paciente ou seu responsável relate sintomas, responda a uma anamnese e receba uma classificação de risco e o encaminhamento correspondente. O fluxo deve permitir interação acessível e tratar casos classificados como críticos sem retê-los em uma fila virtual.

## Perfis de uso

| Perfil | Quem é | O que precisa fazer |
|---|---|---|
| Paciente titular | Pessoa cadastrada que relata sintomas próprios | Realizar triagem e compreender o resultado e o encaminhamento |
| Responsável legal | Titular autenticado vinculado a dependente | Realizar triagem em nome do dependente |
| Pessoa com barreiras de acesso digital | Usuário que se beneficia de voz, áudio ou recursos visuais acessíveis | Interagir com o sistema com menos dependência de digitação e leitura visual |

## Requisitos funcionais

### Anamnese e classificação

- **RF-01:** O paciente ou responsável autorizado pode concluir uma anamnese conversacional por texto ou áudio, informando sintomas, início/duração e intensidade de 0 a 10; a IA pode fazer perguntas adaptativas usando o perfil clínico do paciente. (Fonte: RF004)
- **RF-02:** Ao concluir a anamnese, o sistema classifica o risco segundo regras determinísticas do Protocolo de Manchester e apresenta relatório com queixas, antecedentes, alergias e respostas. (Fonte: RF005)
- **RF-03:** O resultado direciona casos Brancos/Verdes para revisão clínica, Amarelos/Laranjas para atendimento síncrono e Vermelhos para emergência sem fila virtual. O paciente não pode alterar as regras ou classificação. (Fonte: RF005)
- **RF-07:** Durante o alerta Vermelho, o sistema localiza hospitais e prontos-socorros próximos, ordenados por distância, permite abrir rota externa e, sem GPS, mantém o alerta visível e permite busca manual por bairro/cidade. (Fonte: RF013)
- **RF-08:** Anamnese concluída e classificação são registradas de forma imutável no prontuário; nova avaliação gera registro separado. (Fonte: RF004, RF005, RF014)

### Emergência e acessibilidade

- **RF-04:** Quando a classificação for Vermelha, o sistema interrompe o fluxo comum, exibe alerta em tela cheia com sintomas graves, cria ficha clínica resumida para apresentação no hospital e não envia o caso para fila virtual. (Fonte: RF012)
- **RF-05:** O usuário pode interagir por voz para preencher cadastros e perfil clínico, conduzir triagem, usar o chat e ouvir orientações de emergência, mantendo alternativa textual. (Fonte: RF015)
- **RF-06:** O aplicativo oferece comandos de voz e leitura sintetizada em português pausado, dicas visuais, alto contraste, fontes legíveis e mensagens de erro acessíveis. (Fonte: RF015, RNF001, RNF002)

## Requisitos não funcionais

- **RNF-01 (acessibilidade):** A interface deve atender idosos, pessoas com baixa literacia digital e pessoas com limitações visuais ou motoras por meio dos recursos descritos na fonte. (Fonte: RNF001)
- **RNF-02 (mensagens de erro):** Mensagens de validação ou indisponibilidade de recursos, como microfone ou GPS, devem ser claras, acessíveis e orientar a ação corretiva. (Fonte: RNF002)
- **RNF-03 (desempenho):** Cada etapa da anamnese com IA deve responder em até 5 segundos em condições normais de rede; alertas críticos devem ser disparados em até 2 segundos. (Fonte: RNF003)
- **RNF-04 (disponibilidade):** Triagem e encaminhamento de emergência devem ter disponibilidade mínima de 99,5% em regime 24/7. (Fonte: RNF005)
- **RNF-05 (privacidade):** Os dados pessoais e clínicos devem ser protegidos conforme os controles de transmissão e armazenamento especificados pela fonte. O áudio gravado para transcrição deve ser descartado após a conversão em texto. (Fonte: RNF006)
- **RNF-06 (interoperabilidade):** A anamnese e a classificação comunicam-se com um provedor externo de LLM via API REST sobre HTTPS/JSON, com resposta estruturada; timeout ou indisponibilidade gera mensagem orientativa sem apresentar classificação inventada. (Fonte: RNF010)

## Requisitos de segurança

- **RS-01:** Antes de iniciar a triagem, o sistema confirma explicitamente o nome, a idade e o vínculo do paciente e associa o atendimento ao CPF validado. (Fonte: RS001)
- **RS-02:** Sinais de risco crítico devem ter prioridade máxima, impedir o encaminhamento para fila virtual e gerar orientação imediata de deslocamento para atendimento hospitalar, mesmo quando o GPS estiver desativado. (Fonte: RS004)
- **RS-03:** Arquivos de áudio com relatos clínicos devem ser descartados após transcrição validada; o registro textual permanece protegido no prontuário. (Fonte: RS009)
- **RS-04:** Antes de enviar contexto clínico ao provedor externo de LLM, o sistema remove identificadores diretos como CPF e nome completo e envia somente atributos clínicos desidentificados descritos na fonte. (Fonte: RNF006, RS010)

## Fora do escopo desta versão

Este PRD não define diagnóstico, tratamento ou prescrição autônoma pela IA. A fonte prevê classificação e encaminhamentos; receitas para casos Brancos/Verdes dependem de aprovação médica e estão cobertas pelo PRD 0003.

## Critérios de conclusão

- As saídas e encaminhamentos das cinco cores estão especificados e relacionados aos requisitos de origem.
- O fluxo de risco Vermelho não é confundido com atendimento remoto ou espera em fila.
- Os comportamentos de voz, acessibilidade, erro e indisponibilidade de GPS/microfone estão especificados sem presumir detalhes ausentes.

## Dependências, restrições e questões em aberto

- A fonte explica as categorias de prioridade, mas não atribui prioridade aos RFs; este PRD não inventa essa classificação.
- A fonte cita o Protocolo de Manchester e cinco cores, incluindo Branca e Vermelha. Confirmar protocolo, versão, red flags completos e validação clínica das regras antes de especificar ou operar a IA.
- A fonte não define provedor de LLM, política de retenção do contexto no provedor, mecanismo de anonimização reversível para manter conversa, nem resposta clínica de fallback quando a API falhar.
- A fonte determina que a transcrição com baixa confiança deve ser confirmada, mas não define o limiar de confiança nem o tratamento de erro se a pessoa não puder confirmar.
- A fonte pede localização por GPS ou busca manual por bairro/cidade e navegação externa, mas não indica fontes de hospitais, cobertura, consentimento ou comportamento quando não há unidade encontrada.
