# Plano de Avaliação do Projeto por Ponto de Função – SIGATCC (TP3)

Pacote da EAP **1.4 Pontos de função e valor** · atividade **C10** · marco **E2 (18/11/2026)**
Responsável: Tiago Feitosa · Revisão: 12/11/2026 · Base: contagem de 08/11 (234 PF), planilha *SIGATCC_Cronograma_EAP_PF_v4*

Este plano diz **como a equipe mede o tamanho do SIGATCC em pontos de função (PF) e usa essa medida para avaliar o projeto**: quanto já foi entregue, a que custo, com que produtividade e se o ritmo cabe no prazo. A contagem detalhada está na aba *Pontos de Função* da planilha de cronograma; aqui ficam o método, a linha de base, as métricas, os limites de alerta e a rotina de acompanhamento.

Critério de aceite do pacote 1.4: contagem por módulo revisada por 2 pessoas; **plano de avaliação por PF pronto** (este documento); produtividade calibrada com horas reais (D25, seção 6).

---

## 1. Objetivos

1. Ter uma medida de tamanho que não depende da tecnologia, para comparar o que foi planejado com o que foi entregue.
2. Converter tamanho em esforço e em valor (custo simbólico) de forma rastreável.
3. Acompanhar o desempenho do projeto a cada marco (E2, E3, E4) com indicadores objetivos.
4. Dar base às decisões de corte de escopo quando o ritmo real não couber no prazo (seção 4.1.2.4 do Plano de Integração).

## 2. Método de contagem

| Item | Decisão |
|---|---|
| Padrão | IFPUG (CPM 4.3) para as funções de dados; NESMA estimada para as transações até o detalhamento de TD e AR |
| Tipo de contagem | Projeto de desenvolvimento |
| Medida | PF **não ajustados**: o fator de ajuste (VAF) não é aplicado, como no IFPUG a partir do CPM 4.3, em que ele é opcional e fica fora do tamanho funcional |
| Fronteira da aplicação | O SIGATCC (SPA + API + banco). Ficam fora: o Resend (serviço de e-mail chamado pela API) e o navegador |
| Propósito | Estimar esforço e valor e avaliar o desempenho do projeto |
| Fonte das funções | RAN e RBN da planilha de requisitos v2; DER v2 para as funções de dados |

Tabela de contribuição usada (aba *Parâmetros*):

| Tipo | Baixa | Média | Alta | Padrão NESMA |
|---|---|---|---|---|
| ALI – arquivo lógico interno | 7 | 10 | 15 | Baixa |
| AIE – arquivo de interface externa | 5 | 7 | 10 | Baixa |
| EE – entrada externa | 3 | 4 | 6 | Média |
| SE – saída externa | 4 | 5 | 7 | Média |
| CE – consulta externa | 3 | 4 | 6 | Média |

### 2.1 Regras de contagem da equipe (decisões D20 a D24)

- **Generalização = um ALI** (D22): docente, aluno e membro externo são um ALI *Usuário* com 4 registros lógicos.
- **Reunião de alinhamento é registro lógico da solicitação de orientação** (D23), e não um ALI próprio.
- **Login conta como CE** (D24), um para o docente e um para o aluno.
- **O convite automático faz parte de "Incluir banca"** (D24); reenviar e responder convite são EE próprias.
- **Exportação não conta à parte** (D24): é outra forma de apresentar a mesma SE.
- **Campos de formulário fazem parte do processo** (D24): anexar comprovante e escolher a visibilidade não são transações separadas.
- **Listagem com contagens = uma SE** (D24): a lista de professores com orientandos e bancas é uma única SE.
- **Sem duplicidade entre pacotes** (D20, D21): o cadastro de professor fica só no pacote 4.4; "Excluir banca" saiu do escopo.

## 3. Linha de base (contagem de 08/11)

**Total: 234 PF não ajustados, em 51 funções.**

### 3.1 Por tipo de função

| Tipo | Funções | PF | Método |
|---|---|---|---|
| ALI | 6 | 45 | Detalhada (IFPUG), TD e RLR tirados do DER v2 |
| EE | 23 | 92 | Estimada (NESMA, complexidade média) |
| CE | 13 | 52 | Estimada (NESMA, complexidade média) |
| SE | 9 | 45 | Estimada (NESMA, complexidade média) |
| **Total** | **51** | **234** | 45 PF detalhados (19%) e 189 PF estimados (81%) |

