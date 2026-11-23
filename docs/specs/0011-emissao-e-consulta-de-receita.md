# Spec 0011: Emissão e consulta de receita digital

- **Status:** Proposto
- **Requisitos:** RF-02 e RF-03 do [PRD 0003](../prd/0003-atendimento-prescricao-e-prontuario.md)
- **Depende de:** [Spec 0010](0010-validacao-medica-de-prescricao.md)
- **Fonte complementar:** RF007, RF008, RNF006, RNF008, RS002 e RS006 de `docs/Cópia de DocumentoRequisitoMEDIX.AI.md`

## Pré-condição

- Existe prescrição aprovada e assinada por médico credenciado na Spec 0010.

## Fluxo principal

1. Após aprovação assinada, sistema gera identificador único, documento PDF, QR/código de verificação, dados do prescritor e paciente, itens prescritos, orientações, data/hora e status.
2. Receita é disponibilizada ao paciente autenticado para visualizar ou baixar.
3. Farmácia ou pessoa que apresenta o código consulta a página pública de verificação e confirma autenticidade/status, sem revelar dados além do permitido (escopo público não definido).
4. Receita pode transitar entre estados Ativa/Válida, Utilizada/Dispensada e Expirada/Revogada, segundo regras ainda por definir.

## Regras e erros

- Receita não pode ser gerada sem assinatura válida nem vinculada a paciente diferente da triagem confirmada.
- O registro interno pode vincular o CPF do paciente para associação segura ao prontuário; **o CPF não aparece no PDF**. PDF exibe UUID, QR, nome do paciente, médico/CRM/UF, fármacos/posologia, orientações, emissão e validade regulamentar conforme RF008.
- A fonte exige tráfego seguro e consentimento do paciente. Conteúdo e momento do consentimento precisam de definição.
- QR inválido, assinatura inválida, revogação ou receita expirada não podem ser apresentados como válidos.

## Decisões pendentes

- Definir consulta pública via QR: quais dados são exibidos, controle contra enumeração e validade do código.
- Definir transição e critérios para estados utilizada, expirada ou revogada; regras de dispensação não constam integralmente na fonte.
- Confirmar legalidade, conteúdo obrigatório, assinatura e prazo aplicável com responsável competente.
- Serviço de assinatura, emissão PDF e verificação externa requerem avaliação de ADR quando definidos.

## Testes

- [ ] Aprovação válida gera uma receita única associada à triagem, ao paciente e ao médico corretos.
- [ ] Sem assinatura válida não há PDF/QR utilizável.
- [ ] Titular autorizado consulta/baixa a receita; outro usuário não acessa conteúdo restrito.
- [ ] Verificador identifica receita inválida/revogada/expirada sem marcá-la válida.
- [ ] Eventos de emissão e acesso entram na trilha de auditoria.


## Fonte vigente

A fonte atual de requisitos é docs/Cópia de DocumentoRequisitoMEDIX.AI.md (2026-11-23). Quando o texto desta spec divergir de requisito RF/RNF/RS atualizado nessa fonte, prevalece a fonte e deve-se ajustar a especificação antes de implementar.


## Requisitos atualizados da fonte

- Receita exige assinatura ICP-Brasil e CRM válido, hash criptográfico e carimbo de tempo; documento PDF é imutável, sem CPF, inclui paciente, prescritor, medicamento/posologia e validade regulamentar.
- QR aponta a página de validação. Revogação requer justificativa e desativa imediatamente a dispensação. Emissão notifica por Push/SMS.
- Consulta pública de autenticidade apresenta status e dados de validação descritos na fonte: médico/CRM/UF, data/hora, fármacos e validade da assinatura ICP-Brasil; não apresenta CPF.
- Definir campos públicos mínimos, regra de validade, certificado/provedor de assinatura e resposta a falha de integração antes de implementar.
