# ADR 0004: Organização dos apps Django por domínio

- **Status:** Aceito
- **Aprovado em:** 2026-11-25

## Contexto

O MEDIX.AI é um único WebApp Django com fluxos que atravessam perfis de paciente/responsável, médico e administrador. Organizar apps por perfil duplicaria regras e dificultaria a coordenação de fluxos como triagem, atendimento, prescrição e prontuário. O projeto já contém o app `users`, instalado e sem modelos ou migrações de domínio.

## Decisão

Organizar o monólito Django por domínio, mantendo um único deploy e banco PostgreSQL:

- `users`: usuário autenticável, papéis, login, recuperação de senha e sessões; define o modelo customizado de usuário.
- `patients`: titulares, dependentes, perfis clínicos e consentimentos.
- `professionals`: dados profissionais, CRM, documentos, homologação e disponibilidade médica.
- `triage`: anamnese, classificação, red flags e encaminhamento de emergência.
- `care`: filas, chat e encontros/consultas clínicas.
- `prescriptions`: revisão médica, assinatura, emissão, validação pública e dispensação.
- `records`: linha do tempo e consulta do prontuário clínico.
- `audit`: trilhas de auditoria de segurança e operação, separadas do conteúdo clínico do prontuário.
- `notifications`: preferências, despacho e histórico de notificações.

Cada app é proprietário dos seus models e consultas ORM, concentradas nos services do domínio. Um app que precise executar uma operação de outro domínio chama o service público desse domínio; não replica a regra nem contorna o service com consultas ORM. Views e templates pertencem aos fluxos correspondentes, não a apps separados por perfil. O painel administrativo pode compor services dos domínios sem formar um app por papel.

O modelo customizado `users.User` e `AUTH_USER_MODEL` são definidos antes da primeira migração de domínio. Perfis profissionais e clínicos são dados vinculados a `User`; dependentes não recebem conta autenticável.

## Consequências

- Os limites tornam mais claro quem mantém cada regra, dado e migração, preservando o monólito e o deploy único.
- Fluxos completos atravessam vários services e precisam coordenar transações e tratamento de falhas; contratos e dependências entre domínios devem ser registrados nas specs.
- A trilha de auditoria e o prontuário clínico têm modelos e políticas distintos, exigindo coordenação sem permitir alteração dos registros imutáveis.
- Criar o modelo customizado de usuário antes das migrações reduz o risco de uma migração estrutural difícil posteriormente.
