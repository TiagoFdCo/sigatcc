# SIGATCC v0.3.0 · Notas de versão (E2 · TP3)

**Data:** 20/11/2026 (entrega adiada de 18/11, FSM-09) · **Commit:** `main` em `5361cca` · **Versão anterior:** E1 (TP2), 25/10/2026

## O que entra nesta versão

| Pacote | Atividade | O que faz |
|---|---|---|
| 3.2 Modelo de dados atualizado | C9 | Campos de publicação, solicitação, convite, avaliação, auditoria e visibilidade (DER v2) |
| 4.2 Perfil e acesso do aluno | C2a | Professor de TCC confirma ou recusa o cadastro do aluno; aluno só entra depois de confirmado; tela **Meu perfil** com áreas de interesse; aluno vê só o próprio TCC |
| 4.5 Leitura irrestrita da Secretária | C15 | Secretária lê TCC restrito, sem editar |
| 4.7 Visão por perfil | C17 | Orientador só vê e edita os TCCs que orienta; tentativa fora do escopo é registrada |
| 5.3 Aprovação por publicação | C1 | Registra periódico, ISSN ou DOI, data e **comprovante ou link** (D15); aprova o TCC sem banca |
| 6.2 Conflito de banca | C4 | Recusa banca com membro ou sala ocupados no mesmo horário (janela de 2 h); o alerta cita a banca existente; trava contra cadastros simultâneos |
| 8.1 Dashboard base | C8 | Tela **Indicadores** com TCCs em desenvolvimento, apresentados, não apresentados, aprovados por publicação, carga de orientação e carga de bancas por docente; só docente, secretaria e administrador |
| 8.3 Log de auditoria | C7 | Consulta do log de alterações e de acessos pelo Administrador, com filtros e paginação |
| 1.4, 1.6, 10.2 | C10, C12, C11 | Recontagem dos pontos de função, plano de projeto e qualidade, plano de qualidade e de teste |

Também já está no código, mas **ainda não é declarado como entregue** (E3, sem homologação): convites de banca e audiência (6.3), acesso temporário do membro externo (4.6), solicitação e aceite de orientação (7.2) e reunião de alinhamento (7.3).

## Defeitos corrigidos

D-01 (conflito de banca), D-02 (aluno sem confirmação), D-03 (dashboard sem endpoint), D-07 (dashboard aberto a aluno e externo, PR #41), D-08 (comprovante obrigatório, PR #42), D-09 (TCC inativo nos indicadores, PR #43) e D-10 (cadastros simultâneos de banca, PR #44).

## Problemas conhecidos

| # | Problema | Encaminhamento |
|---|---|---|
| D-04 | TCC pode ir a "Apresentado" sem banca cadastrada | Decisão da PO |
| D-06 | nginx de produção sem TLS (não afeta a homologação, que usa Caddy com TLS) | 11.4, antes do ensaio de 01/12 |
| — | A carga de bancas no dashboard soma titulares e suplentes | Confirmar a regra do RBN23 com a PO |

## Qualidade

- 454 testes no back-end e 16 no front-end, todos aprovados; cobertura do back-end de 96,7%.
- CI verde em lint, migrations, testes, type check e build das imagens.
- 20 dos 24 casos de teste da E2 automatizados e aprovados (relatório em `docs/tp3/C13-relatorio-de-execucao-E2.md`).

## Implantação em homologação

1. Fazer o backup do banco de homologação.
2. Fazer o deploy com `scripts/deploy-homologacao.sh` e aplicar as migrations.
3. Criar a tag `v0.3.0` no commit `5361cca`.
4. Rodar o roteiro de fumaça (CT-FUM-01).
5. **Volta atrás:** imagem anterior e restauração do backup da véspera (RTO ≤ 4 h).
