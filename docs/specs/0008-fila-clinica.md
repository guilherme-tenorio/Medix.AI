# Spec 0008: Fila clínica e disponibilidade médica

- **Status:** Proposto
- **Requisitos:** RF-01, RF-02 e RF-03 do [PRD 0004](../prd/0004-fila-medica-e-notificacoes.md)
- **Depende de:** [Spec 0005](0005-gestao-de-profissionais.md), [Spec 0006](0006-triagem-e-classificacao-de-risco.md)
- **Fonte complementar:** RF018, RF019, RNF004, RNF007 e RNF009 de `docs/Cópia de DocumentoRequisitoMEDIX.AI.md`

## Pré-condições e fluxo

1. Médico autenticado e ativo marca-se disponível para atendimento.
2. Painel clínico responsivo é acessado pelo navegador; expõe uma fila para chat síncrono e outra para revisão de prescrição.
3. Fila recebe triagens elegíveis e mostra cor, tempo desde conclusão, identificador parcial (nome abreviado, idade e sexo) e estado do chamado.
4. Cada fila ordena automaticamente por gravidade (Laranja, Amarela, Verde, Branca) e usa maior espera como desempate dentro da mesma cor.
5. Médico filtra por cor, espera e tipo de demanda e aceita chamado elegível.
6. Aceitação muda status para “Em Atendimento” e vincula o médico. Estados incluem Aguardando Atendimento, Em Atendimento, Aguardando Validação de Receita e Finalizado.
7. Médico alterna status Online, Pausa e Offline, atualiza telefone operacional e consulta histórico de turnos/atendimentos com timestamp. Offline impede novos chamados sem cancelar os em curso.

## Regras e erros

- Antes da aceitação, mostrar somente resumo de identidade previsto; detalhe clínico só após autorização/aceitação.
- Não permitir edição manual de status da fila; alterações seguem eventos do fluxo.
- Fila e sincronização de status devem atualizar em até 1 segundo.
- Cor Vermelha segue encaminhamento de emergência e não deve permanecer em fila virtual (Spec 0007).
- Somente médico homologado com CRM regular e certificado ICP-Brasil ativo pode ficar Online.
- O painel médico é web; o cadastro e a experiência do paciente pertencem ao aplicativo móvel, sem autocadastro profissional.
- Se o médico ficar inativo ou perder autorização, não pode aceitar novos chamados; tratamento de chamado já aceito aguarda definição.

## Pendências

- A fonte define filas separadas para chat e revisão de prescrição; não define se um médico pode atender simultaneamente nas duas nem a regra de disponibilidade quando há múltiplas demandas.
- Ordem/empate além da cor e tempo, limite de chamados simultâneos, timeout de aceitação e alertas de gargalo não têm limiares definidos.
- Definir a regra de disponibilidade quando o médico encerra uma consulta mas mantém outras demandas.
- Atualização em tempo real e compatibilidade web dependem de decisões da arquitetura; avaliar ADR para mecanismo estrutural.

## Testes

- [ ] Fila aplica ordem por gravidade e desempate por tempo.
- [ ] Resumo pré-aceitação não expõe dados clínicos detalhados.
- [ ] Aceitar muda status e disponibilidade; encerramento libera o médico conforme regras aprovadas.
- [ ] Usuário não autorizado não aceita chamado nem altera status.
- [ ] Mudanças são sincronizadas dentro do limite especificado.
- [ ] Filas de chat e revisão são separadas; telefone operacional e histórico de plantão são mantidos no painel web.


## Fonte vigente

A fonte atual de requisitos é docs/Cópia de DocumentoRequisitoMEDIX.AI.md (2026-11-23). Quando o texto desta spec divergir de requisito RF/RNF/RS atualizado nessa fonte, prevalece a fonte e deve-se ajustar a especificação antes de implementar.


## Requisitos atualizados da fonte

- Prioridade: Laranja, Amarela, Verde, Branca; dentro da mesma cor, maior tempo de espera primeiro. Fila de chat e fila de revisão de prescrição são separadas.
- Antes do aceite, exibir dados parciais anonimizados; após aceite, liberar dados necessários ao atendimento.
- Médico define Online/Disponível, Pausa ou Offline. Offline impede novos chamados, sem encerrar atendimento iniciado. Online requer CRM e certificado ICP-Brasil válidos.
- Médico pode atualizar telefone operacional e tem histórico de turnos/atendimentos com timestamp; administrador consulta lista de médicos em plantão ativo.
- Casos Vermelhos seguem emergência, fora da fila virtual. Critérios de desempate adicional e frequência de atualização não estão definidos.
