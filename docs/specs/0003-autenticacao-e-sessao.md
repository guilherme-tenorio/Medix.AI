# Spec 0003: Autenticação, recuperação e sessão

- **Status:** Proposto
- **Requisitos:** RF-06 do [PRD 0001](../prd/0001-contas-perfis-e-pacientes.md)
- **Depende de:** [Spec 0002](0002-cadastro-de-pacientes.md)
- **Fonte complementar:** RF016, RF017, RNF006, RNF007 e RS008 de `docs/Cópia de DocumentoRequisitoMEDIX.AI.md`

## Pré-condições

- O usuário possui conta ativa criada pelo cadastro de paciente (Spec 0002) ou pela gestão profissional (Spec 0005).

## Fluxo principal

1. O usuário informa CPF ou e-mail e senha.
2. O sistema localiza conta ativa e compara a senha com o hash armazenado.
3. Após validação, identifica o perfil (Paciente, Médico ou Administrador) e concede as permissões correspondentes.
4. Direciona o paciente ao aplicativo/área de pacientes, o médico ao painel clínico no navegador e o administrador ao painel administrativo no navegador. O login é comum conforme RF016, mas cadastro/provisionamento e interfaces são separados por papel.
5. A sessão encerra após 15 minutos sem atividade. “Sair” encerra e invalida a sessão do dispositivo atual.
6. “Esqueci minha senha” envia ao e-mail cadastrado um link de uso único válido por 30 minutos. O usuário pode alterar a senha nas configurações de segurança.

## Alternativas e erros

- Credenciais inválidas: não autenticar; após cinco falhas consecutivas, bloquear temporariamente a conta por 15 minutos e enviar alerta de segurança por e-mail.
- Conta inativa/suspensa: negar acesso, inclusive a painéis clínicos.
- Link expirado ou já utilizado: negar redefinição e solicitar novo link.
- A fonte não define o comportamento quando o e-mail de recuperação não está acessível ou o envio falha.

## Regras e dados

- Identificador aceita CPF ou e-mail cadastrado; senha nunca trafega nem fica armazenada em texto simples.
- A cada tentativa deve ser possível consultar histórico de acesso por período, identificador, perfil e resultado, conforme acesso administrativo previsto pela fonte.
- A autorização deve distinguir estritamente os três perfis. O vínculo do responsável com dependente é verificado na Spec 0004.

## Contrato web e serviço

Credenciais, operação de redefinição e resultado de autenticação são os contratos funcionais. Rotas, mecanismo de sessão e formato do token de redefinição dependem de `docs/arquitetura.md` e de decisão técnica; regras de autenticação e ORM ficam no service.

## Testes

- [ ] Login com CPF e com e-mail funciona somente para conta ativa.
- [ ] Cinco falhas consecutivas geram bloqueio temporário de 15 minutos e alerta por e-mail.
- [ ] Sessão expira após 15 minutos de inatividade e logout invalida a sessão atual.
- [ ] Link de recuperação é de uso único e expira em 30 minutos.
- [ ] Cada perfil recebe somente as permissões correspondentes.


## Fonte vigente

A fonte atual de requisitos é docs/Cópia de DocumentoRequisitoMEDIX.AI.md (2026-11-23). Quando o texto desta spec divergir de requisito RF/RNF/RS atualizado nessa fonte, prevalece a fonte e deve-se ajustar a especificação antes de implementar.


## Requisitos atualizados da fonte

- Login aceita CPF ou e-mail e senha, com controle por papel e resposta 403 em rota proibida.
- Cinco falhas consecutivas bloqueiam a conta por 15 minutos e geram alerta; sessão expira após 15 minutos sem atividade.
- Recuperação envia link único por e-mail válido por 30 minutos e não revela se a conta existe. Troca autenticada exige senha atual; senha mínima: 8 caracteres, maiúscula, número e símbolo. Primeiro acesso de médico/administrador com senha temporária exige troca.
- A fonte menciona token seguro JWT/OAuth sem escolher fluxo, emissor, duração ou armazenamento. Definir contrato antes da implementação.
