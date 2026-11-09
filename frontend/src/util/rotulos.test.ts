import { describe, expect, it } from "vitest";

import { formatarDataPura, nomeDoCurso, opcoesDeSituacao } from "./rotulos";

describe("opcoesDeSituacao", () => {
  it("só oferece mudança a partir de Em desenvolvimento", () => {
    expect(opcoesDeSituacao("APRESENTADO", "DEFESA_EM_BANCA")).toEqual([]);
    expect(opcoesDeSituacao("NAO_APRESENTADO", "PUBLICACAO_APROVADA")).toEqual([]);
  });

  it("defesa em banca permite Apresentado e Não apresentado", () => {
    const permitidos = opcoesDeSituacao("EM_DESENVOLVIMENTO", "DEFESA_EM_BANCA")
      .filter((o) => o.permitido)
      .map((o) => o.valor);
    expect(permitidos).toEqual(["APRESENTADO", "NAO_APRESENTADO"]);
  });

  it("publicação permite só Não apresentado aqui; a aprovação tem tela própria", () => {
    const opcoes = opcoesDeSituacao("EM_DESENVOLVIMENTO", "PUBLICACAO_APROVADA");
    expect(opcoes.filter((o) => o.permitido).map((o) => o.valor)).toEqual(["NAO_APRESENTADO"]);
    const aprovacao = opcoes.find((o) => o.valor === "APROVADO_POR_PUBLICACAO");
    expect(aprovacao?.permitido).toBe(false);
    expect(aprovacao?.dica).toContain("Registrar publicação");
  });
});

describe("formatarDataPura", () => {
  it("não desloca o dia por causa do fuso", () => {
    expect(formatarDataPura("2026-10-01")).toBe("01/10/2026");
  });

  it("devolve vazio sem valor", () => {
    expect(formatarDataPura(null)).toBe("");
    expect(formatarDataPura(undefined)).toBe("");
  });
});

describe("nomeDoCurso", () => {
  it("traduz o código do curso", () => {
    expect(nomeDoCurso("SISTEMAS_INFORMACAO")).toBe("Sistemas de Informação");
  });

  it("devolve o próprio código quando não conhece e vazio sem valor", () => {
    expect(nomeDoCurso("OUTRO_CURSO")).toBe("OUTRO_CURSO");
    expect(nomeDoCurso(null)).toBe("");
  });
});
