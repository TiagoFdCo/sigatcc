import type { TipoUsuario } from "../api/tipos";

/** Para onde cada perfil vai ao entrar: o aluno abre o proprio perfil (C2a), os demais a lista de TCCs. */
export function rotaInicial(tipo: TipoUsuario | null | undefined): string {
  return tipo === "ALUNO" ? "/meu-perfil" : "/tccs";
}
