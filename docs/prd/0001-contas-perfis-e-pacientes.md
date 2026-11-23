# PRD 0001: Contas, perfis e pacientes

- **Status:** Proposto
- **Data:** 2026-11-23
- **Especificações:** [Spec 0001](../specs/0001-interacao-por-voz-e-acessibilidade.md), [Spec 0002](../specs/0002-cadastro-de-pacientes.md), [Spec 0003](../specs/0003-autenticacao-e-sessao.md), [Spec 0004](../specs/0004-gestao-de-dependentes.md), [Spec 0005](../specs/0005-gestao-de-profissionais.md) e [Spec 0015](../specs/0015-gestao-de-administradores-e-monitoramento.md)
- **Fonte:** `docs/Cópia de DocumentoRequisitoMEDIX.AI.md`

## Objetivo

Permitir que pacientes e responsáveis acessem o MEDIX.AI com seus perfis, e que profissionais e administradores usem a plataforma de acordo com suas funções. Os dados pessoais e de saúde devem permanecer vinculados à pessoa correta e protegidos durante o uso.

## Perfis de uso

| Perfil | Quem é | O que precisa fazer |
|---|---|---|
| Paciente titular | Pessoa que usa o sistema em benefício próprio | Criar e manter seu cadastro, autenticar-se e acessar seus atendimentos |
| Responsável legal | Titular adulto que administra dependentes | Cadastrar e gerenciar dependentes e agir em nome deles |
| Médico credenciado | Profissional homologado por um administrador | Acessar pelo navegador um painel clínico para controlar conversas e consultar dados necessários aos atendimentos |
| Administrador | Operador autorizado da plataforma | Criar/homologar médicos e administrar contas e operações pela interface administrativa |

Paciente e médico têm fluxos de cadastro distintos: o paciente inicia e conclui o próprio cadastro no primeiro acesso; o médico não possui cadastro público e só recebe acesso após criação e homologação por administrador. A autenticação e autorização subsequentes seguem os perfis definidos em RF016.

## Requisitos funcionais

### Cadastro de pacientes e dependentes

- **RF-01:** No primeiro acesso ao aplicativo de pacientes, o titular pode criar a própria conta com CPF, nome, nascimento, gênero, celular, e-mail, senha, acessibilidade e consentimento explícito para tratamento de dados conforme a LGPD; CPF e e-mail são únicos, o celular é confirmado por SMS e o titular tem pelo menos 18 anos. (Fonte: RF001, RNF009)
- **RF-02:** O titular pode manter seus dados clínicos basais, incluindo tipo sanguíneo, alergias, altura, peso, hipertensão, diabetes e medicamentos de uso contínuo; detalhes de alergia são obrigatórios quando informada e alterações mantêm histórico e auditoria. (Fonte: RF003)
- **RF-03:** O responsável legal autenticado e maior de 18 anos pode cadastrar, consultar e atualizar dependentes vinculados; cada dependente não possui credenciais próprias e o vínculo legal é informado no cadastro. (Fonte: RF002)
- **RF-04:** O cadastro de dependente associa automaticamente os dados do responsável autenticado e permite manter os dados pessoais e clínicos do dependente; CPF do dependente é único e imutável, e alergia exige descrição. (Fonte: RF002, RF003)
- **RF-05:** O titular pode solicitar a desativação de sua conta e o responsável pode solicitar a desativação de dependente, preservando dados e histórico sujeitos a retenção legal. (Fonte: RF001, RF002, RF003)

### Autenticação e gestão profissional

- **RF-06:** Pacientes, médicos credenciados e administradores autenticam-se com CPF ou e-mail e senha, recebem acesso conforme o perfil e têm suas sessões encerradas após 15 minutos de inatividade. (Fonte: RF016)
- **RF-07:** O administrador cadastra e homologa médicos após conferência documental de CRM/UF regular e anexação de documentos; não há autocadastro médico. Após homologação, o médico recebe convite por e-mail com senha provisória e acessa pelo navegador o painel clínico restrito, com controles de conversas e dados autorizados necessários ao atendimento. No primeiro login, troca a senha provisória. (Fonte: RF017, RF019, RF021; interface médica web conforme RNF009)
- **RF-08:** O administrador pode suspender ou inativar médico, bloqueando imediatamente novos acessos clínicos; registros associados a atendimento ou receita são preservados. (Fonte: RF021)
- **RF-09:** Durante cadastro, perfil clínico, anamnese, chat e emergência, o usuário pode alternar entre voz e texto; arquivos brutos de áudio são descartados após transcrição. (Fonte: RF001, RF015)
- **RF-10:** O usuário pode solicitar redefinição de senha por link de uso único enviado ao e-mail, trocar a senha no perfil mediante senha atual e redefinir senha provisória no primeiro acesso profissional. (Fonte: RF017)
- **RF-11:** O administrador pode criar e gerir contas administrativas; o sistema impede que o último administrador ativo se auto-inative. (Fonte: RF022)

## Requisitos não funcionais

- **RNF-01 (privacidade e proteção de dados):** Dados pessoais e clínicos devem ser protegidos durante transmissão e armazenamento. A fonte especifica TLS 1.3 e criptografia em repouso AES-256; senhas devem ser armazenadas por hash criptográfico seguro. (Fonte: RNF006)
- **RNF-02 (acesso e auditoria):** O acesso deve separar os perfis Paciente, Médico Credenciado e Administrador; sessões inativas expiram após 15 minutos e alterações cadastrais devem ter trilha de auditoria imutável com autor e data/hora. (Fonte: RNF007)
- **RNF-03 (compatibilidade):** O aplicativo de pacientes e responsáveis deve funcionar em Android 10 ou superior e iOS 15 ou superior; painéis clínicos e administrativos devem funcionar nos navegadores e telas responsivas descritos na fonte. (Fonte: RNF009)

## Requisitos de segurança

- **RS-01:** Antes de triagem, consulta ou prescrição, o sistema confirma identidade e vínculo do paciente para impedir troca entre titulares e dependentes. (Fonte: RS001)
- **RS-02:** O sistema impede atuação clínica de médico não homologado ou com CRM irregular e bloqueia sua sessão após inativação. (Fonte: RS007)
- **RS-03:** O sistema encerra sessões após 15 minutos de inatividade e bloqueia temporariamente a conta por 15 minutos após cinco tentativas de login malsucedidas. (Fonte: RS008)

## Fora do escopo desta versão

A fonte não define outras capacidades de conta além das identificadas neste PRD. Nenhuma funcionalidade adicional de perfil é presumida.

## Critérios de conclusão

- Os fluxos de cadastro, autenticação, gestão de dependentes e homologação profissional cobertos por este PRD estão especificados e podem ser verificados contra os requisitos de origem.
- As regras de identidade, acesso, auditoria e retenção estão rastreáveis às fontes antes da implementação.

## Dependências, restrições e questões em aberto

- A fonte define idade mínima de 18 anos para titularidade plena; confirmar o fluxo de cadastro para menores e sua relação com o cadastro de dependentes.
- A fonte exige consentimento explícito e informado, mas não fornece o conteúdo do termo nem o procedimento para atualização ou retirada do consentimento.
- A fonte exige intervalos biológicos e etários para altura e peso sem indicar limites; também não fornece o catálogo completo de gênero ou a regra de parentesco para outros dependentes legais.
- A fonte exige verificação de CRM/UF e anexação documental, mas não define serviço de verificação nem periodicidade.
- A fonte define regras de retenção, mas não detalha tratamento de pedidos de desativação ou exclusão por titular/dependente.
