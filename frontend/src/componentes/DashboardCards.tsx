import React from 'react';
import { MetricasDashboard } from '../api/dashboardService';

interface DashboardCardsProps {
  metricas: MetricasDashboard;
}

export const DashboardCards: React.FC<DashboardCardsProps> = ({ metricas }) => {
  return (
    <div className="grid-cards">
      <div className="card-metrica">
        <span className="label">Total de TCCs</span>
        <h2 className="valor">{metricas.total_tccs}</h2>
      </div>

      <div className="card-metrica">
        <span className="label">Em Andamento</span>
        <h2 className="valor destaque-andamento">{metricas.em_andamento}</h2>
      </div>

      <div className="card-metrica">
        <span className="label">Defendidos / Concluídos</span>
        <h2 className="valor destaque-sucesso">{metricas.defendidos}</h2>
      </div>

      <div className="card-metrica">
        <span className="label">Bancas Próximas</span>
        <h2 className="valor destaque-alerta">{metricas.bancas_proximas}</h2>
      </div>
    </div>
  );
};
