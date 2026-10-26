/** Converte as respostas de erro do Django REST Framework em mensagens para a tela. */

export type ErrosFormulario = {
  /** Mensagens que nao pertencem a um campo especifico. */
  geral: string[];
  /** Primeira mensagem de cada campo, pelo nome do campo na API. */
  campos: Record<string, string>;
};

function comoTexto(valor: unknown): string[] {
  if (valor == null) return [];
  if (typeof valor === "string") return [valor];
  if (Array.isArray(valor)) return valor.flatMap(comoTexto);
  if (typeof valor === "object") return Object.values(valor).flatMap(comoTexto);
  return [String(valor)];
}

/**
 * Formatos que o DRF devolve:
 * - {"detail": "..."} (permissao, 404, login)
 * - ["mensagem"] (ValidationError sem campo)
 * - {"campo": ["mensagem"], "non_field_errors": ["..."]}
 */
export function lerErros(dados: unknown, padrao = "Não foi possível concluir a operação."): ErrosFormulario {
  const resultado: ErrosFormulario = { geral: [], campos: {} };
  if (dados == null || typeof dados !== "object") {
    resultado.geral.push(typeof dados === "string" && dados ? dados : padrao);
    return resultado;
  }
  if (Array.isArray(dados)) {
    resultado.geral.push(...comoTexto(dados));
  } else {
    for (const [chave, valor] of Object.entries(dados as Record<string, unknown>)) {
      const textos = comoTexto(valor);
      if (textos.length === 0 || chave === "code" || chave === "bloqueado_ate") continue;
      if (chave === "detail" || chave === "non_field_errors") {
        resultado.geral.push(...textos);
      } else {
        resultado.campos[chave] = textos[0];
      }
    }
  }
  if (resultado.geral.length === 0 && Object.keys(resultado.campos).length === 0) {
    resultado.geral.push(padrao);
  }
  return resultado;
}
