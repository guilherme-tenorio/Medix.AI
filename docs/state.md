# Estado atual

Atualizado em: 2026-11-19

Este arquivo registra apenas o andamento geral e as próximas ações. O status detalhado de cada requisito e documento deve ficar no próprio artefato; o histórico fica no Git.

## Em andamento

- Preparação da documentação de produto e desenvolvimento do MEDIX.AI.
- Skill `prd-writer` consolidada com as convenções do projeto, rastreabilidade às fontes e separação entre PRD, specs e ADRs.
- Quatro PRDs propostos foram criados em `docs/prd/`, cobrindo contas e pacientes, triagem e emergência, atendimento/prescrição/prontuário, fila e notificações.
- Treze specs propostas foram criadas em `docs/specs/`, uma para cada fluxo funcional RF001–RF013; os PRDs agora apontam para as specs correspondentes.
- A fonte usada foi `docs/DocumentoRequisitoMEDIX.AI (3).md`, pois o caminho solicitado `docs/DocumentoRequisitoMEDIX.AI.md` não existe no workspace.
- O projeto Django está no estágio inicial: há estrutura de configuração e URLs, além do app `users`, mas seus models, views e testes ainda contêm apenas esqueletos gerados.

## Próximos passos

1. Revisar e validar os quatro PRDs e as treze specs propostas, resolvendo dúvidas clínicas, legais e de produto registradas nos documentos.
2. Preencher `docs/arquitetura.md` com as decisões estruturais já estabelecidas para o projeto, incluindo MVT e a camada de services.
3. Registrar ADRs para decisões técnicas estruturais apontadas pelas specs antes de implementar os fluxos que dependem delas.
4. Implementar as funcionalidades a partir das specs aprovadas, atualizando este estado ao concluir cada etapa.

## Pendências

- `docs/arquitetura.md` está vazio.
- Os PRDs estão com status `Proposto`; aguardam validação e esclarecimento das dúvidas indicadas em cada arquivo.
- As treze specs também estão com status `Proposto`; contratos de rotas, modelos persistentes e integrações estruturais permanecem pendentes onde indicado.
- O caminho canônico citado no pedido (`docs/DocumentoRequisitoMEDIX.AI.md`) está ausente; confirmar se a versão `(3)` é a fonte oficial.
- `docs/adr/` ainda não contém documentos.
- O código ainda não implementa os fluxos de triagem, análise por IA, atendimento médico ou gestão de pacientes descritos nos requisitos.
