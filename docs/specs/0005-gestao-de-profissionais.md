# Spec 0005: Cadastro e gestão de médicos e administradores

- **Status:** Proposto
- **Requisitos:** RF-07 e RF-08 do [PRD 0001](../prd/0001-contas-perfis-e-pacientes.md)
- **Depende de:** [Spec 0003](0003-autenticacao-e-sessao.md)
- **Fonte complementar:** RF013, RNF007, RS007 e RNF009 de `docs/DocumentoRequisitoMEDIX.AI (3).md`

## Pré-condições

- Operador é administrador autenticado e ativo.
- Não existe vínculo ativo duplicado para o profissional a cadastrar.
- Médico não pode fazer autocadastro público.

## Fluxo principal

1. Administrador escolhe cadastrar médico credenciado ou administrador.
2. Informa CPF, nome, nascimento, celular, e-mail corporativo e, para médico, CRM e UF.
3. Sistema valida CPF, e-mail e campos requeridos; para médico, administrador confere documentação e situação regular do CRM/UF.
4. Após homologação, ativa a conta e entrega senha provisória; no primeiro login o profissional define senha pessoal.
5. Administrador pode atualizar contato e status. Inativação/suspensão bloqueia imediatamente o acesso clínico e registra autor, data/hora.

## Regras e validações

- CPF validado e único; nome entre 3 e 120 caracteres; nascimento válido. Administrador deve ter ao menos 18 anos.
- CRM/UF são obrigatórios para médico e não podem ser alterados após cadastro; CPF também não pode ser alterado.
- E-mail é validado e único. Senha provisória segue política descrita na fonte e exige troca no primeiro login.
- Conta associada a receita ou atendimento não pode ser apagada fisicamente; deve ser inativada.

## Erros e acesso

- Operador que não é administrador ativo: negar acesso sem revelar dados profissionais.
- Duplicidade, CRM irregular ou dados inválidos: não ativar conta; informar ao administrador o campo ou validação pendente.
- Conta suspensa/inativa perde acesso a fila, chat, receitas e demais painéis clínicos.

## Decisões pendentes

- A fonte exige validação de CRM ativo e conferência documental, mas não define serviço de consulta, documento comprobatório ou periodicidade. Escolher mecanismo e registrar ADR se houver integração estrutural.
- A fonte exige idade mínima de 18 anos para administradores e idade compatível com a formação para médicos, mas não define como esta última regra é verificada.
- Não define bootstrap do primeiro administrador nem reativação após suspensão; esclarecer antes desses fluxos.
- Contratos de formulário, serviço e rota dependem de `docs/arquitetura.md`.

## Testes

- [ ] Somente administrador ativo cadastra ou altera perfis profissionais.
- [ ] Médico sem CRM/UF regular não é ativado.
- [ ] Primeiro login obriga troca da senha provisória.
- [ ] Inativação bloqueia acesso clínico e gera trilha de auditoria.
- [ ] Conta com atendimento/receita não é excluída fisicamente.
