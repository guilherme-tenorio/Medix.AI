---
name: prd-writer
description: Crie ou revise um PRD para este projeto a partir dos requisitos e materiais de produto fornecidos. Use ao definir ou alterar o que o MEDIX.AI faz, para quem, por quê, seu escopo e resultados esperados.
---

# PRD de produto

Um PRD descreve **o que** o produto faz, **para quem** e **por quê**. Explique problema, necessidades dos usuários, resultados esperados, escopo e comportamento observável. Detalhes de implementação pertencem às specs (`docs/specs/`) e decisões técnicas relevantes pertencem aos ADRs (`docs/adr/`).

## Quando criar ou alterar

- Crie um PRD para um produto ou uma versão com objetivo próprio.
- Altere o PRD quando mudar o comportamento esperado, os usuários, o escopo ou os resultados do produto.
- Mudanças internas sem efeito para os usuários não são requisitos de PRD.
- Ao alterar requisitos existentes, verifique e atualize as specs que os referenciam.

## Fontes e análise

1. Leia os documentos de requisitos anexados ou indicados pelo usuário e os PRDs existentes relacionados. Consulte também o estado do projeto em `docs/state.md` e documentação pertinente.
2. Trate as fontes fornecidas como autoridade para requisitos funcionais, não funcionais e de segurança, restrições, prioridades, contexto e critérios de sucesso. Preserve seus identificadores e força normativa quando possível.
3. Extraia problema, público, necessidades, objetivos, resultados esperados, capacidades, escopo, exclusões, dependências e restrições.
4. Registre a origem dos requisitos (ID ou seção do documento-fonte) para manter rastreabilidade. Não confunda IDs das fontes com IDs do PRD quando os padrões forem diferentes.
5. Separe fatos confirmados, suposições e questões em aberto. Não invente usuários, métricas, políticas, prioridades, controles de segurança, resultados nem critérios de aceitação. Sinalize contradições e ambiguidades; pergunte à pessoa responsável quando uma decisão de produto for necessária.
6. Se um documento citado ou anexo não estiver acessível, informe a limitação e baseie o PRD somente no material disponível.

## Local e nome do arquivo

Crie o PRD em `docs/prd/NNNN-titulo-em-kebab-case.md`, usando o próximo número de quatro dígitos disponível. Antes de criar, confira os PRDs existentes para evitar colisão. Não use `docs/prd.md` quando o projeto adotar a pasta numerada `docs/prd/`.

## Estrutura

Adapte a estrutura ao produto e às fontes, sem manter seções vazias. Use como base:

```markdown
# PRD NNNN: Título

- **Status:** Proposto
- **Data:** AAAA-MM-DD
- **Especificações:** links para as specs relacionadas, se existirem
- **Fontes:** documentos de requisitos utilizados

## Objetivo

## Perfis de uso

| Perfil | Quem é | O que precisa fazer |
|---|---|---|

## Requisitos funcionais

### Área

- **RF-01:** Comportamento observável. (Fonte: RF...)

## Requisitos não funcionais

- **RNF-01 (tema):** Qualidade exigida. (Fonte: NF...)

## Requisitos de segurança

- **RS-01:** Comportamento ou proteção exigida. (Fonte: RS...)

## Fora do escopo desta versão

## Critérios de conclusão

## Dependências, restrições e questões em aberto
```

Inclua requisitos de segurança em seção própria quando as fontes os distinguirem; não os esconda entre requisitos funcionais. Métricas e critérios de conclusão só devem ser incluídos quando as fontes os sustentarem. Se útil, preserve as prioridades da fonte (por exemplo: essencial, importante, desejável).

## Status e identificadores

- Todo PRD criado por um agente começa com status **Proposto**.
- **Proposto** significa que aguarda validação da pessoa responsável; **Aceito** significa que os requisitos foram aprovados.
- Use IDs sequenciais e únicos no PRD, sem reaproveitar ou renumerar IDs existentes citados por specs. Siga o padrão já adotado no conjunto de PRDs (`RF-xx`, `RNF-xx` e `RS-xx`, se aplicável).
- Preserve também os identificadores do documento-fonte por rastreabilidade (por exemplo, `RF001`, `NF001` e `RS001`). Não altere silenciosamente a numeração original.

## Regras de redação

- Escreva em português, a menos que o usuário peça outro idioma. Preserve termos do domínio e IDs das fontes.
- Escreva cada requisito como uma declaração concisa, específica e verificável no nível do produto. Um requisito deve descrever um comportamento ou resultado por vez.
- Nomeie o perfil e o comportamento sem citar tabelas, classes, rotas, bibliotecas ou arquitetura de implementação.
- Diferencie requisito, justificativa e sugestão. Não transforme detalhes de solução técnica em requisito de produto.
- Mantenha a força normativa da fonte (deve, deveria, pode); não fortaleça nem enfraqueça sem registrar a mudança.
- Inclua critérios de aceitação apenas quando forem derivados das fontes sem criar comportamento novo.
- Registre em “Fora do escopo” itens que poderiam ser razoavelmente presumidos como incluídos nesta versão, desde que a exclusão esteja respaldada pelo material ou confirmada pela pessoa responsável.
- Consolide duplicações sem perder rastreabilidade; sinalize conflitos em vez de escolher uma interpretação sem validação.
- Não crie specs ou ADRs como parte da escrita do PRD, a menos que isso seja solicitado. Quando existirem, faça links para os artefatos relacionados.
