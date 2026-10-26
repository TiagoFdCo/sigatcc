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
