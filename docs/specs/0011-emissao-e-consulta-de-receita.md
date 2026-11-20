# Spec 0011: Emissão e consulta de receita digital

- **Status:** Proposto
- **Requisitos:** RF-02 e RF-03 do [PRD 0003](../prd/0003-atendimento-prescricao-e-prontuario.md)
- **Depende de:** [Spec 0010](0010-validacao-medica-de-prescricao.md)
- **Fonte complementar:** RF005, RNF006, RNF008, RS001, RS002 e RS006 de `docs/DocumentoRequisitoMEDIX.AI (3).md`

## Pré-condição

- Existe prescrição aprovada e assinada por médico credenciado na Spec 0010.

## Fluxo principal

1. Após aprovação assinada, sistema gera identificador único, documento PDF, QR/código de verificação, dados do prescritor e paciente, itens prescritos, orientações, data/hora e status.
2. Receita é disponibilizada ao paciente autenticado para visualizar ou baixar.
3. Farmácia ou pessoa que apresenta o código consulta a página pública de verificação e confirma autenticidade/status, sem revelar dados além do permitido (escopo público não definido).
4. Receita pode transitar entre estados Ativa/Válida, Utilizada/Dispensada e Expirada/Revogada, segundo regras ainda por definir.

## Regras e erros

- Receita não pode ser gerada sem assinatura válida nem vinculada a paciente diferente da triagem confirmada.
- Dados incluem identificador, código QR, médico/CRM/UF, paciente/CPF, medicamentos/posologia, orientações, emissão e status conforme RF005.
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
