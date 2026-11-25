# Arquitetura do MEDIX.AI

Atualizado em: 2026-11-25

Este documento registra as regras de arquitetura compartilhadas pelo sistema. O comportamento específico de cada funcionalidade está em `docs/specs/`; decisões arquiteturais e suas justificativas ficam em `docs/adr/`. Consulte também a [matriz de rastreabilidade](rastreabilidade-requisitos.md), que relaciona todos os RFs, RNFs e RSs da fonte vigente.

## Visão geral

- O sistema é desenvolvido com Django seguindo o padrão MVT (Model, View, Template).
- A camada de services concentra as regras de negócio e todas as consultas ao ORM.
- Todas as Views são classes derivadas de `django.views.View` e implementam apenas os métodos HTTP necessários; services não recebem `request` nem retornam `HttpResponse`. A decisão está registrada no [ADR 0002](adr/0002-mvt-com-camada-de-services.md).
- O banco de dados relacional alvo é PostgreSQL, conforme decisão aceita no [ADR 0001](adr/0001-postgresql.md).
- A autenticação do WebApp usa sessões Django armazenadas no servidor, com cookie protegido, CSRF e papéis/verificações de vínculo. CPF ou e-mail identificam a conta; JWT/OAuth não fazem parte do MVP. O modelo customizado `users.User` é definido em `AUTH_USER_MODEL` antes da primeira migração de domínio. Consulte o [ADR 0005](adr/0005-autenticacao-web-por-sessao.md).
- A conexão Django usa variáveis de ambiente `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` e `POSTGRES_PORT`.
- Para o MVP acadêmico, todos os perfis acessam o sistema exclusivamente por interfaces web em navegadores, conforme [PRD 0005](prd/0005-escopo-do-mvp-academico-web.md). Os portais de paciente/responsável, médico e administração têm entradas segregadas: `/login`, `/medico/login` e `/admin/login`. A segregação é de rotas e permissões dentro da aplicação WebApp, não implica aplicativos ou sistemas independentes. Pacientes podem iniciar o próprio cadastro na área pública; médicos são provisionados e homologados por administradores; administradores não têm cadastro público. Acesso cruzado entre portais deve ser negado com HTTP 403. Não oferecer seletor público de papel.
- A aplicação deste repositório é somente WebApp e não inclui aplicativo nativo Android/iOS. O RNF009 da fonte vigente também exige compatibilidade móvel nativa para o produto completo; essa parte permanece explicitamente não atendida no escopo acadêmico. A responsividade da interface web não equivale a um aplicativo nativo.
- A chave Django é fornecida por `DJANGO_SECRET_KEY`; `DJANGO_DEBUG` e `DJANGO_ALLOWED_HOSTS` controlam o modo de depuração e os hosts permitidos.

## Fluxo entre camadas

`URL → View → Form (quando aplicável) → Service → Model/ORM → PostgreSQL`

A View prepara a resposta usando o resultado do service e o Template apresenta a interface. O fluxo concreto de cada funcionalidade deve estar definido na spec correspondente.

## Responsabilidades por camada

### URLs

- Mapeiam caminhos e nomes de rota para Views.
- Não contêm regras de negócio nem consultas ao banco.
- Rotas são incluídas por app de domínio; os portais segregados permanecem entradas do mesmo WebApp.

### Views

- São classes que herdam de `django.views.View` e implementam somente os métodos HTTP necessários.
- Mixins de acesso, como `LoginRequiredMixin`, podem ser usados.
- Recebem a requisição, chamam os services necessários e retornam a resposta HTTP ou selecionam o Template.
- Não implementam regras de negócio nem consultas ao ORM.

### Forms

- Quando usados, validam e normalizam os dados de entrada da interface.
- Não substituem as validações de domínio que devem ser aplicadas pelos services.
- Uso de ModelForms e divisão de validações entre Form e Service devem seguir a spec da funcionalidade.

### Services

- Contêm as regras de negócio e todas as consultas e operações do ORM.
- Não recebem `request` e não retornam `HttpResponse`.
- Recebem dados necessários à operação, aplicam as regras do domínio e retornam dados ou resultados de domínio.
- Tratamento de transações, erros e contratos entre services precisam ser detalhados nas specs/ADRs relevantes; os limites dos apps seguem o ADR 0004.

### Models

- Representam os dados persistidos pelo domínio usando o ORM do Django.
- As regras de negócio e consultas continuam nos services; os Models não devem ser usados pelas Views como caminho alternativo para contornar essa regra.
- Campos, relacionamentos, constraints e índices são definidos nas specs das funcionalidades.

### Templates

- Apresentam dados e formulários preparados pelas Views.
- Não consultam o banco nem implementam regras de negócio.

## Persistência

