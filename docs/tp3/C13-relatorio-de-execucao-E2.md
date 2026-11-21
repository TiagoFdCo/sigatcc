# C13 · Relatório de execução dos testes da E2 (TP3)

Pacote 10.3 · Plano de Testes Detalhado v1.1, anexo C · ISO/IEC/IEEE 29119-3

| Item | Valor |
|---|---|
| Marco · versão | E2 (TP3) · `main` em `5361cca` · 20/11/2026 (entrega adiada de 18/11, FSM-09) |
| Ambiente da parte automatizada | CI do GitHub Actions (PostgreSQL 16) e execução local equivalente |
| Executores | pytest e Vitest (automação); Pedro Augusto e Caio Pereira (parte manual, pendente) |
| Evidências | `docs/evidencias/E2/`: `pytest-backend.txt` (resultado e cobertura), `pytest-backend.xml` (JUnit), `vitest-frontend.txt` |

## 1. Resumo

| Indicador | Valor | Meta (Plano de Testes, seção 4) |
|---|---|---|
| Casos da E2 planejados | 24 | — |
| Executados por automação | 20 (83%) | 100% dos casos Crítica e Alta |
| Aprovados | 20 de 20 executados (100%) | ≥ 90% |
| Pendentes (manuais, em homologação) | 3: CT-LOG-03, CT-DSH-02, CT-FUM-01 | — |
| Aguardando decisão da PO | 1: CT-SIT-02 (D-04) | — |
| Testes automatizados | 454 no back-end (26 arquivos) e 16 no front-end (3 arquivos), todos aprovados | — |
| Cobertura do back-end | 96,7% | ≥ 70% |
| Defeitos críticos ou altos abertos | 0 | 0 |

Os 18 casos de prioridade Crítica ou Alta com automação foram executados e aprovados. Dos casos Crítica e Alta, só o CT-FUM-01 (roteiro de fumaça) depende de homologação. Por isso, o critério de saída da E2 fica **cumprido na parte automatizada** e **condicionado** à execução do roteiro de fumaça na v0.3.0 em homologação.

## 2. Resultado por caso

