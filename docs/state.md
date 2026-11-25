# Estado atual

Atualizado em: 2026-11-25

## Em andamento

- Fonte vigente: [`DocumentoRequisitoMEDIX.AI (4).md`](DocumentoRequisitoMEDIX.AI%20(4).md), atualizada em 2026-11-24. A cópia sem “(4)” é uma versão histórica substituída.
- Os cinco PRDs estão `Aceito`. As 15 specs foram aprovadas pelo responsável em 2026-11-25; mantêm `Status: Proposto` até que código e testes cumpram cada especificação. RF001–RF022, RNF001–RNF014 e RS001–RS011 estão mapeados na [matriz de rastreabilidade](rastreabilidade-requisitos.md).
- Escopo confirmado: um único WebApp para todos os perfis, sem cliente nativo. Portais web segregados: paciente/responsável em `/login`, médico em `/medico/login` e administrador em `/admin/login`; tentativas de acesso cruzado recebem HTTP 403. Cadastro público apenas para paciente; médicos são provisionados/homologados por administrador; sem cadastro público de administrador ou seletor de papel.
- Escopo do MVP confirmado pelo usuário: inclui cadastro/autenticação, triagem e emergência, fila médica, chat, revisão e ciclo de receitas, prontuário/histórico e fluxos administrativos/notificações conforme PRDs e Specs 0001–0015.
- Divisão dos apps por domínio e autenticação por sessão Django server-side foram aprovadas e registradas nos ADRs 0004/0005. A consulta `showmigrations users auth` em 2026-11-25 mostrou `users (no migrations)` e todas as migrações `auth` de 0001 a 0012 aplicadas. `AUTH_USER_MODEL` não está configurado, portanto o projeto usa o modelo padrão `auth.User`.
- A consulta somente de leitura em 2026-11-25 retornou 1 conta e 1 superusuário no modelo padrão. Antes de implementar a autenticação, definir a transição: migrar para `users.User` customizado (o que exige plano de migração ou reconstrução do banco) ou preservar `auth.User` e armazenar CPF/papel num perfil vinculado. Não executar migrações até registrar essa decisão.
- A decisão de sessões interpreta a menção genérica a JWT/OAuth em RF016 para o escopo WebApp; sem JWT/OAuth no MVP. Reavaliar apenas se surgir API para cliente independente ou login federado.
- RNF009 permanece requisito do produto completo: o MVP WebApp não cumpre a exigência de aplicativo Android/iOS. Interfaces web responsivas não são equivalentes a clientes nativos.
- PRDs, arquitetura, matriz e specs atualizados para a fonte vigente, incluindo os novos RNF011–RNF014 e RS011 e os fluxos revistos de triagem e revisão clínica.
- ADRs 0001–0005 estão aceitos. ADR 0003 aprova a estratégia de integração e anonimização; fornecedor, contrato, retenção e região ainda precisam ser definidos antes do tráfego clínico real.

## Implementação

- O código Django continua em estágio de esqueleto: não implementa os fluxos de cadastro, autenticação, painel médico, chat, triagem ou prontuário. A implementação da avaliação está definida como um WebApp; não há cliente móvel nativo neste repositório.
- Ambiente virtual `env` confirmado pelo usuário com Python 3.13.5, Django 6.1.3 e Psycopg instalado. `python manage.py check` concluiu sem problemas e `python manage.py runserver` iniciou em `http://127.0.0.1:8000/`.
- `showmigrations users auth` confirmou todas as migrações `auth` 0001–0012 aplicadas e nenhuma migração para `users`. Consulta de contagem confirmou uma conta, marcada como superusuária; a criação inicial do superusuário está concluída. Não trocar o modelo de usuário nem criar migrações de domínio antes de decidir a transição.
- Não foram implementados provedores de SMS, e-mail transacional, LLM, voz, mapas/hospitais, assinatura ICP-Brasil, verificação CRM/CRF, chat em tempo real ou push/WhatsApp.
- Foi criado `.gitignore` na raiz para ambientes virtuais, caches Python, banco SQLite local, arquivos `.env`, mídia, logs e configurações locais de editor. `db.sqlite3` e `core/__pycache__/*.pyc` foram removidos do índice do Git; os arquivos locais de cache foram preservados.
- O histórico Git contém ao menos uma versão anterior de `db.sqlite3`; `.gitignore` e a remoção atual não apagam cópias de commits anteriores. Verificar se o histórico foi publicado antes de decidir sobre limpeza de histórico/rotação de credenciais.

## Próximos passos

1. Definir banco limpo ou estratégia de transição para `users.User` antes das migrações, preservando o banco atual até a decisão.
2. Fechar consentimento, verificação SMS, convites e retenção antes de implementar os fluxos correspondentes.
3. Implementar a primeira fatia vertical WebApp de contas/autenticação conforme PRDs e Specs aprovados: modelo de identidade após definir a transição do banco, sessões, autocadastro, portais segregados/RBAC e provisionamento médico.
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
