import React, { useEffect, useState } from 'react';
import { getMetricasDashboard, MetricasDashboard } from '../api/dashboardService';
import { DashboardCards } from '../componentes/DashboardCards';

export const DashboardIndicadoresView: React.FC = () => {
  const [metricas, setMetricas] = useState<MetricasDashboard | null>(null);
  const [carregando, setCarregando] = useState<boolean>(true);
  const [erro, setErro] = useState<string>('');

  useEffect(() => {
    getMetricasDashboard()
      .then((dados: MetricasDashboard) => setMetricas(dados))
      .catch((err: Error | any) => setErro(err?.message || 'Erro ao carregar indicadores.'))
      .finally(() => setCarregando(false));
  }, []);

  if (carregando) return <div className="carregando">Carregando painel de indicadores...</div>;
  if (erro) return <div className="alerta alerta-perigo">{erro}</div>;
  if (!metricas) return null;

  return (
    <div className="conteudo-principal">
      <header className="cabecalho-pagina">
        <h1>Painel Geral de Indicadores (C8)</h1>
        <p>Acompanhamento analítico e métricas em tempo real do progresso dos TCCs</p>
      </header>

      <DashboardCards metricas={metricas} />
    </div>
  );
};
