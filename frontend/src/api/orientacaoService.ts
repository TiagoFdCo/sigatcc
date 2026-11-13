import { api } from '../api/cliente';
import { DocenteItem, SolicitacaoOrientacao, AreaInteresse } from '../types/orientacao';

export const getAreasInteresse = async (): Promise<AreaInteresse[]> => {
  return await api<AreaInteresse[]>('/api/areas/');
};

export const buscarDocentes = async (areaId?: string, search?: string): Promise<DocenteItem[]> => {
  const params = new URLSearchParams();
  if (areaId) params.append('area', areaId);
  if (search) params.append('search', search);

  return await api<DocenteItem[]>(`/api/docentes/?${params.toString()}`);
};

export const solicitarOrientacao = async (docenteId: number, mensagem?: string): Promise<SolicitacaoOrientacao> => {
  return await api<SolicitacaoOrientacao>('/api/solicitacoes-orientacao/', {
    method: 'POST',
    body: JSON.stringify({
      docente: docenteId,
      mensagem: mensagem || ''
    })
  });
};

export const responderSolicitacao = async (
  solicitacaoId: number,
  status: 'ACEITA' | 'RECUSADA',
  motivo_recusa?: string
): Promise<SolicitacaoOrientacao> => {
  return await api<SolicitacaoOrientacao>(`/api/solicitacoes-orientacao/${solicitacaoId}/responder/`, {
    method: 'PATCH',
    body: JSON.stringify({
      status,
      motivo_recusa
    })
  });
};