- PostgreSQL é o banco de dados relacional alvo.
- Dados de saúde e dados pessoais são tratados conforme requisitos de privacidade e segurança dos PRDs e das specs.
- Chamadas ao LLM externo partem do backend; antes do envio o service de integração remove identificadores diretos e limita o payload aos campos clínicos desidentificados autorizados. Consulte o [ADR 0003](adr/0003-integracao-externa-de-llm.md) e a [Spec 0006](specs/0006-triagem-e-classificacao-de-risco.md).
- A seleção do provedor, retenção de dados, região de processamento e contrato de tratamento permanecem pendentes; tráfego clínico real depende dessas definições.
- Django 6.1 requer PostgreSQL 15 ou superior e Psycopg 3.1.12 ou superior; o projeto fixa Psycopg em `requirements.txt`. Consulte a [documentação de bancos do Django](https://docs.djangoproject.com/en/6.1/ref/databases/).
- Versão concreta do servidor, hospedagem, valores de ambiente, backups, recuperação, monitoramento e estratégia de migração de dados ainda não foram definidos.

## Segurança e dados clínicos

- As regras de autenticação, autorização, auditoria, criptografia, retenção e acesso a prontuários devem seguir as specs relacionadas e os ADRs aceitos.
- O RBAC deve separar estritamente paciente/responsável, médico credenciado e administrador, incluindo bloqueio entre as rotas de autenticação segregadas e expiração de sessão após 15 minutos de inatividade. Consulte PRD 0001 e Spec 0003.
- Cadastros profissionais e registros clínicos/auditoria não podem ser excluídos fisicamente; desligamentos usam inativação lógica e revogação de sessões. A inativação do último administrador ativo é impedida. Consulte RS011 na matriz e Specs 0005, 0012 e 0015.
- Nenhuma View ou Template deve contornar as verificações de autorização realizadas no fluxo de domínio.
- Os detalhes de proteção de dados em desenvolvimento e produção ainda dependem das specs de segurança e decisões pendentes.

## Estrutura de apps

- O projeto é um monólito Django dividido por domínio, não por papel de usuário: `users`, `patients`, `professionals`, `triage`, `care`, `prescriptions`, `records`, `audit` e `notifications`. Os limites e dependências estão registrados no [ADR 0004](adr/0004-apps-django-por-dominio.md).
- Cada app é proprietário dos seus models e consultas ORM, executadas por services do domínio. Outros apps chamam contratos públicos de service em vez de consultar diretamente os models de outro domínio ou duplicar regras.
- O app `users` é a base de identidade. Seu modelo customizado precisa estar disponível na migração inicial antes que os demais apps dependam dele; perfis de pacientes/profissionais são associados à conta, enquanto dependentes não têm conta própria.
- Prontuário clínico (`records`) e trilha técnica/administrativa (`audit`) são domínios separados, com acesso e retenção controlados.
- No MVP acadêmico, as interfaces de paciente, médico e administrador são web e acessadas por navegadores modernos. A versão nativa para Android/iOS do produto completo não faz parte deste MVP; este repositório Django não contém cliente móvel.
- O painel médico deve oferecer fila, disponibilidade e acesso às conversas/dados clínicos autorizados para o atendimento. O acesso sempre respeita vínculo e RBAC, e regras/consultas ficam em services.
- Cada funcionalidade deve seguir a spec numerada correspondente antes da implementação.
- Não criar dependências entre apps que contornem a camada de services.

## Decisões pendentes

- Definir contratos de serviço, tratamento de erros, limites transacionais e dependências concretas entre apps.
- Definir versão e operação do PostgreSQL, configuração de ambientes e estratégia de backup/recuperação.
- Definir provedores e limites de integração da IA, voz, geolocalização, assinatura digital, chat em tempo real e notificações, conforme as specs.
- Definir provedor/contrato do LLM externo, retenção e região de processamento antes de enviar dados clínicos reais.
- Definir os controles operacionais de ambientes segregados, backup criptografado diário e observabilidade requeridos pelo RNF014.
- Registrar decisões difíceis de reverter em ADRs antes de implementar as funcionalidades dependentes.

## ADRs relacionados

- [ADR 0001: PostgreSQL como banco de dados relacional](adr/0001-postgresql.md) — aceito.
- [ADR 0002: MVT com camada de services](adr/0002-mvt-com-camada-de-services.md) — aceito.
- [ADR 0003: Integração externa de LLM para anamnese](adr/0003-integracao-externa-de-llm.md) — aceito; fornecedor, contrato, retenção e região continuam pendentes antes do tráfego clínico real.
- [ADR 0004: Organização dos apps Django por domínio](adr/0004-apps-django-por-dominio.md) — aceito.
- [ADR 0005: Autenticação Web por sessão Django](adr/0005-autenticacao-web-por-sessao.md) — aceito.