Não há AIE: o SIGATCC não lê dados mantidos por outra aplicação.

### 3.2 Por módulo (entregável da EAP)

| Código | Entregável | PF | % |
|---|---|---|---|
| 3 | Projeto do Sistema (funções de dados) | 45 | 19% |
| 4 | Módulo Perfis e Acesso | 48 | 21% |
| 5 | Módulo Gestão de TCCs | 32 | 14% |
| 6 | Módulo Bancas e Defesas | 32 | 14% |
| 7 | Módulo Orientação Acadêmica | 30 | 13% |
| 8 | Módulo Dashboards e Governança | 39 | 17% |
| 9 | Módulo Acesso Público | 8 | 3% |
| | **Total** | **234** | 100% |

### 3.3 Por marco (o que deve estar entregue em cada um)

| Marco | Data | PF do marco | PF acumulados | % acumulado |
|---|---|---|---|---|
| E1 · TP2 | 25/10 | 81 | 81 | 35% |
| E2 · TP3 | 18/11 | 69 | 150 | 64% |
| E3 · TP4 | 09/12 | 84 | 234 | 100% |

Os 69 PF da E2 vêm dos pacotes 3.2 (21), 4.2 (20), 8.1 (20), 5.3 (4) e 8.3 (4). Os pacotes 4.5, 4.7 e 6.2 não acrescentam função nova (são regras de acesso e de validação sobre funções já contadas) e por isso não somam PF, embora tenham esforço.

## 4. Do tamanho ao esforço e ao valor

| Parâmetro | Valor | Fonte |
|---|---|---|
| Produtividade de referência | 10 h/PF (**provisória**) | aba *Parâmetros*; recalibrada pela D25 (seção 6) |
| Valor-hora simbólico | R$ 40,00 | Plano de Integração, 4.1.4.1 |
| Custo por PF | 10 h × R$ 40,00 = **R$ 400,00/PF** | derivado |
| Esforço estimado | 234 PF × 10 h = **2.340 h** | derivado |
| Valor estimado (BAC) | 234 PF × R$ 400,00 = **R$ 93.600,00** | derivado |

O cronograma planeja **2.936 h** no total, mas só **736 h** estão nos pacotes que têm PF, o que dá **3,1 h/PF**. As outras 2.200 h são de pacotes que não geram função (requisitos, planos, testes, implantação, documentação e entregas). Ou seja, para os mesmos pacotes de software, a estimativa por PF (2.340 h) é cerca de três vezes o que o cronograma planejou por calendário.

Essa diferença é o principal ponto que a calibração da seção 6 precisa esclarecer: se a produtividade real ficar perto de 10 h/PF, o esforço dos pacotes de software da E2 e da E3 está subestimado no cronograma; se ficar perto de 3 h/PF, a referência de 10 h/PF deve baixar.

## 5. Métricas de avaliação

Todas saem da planilha de cronograma: as horas da aba *Horas*, o status (☐ ◐ ☑) da aba *Cronograma EAP* e os PF da aba *Pontos de Função*. Um pacote só conta como entregue quando está ☑ (mesclado na main e aceito na Sprint Review).

| Métrica | Fórmula | Para que serve |
|---|---|---|
| Tamanho entregue | Σ PF dos pacotes ☑ | Quanto do produto já existe |
| % do tamanho entregue | PF entregues ÷ 234 | Avanço real, comparado à seção 3.3 |
| Produtividade realizada | horas realizadas dos pacotes com PF ÷ PF entregues (h/PF) | Calibra a estimativa (seção 6) |
| Custo realizado por PF | custo realizado ÷ PF entregues (R$/PF) | Compara com os R$ 400,00/PF da linha de base |
| Desvio de esforço | (horas realizadas − horas estimadas) ÷ horas estimadas | Mostra se o pacote custou mais ou menos que o previsto |
| Variação de tamanho | (PF da recontagem − 234) ÷ 234 | Mostra crescimento de escopo (*scope creep*) |

### 5.1 Valor agregado medido em PF

Para ligar tamanho, prazo e custo (PMBOK 7, domínio de Medição), o valor agregado usa o PF como unidade de trabalho:

