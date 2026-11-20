# Spec 0012: Prontuário e histórico de atendimentos

- **Status:** Proposto
- **Requisitos:** RF-06 e RF-07 do [PRD 0003](../prd/0003-atendimento-prescricao-e-prontuario.md)
- **Depende de:** [Spec 0004](0004-gestao-de-dependentes.md), [Spec 0006](0006-triagem-e-classificacao-de-risco.md), [Spec 0009](0009-chat-medico.md) e [Spec 0011](0011-emissao-e-consulta-de-receita.md)
- **Fonte complementar:** RF008, RNF006–RNF008, RS001 e RS003 de `docs/DocumentoRequisitoMEDIX.AI (3).md`

## Pré-condições

- Usuário está autenticado e seleciona o próprio histórico ou dependente associado.

## Fluxo principal

1. Sistema apresenta eventos em ordem cronológica: triagens, consultas por chat, receitas e alertas de emergência.
2. Usuário pode filtrar por período, tipo de evento e classificação de cor.
3. Cada item mostra data/hora, tipo, cor quando houver, profissional envolvido e resumo da conduta.
4. Titular vê seus registros; responsável vê somente dependentes autorizados; profissional vê prontuário conforme vínculo autorizado de atendimento.

## Regras e erros

- Período precisa conter datas válidas e início não posterior ao fim.
- Consulta de terceiro sem vínculo é negada e auditada.
- Triagem concluída é imutável e não pode ser apagada pelo usuário. A fonte não define correção ou exclusão dos demais tipos de registro clínico; esclarecer antes de implementar essas operações.
- Preservar registros por prazo mínimo de 20 anos indicado na fonte, sujeito à validação regulatória.
- Dados de prontuário são confidenciais e protegidos em trânsito e armazenamento.

## Dados e pendências

- Filtros: paciente selecionado, intervalo de datas, tipo de evento (triagem, chat, receita, emergência) e cor.
- A fonte não define paginação, busca textual, exportação, ordem de eventos com timestamps iguais, alteração de correções nem políticas de acesso de auditoria.
- Confirmar prazo legal e regras de retenção aplicáveis por tipo de registro antes da implementação.
- Views não fazem consultas ORM; services filtram e autorizam conforme titular/dependente/profissional.

## Testes

- [ ] Eventos das quatro categorias aparecem cronologicamente.
- [ ] Filtros válidos combinam-se; intervalo inválido é rejeitado.
- [ ] Titular/responsável/profissional só acessa registros autorizados.
- [ ] Tentativa não autorizada é recusada e auditada.
- [ ] Registro clínico não pode ser apagado nem editado por usuário comum.
