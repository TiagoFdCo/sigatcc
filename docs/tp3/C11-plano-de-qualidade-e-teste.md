# Plano de Qualidade e de Teste – SIGATCC (TP3)

Pacote da EAP **10.2 Plano de qualidade e de teste (TP3)** · atividade **C11** · marco **E2 (18/11/2026)**
Responsável: Tiago Feitosa · Revisão: 12/11/2026

Este plano diz **como a equipe garante e verifica a qualidade do SIGATCC**: quais características da ISO/IEC 25010:2023 valem para o produto, qual meta mede cada requisito não funcional (RNF), como e quando cada meta é verificada e quais testes rodam em cada nível. Ele alimenta a seção 4.1.5 (Plano de Gerenciamento da Qualidade) do Plano de Integração, que a atividade C12 atualiza.

Critério de aceite do pacote 10.2: **cada RNF em escopo tem uma forma de verificação** (seção 3).

---

## 1. Referências

- ISO/IEC 25010:2023, modelo de qualidade do produto (9 características; aula de Escopo, bloco 3)
- PMBOK 7: domínio de desempenho de Entrega (qualidade) e custo da qualidade (prevenção e avaliação × falhas)
- Planilha de requisitos v2 (aba RNF, RNF01 a RNF14, priorizados por MoSCoW)
- Plano de Integração v2 (dicionário da EAP: metas de cada RNF; seção 4.1.5)
- Documento de Arquitetura (seção 8, atributos de qualidade)
- Cronograma v3.1 (atividades C13, D5, D6 e D7)

## 2. Adaptação do modelo ISO/IEC 25010:2023 ao SIGATCC

A norma recomenda adaptar o modelo antes de usá-lo: nem toda característica pesa igual em todo produto. A tabela mostra o que vale para o SIGATCC e por quê.

| Característica (2023) | Peso no SIGATCC | Subcaracterísticas verificadas | RNF ligados |
|---|---|---|---|
| Adequação funcional | Alto | completude, correção, adequação | todos os RBN Must (testes de fluxo) |
| Eficiência de desempenho | Alto | comportamento no tempo, capacidade | RNF04 |
| Compatibilidade | Baixo | interoperabilidade (Resend) | RNF07 (Could) |
| Capacidade de interação | Médio | operabilidade, proteção contra erro do usuário, inclusão | RNF01 |
| Confiabilidade | Alto | disponibilidade, recuperabilidade | RNF05, RNF10 |
| Segurança (security) | Alto | confidencialidade, integridade, responsabilização (accountability), autenticidade | RNF02, RNF03, RNF08, RNF12 |
| Manutenibilidade | Médio | modularidade, testabilidade | RNF11 (Could) |
| Flexibilidade | Médio | adaptabilidade, instalabilidade | RNF09 |
| Segurança física (safety) | Não se aplica | — | — |

**Segurança física (safety)** não se aplica: o SIGATCC é um sistema administrativo e uma falha dele não põe em risco pessoas, bens ou o ambiente. Os riscos de uso (perda de dados, vazamento) já estão cobertos por Confiabilidade e Segurança.

