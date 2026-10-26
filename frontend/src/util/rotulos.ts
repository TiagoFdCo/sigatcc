import type { Modalidade, MotivoNaoApresentacao, StatusTcc, Visibilidade } from "../api/tipos";

export const STATUS: Record<StatusTcc, string> = {
  EM_DESENVOLVIMENTO: "Em desenvolvimento",
  APRESENTADO: "Apresentado",
  NAO_APRESENTADO: "Não apresentado",
  APROVADO_POR_PUBLICACAO: "Aprovado por publicação",
};

export const MODALIDADES: Record<Modalidade, string> = {
  DEFESA_EM_BANCA: "Defesa em banca",
  PUBLICACAO_APROVADA: "Publicação aprovada",
};

export const VISIBILIDADES: Record<Visibilidade, string> = {
  PUBLICO_TEXTO_COMPLETO: "Público, com texto completo",
  PUBLICO_METADADOS: "Só metadados (título, autor, orientador)",
  RESTRITO: "Restrito",
};

export const MOTIVOS: Record<MotivoNaoApresentacao, string> = {
  DESISTENCIA: "Desistência",
  TRANCAMENTO: "Trancamento de matrícula",
  TRANSFERENCIA: "Transferência",
  OUTRO: "Outro",
};

const CURSOS: Record<string, string> = {
  ENG_COMPUTACAO: "Engenharia de Computação",
  SISTEMAS_INFORMACAO: "Sistemas de Informação",
  LICENCIATURA_COMPUTACAO: "Licenciatura em Computação",
};

export function nomeDoCurso(codigo: string | null | undefined): string {
  if (!codigo) return "";
  return CURSOS[codigo] ?? codigo;
}

export function formatarData(iso: string | null | undefined): string {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("pt-BR");
}

export function formatarDataHora(iso: string | null | undefined): string {
  if (!iso) return "";
  return new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

/**
 * Espelho das regras de mudanca de situacao do backend (core/services/tcc.py),
 * usado so para mostrar as opcoes; quem decide e a API.
 */
export function opcoesDeSituacao(status: StatusTcc, modalidade: Modalidade) {
  if (status !== "EM_DESENVOLVIMENTO") return [];
  const defesa = modalidade === "DEFESA_EM_BANCA";
  return [
    {
      valor: "APRESENTADO" as const,
      permitido: defesa,
      dica: defesa ? "A defesa em banca aconteceu." : "Só para TCC na modalidade Defesa em banca.",
    },
    {
      valor: "NAO_APRESENTADO" as const,
      permitido: true,
      dica: "Exige o motivo: desistência, trancamento, transferência ou outro.",
    },
    {
      valor: "APROVADO_POR_PUBLICACAO" as const,
      permitido: !defesa,
      dica: defesa ? "Só para TCC na modalidade Publicação aprovada." : "Conclusão por artigo publicado, sem banca.",
    },
  ];
}
