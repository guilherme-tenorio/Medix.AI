# Spec 0006: Anamnese e classificação de risco

- **Status:** Proposto
- **Requisitos:** RF-01, RF-02 e RF-03 do [PRD 0002](../prd/0002-triagem-acessibilidade-e-emergencia.md)
- **Depende de:** [Spec 0002](0002-cadastro-de-pacientes.md), [Spec 0003](0003-autenticacao-e-sessao.md), [Spec 0004](0004-gestao-de-dependentes.md)
- **Fonte complementar:** RF003, RNF003, RNF006, RS001 e RS004 de `docs/DocumentoRequisitoMEDIX.AI (3).md`

## Pré-condições e entradas

- Paciente titular ou dependente está cadastrado e possui dados de saúde preenchidos.
- Usuário está autenticado e tem autorização sobre o paciente selecionado.
- Entradas: identificação do paciente, relato de sintomas em texto ou transcrição de voz, respostas estruturadas da anamnese e dados de saúde/vitais disponíveis no perfil.

## Fluxo principal

1. Usuário seleciona titular ou dependente; sistema confirma nome, idade e vínculo antes de iniciar.
2. Usuário relata sintomas e responde às perguntas dinâmicas. Dados de saúde do perfil são apresentados ao fluxo de triagem.
3. IA conduz a anamnese e calcula classificação de risco conforme protocolo clínico aprovado.
4. Sistema apresenta resultado e encaminha: Branca/Verde para orientação e avaliação de receita por médico; Amarela/Laranja para fila/atendimento médico; Vermelha para emergência conforme Spec 0007.
5. Sistema registra a triagem no histórico do paciente. Triagem concluída não pode ser alterada ou apagada; uma nova triagem é um registro sequencial.

## Alternativas e erros

- Vínculo não confirmado ou sessão sem autorização: não iniciar triagem.
- Falha/abandono antes da conclusão: o resultado não é apresentado como triagem concluída; persistência de rascunho aguarda definição.
- Classificação Vermelha deve seguir a Spec 0007 e não pode ser retida em fila virtual.
- Falha/indisponibilidade da IA: mensagem orienta o usuário; fallback clínico não foi definido pela fonte.

## Dados, desempenho e regras

- Resultado contém classificação entre Branca, Verde, Amarela, Laranja ou Vermelha, respostas, relato e data/hora conforme fonte.
- Cada etapa de anamnese responde em até 3 segundos em condições normais de rede.
- Dados clínicos são protegidos durante transmissão e armazenamento; acessos são auditáveis.

## Decisões e pendências

- Não iniciar implementação do classificador antes de validação clínica do protocolo, cores, perguntas, regras de red flags, limites de IA e conjunto de testes clínicos.
- Confirmar o uso do Protocolo de Manchester com as cinco cores citadas, incluindo Branco e Vermelho.
- A fonte não define fornecedor/modelo de IA, origem dos dados vitais, manejo de indisponibilidade ou responsabilidade pela classificação; escolhas estruturais podem exigir ADR.
- Serviço de triagem deve receber dados estruturados, executar regras clínicas aprovadas e devolver resultado de domínio; view não recebe lógica clínica ou acesso direto ao ORM.

## Testes

- [ ] Titular autorizado inicia triagem e responsável só inicia para dependente vinculado.
- [ ] Identidade e vínculo são confirmados antes da coleta clínica.
- [ ] As cinco cores encaminham aos fluxos definidos, sem alterar dados de triagem concluída.
- [ ] Dados clínicos são associados ao paciente correto e acessos ficam registrados.
- [ ] Indisponibilidade é tratada sem apresentar classificação inventada.
