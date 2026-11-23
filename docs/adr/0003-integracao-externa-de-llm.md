# ADR 0003: Integração externa de LLM para anamnese

- **Status:** Proposto
- **Data:** 2026-11-23

## Contexto

A fonte atual exige integração da anamnese com um provedor externo de LLM por REST sobre HTTPS, usando JSON estruturado. Também determina que dados enviados sejam desidentificados pelo backend e limitados a atributos clínicos especificados. A escolha afeta privacidade e todos os fluxos de triagem.

## Decisão

- A integração com o provedor externo é iniciada exclusivamente pelo backend, por API REST sobre HTTPS, com requisição e resposta JSON estruturadas.
- Antes do envio, o backend remove identificadores diretos, incluindo nome e CPF. Envia somente faixa etária, sexo, sintomas, alergias e comorbidades necessários à anamnese.
- Nenhum segredo ou credencial do provedor é exposto ao cliente.
- A escolha do fornecedor, retenção pelo provedor, região de processamento, contrato de dados e estratégia de contingência ficam pendentes e devem ser aprovados antes de habilitar tráfego clínico real.

## Consequências

- O backend controla o limite de dados e centraliza integração, timeout e tratamento de falha.
- A desidentificação não elimina todo risco de reidentificação; dados clínicos ainda podem ser sensíveis e exigem avaliação de privacidade e contrato com o provedor.
- A aplicação depende de serviço externo e precisa apresentar indisponibilidade sem inventar resultado ou classificação.
- A seleção do fornecedor continua em aberto; este ADR não autoriza envio de dados reais até os aspectos de retenção e tratamento serem definidos.
