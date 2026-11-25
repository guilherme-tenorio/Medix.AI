# Spec 0015: Gestão de administradores e monitoramento

- **Status:** Proposto
- **Aprovação:** Aceita pelo responsável em 2026-11-25
- **Requisitos:** RF-07 e RF-08 do [PRD 0004](../prd/0004-fila-medica-e-notificacoes.md), RF-11 do [PRD 0001](../prd/0001-contas-perfis-e-pacientes.md)
- **Depende de:** [Spec 0003](0003-autenticacao-e-sessao.md), [Spec 0008](0008-fila-clinica.md), [Spec 0012](0012-prontuario-e-historico.md)
- **Fonte:** RF022 de `docs/DocumentoRequisitoMEDIX.AI (4).md`

## Fluxos

### Gestão de conta administrativa

- O acesso é restrito ao perfil Administrador autenticado e ocorre pelo painel web administrativo. Administradores gerem contas auxiliares com CPF, nome, data de nascimento, celular, e-mail corporativo, senha provisória e status.
- Convite envia senha provisória por e-mail; primeiro login exige troca. A fonte indica dados únicos e validações de CPF, maioridade e nome, conforme RF022/RF017.
- Somente administrador ativo pode criar, consultar, alterar ou desativar contas administrativas, com cada ação registrada em trilha imutável com autor, data/hora, IP e ação.
- Antes de desativar conta, verificar que existe outro administrador ativo; bloquear a operação quando o alvo é o último administrador.
- Primeiro acesso com senha temporária exige troca conforme Spec 0003.
- A auto-inativação é bloqueada quando o administrador é o último administrador ativo. Cadastros médicos desligados são inativados logicamente e as sessões ativas são revogadas sem apagar histórico. (Fonte: RS011)
- Registros de auditoria são imutáveis e não podem ser excluídos fisicamente. A garantia operacional de não-repúdio deve ser definida antes da implementação.

### Painel operacional

- Administrador autorizado consulta métricas ao vivo de tamanho da fila, tempo de espera, emergências e gargalos.
- Painel é atualizado continuamente e apresenta alertas de gargalo; inclui métricas de fila, tempos de espera, emergências e pareceres.
- Administrador consulta trilha de auditoria por período, CPF/CRM do operador, tipo de evento e severidade; eventos incluem acesso a prontuário, login e emissão/revogação de receita.
- Administra e consulta médicos em plantão ativo e histórico de notificações enviadas.
- Painel não disponibiliza dados clínicos individuais além do necessário para operação e autorização.

## Pendências

- Fonte não define frequência/latência de atualização, limiares para gargalo, fórmulas dos indicadores ou retenção da auditoria.
- Fonte não detalha segundo fator ou segregação de funções administrativas.

## Testes

- [ ] Usuário sem perfil administrador recebe acesso negado.
- [ ] Último administrador ativo não pode se desativar.
- [ ] Métricas incluem fila, espera, emergências e gargalos sem inferir limiares ausentes.
- [ ] Filtros de auditoria por operador, período e evento funcionam e a consulta é registrada.
- [ ] O painel administrativo é separado do painel médico e do fluxo de autocadastro de pacientes.