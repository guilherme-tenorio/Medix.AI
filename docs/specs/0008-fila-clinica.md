# Spec 0008: Fila clínica e disponibilidade médica

- **Status:** Proposto
- **Requisitos:** RF-01, RF-02 e RF-03 do [PRD 0004](../prd/0004-fila-medica-e-notificacoes.md)
- **Depende de:** [Spec 0005](0005-gestao-de-profissionais.md), [Spec 0006](0006-triagem-e-classificacao-de-risco.md)
- **Fonte complementar:** RF011, RNF004, RNF007 e RNF009 de `docs/DocumentoRequisitoMEDIX.AI (3).md`

## Pré-condições e fluxo

1. Médico autenticado e ativo marca-se disponível para atendimento.
2. Fila recebe triagens elegíveis e mostra cor, tempo desde conclusão, nome abreviado, idade, gênero e status do chamado.
3. Fila reordena automaticamente por gravidade (Laranja, Amarela, Verde, Branca) e usa maior espera como desempate dentro da mesma cor.
4. Médico filtra por cor, tempo de espera ou identificador e aceita chamado elegível.
5. Aceitação muda status para “Em Atendimento” e retira o médico da lista de disponíveis. Ao encerrar e não haver outra demanda ativa, médico retorna à disponibilidade.
6. Estados descritos na fonte: Aguardando Atendimento, Em Atendimento, Aguardando Validação de Receita e Finalizado.

## Regras e erros

- Antes da aceitação, mostrar somente resumo de identidade previsto; detalhe clínico só após autorização/aceitação.
- Não permitir edição manual de status da fila; alterações seguem eventos do fluxo.
- Fila e sincronização de status devem atualizar em até 1 segundo.
- Cor Vermelha segue encaminhamento de emergência e não deve permanecer em fila virtual (Spec 0007).
- Se o médico ficar inativo ou perder autorização, não pode aceitar novos chamados; tratamento de chamado já aceito aguarda definição.

## Pendências

- A fonte inclui casos de chat Amarelo/Laranja e validações de receita Branca/Verde no painel, mas não define se compartilham fila, telas ou disponibilidade do profissional.
- Ordem/empate além da cor e tempo, limite de chamados simultâneos, timeout de aceitação e alertas de gargalo não têm limiares definidos.
- Definir a regra de disponibilidade quando o médico encerra uma consulta mas mantém outras demandas.
- Atualização em tempo real e compatibilidade web dependem de decisões da arquitetura; avaliar ADR para mecanismo estrutural.

## Testes

- [ ] Fila aplica ordem por gravidade e desempate por tempo.
- [ ] Resumo pré-aceitação não expõe dados clínicos detalhados.
- [ ] Aceitar muda status e disponibilidade; encerramento libera o médico conforme regras aprovadas.
- [ ] Usuário não autorizado não aceita chamado nem altera status.
- [ ] Mudanças são sincronizadas dentro do limite especificado.
