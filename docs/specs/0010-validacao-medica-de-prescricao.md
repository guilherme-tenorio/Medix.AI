# Spec 0010: Revisão e validação médica de prescrição

- **Status:** Proposto
- **Requisitos:** RF-01 e RF-04 do [PRD 0003](../prd/0003-atendimento-prescricao-e-prontuario.md)
- **Depende de:** [Spec 0006](0006-triagem-e-classificacao-de-risco.md), [Spec 0008](0008-fila-clinica.md)
- **Fonte complementar:** RF004, RS002, RS006 e RNF008 de `docs/DocumentoRequisitoMEDIX.AI (3).md`

## Pré-condições

- Triagem concluída com resultado Branco ou Verde.
- Médico autenticado, credenciado e com CRM ativo; certificado digital ativo segundo a fonte.

## Fluxo principal

1. Médico abre item pendente de validação e consulta ID da triagem, idade, comorbidades, alergias, sintomas, classificação e fármaco sugerido.
2. Sistema cruza sugestão com alergias/comorbidades registradas e mostra alerta crítico em caso de incompatibilidade.
3. Médico escolhe: aprovar integralmente, aprovar com alterações, ou rejeitar/reclassificar para atendimento síncrono.
4. Para aprovação, médico informa fármaco, posologia/via e instruções, assina digitalmente com certificado ICP-Brasil válido e registra parecer.
5. Aprovação gera entrada para emissão digital (Spec 0011); rejeição/reclassificação encaminha para chat quando indicado.

## Regras e validações

- Nenhuma receita é liberada sem revisão e assinatura de médico credenciado com CRM ativo.
- Fármaco incompatível aciona alerta visual crítico antes da assinatura; a fonte não detalha quais incompatibilidades bloqueiam ou apenas alertam.
- Dados de triagem são imutáveis; parecer médico é acrescentado ao histórico.
- Regras de assinatura devem obedecer ao padrão legal indicado na fonte.

## Pendências/ADR

- Definir formato de parecer, motivos de rejeição e critérios de reclassificação; a fonte só enumera resultados possíveis.
- Definir tratamento para certificado expirado/revogado, assinatura indisponível e conflitos de prescrição.
- Confirmar se alerta de incompatibilidade impede assinatura ou exige justificativa; RS006 usa “bloqueio visual”, sem comportamento inequívoco.
- Integração com certificado/ICP-Brasil e validação de status são escolhas estruturais; registrar ADR antes de implementá-las.

## Testes

- [ ] Casos fora de Branco/Verde não entram no fluxo de prescrição desta spec.
- [ ] Médico não credenciado/CRM inativo não aprova.
- [ ] Aprovação exige parecer, dados prescritos e assinatura válida.
- [ ] Sugestão incompatível mostra alerta antes da assinatura.
- [ ] Rejeição/reclassificação não libera receita.
