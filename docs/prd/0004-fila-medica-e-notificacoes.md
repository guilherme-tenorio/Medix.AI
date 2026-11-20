# PRD 0004: Fila médica e notificações

- **Status:** Proposto
- **Data:** 2026-11-19
- **Especificações:** [Spec 0008](../specs/0008-fila-clinica.md) e [Spec 0013](../specs/0013-notificacoes-e-alertas.md)
- **Fonte:** `docs/DocumentoRequisitoMEDIX.AI (3).md`

## Objetivo

Permitir que médicos credenciados acompanhem e priorizem atendimentos pendentes e que pacientes, responsáveis e profissionais recebam avisos sobre eventos relevantes do atendimento.

## Perfis de uso

| Perfil | Quem é | O que precisa fazer |
|---|---|---|
| Médico credenciado | Profissional disponível para atendimento | Consultar a fila, aceitar chamados e acompanhar seus estados |
| Paciente ou responsável | Pessoa vinculada ao atendimento | Receber avisos e acessar o chat, receita ou orientação correspondente |
| Administrador | Operador da plataforma | Consultar eventos e status de entrega conforme suas permissões |

## Requisitos funcionais

### Fila clínica

- **RF-01:** O médico disponível pode consultar uma fila de pacientes triados, ordenada primeiro pela gravidade indicada pelas cores e, entre casos da mesma cor, pelo tempo de espera, conforme a fonte. (Fonte: RF011)
- **RF-02:** Antes de aceitar um chamado, o painel mostra apenas o identificador resumido previsto na fonte; o médico pode filtrar a fila por cor, tempo de espera e identificador. (Fonte: RF011)
- **RF-03:** O sistema atualiza o status do chamado ao ser aceito e conforme o atendimento avança, e ajusta a disponibilidade do médico conforme o fluxo descrito na fonte. (Fonte: RF011)

### Notificações e alertas

- **RF-04:** O sistema notifica pacientes, responsáveis e profissionais sobre eventos do atendimento, incluindo início de chat, liberação de receita aprovada e alertas previstos na fonte. (Fonte: RF012)
- **RF-05:** O usuário pode configurar os tipos e canais de notificação disponíveis; notificações informativas lidas podem ser removidas, enquanto mensagens críticas permanecem no registro de auditoria. (Fonte: RF012)
- **RF-06:** O usuário autorizado pode pesquisar notificações por usuário, canal, período e status de entrega. (Fonte: RF012)

## Requisitos não funcionais

- **RNF-01 (tempo real):** Atualizações da fila e sincronização de mensagens/status do chat devem respeitar a latência máxima de 1 segundo especificada na fonte. (Fonte: RNF004)
- **RNF-02 (urgência):** Notificações urgentes devem ser disparadas em até 2 segundos, conforme a fonte. (Fonte: RNF003)
- **RNF-03 (disponibilidade e fallback):** A plataforma deve manter a disponibilidade de 99,5% em regime 24/7 para triagem e encaminhamento de emergência; se uma notificação push de chamada médica não for confirmada em 30 segundos, deve ser acionado SMS alternativo. (Fonte: RNF005)
- **RNF-04 (auditoria):** Eventos críticos e acessos relacionados devem manter trilha de auditoria imutável, conforme as regras de controle de acesso da fonte. (Fonte: RNF007)
- **RNF-05 (compatibilidade):** O painel clínico/administrativo deve funcionar nos navegadores e telas responsivas descritos na fonte. (Fonte: RNF009)

## Requisitos de segurança

- **RS-01:** Notificações em push e SMS não devem expor diagnósticos ou dados clínicos sensíveis na tela bloqueada; detalhes exigem autenticação ativa. (Fonte: RS005)
- **RS-02:** O resumo mostrado na fila antes da aceitação do chamado deve preservar a privacidade prevista na fonte; o acesso aos dados clínicos completos deve respeitar a relação autorizada com o atendimento. (Fonte: RF011, RS003)

## Fora do escopo desta versão

O PRD não define a infraestrutura de mensageria, os provedores de push/SMS, algoritmos de escalonamento além da ordem descrita, nem a interface detalhada do painel.

## Critérios de conclusão

- A ordenação da fila, o ciclo de status e as notificações estão descritos com referências aos requisitos de origem.
- Os prazos de latência, disparo urgente e fallback estão registrados sem serem tratados como equivalentes.
- O conteúdo exposto em notificações e na fila respeita os limites de privacidade indicados nas fontes.

## Dependências, restrições e questões em aberto

- A fonte explica as categorias de prioridade, mas não atribui prioridade aos RFs; este PRD não inventa essa classificação.
- A fonte estabelece prioridade de gravidade na sequência Laranja, Amarela, Verde e Branca, mas usa também classificação Vermelha para emergência. Confirmar como casos Vermelhos entram ou não na fila; o encaminhamento de emergência está definido no PRD 0002.
- A fonte exige disparo de alerta urgente em até 2 segundos e fallback de push para SMS após 30 segundos sem confirmação. Esclarecer se os 2 segundos medem criação, envio ou entrega da notificação e como o prazo interage com a confirmação.
- A fonte diz que notificações críticas permanecem no log de auditoria, mas não define quem pode consultar esse log ou por quanto tempo.
- Confirmar se o documento-fonte correto é a versão `(3)` utilizada neste PRD; o caminho indicado no pedido, `docs/DocumentoRequisitoMEDIX.AI.md`, não foi encontrado.
