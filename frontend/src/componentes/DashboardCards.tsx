import React from 'react';
import { MetricasDashboard } from '../api/dashboardService';

interface DashboardCardsProps {
  metricas: MetricasDashboard;
}

export const DashboardCards: React.FC<DashboardCardsProps> = ({ metricas }) => {
  return (
    <div className="pilha">
      <div className="grade">
        <div className="cartao">
          <span className="texto-suave">Em Desenvolvimento (RBN20)</span>
          <h2>{metricas.em_desenvolvimento}</h2>
        </div>

        <div className="cartao">
          <span className="texto-suave">Apresentados (RBN21)</span>
          <h2>{metricas.apresentados}</h2>
        </div>

        <div className="cartao">
          <span className="texto-suave">Não Apresentados (RBN21)</span>
          <h2>{metricas.nao_apresentados}</h2>
        </div>

        <div className="cartao">
          <span className="texto-suave">Aprovados por Publicação (RD19)</span>
          <h2>{metricas.aprovados_publicacao}</h2>
        </div>
      </div>

      <div className="duas-colunas">
        <div className="cartao coluna-principal">
          <h2>Carga de Orientação por Docente (RBN22)</h2>
          {metricas.orientacoes_por_docente.length === 0 ? (
            <p className="vazio">Nenhum docente com orientações ativas.</p>
          ) : (
            <ul className="membros">
              {metricas.orientacoes_por_docente.map((doc) => (
                <li key={doc.id}>
                  <span>{doc.nome}</span>
                  <span className="selo selo-convite-aceito">
                    {doc.qtd_orientacoes ?? 0} TCC(s)
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="cartao coluna-principal">
          <h2>Carga de Bancas por Docente (RBN23)</h2>
          {metricas.bancas_por_docente.length === 0 ? (
            <p className="vazio">Nenhum docente atribuído a bancas.</p>
          ) : (
            <ul className="membros">
              {metricas.bancas_por_docente.map((doc) => (
                <li key={doc.id}>
                  <span>{doc.nome}</span>
                  <span className="selo selo-convite-pendente">
                    {doc.qtd_bancas ?? 0} banca(s)
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
};
