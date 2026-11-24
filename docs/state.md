# Estado atual

Atualizado em: 2026-11-24

## Em andamento

- Fonte vigente: `docs/Cópia de DocumentoRequisitoMEDIX.AI.md`.
- Quatro PRDs e 15 specs estão em `Proposto`; todos os identificadores RF001–RF022, RNF001–RNF010 e RS001–RS010 estão mapeados na [matriz de rastreabilidade](rastreabilidade-requisitos.md).
- Regras de experiência por perfil registradas: paciente inicia autocadastro no primeiro acesso ao aplicativo móvel; médico não tem autocadastro, é provisionado/homologado por administrador e usa painel clínico web; administrador usa painel web administrativo.
- A Spec 0005 descreve o fluxo administrativo do médico; Specs 0003/0008/0009 descrevem login, painel, fila e conversas. PRDs/specs atualizados com telefone/histórico de plantão, preferências e limpeza de notificações, pesquisa administrativa, consulta de prontuário e validação pública de receita.
- ADR 0003 (integração externa de LLM) permanece proposto; arquitetura e matriz delimitam tratamento/anônimização de dados enviados.

## Implementação

- O código Django continua em estágio de esqueleto: não implementa os fluxos de cadastro, autenticação, painel médico, chat, triagem ou prontuário. O cliente móvel de pacientes também não existe neste repositório.
- Ambiente virtual `env` confirmado pelo usuário com Python 3.13.5, Django 6.1.3 e Psycopg instalado. `python manage.py check` concluiu sem problemas e `python manage.py runserver` iniciou em `http://127.0.0.1:8000/`.
- O usuário iniciou `createsuperuser`; conclusão da criação do superusuário e saída de `migrate` ainda não foram confirmadas explicitamente.
- Não foram implementados provedores de SMS, e-mail transacional, LLM, voz, mapas/hospitais, assinatura ICP-Brasil, verificação CRM/CRF, chat em tempo real ou push/WhatsApp.
- Foi criado `.gitignore` na raiz para ambientes virtuais, caches Python, banco SQLite local, arquivos `.env`, mídia, logs e configurações locais de editor. `db.sqlite3` e `core/__pycache__/*.pyc` foram removidos do índice do Git; os arquivos locais de cache foram preservados.
- O histórico Git contém ao menos uma versão anterior de `db.sqlite3`; `.gitignore` e a remoção atual não apagam cópias de commits anteriores. Verificar se o histórico foi publicado antes de decidir sobre limpeza de histórico/rotação de credenciais.

## Próximos passos

1. Confirmar que `python manage.py migrate` terminou sem erros e concluir a criação do superusuário.
2. Definir a tecnologia do aplicativo móvel de pacientes e fechar contratos de autenticação, consentimento, verificação SMS, convites e retenção.
3. Implementar a primeira fatia vertical de contas/autenticação: autocadastro de paciente, perfil/papel e provisionamento de médicos por administrador; especificar painel web médico.
4. Validar protocolo/red flags e regras de prescrição com responsáveis clínicos; validar requisitos jurídicos/regulatórios com responsáveis competentes antes dos fluxos clínicos.
5. Implementar funcionalidades progressivamente a partir das specs aceitas, gerando/revisando migrações e testes.

## Pendências de produto e operação

- Limites clínicos/etários de altura e peso, texto e retirada de consentimento, verificação de SMS e processo para menores.
- Provedor, região, retenção e contrato de processamento do LLM; integração de STT/TTS e tratamento de áudio de chat (RF010 versus descarte RF015).
- Validar versão do Protocolo de Manchester, red flags, algoritmos de compatibilidade e critérios de alerta de alergia.
- Provedores e contratos para e-mail, SMS, notificações multicanal, geolocalização/diretório hospitalar, ICP-Brasil, CRM e CRF/CNPJ.
- Definição de JWT/OAuth, validade/armazenamento de tokens, confirmação de entrega, métricas de disponibilidade/latência e limites de gargalo.
- Bootstrap do primeiro administrador, autorização do farmacêutico para baixa e retenção/regra de expurgo por tipo de registro.
