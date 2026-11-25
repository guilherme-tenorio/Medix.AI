# Estado atual

Atualizado em: 2026-11-25

## Em andamento

- Fonte vigente: [`DocumentoRequisitoMEDIX.AI (4).md`](DocumentoRequisitoMEDIX.AI%20(4).md), atualizada em 2026-11-24. A cópia sem “(4)” é uma versão histórica substituída.
- Os cinco PRDs estão `Aceito`. As 15 specs foram aprovadas pelo responsável em 2026-11-25; mantêm `Status: Proposto` até que código e testes cumpram cada especificação. RF001–RF022, RNF001–RNF014 e RS001–RS011 estão mapeados na [matriz de rastreabilidade](rastreabilidade-requisitos.md).
- Escopo confirmado: um único WebApp para todos os perfis, sem cliente nativo. Portais web segregados: paciente/responsável em `/login`, médico em `/medico/login` e administrador em `/admin/login`; tentativas de acesso cruzado recebem HTTP 403. Cadastro público apenas para paciente; médicos são provisionados/homologados por administrador; sem cadastro público de administrador ou seletor de papel.
- Escopo do MVP confirmado pelo usuário: inclui cadastro/autenticação, triagem e emergência, fila médica, chat, revisão e ciclo de receitas, prontuário/histórico e fluxos administrativos/notificações conforme PRDs e Specs 0001–0015.
- Divisão dos apps por domínio e autenticação por sessão Django server-side foram aprovadas e registradas nos ADRs 0004/0005. O banco anterior tinha migrações `auth` 0001–0012 aplicadas e uma conta superusuária em `auth.User`.
- O responsável criou o banco novo `medix_ai_webapp` para iniciar uma instalação limpa; o banco anterior deve ser preservado. `AUTH_USER_MODEL = 'users.User'` foi configurado antes da primeira migração; a migração inicial e o superusuário foram criados no banco novo, com sucesso informado pelo responsável em 2026-11-25.
- A decisão de sessões interpreta a menção genérica a JWT/OAuth em RF016 para o escopo WebApp; sem JWT/OAuth no MVP. Reavaliar apenas se surgir API para cliente independente ou login federado.
- RNF009 permanece requisito do produto completo: o MVP WebApp não cumpre a exigência de aplicativo Android/iOS. Interfaces web responsivas não são equivalentes a clientes nativos.
- PRDs, arquitetura, matriz e specs atualizados para a fonte vigente, incluindo os novos RNF011–RNF014 e RS011 e os fluxos revistos de triagem e revisão clínica.
- ADRs 0001–0005 estão aceitos. ADR 0003 aprova a estratégia de integração e anonimização; fornecedor, contrato, retenção e região ainda precisam ser definidos antes do tráfego clínico real.

## Implementação

- O código Django está iniciando a implementação WebApp: `users.User` está configurado e os apps `patients`, `professionals`, `triage`, `care`, `prescriptions`, `records`, `audit` e `notifications` têm agora a estrutura padrão do `django-admin startapp` (admin, apps, migrations, models, tests e views). Os fluxos funcionais ainda não foram implementados e não há cliente móvel nativo neste repositório.
- Ambiente virtual `env` confirmado pelo usuário com Python 3.13.5, Django 6.1.3 e Psycopg instalado. `python manage.py check` concluiu sem problemas e `python manage.py runserver` iniciou em `http://127.0.0.1:8000/`.
- `AUTH_USER_MODEL` aponta para `users.User`; `users.0001_initial` foi gerada e as migrações foram aplicadas ao banco `medix_ai_webapp`. O responsável confirmou que a conexão aponta para esse banco e informou que a migração e a criação do superusuário terminaram corretamente. O banco antigo e sua conta permanecem independentes.
- `python manage.py check` concluiu sem problemas após corrigir a configuração de e-mail incompatível (`MAILERS` junto com `EMAIL_BACKEND`). A checagem não aplica migrações. A tabela customizada e o primeiro superusuário estão criados no banco novo, conforme confirmação do responsável.
- Auditoria estática de 2026-11-25: os apps de domínio seguem como scaffolds vazios; somente `users.User` e sua configuração no Admin têm código de domínio. A política de senha exige oito caracteres, maiúscula, número e símbolo; as sessões expiram após 15 minutos de inatividade e os cookies têm atributos `HttpOnly`, `SameSite=Lax` e `Secure` fora de DEBUG. O Admin de usuários permite consulta, mas bloqueia inclusão, edição e exclusão até que services de domínio controlem essas operações. Serviços, rotas dos portais, RBAC, templates e testes funcionais ainda não existem. Revisão estática; testes não executados.
- Não foram implementados provedores de SMS, e-mail transacional, LLM, voz, mapas/hospitais, assinatura ICP-Brasil, verificação CRM/CRF, chat em tempo real ou push/WhatsApp.
- Foi criado `.gitignore` na raiz para ambientes virtuais, caches Python, banco SQLite local, arquivos `.env`, mídia, logs e configurações locais de editor. `db.sqlite3` e `core/__pycache__/*.pyc` foram removidos do índice do Git; os arquivos locais de cache foram preservados.
- Auditoria Git de 2026-11-25: a árvore de trabalho não tem `.env`, banco local ou credenciais staged/rastreados e o `.gitignore` cobre `env/`, `.env*` e `db.sqlite3`. Porém o histórico local de `origin/main` contém commits antigos com `db.sqlite3` e uma chave Django gerada em `core/settings.py`; `.gitignore` não os remove retroativamente. Confirmar conteúdo/visibilidade do repositório e rotacionar qualquer chave ainda em uso. Uma limpeza do histórico exige reescrita coordenada dos commits antes de publicar em novo remoto ou repositório público.

## Próximos passos

1. Implementar a primeira fatia vertical WebApp de contas conforme Specs 0002 e 0003: cadastro de paciente titular, autenticação por CPF/e-mail, sessões e portais segregados/RBAC.
2. Definir o texto/registro de consentimento e a integração de verificação por SMS antes de concluir o fluxo de cadastro público.
3. Implementar dependentes e gestão/provisionamento profissional conforme Specs 0004 e 0005.
4. Validar protocolo/red flags e regras de prescrição com responsáveis clínicos; validar requisitos jurídicos/regulatórios com responsáveis competentes antes dos fluxos clínicos.
5. Implementar funcionalidades progressivamente a partir das specs aceitas, gerando/revisando migrações e testes.

## Pendências de produto e operação

- Limites clínicos/etários de altura e peso, texto e retirada de consentimento, verificação de SMS e processo para menores.
- Provedor, região, retenção e contrato de processamento do LLM; integração de STT/TTS e tratamento de áudio de chat (RF010 versus descarte RF015).
- Validar versão do Protocolo de Manchester, red flags, algoritmos de compatibilidade e critérios de alerta de alergia.
- Provedores e contratos para e-mail, SMS, notificações multicanal, geolocalização/diretório hospitalar, ICP-Brasil, CRM e CRF/CNPJ.
- Confirmação de entrega, métricas de disponibilidade/latência e limites de gargalo; links de redefinição seguem validade de 30 minutos da Spec 0003.
- Todas as decisões de arquitetura (ADRs 0001–0005) foram aceitas; permanecem pendentes escolhas operacionais de provedores e contratos externas listadas acima.
- Bootstrap do primeiro administrador, autorização do farmacêutico para baixa e retenção/regra de expurgo por tipo de registro.
- Definição operacional de ambientes segregados, backup diário criptografado, monitoramento/alertas, arquivamento em camadas e proteção de imutabilidade/não-repúdio da auditoria (RNF011, RNF014 e RS011).
