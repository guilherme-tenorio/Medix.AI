# PRD 0001: Contas, perfis e pacientes

- **Status:** Proposto
- **Data:** 2026-11-19
- **Especificações:** [Spec 0001](../specs/0001-interacao-por-voz-e-acessibilidade.md), [Spec 0002](../specs/0002-cadastro-de-pacientes.md), [Spec 0003](../specs/0003-autenticacao-e-sessao.md), [Spec 0004](../specs/0004-gestao-de-dependentes.md) e [Spec 0005](../specs/0005-gestao-de-profissionais.md)
- **Fonte:** `docs/DocumentoRequisitoMEDIX.AI (3).md`

## Objetivo

Permitir que pacientes e responsáveis acessem o MEDIX.AI com seus perfis, e que profissionais e administradores usem a plataforma de acordo com suas funções. Os dados pessoais e de saúde devem permanecer vinculados à pessoa correta e protegidos durante o uso.

## Perfis de uso

| Perfil | Quem é | O que precisa fazer |
|---|---|---|
| Paciente titular | Pessoa que usa o sistema em benefício próprio | Criar e manter seu cadastro, autenticar-se e acessar seus atendimentos |
| Responsável legal | Titular adulto que administra dependentes | Cadastrar e gerenciar dependentes e agir em nome deles |
| Médico credenciado | Profissional homologado | Acessar as funções clínicas permitidas ao seu perfil |
| Administrador | Operador autorizado da plataforma | Homologar e administrar contas profissionais e administrativas |

## Requisitos funcionais

### Cadastro de pacientes e dependentes

- **RF-01:** O paciente titular pode criar e atualizar um cadastro com os dados pessoais e de saúde previstos na fonte, com validação dos campos e prevenção de duplicidade de CPF e e-mail. (Fonte: RF001)
- **RF-02:** O titular pode informar condições de saúde, alergias e deficiências conforme os campos definidos na fonte; quando indicar que possui alergia ou deficiência, deve informar os detalhes correspondentes. (Fonte: RF001)
- **RF-03:** O responsável legal autenticado e maior de 18 anos pode cadastrar, consultar, atualizar e desativar dependentes vinculados à sua conta; o dependente não possui conta própria segundo a fonte. (Fonte: RF002)
- **RF-04:** O cadastro de dependente mantém os dados do responsável associados à sessão autenticada e permite manter os dados pessoais e de saúde do dependente previstos na fonte. (Fonte: RF002)
- **RF-05:** O sistema permite desativar cadastros de pacientes, dependentes e profissionais, preservando registros cuja retenção seja exigida na fonte. A fonte atribui ao administrador a inativação de profissionais, mas não identifica quem inicia a desativação de pacientes e dependentes. (Fonte: RF001, RF002, RF013)

### Autenticação e gestão profissional

- **RF-06:** Pacientes, médicos credenciados e administradores autenticam-se e recebem acesso conforme o perfil; o sistema oferece recuperação de senha e gestão de sessão. (Fonte: RF010)
- **RF-07:** O administrador pode cadastrar e gerenciar médicos e administradores. O acesso clínico de um médico depende da homologação e da verificação de CRM/UF ativo descritas na fonte. (Fonte: RF013)
- **RF-08:** O administrador pode inativar ou suspender uma conta profissional, bloqueando o acesso às funções clínicas; contas vinculadas a atendimentos ou receitas não são apagadas fisicamente conforme a fonte. (Fonte: RF013)
- **RF-09:** Durante o cadastro, a pessoa pode usar entrada por voz para auxiliar o preenchimento dos campos, mantendo disponível a digitação. (Fonte: RF001, RF009)

## Requisitos não funcionais

- **RNF-01 (privacidade e proteção de dados):** Dados pessoais e clínicos devem ser protegidos durante transmissão e armazenamento. A fonte especifica TLS 1.3 e criptografia em repouso AES-256; senhas devem ser armazenadas por hash criptográfico seguro. (Fonte: RNF006)
- **RNF-02 (acesso e auditoria):** O acesso deve separar os perfis Paciente, Médico Credenciado e Administrador; sessões inativas expiram após 15 minutos e alterações cadastrais devem ter trilha de auditoria imutável com autor e data/hora. (Fonte: RNF007)
- **RNF-03 (compatibilidade):** O aplicativo de pacientes e responsáveis deve funcionar em Android 10 ou superior e iOS 15 ou superior; painéis clínicos e administrativos devem funcionar nos navegadores e telas responsivas descritos na fonte. (Fonte: RNF009)

## Requisitos de segurança

- **RS-01:** Antes de uma triagem ou emissão de receita, o sistema deve confirmar explicitamente a identidade e o vínculo do paciente, evitando troca entre titulares e dependentes. (Fonte: RS001)
- **RS-02:** O sistema deve impedir atuação clínica de médico não homologado ou com CRM irregular e bloquear o acesso após inativação da conta. (Fonte: RS007)
- **RS-03:** O sistema deve encerrar sessões após 15 minutos de inatividade e bloquear temporariamente o acesso por 15 minutos após cinco tentativas de login malsucedidas. (Fonte: RS008)

## Fora do escopo desta versão

A fonte não define funcionalidades de conta além das descritas nos requisitos RF001, RF002, RF010 e RF013. Nenhuma outra capacidade de perfil é assumida neste PRD.

## Critérios de conclusão

- Os fluxos de cadastro, autenticação, gestão de dependentes e homologação profissional cobertos por este PRD estão especificados e podem ser verificados contra os requisitos de origem.
- As regras de identidade, acesso, auditoria e retenção estão rastreáveis às fontes antes da implementação.

## Dependências, restrições e questões em aberto

- A fonte explica as categorias de prioridade, mas não atribui prioridade aos RFs; este PRD não inventa essa classificação.
- A fonte menciona consentimento, LGPD, retenção legal e auditoria, mas não define os textos de consentimento, prazos por categoria de dado nem o processo de atendimento a solicitações do titular. Esclarecer esses pontos antes de especificar os fluxos correspondentes.
- A fonte exige validação de CRM/UF ativo, mas não define como a verificação será realizada nem sua periodicidade. A decisão de implementação pertence à spec/ADR correspondente.
- Confirmar se o documento-fonte correto é a versão `(3)` utilizada neste PRD; o caminho indicado no pedido, `docs/DocumentoRequisitoMEDIX.AI.md`, não foi encontrado.