| Indicador | Fórmula | Leitura |
|---|---|---|
| VP (valor planejado) | PF planejados até a data × R$ 400,00 | Quanto deveria estar pronto |
| VA (valor agregado) | PF entregues × R$ 400,00 | Quanto está pronto |
| CR (custo real) | horas realizadas × R$ 40,00 | Quanto custou |
| IDP (desempenho de prazo) | VA ÷ VP | < 1: atrasado |
| IDC (desempenho de custo) | VA ÷ CR | < 1: acima do custo |
| EPT (estimativa no término) | 93.600 ÷ IDC | Custo final projetado |

**Exemplo com os dados de hoje (12/11):** os 81 PF da E1 estão entregues, então VA = 81 × 400 = R$ 32.400,00. No fim da E2, o VP será 150 × 400 = R$ 60.000,00; se a E2 fechar só com a E1 entregue, o IDP será 32.400 ÷ 60.000 = 0,54. O IDC ainda não pode ser calculado porque a aba *Horas* está vazia (seção 6).

### 5.2 Limites de alerta e resposta

| Situação | Limite | Resposta |
|---|---|---|
| Atraso | IDP < 0,90 em um marco | Replanejar no Sprint Planning; aplicar a ordem de corte da seção 4.1.2.4 do Plano de Integração |
| Estouro de custo | IDC < 0,90 | Rever a produtividade de referência e o esforço do próximo marco |
| Crescimento de escopo | Variação de tamanho > 10% | Abrir Formulário de Solicitação de Mudança (FSM) |
| Estimativa imprecisa | Produtividade realizada mais de 30% acima ou abaixo da referência vigente | Recalibrar na aba *Parâmetros* e registrar a mudança |

## 6. Calibração da produtividade (D25)

Os 10 h/PF são um valor de partida. A D25 manda substituí-los pela produtividade medida pela equipe.

1. **Lançar as horas da E1** na aba *Horas*, uma linha por sessão, como estimativa retroativa marcada como tal na coluna "O que foi feito". Hoje a aba só tem a linha de exemplo, então a calibração ainda **não foi feita**.
2. **Calcular a produtividade realizada da E1** (81 PF): a planilha mostra o valor na aba *Resumo* ("Produtividade real").
3. **Substituir** os 10 h/PF da aba *Parâmetros* pelo valor medido; o esforço e o valor da seção 4 se recalculam sozinhos.
4. **Repetir no fim da E2** com as horas reais (não retroativas) dos 69 PF da E2; a média ponderada das duas vira a referência da E3.
5. **Registrar** cada recalibração no Registro de Alterações do Plano de Integração (4.1.10) e recalcular o VME do risco R7, que hoje usa os 10 h/PF provisórios.

Prazo: passos 1 a 3 até a entrega do TP3 (18/11), com as horas lançadas por cada integrante.

## 7. Recontagem e refinamento

| Quando | O que fazer |
|---|---|
| A cada mudança de escopo aprovada (FSM) | Recontar as funções afetadas e registrar a variação de tamanho |
| Ao implementar cada transação | Preencher TD e AR na aba *Pontos de Função* (células amarelas), trocando a complexidade NESMA pela IFPUG detalhada |
| No fim da E3 (09/12) | Recontagem completa do que foi entregue; comparação com a linha de base de 08/11 |
| No encerramento (E4, 10/12) | Relatório final: PF entregues, produtividade realizada, IDC, IDP e lições aprendidas (seção 6.3 do Plano de Integração) |

Toda contagem ou recontagem é **revisada por 2 pessoas** antes de virar linha de base.

## 8. Responsabilidades

| Papel | Responsabilidade |
|---|---|
| Responsável pela contagem (Tiago Feitosa) | Mantém a aba *Pontos de Função*, conduz a recontagem e calcula os indicadores |
| Revisor da contagem (um segundo integrante, definido no planning) | Confere cada contagem antes de virar linha de base |
| Cada integrante | Lança as próprias horas na aba *Horas* toda semana, com o código do pacote |
| Scrum Master | Leva os indicadores à Sprint Review e aciona as respostas da seção 5.2 |
| Product Owner (Profa. Diana) | Aprova as mudanças de escopo que alteram o tamanho |

## 9. Relatório por marco

A cada marco, o status formal enviado à Product Owner (seção 4.1.6.5 do Plano de Integração) traz:

1. PF entregues e % do tamanho entregue, comparados à seção 3.3;
2. Produtividade realizada (h/PF) e custo por PF;
3. IDP, IDC e EPT;
4. Variação de tamanho desde a linha de base e FSM abertas;
5. Ações tomadas pelos limites da seção 5.2.
