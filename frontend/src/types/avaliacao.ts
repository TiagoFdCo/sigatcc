export interface AvaliacaoMembroPayload {
  bancaId: number;
  notaApresentacao: number | null;
  notaEscrita: number | null;
  parecer: string;
  isRascunho: boolean;
}

export interface DadosBancaAvaliacao {
  bancaId: number;
  tituloTcc: string;
  autorNome: string;
  orientadorNome: string;
  dataHoraInicio: string;
  tipoLocal: 'PRESENCIAL' | 'REMOTO';
  localInfo: string; // Ex: "Bloco A - Sala 101" ou Link da reunião
}
