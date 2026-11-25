# ADR 0005: Autenticação Web por sessão Django

- **Status:** Aceito
- **Aprovado em:** 2026-11-25

## Contexto

O MEDIX.AI é um WebApp Django servido pelo mesmo domínio para pacientes/responsáveis, médicos e administradores, com entradas segregadas em `/login`, `/medico/login` e `/admin/login`. O MVP não inclui cliente móvel nativo nem exige autenticação federada. A fonte RF016 menciona JWT/OAuth sem especificar fluxo, emissor ou cliente que os consuma.

## Decisão

- Usar autenticação de sessão do Django com sessão armazenada no servidor e cookie de sessão no navegador.
- Usar o modelo customizado `users.User`, com CPF e e-mail únicos, hash de senha gerido pelo Django e papel de acesso do MEDIX.AI. Identidades de dependentes não têm credenciais próprias.
- Aceitar CPF ou e-mail como identificador de login. Um adaptador de autenticação encaminha a validação ao service de autenticação, que localiza a conta e verifica a senha sem armazená-la em texto simples.
- As três rotas de login usam o mesmo mecanismo, mas cada uma permite apenas o papel correspondente. Credenciais corretas usadas em portal incompatível recebem HTTP 403, sem revelar detalhes da conta.
- Autorizar áreas protegidas por papel/permissões e vínculo com o paciente ou atendimento. O papel de negócio não é inferido de `is_staff` nem de `is_superuser`.
- Encerrar sessão após 15 minutos de inatividade por controle de atividade; logout e suspensão/inativação invalidam as sessões aplicáveis.
- Proteger cookies com `HttpOnly`, `SameSite` e `Secure` em produção HTTPS, e exigir proteção CSRF em operações de escrita.
- Não emitir JWT nem usar OAuth no MVP WebApp. Para este escopo, a menção genérica de JWT/OAuth em RF016 é atendida pela autenticação e sessão seguras do Django; uma API para clientes independentes exigirá decisão própria antes de sua implementação.

## Consequências

- O navegador não precisa armazenar tokens de acesso em JavaScript, e as páginas server-side usam o mecanismo de autenticação e permissões do Django.
- A aplicação mantém estado de sessão no servidor e precisa operar a expiração por inatividade, revogação e armazenamento de sessões.
- A proteção CSRF faz parte do contrato das operações POST do WebApp.
- Uma futura API pública, aplicativo nativo ou login federado não pode reutilizar automaticamente esta decisão; requer desenho de autenticação e autorização específico.
