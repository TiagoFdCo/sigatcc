import { api } from './cliente';
import { Tcc } from './tipos';

export interface SolicitacaoPublicacaoPayload {
  tcc_id: number;
  link_publicacao?: string;
  comprovante_file?: File;
  observacoes?: string;
}

export const submeterAprovacaoPublicacao = async (
  payload: SolicitacaoPublicacaoPayload
): Promise<Tcc> => {
  const formData = new FormData();
  formData.append('tcc_id', payload.tcc_id.toString());
  
  if (payload.link_publicacao) {
    formData.append('link_publicacao', payload.link_publicacao);
  }
  if (payload.comprovante_file) {
    formData.append('comprovante', payload.comprovante_file);
  }
  if (payload.observacoes) {
    formData.append('observacoes', payload.observacoes);
  }

  return await api<Tcc>('/tccs/aprovar-por-publicacao/', {
    metodo: 'POST',
    corpo: formData,
  });
};
