# Spec 0002: Cadastro de pacientes titulares

- **Status:** Proposto
- **Requisitos:** RF-01 e RF-02 do [PRD 0001](../prd/0001-contas-perfis-e-pacientes.md)
- **Dependências:** [Spec 0001](0001-interacao-por-voz-e-acessibilidade.md) para entrada acessível
- **Fonte complementar:** RF001, RNF006 e RNF007 de `docs/DocumentoRequisitoMEDIX.AI (3).md`

## Pré-condições

- A pessoa ainda não possui cadastro titular.
- O consentimento para tratamento de dados pessoais e de saúde deve ser obtido conforme a fonte; texto e registro do consentimento aguardam definição.

## Fluxo principal

1. A pessoa abre o cadastro e informa dados pessoais, credenciais e dados de saúde.
2. O sistema valida os campos, unicidade de CPF e e-mail e verifica o celular pelo código SMS.
3. Se todos os dados forem válidos, o cadastro é criado e fica disponível para autenticação.
4. O titular pode atualizar seus dados posteriormente; alterações mantêm trilha de auditoria.

## Dados e regras de validação

| Dado | Regra derivada da fonte |
|---|---|
| CPF | Formato mascarado, dígitos verificadores válidos e único |
| Nome completo | Obrigatório, 3 a 120 caracteres |
| Nascimento | Data válida, não futura |
| Gênero | Seleção entre opções predefinidas; catálogo ainda não fornecido |
| Celular | Formato brasileiro indicado na fonte e confirmação por SMS |
| E-mail | Formato válido e único |
| Senha e confirmação | Mínimo de 8 caracteres, maiúscula, número e caractere especial; confirmação idêntica |
| Deficiência | Sim/Não; descrição obrigatória quando Sim, até 120 caracteres |
| Tipo sanguíneo | Opções padronizadas, incluindo “Não sei informar” |
| Alergia | Sim/Não; descrição obrigatória quando Sim, até 200 caracteres |
| Altura e peso | Altura inteira em cm; peso decimal em kg com uma casa. Limites biologicamente válidos não estão definidos |
| Pressão alta e diabetes | Valores auto-declarados Sim/Não |

## Fluxos alternativos e erros

- CPF inválido ou já utilizado: impedir cadastro e indicar o campo a corrigir.
- E-mail inválido ou já utilizado: impedir cadastro e indicar o campo a corrigir.
- Código SMS inválido/expirado ou serviço indisponível: informar falha; prazo, reenvio e limite de tentativas aguardam definição.
- Campo condicional ausente ou valor fora dos limites definidos: não concluir o cadastro.
- Interrupção antes da conclusão: a fonte não define rascunho ou recuperação do formulário.

## Regras de serviço e acesso

- Toda validação de domínio, unicidade, persistência e trilha de auditoria ocorre na camada service; a view não recebe regra de negócio.
- Não persistir senha em texto simples. Aplicar a política de proteção referenciada por RNF006.
- O titular pode consultar e alterar somente o próprio cadastro; detalhes de perfis e autorização seguem a Spec 0003.
- A desativação deve preservar registros sujeitos à retenção. A fonte não identifica quem solicita a desativação do titular.

## Contrato web pendente

Campos de formulário derivam da tabela acima. Rota, métodos HTTP, nome de view, modelo persistente e armazenamento de consentimento aguardam `docs/arquitetura.md` e decisões de produto; não inferir esses contratos nesta proposta.

## Testes

- [ ] Cadastro válido cria um titular sem duplicar CPF/e-mail.
- [ ] Datas futuras, CPF inválido, campos condicionais vazios e senha fora da política são rejeitados.
- [ ] Código SMS é exigido para confirmação do celular.
- [ ] Alterações cadastrais deixam trilha com autor e data/hora.
- [ ] Dados de saúde e credenciais não são expostos a outro titular.
