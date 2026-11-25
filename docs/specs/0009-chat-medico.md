# Spec 0009: Atendimento síncrono por chat

- **Status:** Proposto
- **Aprovação:** Aceita pelo responsável em 2026-11-25
- **Requisitos:** RF-05 do [PRD 0003](../prd/0003-atendimento-prescricao-e-prontuario.md)
- **Depende de:** [Spec 0007](0007-encaminhamento-de-emergencia.md), [Spec 0008](0008-fila-clinica.md)
- **Fonte complementar:** RF010, RF011, RNF004, RNF006, RNF007 e RS003 de `docs/DocumentoRequisitoMEDIX.AI (4).md`

## Pré-condições

- Triagem está classificada Amarela ou Laranja, ou médico encaminhou deliberadamente durante revisão.
- Paciente/responsável e médico estão autenticados; o médico aceitou o chamado da fila.

## Fluxo principal

1. Aceitação do chamado cria sessão identificada e associa médico, paciente e triagem.
2. Médico acessa a sala no painel clínico pelo navegador e vê, antes da primeira mensagem, o resumo da triagem e dados de saúde/alergias necessários; paciente/responsável acompanha pelo aplicativo.
3. Participantes trocam mensagens síncronas criptografadas; cada mensagem registra timestamp, estado de entrega e leitura.
4. Paciente pode enviar anexos PDF, PNG ou JPEG de até 10 MB e áudio de até 120 segundos com transcrição STT. O áudio bruto é eliminado após transcrição conforme Spec 0001.
5. Médico registra tipo de desfecho obrigatório, resumo/conduta e sinais de alerta. Red flag ou reclassificação Vermelha aciona Spec 0007 imediatamente. Encerramento torna o diálogo imutável, atualiza fila e prontuário (Specs 0008 e 0012).

## Regras e erros

- Mensagens e estados sincronizam em até 1 segundo.
- Acesso à sessão é limitado aos participantes autorizados e vínculos válidos.
- Anexo com formato/tamanho não permitido é rejeitado com mensagem clara.
- Reclassificação para Vermelho dispara Spec 0007 imediatamente; sessão não deve reter o paciente.
- Falha de conexão, abandono, reconexão, indisponibilidade do médico e prazo de atendimento não têm comportamento definido na fonte.

## Dados e decisões

- Sessão, médico (nome/CRM), paciente (nome, idade, sexo e resumo), mensagem de texto até 1000 caracteres, anexos, áudio e desfecho/conduta até 1000 caracteres.
- RF010 pede mensagem de áudio e transcrição, enquanto RF015/RNF006/RS009 determinam descarte imediato dos arquivos brutos após transcrição. Esta spec interpreta que o áudio bruto é transitório e só a transcrição textual permanece; confirmar antes de armazenar qualquer gravação.
- Escolha de comunicação em tempo real, armazenamento de anexos e consentimento para anexos exigem definição de arquitetura/privacidade; avaliar ADR quando estruturais.

## Testes

- [ ] Somente triagem elegível e médico que aceitou podem acessar a sessão.
- [ ] Mensagens recebem timestamps auditáveis e sincronizam no limite previsto.
- [ ] Arquivos acima dos limites ou fora dos formatos permitidos são recusados.
- [ ] Reclassificação Vermelha dispara encaminhamento de emergência.
- [ ] Usuário fora do vínculo não lê mensagens nem anexos.


## Fonte vigente

A fonte atual de requisitos é docs/DocumentoRequisitoMEDIX.AI (4).md (2026-11-24). Quando o texto desta spec divergir de requisito RF/RNF/RS atualizado nessa fonte, prevalece a fonte e deve-se ajustar a especificação antes de implementar.


## Requisitos atualizados da fonte

- Antes da primeira mensagem, médico vê resumo clínico e alergias. Chat em tempo real é criptografado; registra entrega/leitura; aceita anexos PDF/JPEG/PNG até 10 MB e áudio até 120 segundos com STT.
- Ao encerrar, médico registra desfecho e plano clínico obrigatório antes de retornar à fila. Red flags ou reclassificação Vermelha iniciam fluxo de emergência.
- Diálogo concluído é imutável. Definir formatos/tipos do desfecho, limites contra conteúdo malicioso em anexos e como o usuário é informado sobre indisponibilidade.