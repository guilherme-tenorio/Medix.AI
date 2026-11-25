# Rastreabilidade do documento de requisitos

- **Fonte vigente:** [`DocumentoRequisitoMEDIX.AI (4).md`](DocumentoRequisitoMEDIX.AI%20(4).md)
- **Atualizado em:** 2026-11-24
- **Escopo desta matriz:** localizar cada RF, RNF e RS nos PRDs e specs. “Rastreado” significa que há descrição documental; não significa que o fluxo esteja implementado ou validado.

## Requisitos funcionais

| Fonte | PRD | Spec | Situação/documentação |
|---|---|---|---|
| RF001 | PRD 0001 RF-01 | 0001, 0002 | Autocadastro do titular no primeiro acesso, idade mínima, consentimento, CPF/e-mail, SMS e acessibilidade. |
| RF002 | PRD 0001 RF-03–05 | 0004 | Responsável adulto, dependente sem credenciais, vínculo legal, cadastro, auditoria e desativação. |
| RF003 | PRD 0001 RF-02/04 | 0002, 0004, 0006, 0010 | Perfil clínico de titular/dependente, histórico, alergias, comorbidades e uso autorizado. Limites etários de altura/peso pendentes. |
| RF004 | PRD 0002 RF-01/08 | 0001, 0006, 0012 | Anamnese conversacional, sintomas, duração, escala 0–10, perguntas adaptativas e registro imutável. |
| RF005 | PRD 0002 RF-02/03/08 | 0006, 0007, 0008, 0010 | Manchester determinístico, UUID, relatório e quatro fluxos: orientação IA para Branca/Verde sem medicação; fila de validação para Branca/Verde com sugestão; chat para Amarela/Laranja; emergência para Vermelha. Protocolo/red flags aguardam validação clínica. |
| RF006 | PRD 0003 RF-01/04/11 | 0010 | Revisão humana Branca/Verde com medicação ou durante chat; parecer obrigatório, alerta por alergia, justificativa e encaminhamento para chat quando rejeitada/reclassificada. |
| RF007 | PRD 0003 RF-02/10 | 0011 | ICP-Brasil, CRM, assinatura, hash, carimbo de tempo e revogação auditada; hash criptográfico explicitado na fonte atualizada. Provedor/certificado pendentes. |
| RF008 | PRD 0003 RF-02/03 | 0011 | PDF imutável, sem CPF, QR e notificação Push/SMS. Validade deve ser confirmada com fonte competente. |
| RF009 | PRD 0003 RF-03/08 | 0014 | Validação pública, CRF/CNPJ e baixa única imutável; validação de credenciais pendente. |
| RF010 | PRD 0003 RF-05 | 0001, 0008, 0009 | Chat síncrono, contexto clínico prévio ao médico, anexos, áudio/STT, timestamps e diálogo imutável. Retenção do áudio bruto requer confirmação entre RF010 e RF015. |
| RF011 | PRD 0003 RF-09 | 0009, 0012 | Desfecho e conduta obrigatórios, imutabilidade e passagem para emergência quando aplicável. |
| RF012 | PRD 0002 RF-04 | 0001, 0007, 0012 | Alerta em tela cheia, ficha resumida, TTS e exclusão de fila. |
| RF013 | PRD 0002 RF-07 | 0007 | Hospitais ordenados por distância, GPS, busca manual e rota externa. Provedor/diretório pendentes. |
| RF014 | PRD 0002 RF-08; PRD 0003 RF-06/07 | 0012 | Linha do tempo, filtros, isolamento por vínculo, auditoria e retenção. |
| RF015 | PRD 0001 RF-09; PRD 0002 RF-05/06 | 0001 | STT/TTS português brasileiro, alternância voz/texto, confirmação e descarte do áudio. Integração pendente. |
| RF016 | PRD 0001 RF-06 | 0003 | Login CPF/e-mail, RBAC, 403, bloqueio após cinco falhas e sessão de 15 minutos; sessão Django server-side escolhida para o WebApp (ADR 0005), sem JWT/OAuth no MVP. |
| RF017 | PRD 0001 RF-10 | 0003, 0005, 0015 | Recuperação sem enumeração, link único de 30 min, senha forte, troca autenticada e senha provisória no primeiro acesso. |
| RF018 | PRD 0004 RF-01/02 | 0008 | Filas separadas, prioridade, desempate por espera e anonimização parcial até aceite. |
| RF019 | PRD 0004 RF-03 | 0005, 0008 | Online/Pausa/Offline, CRM/certificado, telefone, histórico de plantão e bloqueio de novos chamados Offline. |
| RF020 | PRD 0004 RF-04/05/06 | 0013 | Push/SMS/e-mail/WhatsApp, urgência, deep links, máscara, fallback, preferências e limpeza de lidos. Sem definição sobre preferências e eventos urgentes. |
| RF021 | PRD 0001 RF-07/08 | 0005 | Cadastro/homologação somente por administrador, CRM/UF/documentos, convite e suspensão imediata. |
| RF022 | PRD 0001 RF-11; PRD 0004 RF-06/07/08 | 0015 | Contas administrativas, monitoramento, gargalos, pesquisa de auditoria e proteção do último administrador ativo. |

## Requisitos não funcionais

