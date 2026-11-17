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
  if (erro) return <div className="alerta alerta-erro">{erro}</div>;
  if (!metricas) return null;

  return (
    <div className="pilha">
      <header className="cabecalho-pagina">
        <div>
          <h1>Painel Geral de Indicadores (C8)</h1>
          <p className="subtitulo texto-suave">
            Acompanhamento de métricas RBN20-RBN23 e conclusões do TCC
          </p>
        </div>
      </header>

      <DashboardCards metricas={metricas} />
    </div>
  );
};
