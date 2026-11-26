---
name: medix-figma-design
description: Aplique ao MEDIX.AI os padrões visuais e de interação do protótipo Figma do projeto ao criar ou ajustar telas e componentes web Django.
---

# Design do protótipo MEDIX.AI

Use esta skill para toda implementação ou ajuste de interface do MEDIX.AI. O pedido do responsável é que **todo o sistema siga o design dessas telas**: trate as duas telas como referências complementares para uma linguagem visual comum em todos os portais, páginas e componentes, não como padrões restritos aos próprios formulários. O arquivo de referência é [MEDIX.AI no Figma](https://www.figma.com/design/9F2EIVikukTCVk5FxGzpf9/Sem-t%C3%ADtulo?node-id=0-1&t=gAgZBOlfF5tD8iPb-1).

## Escopo visual conhecido

O arquivo contém dois code layers de 1280 × 1080:

- **Tela de Revisão Médica** — node `1:3`.
- **Cadastro de Paciente MEDIX.AI** — node `2:3`.

Use a tela médica e a de cadastro em conjunto para identificar os elementos visuais recorrentes e estabelecer uma linguagem visual comum a todo o sistema. Aplique essa linguagem também às telas ainda não representadas no arquivo, adaptando a composição ao conteúdo e à tarefa de cada uma. Consulte o frame e o contexto de design correspondente à tela que estiver implementando. A listagem de metadados confirma nomes e dimensões, mas não define paleta, tipografia, espaçamentos nem comportamento responsivo. Extraia os padrões do contexto visual acessível; não invente tokens como se fossem especificados pelo Figma. Se detalhes não estiverem acessíveis, mantenha coerência entre telas com base nos elementos observáveis e sinalize a limitação.

## Fluxo de aplicação

1. Leia `docs/state.md`, `docs/arquitetura.md` e a spec funcional numerada aplicável antes de alterar a tela. Respeite também as skills Python, Django e segurança do projeto quando os arquivos envolvidos exigirem.
2. Consulte no Figma os dois frames e identifique hierarquia, padrões recorrentes, componentes, estados e ativos visuais. Ao criar qualquer outra tela do sistema, reutilize essa linguagem comum e os componentes compartilhados existentes; adapte o layout ao propósito da página sem deixar que portais distintos pareçam produtos diferentes. Evite copiar uma aplicação React/Vite do code layer para dentro do Django.
3. Adapte o layout ao MVT do projeto: templates apresentam dados preparados pela View; regras e consultas permanecem nos services. Preserve formulários, rotas, permissões, acessibilidade e comportamento descritos pela spec.
4. Implemente estilos responsivos para a WebApp, mantendo a hierarquia e intenção do protótipo em telas menores. Use os recursos estáticos e padrões de CSS já existentes; não adicione dependências sem necessidade.
5. Se o Figma estiver inacessível ou não expuser detalhes visuais necessários, implemente somente o que puder ser sustentado pelo contexto disponível e sinalize os pontos incertos em vez de fabricar especificações.

## Critérios de fidelidade

- Preserve a hierarquia visual, alinhamentos, proporções, agrupamento, densidade e estados visíveis do frame de referência.
- Mantenha consistência visual entre as telas de paciente/responsável, médico e administração, reaproveitando tipografia, cores, formas, componentes, espaçamentos e padrões de navegação que forem confirmados nos frames.
- Reproduza conteúdo, rótulos e affordances observáveis com linguagem consistente com o produto; não crie fluxos funcionais que não estejam definidos pela spec.
- Use elementos semânticos, rótulos associados aos campos, foco visível, navegação por teclado e contraste legível. O protótipo não substitui os requisitos de acessibilidade do produto.
- Não exponha dados clínicos ou pessoais de exemplo no código, em logs ou em capturas compartilhadas; use conteúdo fictício quando precisar preencher estados visuais.
- Não altere regras de produto, autenticação, autorização ou escopo para aproximar uma tela do protótipo. Documente incompatibilidades entre o frame e as specs para resolução explícita.

## Referência do Figma

Use o arquivo e os node IDs acima como fonte de design. Para a tela médica, consulte `1:3`; para cadastro de paciente, consulte `2:3`. Se o arquivo ou os nodes mudarem, atualize esta referência após confirmar os novos IDs e nomes.
