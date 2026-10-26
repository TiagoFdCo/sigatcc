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
};

export type HistoricoStatus = {
  status: StatusTcc;
  data_alteracao: string;
  justificativa: string | null;
};

export type TccDetalhe = Tcc & { historico: HistoricoStatus[] };

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

export type Curso = { id: string; nome: string; rotulo: string };
export type Area = { id: string; nome: string };
