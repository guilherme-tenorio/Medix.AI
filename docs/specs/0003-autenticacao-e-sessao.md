# Spec 0003: Autenticação, recuperação e sessão

- **Status:** Proposto
- **Aprovação:** Aceita pelo responsável em 2026-11-25
- **Requisitos:** RF-06 do [PRD 0001](../prd/0001-contas-perfis-e-pacientes.md)
- **Decisões:** [ADR 0005](../adr/0005-autenticacao-web-por-sessao.md)
- **Depende de:** [Spec 0002](0002-cadastro-de-pacientes.md)
- **Fonte complementar:** RF016, RF017, RNF006, RNF007 e RS008 de `docs/DocumentoRequisitoMEDIX.AI (4).md`

## Pré-condições

- O usuário possui conta ativa criada pelo cadastro de paciente (Spec 0002) ou pela gestão profissional (Spec 0005).

## Fluxo principal

1. O usuário informa CPF ou e-mail e senha.
2. O sistema localiza conta ativa e compara a senha com o hash armazenado.
3. Após validação, verifica que o papel corresponde ao portal utilizado: paciente/responsável em `/login`, médico em `/medico/login` ou administrador em `/admin/login`.
4. Concede acesso somente à área web correspondente ao perfil. Todos os portais fazem parte do mesmo WebApp; a página de autenticação é segregada por rota e não há cliente móvel nativo no MVP. O cadastro público não permite selecionar papel.
5. A sessão encerra após 15 minutos sem atividade. “Sair” encerra e invalida a sessão do dispositivo atual.
6. No portal de paciente, “Esqueci minha senha” envia ao e-mail cadastrado um link de uso único válido por 30 minutos, sem revelar a existência da conta. Médicos solicitam nova senha provisória ao administrador; administradores podem solicitar redefinição a outro administrador ativo. Todos os perfis podem trocar a senha autenticados, informando a senha atual.

## Alternativas e erros

- Credenciais inválidas: não autenticar; após cinco falhas consecutivas, bloquear temporariamente a conta por 15 minutos e enviar alerta de segurança por e-mail.
- Conta inativa/suspensa: negar acesso, inclusive a painéis clínicos.
- Credencial válida apresentada no portal de outro perfil, ou acesso direto a rota de outro portal: negar com HTTP 403 Forbidden.
- Link expirado ou já utilizado: negar redefinição e solicitar novo link.
- Solicitação de recuperação nos portais médico ou administrativo: não iniciar recuperação pública automatizada; apresentar orientação conforme o fluxo restrito do respectivo perfil sem revelar estado de conta.
- A fonte não define o comportamento quando o e-mail de recuperação não está acessível ou o envio falha.

## Regras e dados

- A autenticação usa o modelo `users.User` configurado como `AUTH_USER_MODEL`, com CPF/e-mail únicos e papel de acesso; esse modelo precisa existir antes da primeira migração que o referencie.
- A sessão é armazenada no servidor; o navegador recebe somente cookie de sessão protegido. Escritas usam CSRF; produção exige HTTPS e cookies `Secure`, `HttpOnly` e `SameSite` conforme ADR 0005.
- O identificador informado pode ser CPF ou e-mail. A autenticação normaliza o identificador e verifica a senha usando os hashes do Django. O vínculo clínico do usuário é validado no service da operação, além do papel.
- Senha nunca trafega em texto simples na aplicação nem é armazenada sem hash.
- A cada tentativa deve ser possível consultar histórico de acesso por período, identificador, perfil e resultado, conforme acesso administrativo previsto pela fonte.
- A autorização deve distinguir estritamente os três perfis. O vínculo do responsável com dependente é verificado na Spec 0004.

## Contrato web e serviço

Credenciais, operação de redefinição e resultado de autenticação são os contratos funcionais. As rotas de entrada são segregadas (`/login`, `/medico/login`, `/admin/login`) e usam sessão Django. Regras de autenticação, resolução CPF/e-mail e ORM ficam nos services; adaptador/backend de autenticação delega a validação a esses services.

## Testes

- [ ] Login com CPF e com e-mail funciona somente para conta ativa.
- [ ] Cinco falhas consecutivas geram bloqueio temporário de 15 minutos e alerta por e-mail.
- [ ] Sessão expira após 15 minutos de inatividade e logout invalida a sessão atual.
- [ ] Link de recuperação é de uso único e expira em 30 minutos.
- [ ] Cada perfil recebe somente as permissões correspondentes.
- [ ] Usar conta válida no portal de outro papel retorna HTTP 403 sem revelar dados da conta.
- [ ] Suspensão/inativação invalida a sessão existente; cookie e CSRF seguem a configuração segura de produção.


## Fonte vigente

A fonte atual de requisitos é docs/DocumentoRequisitoMEDIX.AI (4).md (2026-11-24). Quando o texto desta spec divergir de requisito RF/RNF/RS atualizado nessa fonte, prevalece a fonte e deve-se ajustar a especificação antes de implementar.


## Requisitos atualizados da fonte

- Login aceita CPF ou e-mail e senha, com controle por papel e resposta 403 em rota proibida.
- Cinco falhas consecutivas bloqueiam a conta por 15 minutos e geram alerta; sessão expira após 15 minutos sem atividade.
- Recuperação pública por link único de 30 minutos e sem enumeração é exclusiva do paciente. Médico solicita senha provisória ao administrador; administrador é redefinido por outro administrador ativo. Troca autenticada exige senha atual; senha mínima: 8 caracteres, maiúscula, número e símbolo. Primeiro acesso de médico/administrador com senha temporária exige troca.
- A fonte menciona JWT/OAuth de forma genérica. Pelo escopo WebApp, o [ADR 0005](../adr/0005-autenticacao-web-por-sessao.md) registra a interpretação aprovada: sessão Django no MVP; JWT/OAuth só será reavaliado se surgir API para clientes independentes ou autenticação federada.