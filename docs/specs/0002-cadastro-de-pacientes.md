# Spec 0002: Cadastro de pacientes titulares

- **Status:** Proposto
- **Requisitos:** RF-01 e RF-02 do [PRD 0001](../prd/0001-contas-perfis-e-pacientes.md)
- **Dependências:** [Spec 0001](0001-interacao-por-voz-e-acessibilidade.md) para entrada acessível
- **Fonte complementar:** RF001 e RF003, RNF006, RNF007 e RS001 de `docs/Cópia de DocumentoRequisitoMEDIX.AI.md`

## Pré-condições

- A pessoa ainda não possui cadastro titular.
- O consentimento para tratamento de dados pessoais e de saúde deve ser obtido conforme a fonte; texto e registro do consentimento aguardam definição.

## Fluxo principal

1. Pessoa ainda sem conta abre o aplicativo de pacientes e inicia o cadastro no primeiro acesso. Esse é um fluxo de autocadastro de paciente, separado do fluxo de provisionamento médico, que não é público (Spec 0005).
2. O titular informa identificação/contato, acessibilidade e consentimento explícito; a idade deve ser pelo menos 18 anos. Informa credenciais e dados clínicos basais.
3. O sistema valida os campos, unicidade de CPF/e-mail, consentimento e confirmação do celular por SMS.
4. Se as validações forem concluídas, cria conta com perfil Paciente e permite autenticação pelo mecanismo comum de RF016.
5. Titular pode atualizar seus dados; alterações de cadastro/perfil clínico mantêm histórico e auditoria.

## Dados e regras de validação

| Dado | Regra derivada da fonte |
|---|---|
| CPF | Formato mascarado, dígitos verificadores válidos e único |
| Nome completo | Obrigatório, 3 a 120 caracteres |
| Nascimento | Data válida, não futura |
| Maioridade | Idade mínima de 18 anos para conta titular |
| Gênero | Seleção entre opções predefinidas; catálogo ainda não fornecido |
| Celular | Formato brasileiro indicado na fonte e confirmação por SMS |
| E-mail | Formato válido e único |
| Senha e confirmação | Mínimo de 8 caracteres, maiúscula, número e caractere especial; confirmação idêntica |
| Deficiência | Sim/Não; descrição obrigatória quando Sim, até 120 caracteres |
| Tipo sanguíneo | Opções padronizadas, incluindo “Não sei informar” |
| Alergia | Sim/Não; descrição obrigatória quando Sim, até 200 caracteres |
| Medicamentos contínuos | Texto até 300 caracteres, conforme fonte |
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

## Contrato técnico pendente

Campos de formulário derivam da tabela acima. Rota, métodos HTTP, nome de view, modelo persistente e armazenamento de consentimento aguardam `docs/arquitetura.md` e decisões de produto; não inferir esses contratos nesta proposta.

## Separação de cadastro e interface

- O autocadastro desta spec é exclusivo de pacientes titulares. Dependentes são cadastrados por responsável autenticado na Spec 0004 e não recebem login.
- Médicos são criados/homologados somente por administrador na Spec 0005; médico não se registra por esse formulário nem pelo aplicativo de pacientes.
- A aplicação móvel de pacientes deve seguir RNF009. Este fluxo documenta o comportamento do produto; o repositório atual contém somente Django e não inclui o cliente móvel.

## Testes

- [ ] Cadastro válido cria um titular sem duplicar CPF/e-mail.
- [ ] Datas futuras, CPF inválido, campos condicionais vazios e senha fora da política são rejeitados.
- [ ] Código SMS é exigido para confirmação do celular.
- [ ] Alterações cadastrais deixam trilha com autor e data/hora.
- [ ] Dados de saúde e credenciais não são expostos a outro titular.


## Fonte vigente

A fonte atual de requisitos é docs/Cópia de DocumentoRequisitoMEDIX.AI.md (2026-11-23). Quando o texto desta spec divergir de requisito RF/RNF/RS atualizado nessa fonte, prevalece a fonte e deve-se ajustar a especificação antes de implementar.


## Requisitos atualizados da fonte

- Titularidade de conta exige idade mínima de 18 anos e consentimento explícito e informado para tratamento de dados. Celular é verificado por SMS; CPF e e-mail devem ser únicos.
- Perfil clínico contempla tipo sanguíneo, alergias (detalhe obrigatório), altura, peso, hipertensão, diabetes e medicamentos contínuos. Alterações mantêm histórico e auditoria; registros não são apagados fisicamente.
- Altura/peso devem obedecer aos intervalos etários descritos pela fonte, mas os limites concretos não estão especificados. Cadastro para menores fora do fluxo de dependentes permanece em aberto.
