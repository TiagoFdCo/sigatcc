/** Tipos das respostas da API (espelham os serializers do backend). */

export type TipoUsuario = "ADMINISTRADOR" | "DOCENTE" | "SECRETARIA" | "ALUNO" | "MEMBRO_EXTERNO";

export type UsuarioLogado = {
  id: string;
  nome_completo: string;
  email: string;
  tipo_usuario: TipoUsuario;
  professor_tcc: boolean;
};

export type RespostaLogin = {
  access: string;
  refresh: string;
  usuario: UsuarioLogado;
};

// ------------------------------------------------------------------ TCC
export type StatusTcc = "EM_DESENVOLVIMENTO" | "APRESENTADO" | "NAO_APRESENTADO" | "APROVADO_POR_PUBLICACAO";
export type Modalidade = "DEFESA_EM_BANCA" | "PUBLICACAO_APROVADA";
export type Visibilidade = "PUBLICO_TEXTO_COMPLETO" | "PUBLICO_METADADOS" | "RESTRITO";
export type MotivoNaoApresentacao = "DESISTENCIA" | "TRANCAMENTO" | "TRANSFERENCIA" | "OUTRO";

export type Tcc = {
  id: string;
  titulo: string;
  subtitulo: string | null;
  curso: string;
  curso_nome: string;
  area_conhecimento: string;
  area_nome: string;
  modalidade: Modalidade;
  visibilidade: Visibilidade;
  status: StatusTcc;
  motivo_nao_apresentacao: MotivoNaoApresentacao | null;
  motivo_outro: string | null;
  ativo: boolean;
  data_cadastro: string;
  autor: string;
  autor_nome: string;
  autor_matricula: string;
  orientador: string;
  orientador_nome: string;
  coorientador: string | null;
  coorientador_nome: string | null;
  /** C17: o usuario logado pode editar este TCC (visao por perfil). */
  pode_editar: boolean;
};

export type HistoricoStatus = {
  status: StatusTcc;
  data_alteracao: string;
  /** DER v2: quem mudou o status. */
  alterado_por: string;
  alterado_por_nome: string;
  justificativa: string | null;
};

/** C1: publicacao que aprovou o TCC (data_publicacao vem como AAAA-MM-DD). */
export type Publicacao = {
  periodico: string;
  issn_doi: string;
  data_publicacao: string;
  comprovante_arquivo_path: string | null;
  link_artigo: string | null;
};

export type TccDetalhe = Tcc & { historico: HistoricoStatus[]; banca: Banca | null; publicacao: Publicacao | null };

// ---------------------------------------------------------------- Banca
export type TipoLocal = "PRESENCIAL" | "REMOTO";

export type ParticipacaoBanca = {
  usuario: string;
  usuario_nome: string;
  tipo_usuario: TipoUsuario;
  tipo_membro: "TITULAR" | "SUPLENTE";
  presente: boolean | null;
};

export type Convite = {
  id: string;
  usuario: string;
  usuario_nome: string;
  tipo_usuario: TipoUsuario;
  tipo: "BANCA" | "AUDIENCIA";
  status: "PENDENTE" | "ACEITO" | "RECUSADO";
  enviado_em: string;
  respondido_em: string | null;
};

/** DER v2: a defesa dura 2 h (D5); presencial em bloco e sala, remota por link (D17). */
export type Banca = {
  id: string;
  tcc: string;
  tcc_titulo: string;
  data_hora_inicio: string;
  data_hora_fim: string;
  tipo_local: TipoLocal;
  bloco: string | null;
  sala: string | null;
  link_remoto: string | null;
  participacoes: ParticipacaoBanca[];
  convites: Convite[];
};

// ------------------------------------------------------- pessoas e catalogos
export type Docente = {
  id: string;
  nome_completo: string;
  email: string;
  matricula_institucional: string;
  departamento: "SI" | "ECP" | "LIC";
  ativo: boolean;
  professor_tcc: boolean;
  qtd_orientacoes: number;
  qtd_bancas: number;
};

export type Aluno = {
  id: string;
  nome_completo: string;
  matricula: string;
  curso: string;
  curso_nome: string;
  ativo: boolean;
};

export type UsuarioGeral = {
  id: string;
  nome_completo: string;
  email: string;
  tipo_usuario: TipoUsuario;
  ativo: boolean;
  instituicao_origem: string | null;
};

export type Curso = { id: string; nome: string; rotulo: string };
export type Area = { id: string; nome: string };

/* C3a (7.2): orientacao academica */
export type Orientador = {
  id: string;
  nome_completo: string;
  email: string;
  departamento: "SI" | "ECP" | "LIC";
  aceita_orientacoes: boolean;
  areas_interesse: Area[];
  qtd_orientacoes: number;
};

export type StatusSolicitacao = "PENDENTE" | "ACEITA" | "RECUSADA";

export type SolicitacaoOrientacao = {
  id: string;
  aluno: string;
  aluno_nome: string;
  aluno_email: string;
  aluno_curso: string;
  docente: string;
  docente_nome: string;
  mensagem: string | null;
  status: StatusSolicitacao;
  motivo_recusa: string | null;
  enviada_em: string;
  respondida_em: string | null;
  /** C3b: reunião de alinhamento agendada depois do aceite. */
  reuniao: ResumoReuniao | null;
};

/* C3b (7.3): reuniao de alinhamento */
export type ResumoReuniao = { id: string; data_hora: string; tipo_local: TipoLocal; local: string };

export type Reuniao = ResumoReuniao & {
  solicitacao: string;
  aluno_nome: string;
  docente_nome: string;
};

export type RespostaReuniao = { reuniao: Reuniao; alertas: string[] };

/* C6 (6.3): convites de banca e audiencia */
export type BancaResumo = {
  id: string;
  data_hora_inicio: string;
  data_hora_fim: string;
  tipo_local: TipoLocal;
  bloco: string | null;
  sala: string | null;
  link_remoto: string | null;
};

export type ConviteRecebido = {
  id: string;
  tipo: "BANCA" | "AUDIENCIA";
  status: "PENDENTE" | "ACEITO" | "RECUSADO";
  enviado_em: string;
  respondido_em: string | null;
  convidado_nome: string;
  /** C16: o externo recebe o link de acesso ao TCC depois de aceitar. */
  convidado_externo: boolean;
  papel: "TITULAR" | "SUPLENTE" | null;
  tcc: string;
  tcc_titulo: string;
  autor_nome: string;
  orientador_nome: string;
  banca: BancaResumo;
};

/* C16 (4.6): leitura do TCC pelo membro externo, via token */
export type AcessoExterno = {
  membro_nome: string;
  expira_em: string;
  tcc: {
    titulo: string;
    subtitulo: string | null;
    autor_nome: string;
    orientador_nome: string;
    coorientador_nome: string | null;
    curso_nome: string;
    area_nome: string;
    modalidade: Modalidade;
    link_externo: string | null;
    arquivo_tcc_path: string | null;
  };
  banca: BancaResumo & {
    membros: { nome: string; tipo_membro: "TITULAR" | "SUPLENTE"; membro_externo: boolean }[];
  };
};

/* C7 (8.3): consulta dos logs, so administrador */
export type Pagina<T> = { count: number; next: string | null; previous: string | null; results: T[] };

export type LogAuditoria = {
  id: string;
  data_hora: string;
  responsavel: string;
  responsavel_nome: string;
  entidade: string;
  registro_id: string;
  campo: string;
  valor_anterior: string | null;
  valor_novo: string | null;
};

export type LogAcesso = {
  id: string;
  data_hora: string;
  usuario: string;
  usuario_nome: string;
  ip: string;
};
