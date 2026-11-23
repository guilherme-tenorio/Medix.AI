# Spec 0006: Anamnese e classificação de risco

- **Status:** Proposto
- **Requisitos:** RF-01, RF-02 e RF-03 do [PRD 0002](../prd/0002-triagem-acessibilidade-e-emergencia.md)
- **Depende de:** [Spec 0002](0002-cadastro-de-pacientes.md), [Spec 0003](0003-autenticacao-e-sessao.md), [Spec 0004](0004-gestao-de-dependentes.md)
- **Fonte complementar:** RF003–RF005, RNF003, RNF006, RNF010, RS001, RS004 e RS010 de `docs/Cópia de DocumentoRequisitoMEDIX.AI.md`

## Pré-condições e entradas

- Paciente titular ou dependente está cadastrado e possui dados de saúde preenchidos.
- Usuário está autenticado e tem autorização sobre o paciente selecionado.
- Entradas: identificação do paciente, relato de sintomas em texto ou transcrição de voz, respostas estruturadas da anamnese e dados de saúde/vitais disponíveis no perfil.

## Fluxo principal

1. Usuário seleciona titular ou dependente; sistema confirma nome, idade e vínculo antes de iniciar.
2. Usuário relata sintomas e responde às perguntas dinâmicas. Dados de saúde do perfil são apresentados ao fluxo de triagem.
3. IA conduz a entrevista e estrutura as respostas; regras determinísticas aprovadas conforme Protocolo de Manchester calculam a classificação de risco. A IA não escolhe nem pode alterar a cor.
4. Sistema apresenta resultado e encaminha: Branca/Verde para orientação e avaliação de receita por médico; Amarela/Laranja para fila/atendimento médico; Vermelha para emergência conforme Spec 0007.
5. Sistema registra a triagem no histórico do paciente. Triagem concluída não pode ser alterada ou apagada; uma nova triagem é um registro sequencial.

## Alternativas e erros

- Vínculo não confirmado ou sessão sem autorização: não iniciar triagem.
- Falha/abandono antes da conclusão: o resultado não é apresentado como triagem concluída; persistência de rascunho aguarda definição.
- Classificação Vermelha deve seguir a Spec 0007 e não pode ser retida em fila virtual.
- Falha/indisponibilidade da IA: mensagem orienta o usuário; fallback clínico não foi definido pela fonte.

## Dados, desempenho e regras

- Resultado contém classificação entre Branca, Verde, Amarela, Laranja ou Vermelha, respostas, relato e data/hora conforme fonte.
- Cada etapa de anamnese responde em até 5 segundos em condições normais de rede.
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

## Atualização da fonte de requisitos (2026-11-23)

- A anamnese registra início/duração do sintoma e intensidade de 0 a 10; as perguntas adaptativas consideram o perfil clínico.
- A transcrição com baixa confiança exige confirmação do usuário, conforme Spec 0001.
- A classificação de Manchester segue regras determinísticas e red flags aprovadas clinicamente; o sistema gera identificador único imutável e resumo do caso.
- Antes da chamada externa de LLM, o backend remove nome e CPF e envia apenas faixa etária, sexo e dados clínicos desidentificados necessários. A chamada é REST sobre HTTPS com JSON estruturado. Timeout/indisponibilidade apresenta orientação de indisponibilidade sem criar classificação.
- Encaminhamento atualizado: Branca/Verde para avaliação médica (Spec 0010), Amarela/Laranja para chat (Spec 0009) e Vermelha para emergência (Spec 0007).
- Triagem concluída é imutável. A fonte não define provedor/modelo, limiar de confiança, versão clínica do protocolo nem retenção do contexto pelo provedor; permanecem pendentes.


## Fonte vigente

A fonte atual de requisitos é docs/Cópia de DocumentoRequisitoMEDIX.AI.md (2026-11-23). Quando o texto desta spec divergir de requisito RF/RNF/RS atualizado nessa fonte, prevalece a fonte e deve-se ajustar a especificação antes de implementar.
