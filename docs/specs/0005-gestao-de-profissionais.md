# Spec 0005: Cadastro e homologação de médicos

- **Status:** Proposto
- **Requisitos:** RF-07 e RF-08 do [PRD 0001](../prd/0001-contas-perfis-e-pacientes.md)
- **Depende de:** [Spec 0003](0003-autenticacao-e-sessao.md)
- **Fonte:** RF017, RF019, RF021, RNF007, RNF009 e RS007 de `docs/Cópia de DocumentoRequisitoMEDIX.AI.md`

## Separação dos perfis

- Pacientes criam a própria conta pelo fluxo de primeiro acesso descrito na Spec 0002.
- Médicos não têm formulário público de cadastro e não entram pelo cadastro de pacientes.
- Administrador cria e homologa a conta do médico, que recebe convite e acessa o painel clínico pelo navegador.

## Dados e validações

| Campo | Regra |
|---|---|
| CPF | Formato/dígitos válidos, único e imutável |
| Nome | Obrigatório, 3 a 120 caracteres |
| Nascimento | Data válida e não futura; verificar idade compatível com formação conforme regra a definir |
| Celular | Formato brasileiro válido |
| E-mail corporativo | Obrigatório, formato válido e único; recebe convite/login |
| CRM e UF | Obrigatórios; conferir regularidade junto ao conselho; imutáveis após cadastro |
| Comprovante CRM | Obrigatório antes da homologação; PDF, PNG ou JPEG |
| Status | Ativo/Homologado ou Inativo/Suspenso |
| Senha provisória | Forte, enviada por convite; deve ser trocada no primeiro login |

## Fluxo administrativo

1. Administrador autenticado pelo painel web inicia cadastro e informa os dados do profissional.
2. Service valida campos, duplicidade de CPF/e-mail/CRM e presença do comprovante. Médico não tem acesso enquanto a conta não estiver homologada.
3. Administrador confirma CRM/UF regular e homologa o cadastro após verificação documental.
4. Sistema cria perfil Médico, envia convite por e-mail com senha provisória e marca troca obrigatória no primeiro acesso.
5. Médico autentica-se conforme Spec 0003. O roteamento pós-login leva ao painel clínico web responsivo (fila, chats, plantão e dados autorizados do atendimento).
6. Administrador pode atualizar os dados permitidos ou suspender/inativar. Suspensão revoga sessões imediatamente e bloqueia acesso clínico; histórico de atendimento/receita é preservado.

## Disponibilidade e autorização clínica

- Somente médico homologado, ativo, com CRM regular e certificado ICP-Brasil configurado, válido e ativo pode ficar Online.
- Médico suspenso ou inativo não acessa fila, chats, prontuários ou funções clínicas.
- O painel só revela dados de pacientes após aceitação/vínculo autorizado do atendimento; consultas e alterações relevantes são auditadas.
- Cadastro médico é exclusivo de administradores. Administrador não escolhe usar o formulário de cadastro de pacientes para provisionar médico.

## Services, acesso e erros

- Services concentram consultas ao ORM, validações de unicidade, homologação, geração de convite, estado da conta e revogação de sessões; não recebem `request` nem retornam `HttpResponse`.
- Views são classes baseadas em `django.views.View`; rotas administrativas são protegidas por autenticação e papel Administrador. O painel clínico é protegido por papel Médico.
- CRM irregular, documento ausente, duplicidade, operador sem permissão ou certificado inválido impede ativação/entrada Online. Mensagens não revelam dados sensíveis a usuários não autorizados.
- Contas com atendimentos ou receitas nunca são apagadas fisicamente; são suspensas/inativadas.

## Pendências

- A fonte não define provedor de consulta CRM, periodicidade, mecanismo de validação documental, política de certificado, envio/expiração do convite ou bootstrap do primeiro administrador.
- A verificação de idade compatível com formação médica não tem regra definida.
- A interface do aplicativo móvel de pacientes não faz parte deste painel Django.

## Testes

- [ ] Apenas administrador ativo cria/homologa médico; autocadastro médico não existe.
- [ ] Campos, CPF/e-mail/CRM duplicados, documento obrigatório e estado de homologação são validados.
- [ ] Convite temporário exige troca de senha no primeiro acesso.
- [ ] Médico acessa painel web; usuário de outro papel não entra nele.
- [ ] Suspensão revoga sessões e impede novas ações clínicas, preservando prontuários.
- [ ] Apenas CRM e certificado válidos permitem estado Online.
