# Spec 0009: Atendimento síncrono por chat

- **Status:** Proposto
- **Requisitos:** RF-05 do [PRD 0003](../prd/0003-atendimento-prescricao-e-prontuario.md)
- **Depende de:** [Spec 0007](0007-encaminhamento-de-emergencia.md), [Spec 0008](0008-fila-clinica.md)
- **Fonte complementar:** RF006, RNF004, RNF006, RNF007, RS003 e RF007 de `docs/DocumentoRequisitoMEDIX.AI (3).md`

## Pré-condições

- Triagem está classificada Amarela ou Laranja, ou médico encaminhou deliberadamente durante revisão.
- Paciente/responsável e médico estão autenticados; o médico aceitou o chamado da fila.

## Fluxo principal

1. Aceitação do chamado cria sessão identificada e associa médico, paciente e triagem.
2. Médico visualiza dados cadastrais necessários e resumo da triagem antes da interação.
3. Participantes trocam mensagens síncronas; cada mensagem tem data/hora auditável.
4. Podem ser enviados anexos PDF, PNG ou JPEG de até 10 MB e áudio de até 120 segundos, conforme fonte. O áudio capturado deve seguir a regra de descarte da [Spec 0001](0001-interacao-por-voz-e-acessibilidade.md); retenção de mensagens de áudio enviadas no chat requer esclarecimento específico.
5. Médico registra desfecho clínico e conduta. Encerramento atualiza o estado da fila e o histórico (Specs 0008 e 0012).

## Regras e erros

- Mensagens e estados sincronizam em até 1 segundo.
- Acesso à sessão é limitado aos participantes autorizados e vínculos válidos.
- Anexo com formato/tamanho não permitido é rejeitado com mensagem clara.
- Reclassificação para Vermelho dispara Spec 0007 imediatamente; sessão não deve reter o paciente.
- Falha de conexão, abandono, reconexão, indisponibilidade do médico e prazo de atendimento não têm comportamento definido na fonte.

## Dados e decisões

- Sessão, médico (nome/CRM), paciente (nome, idade, sexo e resumo), mensagem de texto até 1000 caracteres, anexos, áudio e desfecho/conduta até 1000 caracteres.
- A fonte pede histórico integral de mensagens e timestamps auditáveis. Retenção de anexos e política de exclusão não estão especificadas; RS009 fala de áudios de voz usados na transcrição, mas não esclarece áudio anexado ao chat.
- Escolha de comunicação em tempo real, armazenamento de anexos e consentimento para anexos exigem definição de arquitetura/privacidade; avaliar ADR quando estruturais.

## Testes

- [ ] Somente triagem elegível e médico que aceitou podem acessar a sessão.
- [ ] Mensagens recebem timestamps auditáveis e sincronizam no limite previsto.
- [ ] Arquivos acima dos limites ou fora dos formatos permitidos são recusados.
- [ ] Reclassificação Vermelha dispara encaminhamento de emergência.
- [ ] Usuário fora do vínculo não lê mensagens nem anexos.
