# Spec 0013: Notificações e alertas

- **Status:** Proposto
- **Requisitos:** RF-04, RF-05 e RF-06 do [PRD 0004](../prd/0004-fila-medica-e-notificacoes.md)
- **Depende de:** [Spec 0008](0008-fila-clinica.md), [Spec 0009](0009-chat-medico.md), [Spec 0010](0010-validacao-medica-de-prescricao.md), [Spec 0011](0011-emissao-e-consulta-de-receita.md) e [Spec 0012](0012-prontuario-e-historico.md)
- **Fonte complementar:** RF020, RNF002–RNF007, RS005 e RS008 de `docs/Cópia de DocumentoRequisitoMEDIX.AI.md`

## Gatilhos e fluxo

1. Evento do produto gera aviso ao paciente, responsável ou profissional pertinente: início de chat, receita aprovada/liberada, entrada na fila, alerta clínico ou lembrete previsto.
2. Sistema consulta preferências de tipo e canal e envia push, SMS, e-mail ou WhatsApp quando disponível e habilitado.
3. Aviso contém título, corpo, prioridade e link para chat, receita ou alerta correspondente.
4. Para push de chamada médica ativa sem confirmação por 30 segundos, sistema aciona SMS alternativo.
5. Usuário pode consultar notificações, pesquisar por usuário/canal/período/status e limpar notificações informativas lidas. Notificações críticas permanecem no log de auditoria.
6. Administrador pesquisa histórico de notificações no painel web; preferências de canais são mantidas no perfil do usuário. A fonte não esclarece se preferências podem suprimir eventos urgentes.

## Regras de conteúdo e desempenho

- Título até 80 caracteres; corpo até 300; prioridade Informativo, Moderado ou Urgente; deep link até 200, conforme fonte.
- Mensagem em tela bloqueada não expõe diagnóstico nem dado clínico; detalhe exige autenticação ativa (RS005).
- Alertas críticos/urgentes têm prioridade de envio; RNF003 determina disparo em até 2 segundos. RNF005 determina fallback após 30 segundos sem confirmação.
- Falha de entrega deve atualizar o status pesquisável; política de tentativas adicionais não está definida.
- Cada notificação possui UUID, destinatário, canal, prioridade, título (até 80), mensagem mascarada (até 300), deep link (até 200) e status de entrega/lida/falha/fallback conforme RF020.
- Limpar uma notificação lida da central não remove o registro de auditoria imutável.

## Pendências/decisões

- Definir qual canal é habilitado por padrão, consentimento/preferências e como tratar canal inválido.
- Esclarecer se os 2 segundos de RNF003 medem criação, despacho ou entrega e como se conciliam com fallback de 30 segundos.
- Definir confirmação de entrega, repetição, idempotência, retenção do log e autorização de consulta administrativa.
- Definir proteção e validade dos deep links; escolha de provedores de push/SMS/e-mail/WhatsApp pode exigir ADR.
- Fonte não define exatamente quais preferências o usuário pode configurar nem o tratamento de conflito entre preferência e alerta urgente; não descartar evento urgente obrigatório por preferência sem validação de produto.

## Testes

- [ ] Eventos suportados geram aviso para destinatários vinculados.
- [ ] Preferências de canal e tipo são respeitadas.
- [ ] Push de chamada sem confirmação aciona SMS após 30 segundos.
- [ ] Notificação bloqueada/visível não revela dados clínicos.
- [ ] Pesquisa aplica filtros e notificações críticas não são apagadas pelo usuário.


## Fonte vigente

A fonte atual de requisitos é docs/Cópia de DocumentoRequisitoMEDIX.AI.md (2026-11-23). Quando o texto desta spec divergir de requisito RF/RNF/RS atualizado nessa fonte, prevalece a fonte e deve-se ajustar a especificação antes de implementar.


## Requisitos atualizados da fonte

- Canais: Push, SMS, e-mail e WhatsApp; links profundos abrem o fluxo correspondente. Notificações urgentes devem ser disparadas em até 2 segundos.
- Se Push de chamada médica não tiver confirmação em 30 segundos, enviar SMS. Conteúdo visível em tela bloqueada mascara dados clínicos.
- A fonte não define provedor, confirmação técnica de entrega/leitura por canal ou comportamento quando todos os canais falham.
