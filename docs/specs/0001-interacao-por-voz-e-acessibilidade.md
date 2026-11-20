# Spec 0001: Interação por voz e acessibilidade

- **Status:** Proposto
- **Requisitos:** RF-09 do [PRD 0001](../prd/0001-contas-perfis-e-pacientes.md), RF-05 e RF-06 do [PRD 0002](../prd/0002-triagem-acessibilidade-e-emergencia.md)
- **Fonte complementar:** RF009, RNF001, RNF002, RNF006 e RS009 de `docs/DocumentoRequisitoMEDIX.AI (3).md`

## Fluxo

1. O usuário escolhe interação por voz ou digitação. A troca entre modos pode ocorrer durante cadastro ou triagem.
2. Para falar, o usuário concede acesso ao microfone. O sistema captura fala e a converte em texto para auxiliar o preenchimento ou conduzir a anamnese.
3. O sistema pode reproduzir por áudio perguntas, resultados e orientações médicas, em português acessível e pausado.
4. Se o microfone não estiver disponível ou a permissão for negada, o sistema informa a limitação e permite continuar digitando.
5. Após a transcrição validada, o áudio clínico é descartado; o texto validado pode seguir para o fluxo de cadastro ou triagem correspondente.

## Regras e validações

- A interface oferece ativação e desativação do modo de voz a qualquer momento.
- O áudio só é capturado com permissão do dispositivo; a fonte pede filtragem básica de ruído.
- A fonte exige que o texto transcrito interprete termos populares e descrições simples de sintomas.
- A fonte determina descarte imediato do áudio após conversão para texto validado; não manter cópia persistente.
- Oferecer também dicas visuais, alto contraste, fontes legíveis e mensagens claras para erros e indisponibilidade.

## Contratos e decisões pendentes

- Definir onde o usuário revisa/corrige a transcrição antes do envio: a fonte não define esse passo.
- Definir o comportamento se a transcrição não puder ser validada, incluindo o momento seguro para descarte do áudio.
- Escolher solução de STT/TTS, tratamento de áudio e política de retenção temporária; avaliar ADR antes de uma escolha estrutural. A arquitetura não especifica esses contratos.
- Os fluxos de cadastro e triagem são especificados, respectivamente, nas Specs 0002 e 0006.

## Testes

- [ ] O usuário alterna entre voz e digitação durante cadastro e triagem.
- [ ] Sem permissão de microfone, a mensagem orienta e a digitação continua disponível.
- [ ] Perguntas e orientações são disponibilizadas para leitura sintetizada.
- [ ] O áudio é descartado após transcrição validada e não aparece no registro persistente.
- [ ] Falhas de microfone e transcrição apresentam mensagem acessível.