**Fora do escopo desta versão (Won't have):** RNF06 Escalabilidade, RNF13 Internacionalização e RNF14 Modo offline. Não recebem meta nem teste.

## 3. RNF em escopo: meta, verificação e momento

Cada linha é um RNF Must, Should ou Could. A meta vem do dicionário da EAP do Plano de Integração; a forma de verificação diz o que conta como evidência.

| RNF | Prioridade | Característica · subcaracterística | Meta | Como é verificado | Quando (pacote · marco) |
|---|---|---|---|---|---|
| RNF01 Usabilidade | Must | Capacidade de interação · operabilidade, inclusão | Contraste WCAG 2.1 AA; telas utilizáveis de 360 a 1920 px; mensagens de erro por campo | Checklist de acessibilidade (Lighthouse ou axe) nas telas principais; teste manual nas larguras 360, 768 e 1920 px; validação de usabilidade com a coordenação e a secretaria do NUCOMP | 2.5 e cada tela nova; validação nos marcos E2 e E3 |
| RNF02 Segurança de credenciais | Must | Segurança · confidencialidade, autenticidade | Senha com hash forte (PBKDF2 do Django); HTTPS com TLS 1.2 ou superior; sessão de 30 min (token de acesso de 15 min renovável até 30 min); 5 erros bloqueiam a conta por 15 min | Testes automatizados de login e bloqueio (`test_login.py`); checagem do certificado e do protocolo TLS em homologação e produção (SSL Labs ou `openssl s_client`); conferência de que o banco guarda só o hash | 4.1 (feito), 10.5 e 11.4 · E3 |
| RNF03 Controle de acesso | Must | Segurança · confidencialidade, integridade | 7 perfis com permissões distintas; nenhuma ação fora da matriz perfil × ação | Testes automatizados da matriz perfil × ação (`test_visao_por_perfil.py`, `test_perfis.py`, `test_docentes.py`); tentativa fora do escopo devolve 403 e é registrada | 4.4, 4.5, 4.7 · E2; 4.6 · E3 |
| RNF04 Desempenho | Must | Eficiência de desempenho · comportamento no tempo, capacidade | API com p95 ≤ 2 s com 2.000 TCCs e 50 usuários simultâneos; LCP ≤ 2,5 s no dashboard; exportação ≤ 10 s | Teste de carga com k6 (ou JMeter) sobre base gerada com 2.000 TCCs; LCP medido pelo Lighthouse; tempo da exportação cronometrado no teste | 10.5 · E3 (linha de base do dashboard medida no 8.1, E2) |
| RNF05 Disponibilidade | Should | Confiabilidade · disponibilidade | ≥ 99% no período de defesas | Monitor de disponibilidade (UptimeRobot ou similar) no endpoint `/saude/` a partir da publicação em produção; relatório no encerramento | 11.4 · E3; relatório no E4 |
| RNF07 Interoperabilidade | Could | Compatibilidade · interoperabilidade | ≥ 95% dos convites entregues em até 5 min | Envio de lote de teste pelo Resend com SPF e DKIM configurados; leitura do painel de entregas | 6.3 · E3 |
| RNF08 Auditabilidade | Must | Segurança · responsabilização, integridade | 100% das escritas com linha em LOG_AUDITORIA; log só de acréscimo; retenção ≥ 12 meses; falha no log desfaz a operação | Testes automatizados: um log por escrita e rollback quando o log falha (`test_tcc.py`, `test_banca.py`, `test_publicacao.py`); teste do gatilho que recusa UPDATE e DELETE em LOG_ACESSO (`test_modelo.py`), com o mesmo teste para LOG_AUDITORIA no pacote 8.3 | 8.3 · E2 |
| RNF09 Portabilidade | Must | Flexibilidade · adaptabilidade, instalabilidade | Funciona em Chrome, Firefox, Edge e Safari atuais, de 360 a 1920 px, sem instalação local; o ambiente sobe do zero pelo README | Roteiro manual de fumaça nos 4 navegadores; subida do zero com `docker compose` seguindo o README | 9.2 · E3; cada release |
| RNF10 Backup | Must | Confiabilidade · recuperabilidade | Backup diário; RPO ≤ 24 h; RTO ≤ 4 h; 1 restauração ensaiada e documentada | Ensaio de restauração em ambiente separado, cronometrado, com o registro do resultado | 11.4 · E3 |
| RNF11 Manutenibilidade | Could | Manutenibilidade · modularidade, testabilidade | Cobertura de testes ≥ 70%; 100% dos PRs revisados; lint sem erro | CI do GitHub Actions: `ruff`, `makemigrations --check` e `pytest --cov-fail-under=70` a cada push; proteção da branch main exigindo 1 aprovação | Contínuo (11.1) |
| RNF12 Conformidade (LGPD) | Must | Segurança · confidencialidade | CPF mascarado em toda saída; CPF e matrícula nunca em log nem em URL; dados pessoais só para quem precisa | Testes automatizados de máscara de CPF (`test_docentes.py`, `test_perfis.py`); revisão de logs e URLs; checklist LGPD no teste de RNF | 4.2 · E2; 10.5 · E3 |

## 4. Níveis de teste

| Nível | O que cobre | Ferramenta | Onde roda | Quem |
|---|---|---|---|---|
| Unitário | Regras de negócio dos serviços (`core/services`), validadores e restrições do banco | pytest + pytest-django | Docker local e CI | Quem escreve o código |
| Integração (API) | Endpoints REST com perfil, permissão e transação (o que a SPA usa) | `APIClient` do DRF | Docker local e CI | Quem escreve o código |
| Fluxo (sistema) | Fluxos de ponta a ponta com login JWT real (como `test_fluxo_integracao.py`) | pytest | CI | Qualidade (C13) |
| Front-end | Funções utilitárias e tratamento de erro da SPA | Vitest | CI | Front-end |
| Aceitação | Critério de aceite de cada pacote, demonstrado na Sprint Review | Roteiro manual em homologação | Homologação | Product Owner |
| Não funcional | Carga, segurança, backup e LGPD (seção 3) | k6, Lighthouse, SSL Labs | Homologação | Qualidade (D5) |

Regras gerais:

- Todo código novo chega com teste (regra de ouro do Manual do Integrante).
- Teste de banco usa o PostgreSQL real do container, para que as restrições e o gatilho de log sejam exercitados.
- Teste não depende de ordem nem de dados de outro teste: cada um cria o que usa pelas fixtures de `conftest.py`.

## 5. Escopo dos testes da E2 (atividade C13)

Fluxos que ficaram no E2 depois do replanejamento de 08/11 (FSM-06):

| Fluxo | Pacote | Casos mínimos |
|---|---|---|
| Aprovação por publicação | 5.3 | conclui sem banca; ISSN/DOI inválido é recusado; exige comprovante ou link; não convive com banca |
| Perfil e acesso do aluno | 4.2 | CPF, matrícula ou e-mail duplicados recusados; sem confirmação não entra; vê só o próprio TCC |
| Conflito de banca | 6.2 | sobreposição dos intervalos de 2 h com membro em comum; mesmo local; bancas encostadas não conflitam |
| Log de auditoria | 8.3 | um log por escrita; falha no log desfaz; consulta do log |
| Dashboard base | 8.1 | números batem com consulta direta em amostra; os 4 gráficos presentes; tempo medido |
| Visão por perfil e Secretária | 4.5, 4.7 | matriz perfil × ação; tentativa fora do escopo dá 403 e é registrada; Secretária lê TCC restrito sem editar |
| Modelo de dados v2 | 3.2 | migrations 0004 a 0006 aplicam sem perda; restrições novas recusam dado inválido |

Critério de saída da E2 (pacote 10.3): **nenhum defeito crítico ou alto aberto** e CI verde na main.

## 6. Critérios de entrada e de saída

**Para abrir um PR:** testes do código novo escritos; `pytest` passando no Docker local; pre-commit (ruff) sem erro.

**Para mesclar na main:** CI verde (lint, migrations em dia, testes com cobertura ≥ 70%, type check do front-end, build das imagens); 1 aprovação de outro integrante; critério de aceite do pacote atendido.

**Para fechar um marco:** todos os pacotes do marco mesclados; testes de fluxo do marco passando em homologação; nenhum defeito crítico ou alto aberto; demonstração à Product Owner.

## 7. Gestão de defeitos

Defeitos são registrados como *issue* no GitHub, com o rótulo de severidade, o pacote da EAP e os passos para reproduzir.

| Severidade | Exemplo | Prazo de correção |
|---|---|---|
| Crítica | Perda de dado, acesso indevido a TCC restrito, sistema fora do ar | Antes de qualquer outra tarefa |
| Alta | Fluxo Must quebrado sem contorno | Dentro do sprint |
| Média | Fluxo com contorno, mensagem errada | Até o próximo marco |
| Baixa | Texto, alinhamento | Quando houver folga |

Todo defeito corrigido ganha um teste que o reproduz, para não voltar.

## 8. Garantia de qualidade (prevenção)

- **Revisão de código:** pull request obrigatório, revisado por outro integrante (seção 4.1.5.2 do plano).
- **Revisão de documentos:** requisitos, DER e planos revisados por 2 pessoas antes de cada marco.
- **Definição de pronto (DoD):** funciona, passa nos testes, está no CI verde e foi aprovado pela Product Owner.
- **Retrospectiva quinzenal:** defeitos recorrentes viram ajuste de processo (seção 4.1.8).

O custo da qualidade (PMBOK 7) fica concentrado em prevenção e avaliação (revisão, testes automatizados, CI), porque corrigir um defeito em produção custa muito mais do que na especificação.

## 9. Métricas acompanhadas

| Métrica | Fonte | Meta |
|---|---|---|
| Cobertura de testes do backend | Relatório do `pytest --cov` no CI | ≥ 70% |
| PRs revisados antes do merge | Histórico do GitHub | 100% |
| Defeitos críticos ou altos abertos no marco | Issues do GitHub | 0 |
| RNF Must verificados | Seção 3 deste plano | 100% até o E3 |
| Tempo p95 da API | Relatório do k6 | ≤ 2 s |

## 10. Administração do plano

| Item | Valor |
|---|---|
| Responsável | Tiago Feitosa |
| Atualização | A cada marco e sempre que um RNF mudar |
| Próximos passos | C12 incorpora este plano à seção 4.1.5 do Plano de Integração; D6 detalha os casos de teste do TP4; D5 executa os testes de RNF |
