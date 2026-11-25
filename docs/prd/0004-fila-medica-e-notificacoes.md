# PRD 0004: Fila médica, disponibilidade e notificações

- **Status:** Aceito
- **Aprovado em:** 2026-11-25
- **Data:** 2026-11-24
- **Especificações:** [Spec 0008](../specs/0008-fila-clinica.md), [Spec 0013](../specs/0013-notificacoes-e-alertas.md) e [Spec 0015](../specs/0015-gestao-de-administradores-e-monitoramento.md)
- **Fonte:** [`DocumentoRequisitoMEDIX.AI (4).md`](../DocumentoRequisitoMEDIX.AI%20(4).md)

## Objetivo

Organizar o atendimento médico por prioridade e disponibilidade, comunicar eventos aos usuários e permitir que administradores acompanhem a operação e auditem atividades.

## Perfis de uso

| Perfil | Quem é | O que precisa fazer |
|---|---|---|
| Médico credenciado | Profissional homologado | Definir disponibilidade e atender casos encaminhados |
| Paciente ou responsável | Pessoa vinculada ao atendimento | Receber avisos e acessar o fluxo correspondente |
| Administrador | Operador autorizado | Gerir contas administrativas, acompanhar indicadores e consultar auditoria |

## Requisitos funcionais

### Fila e disponibilidade médica

- **RF-01:** A fila separa atendimentos síncronos e revisões de prescrição; ordena a fila clínica por Laranja, Amarela, Verde e Branca e desempata pelo maior tempo de espera. (Fonte: RF018)
- **RF-02:** Antes de aceitar o atendimento, a fila apresenta somente dados parciais anonimizados; após aceite, disponibiliza os dados autorizados do paciente. (Fonte: RF018)
- **RF-03:** No painel acessado pelo navegador, o médico define status Disponível/Online, Pausa ou Offline e atualiza o telefone de contato operacional. Somente médico com CRM homologado e certificado ICP-Brasil válido pode ficar Online; Offline impede novos chamados sem cancelar atendimentos em curso. O painel registra com data/hora entradas e saídas de plantão e atendimentos; administradores autorizados consultam médicos em plantão ativo. (Fonte: RF019, RF022, RNF009)

### Notificações e administração

- **RF-04:** O WebApp envia notificações por Push web (quando suportado pelo navegador), SMS, e-mail e WhatsApp para eventos relevantes, com links que abrem o fluxo web associado; mensagens em tela bloqueada mascaram dados clínicos. O usuário personaliza canais preferenciais e pode remover notificações lidas da central. (Fonte: RF020; plataforma: PRD 0005)
- **RF-05:** Se uma notificação Push de chamada não tiver confirmação em 30 segundos, o sistema envia SMS de fallback. (Fonte: RF020)
- **RF-06:** Administradores consultam histórico de notificações enviadas e estados de entrega conforme permissões. A pesquisa de auditoria permite filtrar por período, CPF/CRM do operador, tipo de evento e severidade; registros incluem autor, data/hora, IP e ação e não podem ser alterados ou apagados. O histórico de notificações permanece pesquisável no painel administrativo. (Fonte: RF020, RF022)
- **RF-07:** O administrador acompanha painel operacional atualizado com volume da fila, tempo de espera, emergências e gargalos; consulta trilha imutável por operador, período e evento. (Fonte: RF022)
- **RF-08:** O sistema impede que o último administrador ativo desative a própria conta. (Fonte: RF022)

## Requisitos não funcionais

- **RNF-01 (tempo real):** Atualizações da fila e sincronização do chat devem respeitar latência máxima de 1 segundo conforme a fonte. (Fonte: RNF004)
- **RNF-02 (urgência):** Alertas urgentes devem ser disparados em até 2 segundos. (Fonte: RNF003)
- **RNF-03 (disponibilidade e fallback):** Triagem e encaminhamento de emergência devem manter disponibilidade de 99,5% em regime 24/7; Push sem confirmação em 30 segundos aciona SMS. (Fonte: RNF005, RF020)
- **RNF-04 (auditoria):** Eventos críticos e acessos relacionados mantêm trilha de auditoria imutável. (Fonte: RNF007)
- **RNF-05 (compatibilidade):** Painéis clínico e administrativo funcionam nos navegadores web descritos na fonte. (Fonte: RNF009)
- **RNF-06 (implantação e observabilidade):** Ambientes de desenvolvimento, homologação e produção devem ser segregados, com backup diário criptografado, monitoramento contínuo de disponibilidade e alertas operacionais de falha. (Fonte: RNF014)

## Requisitos de segurança

- **RS-01:** Notificações Push e SMS não expõem diagnóstico ou dados clínicos sensíveis na tela bloqueada. (Fonte: RS005)
- **RS-02:** A fila mostra apenas os dados parcialmente anonimizados previstos pela fonte (nome abreviado, idade e sexo) até o aceite; acesso clínico completo respeita vínculo e autorização. (Fonte: RF018, RS003)
- **RS-03:** Mudanças de disponibilidade, administração e consulta à trilha de auditoria devem ser rastreáveis com autor e data/hora. (Fonte: RF019, RF022, RNF007)
- **RS-04:** O sistema veda exclusão física de cadastros médicos e registros de prontuário/auditoria, revoga sessões no desligamento profissional, impede inativar o último administrador ativo e protege a imutabilidade dos logs. (Fonte: RS011)

## Fora do escopo desta versão

O documento não define provedor de mensageria, limiares de gargalo, detalhes visuais do painel ou mecanismo de verificação de CRM/certificado.

## Dependências, restrições e questões em aberto

- A fonte não define se casos Vermelhos entram em alguma fila; o PRD 0002 determina encaminhamento de emergência sem fila virtual.
- Esclarecer se os 2 segundos medem criação, envio ou entrega de alerta urgente.
- Definir limiares operacionais do painel e frequência de atualização, sem inventá-los na implementação.
- Confirmar critérios técnicos de validade e revogação de certificado/CRM e o meio de confirmação de entrega Push.
- Confirmar quem pode consultar registros de auditoria e por quanto tempo serão mantidos.
