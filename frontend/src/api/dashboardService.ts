import { api } from './cliente';

export interface DocenteCarga {
  id: string;
  nome: string;
  qtd_orientacoes?: number;
  qtd_bancas?: number;
}

export interface MetricasDashboard {
  em_desenvolvimento: number;
  apresentados: number;
  nao_apresentados: number;
  aprovados_publicacao: number;
  orientacoes_por_docente: DocenteCarga[];
  bancas_por_docente: DocenteCarga[];
}

export const getMetricasDashboard = async (): Promise<MetricasDashboard> => {
  return await api<MetricasDashboard>('/dashboard/metricas/');
};