| Fonte | PRD/specs | Ponto que ainda exige decisão/validação |
|---|---|---|
| RNF001 | PRD 0002; Spec 0001 | Conteúdo e validação de acessibilidade; recursos de voz devem funcionar na interface WebApp quando navegador/dispositivo suportar. |
| RNF002 | PRD 0002; Specs 0001, 0006, 0007 | Mensagens acessíveis para validação, GPS, microfone e falhas de serviço. |
| RNF003 | PRDs 0002/0004; Specs 0006/0007/0013 | Definir se 5s/2s medem resposta, despacho ou entrega e como medir “condições normais”. |
| RNF004 | PRDs 0003/0004; Specs 0008/0009 | Definição de arquitetura de tempo real e critérios de medição de latência. |
| RNF005 | PRDs 0002/0004; Specs 0007/0013 | Plano operacional para disponibilidade 99,5% e confirmação de Push. |
| RNF006 | PRDs 0001/0002/0003; Specs 0001/0002/0003/0006/0009/0011/0012 | Criptografia TLS 1.3/AES-256, hashing e descarte de áudio precisam ser configurados e verificados; anonimização LLM em ADR 0003. |
| RNF007 | PRDs 0001/0003/0004; Specs 0002/0003/0005/0008/0009/0012/0015 | Eventos, retenção e mecanismos de não-repúdio da trilha ainda precisam ser definidos. |
| RNF008 | PRD 0003; Specs 0010–0012/0014 | Validar aplicabilidade de CFM/Anvisa e prazo de 20 anos; escolha de assinatura pendente. |
| RNF009 | PRDs 0001/0004/0005; Specs 0002/0005/0008 | MVP acadêmico definido como web para todos os perfis; requisito de aplicativo nativo Android/iOS fica fora do escopo e não está atendido. Painéis web médico/admin permanecem especificados. |
| RNF010 | PRD 0002; Spec 0006; ADR 0003 | Provedor externo, contrato, região e retenção ainda não selecionados. |
| RNF011 | PRD 0003; Specs 0009/0011/0012 | Arquivamento em camadas, compressão sem perda diagnóstica, escalabilidade e retenção mínima indicada de 20 anos; política e aplicabilidade legal precisam validação. |
| RNF012 | PRDs 0002/0003; Specs 0006/0010/0011/0012 | Confirmar versões e aplicabilidade dos padrões Manchester, DCB, ICP-Brasil, LGPD, CFM e Anvisa antes de produção. |
| RNF013 | PRD 0002; Specs 0006/0007/0010 | IA limitada a apoio clínico, sem prescrição autônoma; red flags determinísticas e validação estruturada. |
| RNF014 | PRD 0004; arquitetura | Ambientes segregados, backup criptografado diário, monitoramento contínuo e alertas operacionais precisam de desenho operacional. |

## Requisitos de segurança

| Fonte | PRD/specs | Situação |
|---|---|---|
| RS001 | PRDs 0001/0002; Specs 0002/0004/0006/0012 | Identidade, idade e vínculo confirmados antes de triagem/consulta/receita. |
| RS002 | PRD 0003; Specs 0010/0011/0014 | Revisão e assinatura válidas, hash, verificação e baixa única. |
| RS003 | PRD 0003; Specs 0008/0009/0012 | Acesso por vínculo/RBAC, criptografia e auditoria médica. |
| RS004 | PRD 0002; Specs 0006/0007 | Red flags têm precedência e não entram em fila virtual. Regras clínicas carecem de validação. |
| RS005 | PRD 0004; Spec 0013 | Push/SMS mascarados até autenticação. |
| RS006 | PRD 0003; Spec 0010 | Cruzamento com alergias/comorbidades e impedimento visual antes da assinatura; catálogo clínico pendente. |
| RS007 | PRD 0001; Spec 0005 | Homologação administrativa e bloqueio imediato de profissional irregular/inativo. |
| RS008 | PRD 0001; Spec 0003 | Bloqueio por força bruta e expiração de sessão. |
| RS009 | PRD 0002; Specs 0001/0009 | Descarte de áudio bruto após transcrição; confirmar comportamento do áudio no chat. |
| RS010 | PRD 0002; Spec 0006; ADR 0003 | Remover nome/CPF e enviar apenas atributos clínicos desidentificados sob TLS 1.3. |
| RS011 | PRDs 0001/0004; Specs 0005/0012/0015 | Inativação lógica de médicos com revogação de sessão, sem exclusão física de registros clínicos/auditoria, logs imutáveis e proteção do último administrador ativo. |

## Contagem de pontos de função da fonte

O documento atualizado mantém a estimativa total em **516 PFNA**: 224 ALI, 15 AIE, 109 SE, 96 EE e 72 CE. A fonte passou a contabilizar como AIE os dados de serviços externos indispensáveis de ICP-Brasil (RF007), mapas/geolocalização (RF013) e STT/TTS (RF015). Essa contagem representa o escopo funcional declarado no documento de requisitos; a implementação deste repositório permanece WebApp, e a compatibilidade nativa Android/iOS do RNF009 não está atendida.

## Limite de conclusão

Todos os identificadores da fonte (RF001–RF022, RNF001–RNF014 e RS001–RS011) estão mapeados documentalmente. Ainda não se pode afirmar que o produto está funcionalmente em conformidade: as specs continuam `Proposto`, os fluxos Django não estão implementados e as decisões listadas acima impedem implementação segura de várias integrações e regras clínicas. A entrega deste projeto é exclusivamente WebApp; o componente de aplicativo nativo Android/iOS previsto no RNF009 do produto completo permanece fora do escopo e não atendido.
