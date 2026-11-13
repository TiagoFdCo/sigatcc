import { api } from './cliente';

export interface MetricasDashboard {
  total_tccs: number;
  em_andamento: number;
  defendidos: number;
  bancas_proximas: number;
  pendentes_avaliacao?: number;
}

export const getMetricasDashboard = async (): Promise<MetricasDashboard> => {
  return await api<MetricasDashboard>('/dashboard/metricas/');
};
