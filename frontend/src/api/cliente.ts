/**
 * Cliente da API do SIGATCC: envia o JWT em cada chamada e renova o token
 * quando ele vence (RNF02: sessao de 30 min sem atividade).
 */
import { lerErros, type ErrosFormulario } from "./erros";

const BASE = (import.meta.env.VITE_API_URL ?? "http://localhost:8000/api").replace(/\/$/, "");
const CHAVE_SESSAO = "sigatcc.sessao";

export type Tokens = { access: string; refresh: string };

export class ErroApi extends Error {
  readonly status: number;
  readonly dados: unknown;
  readonly erros: ErrosFormulario;

  constructor(status: number, dados: unknown) {
    const erros = lerErros(
      dados,
      status === 0 ? "Sem conexão com o servidor. Tente de novo." : undefined,
    );
    super(erros.geral[0] ?? Object.values(erros.campos)[0] ?? `Erro ${status}`);
    this.status = status;
    this.dados = dados;
    this.erros = erros;
  }
}

function lerTokens(): Tokens | null {
  try {
    const salvo = sessionStorage.getItem(CHAVE_SESSAO);
    return salvo ? (JSON.parse(salvo) as Tokens) : null;
  } catch {
    return null;
  }
}

let tokens: Tokens | null = lerTokens();
let aoExpirar: (() => void) | null = null;
let renovacao: Promise<boolean> | null = null;

/** Guarda os tokens na aba atual (somem quando a aba fecha). */
export function guardarTokens(novos: Tokens | null) {
  tokens = novos;
  try {
    if (novos) sessionStorage.setItem(CHAVE_SESSAO, JSON.stringify(novos));
    else sessionStorage.removeItem(CHAVE_SESSAO);
  } catch {
    // navegador sem sessionStorage: a sessao fica so na memoria
  }
}

export function tokensAtuais(): Tokens | null {
  return tokens;
}

/** Chamado quando a sessao acaba (refresh vencido ou invalidado). */
export function aoExpirarSessao(funcao: (() => void) | null) {
  aoExpirar = funcao;
}

async function renovarSessao(): Promise<boolean> {
  const atuais = tokens;
  if (!atuais) return false;
  renovacao ??= (async () => {
    try {
      const resposta = await fetch(`${BASE}/auth/refresh/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh: atuais.refresh }),
      });
      if (!resposta.ok) return false;
      const dados = (await resposta.json()) as Partial<Tokens>;
      guardarTokens({ access: dados.access ?? "", refresh: dados.refresh ?? atuais.refresh });
      return Boolean(dados.access);
    } catch {
      return false;
    }
  })().finally(() => {
    renovacao = null;
  });
  return renovacao;
}

type Parametros = Record<string, string | number | boolean | undefined | null>;

export type OpcoesRequisicao = {
  metodo?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  corpo?: unknown;
  params?: Parametros;
};

function montarUrl(caminho: string, params?: Parametros) {
  const busca = new URLSearchParams();
  for (const [chave, valor] of Object.entries(params ?? {})) {
    if (valor !== undefined && valor !== null && valor !== "") busca.set(chave, String(valor));
  }
  const consulta = busca.toString();
  return `${BASE}${caminho}${consulta ? `?${consulta}` : ""}`;
}

export async function api<T>(caminho: string, opcoes: OpcoesRequisicao = {}): Promise<T> {
  const { metodo = "GET", corpo, params } = opcoes;
  const rotaDeAutenticacao = caminho.startsWith("/auth/login") || caminho.startsWith("/auth/refresh");

  const enviar = () => {
    const cabecalhos: Record<string, string> = { Accept: "application/json" };
    if (corpo !== undefined) cabecalhos["Content-Type"] = "application/json";
    if (tokens && !rotaDeAutenticacao) cabecalhos.Authorization = `Bearer ${tokens.access}`;
    return fetch(montarUrl(caminho, params), {
      method: metodo,
      headers: cabecalhos,
      body: corpo === undefined ? undefined : JSON.stringify(corpo),
    });
  };

  let resposta: Response;
  try {
    resposta = await enviar();
    if (resposta.status === 401 && !rotaDeAutenticacao && (await renovarSessao())) {
      resposta = await enviar();
    }
  } catch {
    throw new ErroApi(0, null);
  }

  if (resposta.status === 401 && !rotaDeAutenticacao) {
    guardarTokens(null);
    aoExpirar?.();
  }

  const dados: unknown = resposta.status === 204 ? null : await resposta.json().catch(() => null);
  if (!resposta.ok) throw new ErroApi(resposta.status, dados);
  return dados as T;
}
