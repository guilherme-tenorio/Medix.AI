# Estado atual

Atualizado em: 2026-11-23

## Em andamento

- Fonte vigente: `docs/Cópia de DocumentoRequisitoMEDIX.AI.md`.
- Quatro PRDs e 15 specs estão em `Proposto`; todos os identificadores RF001–RF022, RNF001–RNF010 e RS001–RS010 estão mapeados na [matriz de rastreabilidade](rastreabilidade-requisitos.md).
- Regras de experiência por perfil registradas: paciente inicia autocadastro no primeiro acesso ao aplicativo móvel; médico não tem autocadastro, é provisionado/homologado por administrador e usa painel clínico web; administrador usa painel web administrativo.
- A Spec 0005 descreve o fluxo administrativo do médico; Specs 0003/0008/0009 descrevem login, painel, fila e conversas. PRDs/specs atualizados com telefone/histórico de plantão, preferências e limpeza de notificações, pesquisa administrativa, consulta de prontuário e validação pública de receita.
- ADR 0003 (integração externa de LLM) permanece proposto; arquitetura e matriz delimitam tratamento/anônimização de dados enviados.

## Implementação

- O código Django continua em estágio de esqueleto: não implementa os fluxos de cadastro, autenticação, painel médico, chat, triagem ou prontuário. O cliente móvel de pacientes também não existe neste repositório.
- O ambiente virtual `env` aponta para uma instalação Python 3.13 ausente/inacessível (`C:\Users\gteno\AppData\Local\Programs\Python\Python313\python.exe`); `py` não encontra interpreters instalados. Não foi possível executar ou validar migrações/aplicação neste ambiente.
- Não foram implementados provedores de SMS, e-mail transacional, LLM, voz, mapas/hospitais, assinatura ICP-Brasil, verificação CRM/CRF, chat em tempo real ou push/WhatsApp.

## Próximos passos

1. Provisionar um runtime Python compatível com o projeto e verificar dependências/Django.
2. Definir e aceitar contratos para autenticação/token, consentimento, verificação SMS, convites, retenção e serviços externos.
3. Validar protocolo/red flags e regras de prescrição com responsáveis clínicos; validar requisitos jurídicos/regulatórios com responsáveis competentes.
4. Implementar o cliente móvel do paciente e as interfaces web médico/administrador a partir das specs aceitas.
5. Implementar serviços e persistência conforme as specs, gerando/revisando migrações e testes.

## Pendências de produto e operação

- Limites clínicos/etários de altura e peso, texto e retirada de consentimento, verificação de SMS e processo para menores.
- Provedor, região, retenção e contrato de processamento do LLM; integração de STT/TTS e tratamento de áudio de chat (RF010 versus descarte RF015).
- Validar versão do Protocolo de Manchester, red flags, algoritmos de compatibilidade e critérios de alerta de alergia.
- Provedores e contratos para e-mail, SMS, notificações multicanal, geolocalização/diretório hospitalar, ICP-Brasil, CRM e CRF/CNPJ.
- Definição de JWT/OAuth, validade/armazenamento de tokens, confirmação de entrega, métricas de disponibilidade/latência e limites de gargalo.
- Bootstrap do primeiro administrador, autorização do farmacêutico para baixa e retenção/regra de expurgo por tipo de registro.
