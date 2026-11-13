import { api } from './cliente';
import { DocenteItem, SolicitacaoOrientacao, AreaInteresse } from './tipos';

export const getAreasInteresse = async (): Promise<AreaInteresse[]> => {
  return await api<AreaInteresse[]>('/areas/');
};

export const buscarDocentes = async (areaId?: string, busca?: string): Promise<DocenteItem[]> => {
  const params = new URLSearchParams();
  if (areaId) params.append('area', areaId);
  if (busca) params.append('busca', busca);

  return await api<DocenteItem[]>(`/docentes/?${params.toString()}`);
};

export const solicitarOrientacao = async (docenteId: number, mensagem?: string): Promise<SolicitacaoOrientacao> => {
  return await api<SolicitacaoOrientacao>('/solicitacoes-orientacao/', {
    method: 'POST',
    body: JSON.stringify({ docente: docenteId, mensagem: mensagem || '' })
  });
};
