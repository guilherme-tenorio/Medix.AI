# Arquitetura do MEDIX.AI

Atualizado em: 2026-11-23

Este documento registra as regras de arquitetura compartilhadas pelo sistema. O comportamento específico de cada funcionalidade está em `docs/specs/`; decisões arquiteturais e suas justificativas ficam em `docs/adr/`. Consulte também a [matriz de rastreabilidade](rastreabilidade-requisitos.md), que relaciona todos os RFs, RNFs e RSs da fonte vigente.

## Visão geral

- O sistema é desenvolvido com Django seguindo o padrão MVT (Model, View, Template).
- A camada de services concentra as regras de negócio e todas as consultas ao ORM.
- Todas as Views são classes derivadas de `django.views.View` e implementam apenas os métodos HTTP necessários; services não recebem `request` nem retornam `HttpResponse`. A decisão está registrada no [ADR 0002](adr/0002-mvt-com-camada-de-services.md).
- O banco de dados relacional alvo é PostgreSQL, conforme decisão aceita no [ADR 0001](adr/0001-postgresql.md).
- A conexão Django usa variáveis de ambiente `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` e `POSTGRES_PORT`.
- Os fluxos de conta são distintos por perfil: pacientes iniciam o próprio cadastro no primeiro acesso ao aplicativo de pacientes; médicos não têm autocadastro e são provisionados por administradores. O médico usa painel clínico no navegador, conforme RNF009. Essa separação não cria uma rota de cadastro público para profissionais; a autenticação e o RBAC seguem RF016.
- A chave Django é fornecida por `DJANGO_SECRET_KEY`; `DJANGO_DEBUG` e `DJANGO_ALLOWED_HOSTS` controlam o modo de depuração e os hosts permitidos.

## Fluxo entre camadas

`URL → View → Form (quando aplicável) → Service → Model/ORM → PostgreSQL`

A View prepara a resposta usando o resultado do service e o Template apresenta a interface. O fluxo concreto de cada funcionalidade deve estar definido na spec correspondente.

## Responsabilidades por camada

### URLs

- Mapeiam caminhos e nomes de rota para Views.
- Não contêm regras de negócio nem consultas ao banco.
- A organização das rotas por app será definida quando a estrutura dos apps for documentada.

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
- Tratamento de transações e organização de services por domínio ainda precisam ser detalhados nas specs/ADRs relevantes.

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
- Nenhuma View ou Template deve contornar as verificações de autorização realizadas no fluxo de domínio.
- Os detalhes de proteção de dados em desenvolvimento e produção ainda dependem das specs de segurança e decisões pendentes.

## Estrutura de apps

- A separação de responsabilidades entre apps Django ainda não foi definida neste documento.
- A interface de pacientes é o aplicativo móvel destinado a Android 10+ e iOS 15+; o painel médico e o painel administrativo são interfaces web responsivas para navegadores modernos. Este repositório Django não contém hoje um cliente móvel; a integração de autenticação/API para esse cliente deve seguir as specs antes de ser implementada.
- O painel médico deve oferecer fila, disponibilidade e acesso às conversas/dados clínicos autorizados para o atendimento. O acesso sempre respeita vínculo e RBAC, e regras/consultas ficam em services.
- Cada funcionalidade deve seguir a spec numerada correspondente antes da implementação.
- Não criar dependências entre apps que contornem a camada de services.

## Decisões pendentes

- Definir organização dos apps, contratos de serviço, tratamento de erros e limites transacionais.
- Definir versão e operação do PostgreSQL, configuração de ambientes e estratégia de backup/recuperação.
- Definir provedores e limites de integração da IA, voz, geolocalização, assinatura digital, chat em tempo real e notificações, conforme as specs.
- Definir provedor/contrato do LLM externo, retenção e região de processamento antes de enviar dados clínicos reais.
- Registrar decisões difíceis de reverter em ADRs antes de implementar as funcionalidades dependentes.

## ADRs relacionados

- [ADR 0001: PostgreSQL como banco de dados relacional](adr/0001-postgresql.md) — aceito.
- [ADR 0002: MVT com camada de services](adr/0002-mvt-com-camada-de-services.md) — proposto.
- [ADR 0003: Integração externa de LLM para anamnese](adr/0003-integracao-externa-de-llm.md) — proposto.