| Caso | Título | Prioridade | Testes aprovados | Resultado | Observação |
|---|---|---|---|---|---|
| CT-PUB-01 | Registrar publicação aprova o TCC sem banca | Alta | 2/2 | Aprovado |  |
| CT-PUB-02 | ISSN ou DOI inválido é recusado | Alta | 11/11 | Aprovado |  |
| CT-PUB-03 | Publicação exige comprovante ou link; data futura é recusada | Alta | 6/6 | Aprovado | Regra da D15 corrigida no PR #42 (D-08): basta o comprovante ou o link. |
| CT-PUB-04 | Publicação não convive com banca | Alta | 2/2 | Aprovado |  |
| CT-PUB-05 | Falha no log desfaz a publicação | Crítica | 1/1 | Aprovado |  |
| CT-ALU-01 | Cadastro do aluno com dados únicos | Alta | 3/3 | Aprovado |  |
| CT-ALU-02 | Aluno só entra depois de confirmado pelo Professor de TCC | Alta | 18/18 | Aprovado | Desvio a confirmar com a PO: a senha é definida pelo Administrador, e não pelo aluno no primeiro acesso. |
| CT-ALU-03 | Aluno vê só o próprio TCC e CPF mascarado | Alta | 13/13 | Aprovado |  |
| CT-BAN-01 | Conflito de horário com membro em comum | Alta | 2/2 | Aprovado | O alerta cita a banca existente (TCC, dia e hora) e o membro (PR #44). |
| CT-BAN-02 | Conflito de local (mesmo bloco e sala) | Alta | 2/2 | Aprovado |  |
| CT-BAN-03 | Bancas encostadas não conflitam (valor-limite) | Média | 2/2 | Aprovado |  |
| CT-BAN-04 | Validação do conflito dentro da meta de tempo | Média | 1/1 | Aprovado | Automatizado: a validação consulta só a janela de horário (no máximo 2 consultas). A medição do p95 com 2.000 TCCs fica para o 10.5 (k6). |
| CT-BAN-05 | Regressão do cadastro de banca | Alta | 40/40 | Aprovado |  |
| CT-LOG-01 | Só o Administrador consulta os logs | Alta | 10/10 | Aprovado |  |
| CT-LOG-02 | Log é só de acréscimo e filtrável | Alta | 20/20 | Aprovado |  |
| CT-DSH-01 | Números do dashboard batem com consulta direta | Alta | 8/8 | Aprovado | Achou e corrigiu o defeito D-09 (TCC inativo nos indicadores). Inclui a matriz de permissão (D-07). |
| CT-PRF-01 | Orientador não abre nem edita TCC de outro orientador | Crítica | 21/21 | Aprovado |  |
| CT-PRF-02 | Secretária lê TCC restrito sem editar | Alta | 2/2 | Aprovado |  |
| CT-SIT-01 | Transições de situação do TCC | Alta | 26/26 | Aprovado |  |
| CT-MOD-01 | Migrations do modelo v2 sem perda de dados | Alta | 23/23 | Aprovado | Automatizado no banco de teste. Falta a conferência das contagens numa cópia da base de homologação. |
| CT-LOG-03 | Tela de consulta do log | Média | — | Pendente | Roteiro manual em homologação. |
| CT-DSH-02 | Linha de base de tempo do dashboard | Média | — | Pendente | Lighthouse (LCP) e p95 do endpoint em homologação. |
| CT-FUM-01 | Roteiro de fumaça da E2 em homologação | Alta | — | Pendente | Depende do deploy da v0.3.0 em homologação. |
| CT-SIT-02 | "Apresentado" exige banca cadastrada | Média | — | Bloqueado | Aguarda a decisão da PO sobre o D-04. |

A lista de testes de cada caso está em `docs/evidencias/E2/pytest-backend.txt` (linhas `PASSED`). O mapa entre caso e teste foi gerado a partir do relatório JUnit.

## 3. Defeitos

| # | Descrição | Pacote | Severidade | Situação |
|---|---|---|---|---|
| D-01 | Conflito de horário e de local da banca não era validado | 6.2 | Alta | Fechado em 20/11 (merge da C4; ajustes no PR #44) |
| D-02 | Aluno sem confirmação pelo Professor de TCC e sem acesso | 4.2 | Alta | Fechado em 20/11 (merge da C2a) |
| D-03 | Dashboard sem endpoint e fora do menu | 8.1 | Alta | Fechado em 20/11 (merge da C8) |
| D-04 | TCC pode ir a "Apresentado" sem banca cadastrada | 5.2/6.1 | Média | Aberto: aguarda a PO |
| D-05 | Commits direto na `main` sem PR (13/11) | 8.1 / RNF11 | Média (processo) | Aberto: proteger a branch `main` (R18) |
| D-06 | nginx de produção sem TLS | 11.4 / RNF02 | Alta para o E3 | Aberto: tratar antes do ensaio de 01/12 (R13) |
| D-07 | Dashboard respondia a aluno e membro externo | 8.1 / RNF03 | Alta | Fechado em 20/11 (PR #41) |
| D-08 | Publicação exigia o comprovante mesmo com link (contra a D15) | 5.3 | Média | Fechado em 20/11 (PR #42) |
| D-09 | TCC inativo contado nos indicadores do dashboard | 8.1 | Média | Fechado em 20/11 (PR #43) |
| D-10 | Dois cadastros simultâneos de banca podiam passar pela validação de conflito; alerta não citava a banca existente | 6.2 | Média | Fechado em 20/11 (PR #44) |

Cada defeito fechado tem um teste automatizado que o reproduz.

## 4. Desvios e riscos

- **Data:** a entrega passou de 18/11 para 20/11 (FSM-09, problema P2 no Plano de Integração v3.5).
- **CT-ALU-02:** o fluxo implementado é "Professor de TCC confirma e Administrador define a senha". O plano previa que o aluno definisse a senha no primeiro acesso. Confirmar com a PO.
- **Riscos ligados:** R19 (defeitos de ambiente que só aparecem na demonstração) até a execução do CT-FUM-01; R18 (integração sem revisão) até a branch `main` ser protegida.

## 5. Recomendação

☐ Liberar · ☒ **Liberar com ressalvas** · ☐ Não liberar

Ressalvas: executar CT-FUM-01, CT-LOG-03 e CT-DSH-02 em homologação com a v0.3.0, e conferir as contagens do CT-MOD-01 na cópia da base. Também falta registrar a decisão da PO sobre o D-04 e o CT-ALU-02.

| Assinaturas | Nome | Data |
|---|---|---|
| Testers | Caio Pereira, Pedro Augusto | |
| Product Owner | Profa. Diana | |
