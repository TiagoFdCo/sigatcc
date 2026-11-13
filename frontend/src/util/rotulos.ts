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

/**
 * Data pura (AAAA-MM-DD), sem fuso. `new Date("2026-10-01")` vale meia-noite em UTC
 * e, em Manaus (UTC-4), apareceria como 30/09; aqui o texto e so reorganizado.
 */
export function formatarDataPura(data: string | null | undefined): string {
  if (!data) return "";
  const [ano, mes, dia] = data.split("-");
  return `${dia}/${mes}/${ano}`;
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
      // C1: a aprovacao por publicacao tem tela propria ("Registrar publicacao"),
      // porque exige periodico, ISSN/DOI, data e comprovante.
      valor: "APROVADO_POR_PUBLICACAO" as const,
      permitido: false,
      dica: defesa
        ? "Só para TCC na modalidade Publicação aprovada."
        : "Use “Registrar publicação”: ela pede periódico, ISSN/DOI, data e comprovante.",
    },
  ];
}

export const STATUS_CONVITE: Record<string, string> = {
  PENDENTE: "Convite pendente",
  ACEITO: "Convite aceito",
  RECUSADO: "Convite recusado",
};

/* C3a: situacao da solicitacao de orientacao */
export const STATUS_SOLICITACAO: Record<string, string> = {
  PENDENTE: "Aguardando resposta",
  ACEITA: "Aceita",
  RECUSADA: "Recusada",
};

export const DEPARTAMENTOS: Record<string, string> = {
  SI: "Sistemas de Informação",
  ECP: "Engenharia de Computação",
  LIC: "Licenciatura em Computação",
};
