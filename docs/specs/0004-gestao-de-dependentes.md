# Spec 0004: Cadastro e gestão de dependentes

- **Status:** Proposto
- **Aprovação:** Aceita pelo responsável em 2026-11-25
- **Requisitos:** RF-03, RF-04 e RF-05 do [PRD 0001](../prd/0001-contas-perfis-e-pacientes.md)
- **Depende de:** [Spec 0002](0002-cadastro-de-pacientes.md), [Spec 0003](0003-autenticacao-e-sessao.md)
- **Fonte complementar:** RF002, RF003, RNF007 e RS001 de `docs/DocumentoRequisitoMEDIX.AI (4).md`

## Pré-condições

- Responsável está autenticado, tem pelo menos 18 anos e possui cadastro ativo.
- Dependente não possui conta própria; o vínculo ao responsável vem da sessão autenticada.

## Fluxo principal

1. Responsável abre a gestão de dependentes e inicia cadastro.
2. O sistema preenche automaticamente CPF, nome, celular e e-mail do responsável a partir da sessão, sem pedir redigitação.
3. Responsável informa dados pessoais e de saúde do dependente; o sistema valida os campos e a unicidade do CPF entre usuários e dependentes.
4. O dependente passa a constar na lista do responsável autenticado.
5. Responsável pode consultar e atualizar dados, mantendo auditoria, ou desativar o dependente sem apagar registros sujeitos à retenção.

## Dados e validações

- CPF do dependente: dígitos verificadores válidos e sem duplicidade.
- Nome obrigatório, entre 3 e 120 caracteres; nascimento válido e não futuro; gênero de catálogo predefinido.
- Deficiência e alergia: Sim/Não; se Sim, descrição correspondente obrigatória.
- Tipo sanguíneo inclui “Não sei informar”; altura inteira e peso decimal devem respeitar limites clínicos por faixa etária, ainda não definidos.
- Pressão alta e diabetes são auto-declaradas como Sim/Não. CPF do dependente é imutável após cadastro.

## Acesso e erros

- Visitante, titular sem vínculo de responsável ou responsável com menos de 18 anos não pode cadastrar/gerenciar dependentes.
- CPF inválido/duplicado ou dados obrigatórios inválidos impedem conclusão e identificam os campos a corrigir.
- Acesso a lista, alteração e prontuário do dependente é limitado ao vínculo autorizado; tentativa de consultar dependente de outra pessoa é negada.
- Fluxo de remoção é desativação, sem exclusão física dos registros legais.

## Contrato e pendências

O serviço deve validar vínculo e idade do responsável antes de ler ou alterar dados. Limites clínicos por idade, comprovação do vínculo legal e procedimento de transferência de responsabilidade não estão descritos e precisam ser definidos antes da implementação correspondente. Rotas e modelo persistente dependem da arquitetura.

## Testes

- [ ] Responsável adulto autenticado cria dependente com CPF válido e único.
- [ ] Dados do responsável são associados da sessão sem redigitação.
- [ ] CPF não pode ser alterado depois do cadastro.
- [ ] Responsável não acessa dependente sem vínculo.
- [ ] Desativar mantém histórico e não executa exclusão física.


## Fonte vigente

A fonte atual de requisitos é docs/DocumentoRequisitoMEDIX.AI (4).md (2026-11-24). Quando o texto desta spec divergir de requisito RF/RNF/RS atualizado nessa fonte, prevalece a fonte e deve-se ajustar a especificação antes de implementar.


## Requisitos atualizados da fonte

- Responsável deve ter 18 anos ou mais; dependente não recebe credenciais próprias nem login. CPF/nome/celular/e-mail do responsável são associados pela sessão ativa. O vínculo legal obrigatório oferece Filho(a), Tutelado/Curatelado e Outro Dependente Legal.
- Perfil de saúde do dependente inclui os campos descritos na RF003 e conserva versões/auditoria sem exclusão física.
- CPF do dependente é validado, único entre titulares e dependentes e imutável; nome tem 3–120 caracteres; nascimento não pode ser futuro; descrição de deficiência é obrigatória quando declarada.
- A fonte não lista todos os vínculos legais aceitos nem os limites biológicos por idade; confirmar catálogo e regras clínicas.