# Spec 0007: Encaminhamento de emergência

- **Status:** Proposto
- **Requisitos:** RF-04 do [PRD 0002](../prd/0002-triagem-acessibilidade-e-emergencia.md)
- **Depende de:** [Spec 0006](0006-triagem-e-classificacao-de-risco.md)
- **Fonte complementar:** RF012, RF013, RNF003, RNF005 e RS004 de `docs/Cópia de DocumentoRequisitoMEDIX.AI.md`

## Gatilhos

- Triagem classificada Vermelha; ou
- Médico reclassifica como Vermelha durante atendimento por chat.

## Fluxo principal

1. Ao receber o gatilho, sistema interrompe etapas comuns e exibe alerta destacado para procurar atendimento presencial urgente.
2. Alerta apresenta sintomas graves detectados e orientação imediata; não exige etapas burocráticas nem aguarda fila virtual.
3. Se localização estiver ativada, sistema apresenta hospitais/prontos-socorros próximos por distância e rota.
4. Com GPS desativado, o alerta e a orientação permanecem disponíveis; mensagem explica indisponibilidade da lista/rota, comportamento detalhado a validar.
5. O evento é registrado no histórico clínico e alerta é disparado em até 2 segundos, conforme RNF003.

## Dados e controles

- Alerta: mensagem até 500 caracteres na fonte.
- Ficha resumida: nome, idade, tipo sanguíneo, alergias e comorbidades.
- Localização: coordenadas do aparelho somente quando GPS ativado.
- Unidades próximas: nome, endereço e distância, ordenadas por proximidade.
- Regras determinísticas de red flags têm prioridade máxima sobre fluxos virtuais, conforme RS004.

## Pendências e decisões

- Definir origem dos dados de hospitais, atualização, cobertura geográfica e o que exibir sem localização.
- A fonte não prevê ligação automática a serviço de emergência; não realizar esse acionamento sem decisão explícita.
- Confirmar texto clínico do alerta, red flags e validação por responsável clínico antes de implementação.
- A escolha de fornecedor de geolocalização/mapas pode demandar ADR.

## Testes

- [ ] Vermelho oriundo de IA interrompe fluxo comum e não entra na fila virtual.
- [ ] Reclassificação Vermelha pelo médico gera o mesmo encaminhamento.
- [ ] GPS ativo mostra unidades e rotas ordenadas por proximidade.
- [ ] GPS desativado não impede alerta e orientação urgente.
- [ ] Alerta não é atrasado por coleta de localização.


## Fonte vigente

A fonte atual de requisitos é docs/Cópia de DocumentoRequisitoMEDIX.AI.md (2026-11-23). Quando o texto desta spec divergir de requisito RF/RNF/RS atualizado nessa fonte, prevalece a fonte e deve-se ajustar a especificação antes de implementar.


## Requisitos atualizados da fonte

- Alerta Vermelho ocupa a tela, apresenta sintomas e resumo clínico, emite orientação por TTS e cria registro de emergência sem encaminhar a fila virtual.
- Exibe hospitais/prontos-socorros por distância e oferece rota externa. GPS desativado não remove o alerta: permite ativação ou busca manual por bairro/cidade; lista acompanha localização.
- Alertas urgentes são disparados em até 2 segundos. A fonte não indica diretório de unidades, integração de mapas ou contato automático com serviço de emergência.
