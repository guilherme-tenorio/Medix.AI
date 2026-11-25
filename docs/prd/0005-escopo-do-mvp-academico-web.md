# PRD 0005: Escopo do MVP acadêmico web

- **Status:** Aceito
- **Aprovado em:** 2026-11-25
- **Data:** 2026-11-25
- **Especificações:** [Spec 0002](../specs/0002-cadastro-de-pacientes.md), [Spec 0003](../specs/0003-autenticacao-e-sessao.md), [Spec 0005](../specs/0005-gestao-de-profissionais.md), [Spec 0006](../specs/0006-triagem-e-classificacao-de-risco.md), [Spec 0007](../specs/0007-encaminhamento-de-emergencia.md), [Spec 0008](../specs/0008-fila-clinica.md), [Spec 0009](../specs/0009-chat-medico.md), [Spec 0010](../specs/0010-validacao-medica-de-prescricao.md), [Spec 0011](../specs/0011-emissao-e-consulta-de-receita.md), [Spec 0012](../specs/0012-prontuario-e-historico.md), [Spec 0013](../specs/0013-notificacoes-e-alertas.md), [Spec 0014](../specs/0014-verificacao-e-dispensacao-de-receita.md) e [Spec 0015](../specs/0015-gestao-de-administradores-e-monitoramento.md)
- **Fontes:** decisão de plataforma WebApp definida pelo responsável; requisitos completos e atualizados em [`DocumentoRequisitoMEDIX.AI (4).md`](../DocumentoRequisitoMEDIX.AI%20(4).md)

## Objetivo

Definir o escopo de plataforma da versão do MEDIX.AI desenvolvida para avaliação acadêmica. Essa versão será acessada pelo navegador e terá interfaces web para pacientes, médicos e administradores.

Este PRD limita a plataforma do MVP. Ele não substitui os PRDs que descrevem o produto completo nem altera o documento de requisitos original.

## Perfis de uso e cadastro

| Perfil | Cadastro/acesso no MVP |
|---|---|
| Paciente | Pode criar a própria conta pelo formulário público de cadastro no site e acessar sua área web. |
| Médico | Não pode se cadastrar publicamente. Conta criada e homologada por administrador; acesso ao painel clínico web. |
| Administrador | Não pode se cadastrar publicamente. Conta inicial criada por procedimento administrativo privado; acesso ao painel web administrativo. |

O sistema é um único WebApp, com portais de entrada segregados por perfil: paciente/responsável em `/login`, médico em `/medico/login` e administrador em `/admin/login`. As rotas segregadas não criam clientes nativos nem aplicações independentes. A autorização é verificada em toda área protegida; tentativa de acesso cruzado entre perfis recebe HTTP 403. A escolha de papel não é oferecida no cadastro público.

As regras de cadastro e separação de portais deste PRD seguem a fonte atualizada e permanecem propostas para validação do produto.

## Escopo desta versão

- Um único WebApp acessível por navegadores modernos para todos os perfis incluídos, com portais/rotas segregados conforme a fonte.
- Cadastro público exclusivo para pacientes.
- Provisionamento administrativo de contas médicas e acesso clínico web após homologação.
- Acesso administrativo web; a criação do primeiro administrador ocorre por procedimento privado de operação/desenvolvimento.
- Autenticação comum com direcionamento à área web correspondente ao perfil.
- Notificações e links abrem as áreas web; Push, quando habilitado, é entregue pelo navegador (Web Push), sem dependência de aplicativo nativo.
- Fluxos clínicos do MVP: triagem e encaminhamento de emergência, fila médica, chat síncrono, revisão/assinatura/emissão/verificação/dispensação de receitas e prontuário/histórico, conforme as Specs 0006–0014.

## Fora do escopo desta versão

- Aplicativo móvel nativo para Android ou iOS. A parte nativa do RNF009 fica fora do escopo deste MVP acadêmico; responsividade web não é considerada cumprimento da exigência de aplicativo nativo.
- Cadastro público de médicos ou administradores, ou escolha de papel/perfil pelo visitante no formulário público.
- Integrações clínicas externas só serão ativadas após definição dos provedores, contratos, privacidade, disponibilidade e critérios clínicos/regulatórios documentados nas specs e ADRs.

## Restrições e rastreabilidade

- Regras de autocadastro de paciente e separação dos perfis são detalhadas no PRD 0001 e nas Specs 0002, 0003, 0005 e 0015.
- Os requisitos funcionais, de segurança e de qualidade do produto completo continuam rastreados aos IDs do documento-fonte vigente. A decisão de construir somente um WebApp representa implementação parcial do RNF009.
- A arquitetura de interface, autenticação e autorização deve seguir `docs/arquitetura.md` e as specs relacionadas.

## Questões em aberto

- Definir critérios de responsividade e acessibilidade das interfaces web. Essa definição não altera a exclusão de clientes nativos do MVP.
- Definir se o MVP acadêmico demonstrará conectores reais de assinatura ICP-Brasil, LLM, voz, mapas e mensageria ou adaptadores simulados; não liberar dados clínicos reais para integrações ainda não aprovadas.
