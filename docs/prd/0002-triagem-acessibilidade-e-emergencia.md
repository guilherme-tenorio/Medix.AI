# PRD 0002: Triagem acessível e encaminhamento de emergência

- **Status:** Proposto
- **Data:** 2026-11-19
- **Especificações:** [Spec 0001](../specs/0001-interacao-por-voz-e-acessibilidade.md), [Spec 0006](../specs/0006-triagem-e-classificacao-de-risco.md) e [Spec 0007](../specs/0007-encaminhamento-de-emergencia.md)
- **Fonte:** `docs/DocumentoRequisitoMEDIX.AI (3).md`

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

- **RF-01:** O paciente ou responsável autorizado pode iniciar uma anamnese conduzida por IA para o titular ou dependente cadastrado, fornecendo sintomas por texto ou voz e usando os dados de saúde disponíveis no perfil. (Fonte: RF003)
- **RF-02:** Ao concluir a anamnese, o sistema apresenta uma classificação de risco por cor e o fluxo associado, conforme os resultados descritos na fonte: orientação para casos Brancos/Verdes, atendimento médico para Amarelos/Laranjas e encaminhamento presencial urgente para Vermelhos. (Fonte: RF003, RF007)
- **RF-03:** Uma triagem concluída não pode ser alterada nem excluída; a fonte permite iniciar uma nova triagem sequencial e manter o histórico no prontuário. (Fonte: RF003, RF008)

### Emergência e acessibilidade

- **RF-04:** Quando a classificação for Vermelha, o sistema interrompe o fluxo comum e orienta o paciente ou responsável a procurar atendimento presencial urgente, apresentando unidades próximas e rota quando disponíveis. A orientação de emergência não deve depender de GPS ativo. (Fonte: RF003, RF007)
- **RF-05:** O usuário pode interagir por voz para preencher informações e ouvir orientações faladas, conforme os usos descritos para cadastro, triagem e navegação. (Fonte: RF009)
- **RF-06:** O aplicativo oferece recursos de acessibilidade e inclusão digital descritos na fonte, incluindo comandos de voz, leitura sintetizada, dicas visuais, alto contraste e fontes legíveis. (Fonte: RF009, RNF001)

## Requisitos não funcionais

- **RNF-01 (acessibilidade):** A interface deve atender idosos, pessoas com baixa literacia digital e pessoas com limitações visuais ou motoras por meio dos recursos descritos na fonte. (Fonte: RNF001)
- **RNF-02 (mensagens de erro):** Mensagens de validação ou indisponibilidade de recursos, como microfone ou GPS, devem ser claras, acessíveis e orientar a ação corretiva. (Fonte: RNF002)
- **RNF-03 (desempenho):** Cada etapa da anamnese com IA deve responder em até 3 segundos em condições normais de rede; alertas críticos devem ser disparados em até 2 segundos. (Fonte: RNF003)
- **RNF-04 (disponibilidade):** Triagem e encaminhamento de emergência devem ter disponibilidade mínima de 99,5% em regime 24/7. (Fonte: RNF005)
- **RNF-05 (privacidade):** Os dados pessoais e clínicos devem ser protegidos conforme os controles de transmissão e armazenamento especificados pela fonte. O áudio gravado para transcrição deve ser descartado após a conversão em texto. (Fonte: RNF006)

## Requisitos de segurança

- **RS-01:** Antes de iniciar a triagem, o sistema confirma explicitamente o nome, a idade e o vínculo do paciente e associa o atendimento ao CPF validado. (Fonte: RS001)
- **RS-02:** Sinais de risco crítico devem ter prioridade máxima, impedir o encaminhamento para fila virtual e gerar orientação imediata de deslocamento para atendimento hospitalar, mesmo quando o GPS estiver desativado. (Fonte: RS004)
- **RS-03:** Arquivos de áudio com relatos clínicos devem ser descartados após transcrição validada; o registro textual permanece protegido no prontuário. (Fonte: RS009)

## Fora do escopo desta versão

Este PRD não define diagnóstico, tratamento ou prescrição autônoma pela IA. A fonte prevê classificação e encaminhamentos; receitas para casos Brancos/Verdes dependem de aprovação médica e estão cobertas pelo PRD 0003.

## Critérios de conclusão

- As saídas e encaminhamentos das cinco cores estão especificados e relacionados aos requisitos de origem.
- O fluxo de risco Vermelho não é confundido com atendimento remoto ou espera em fila.
- Os comportamentos de voz, acessibilidade, erro e indisponibilidade de GPS/microfone estão especificados sem presumir detalhes ausentes.

## Dependências, restrições e questões em aberto

- A fonte explica as categorias de prioridade, mas não atribui prioridade aos RFs; este PRD não inventa essa classificação.
- A fonte cita o Protocolo de Manchester e cinco cores, incluindo Branca e Vermelha. Confirmar protocolo, versão e validação clínica do conjunto de cores e das regras de classificação antes de especificar a IA.
- A fonte não define os limites clínicos, conteúdo da anamnese, governança de atualização do protocolo nem validação das respostas da IA. Esses pontos exigem definição clínica responsável; não devem ser inferidos pelo PRD.
- A fonte pede unidades próximas e rota, mas também determina orientação emergencial mesmo com GPS desativado. Esclarecer a apresentação quando a localização não estiver disponível e qual serviço de emergência, se algum, deve ser acionado.
- Confirmar se o documento-fonte correto é a versão `(3)` utilizada neste PRD; o caminho indicado no pedido, `docs/DocumentoRequisitoMEDIX.AI.md`, não foi encontrado.
