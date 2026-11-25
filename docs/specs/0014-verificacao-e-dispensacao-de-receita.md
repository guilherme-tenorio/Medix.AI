# Spec 0014: Verificação e dispensação de receita

- **Status:** Proposto
- **Aprovação:** Aceita pelo responsável em 2026-11-25
- **Requisitos:** RF-03, RF-08 e RS-04 do [PRD 0003](../prd/0003-atendimento-prescricao-e-prontuario.md)
- **Depende de:** [Spec 0011](0011-emissao-e-consulta-de-receita.md)
- **Fonte:** RF009, RS002 de `docs/DocumentoRequisitoMEDIX.AI (4).md`

## Fluxo

1. Farmacêutico abre o QR Code/código e consulta a página pública de autenticidade.
2. A página pública é limitada à conferência de autenticidade e mostra o status, nome do médico, CRM/UF, data/hora, fármacos e validade/validação ICP-Brasil indicados pela fonte; não mostra CPF.
3. Para registrar dispensação, o farmacêutico informa CRF e a farmácia informa CNPJ.
4. O sistema valida que a receita está ativa e nunca foi dispensada; registra a dispensação com data/hora permanente.
5. Tentativa para receita revogada, inexistente ou já dispensada é recusada e não altera o registro anterior.

## Regras de domínio

- Uma receita pode ser dispensada no máximo uma vez.
- Revogação ou dispensação torna a receita indisponível para baixa subsequente.
- A gravação deve ser atômica para evitar dispensações concorrentes.
- Registrar ator identificado como farmacêutico, CRF, CNPJ, instante e identificador da receita; auditar tentativas inválidas conforme política de segurança.

## Pendências

- A fonte não define como validar a regularidade de CRF/CNPJ nem o método de autenticação/identificação do farmacêutico para a baixa.
- A página é pública para autenticação, mas dados que não sejam os campos enumerados acima não devem ser expostos. Definir controles contra enumeração do identificador.

## Testes

- [ ] Receita ativa permite uma baixa e registra data/hora.
- [ ] Segunda baixa, receita revogada ou identificador inválido são recusados.
- [ ] Duas solicitações concorrentes não geram dispensação duplicada.
- [ ] Página pública não revela CPF ou conteúdo clínico.