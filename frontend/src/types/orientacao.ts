export interface AreaInteresse {
  id: number;
  nome: string;
}

export interface DocenteItem {
  id: number;
  nome: string;
  email: string;
  departamento: string;
  aceita_orientacoes: boolean;
  qtd_orientacoes: number;
  areas: AreaInteresse[];
}

export type StatusSolicitacao = 'PENDENTE' | 'ACEITA' | 'RECUSADA';

export interface SolicitacaoOrientacao {
  id: number;
  aluno_id: number;
  aluno_nome?: string;
  docente_id: number;
  docente_nome?: string;
  mensagem?: string;
  status: StatusSolicitacao;
  motivo_recusa?: string;
  enviada_em: string;
  respondida_em?: string;
}
