import { describe, expect, it } from "vitest";

import { nomeDoCurso, opcoesDeSituacao } from "./rotulos";

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

  it("publicação permite Aprovado por publicação e Não apresentado", () => {
    const permitidos = opcoesDeSituacao("EM_DESENVOLVIMENTO", "PUBLICACAO_APROVADA")
      .filter((o) => o.permitido)
      .map((o) => o.valor);
    expect(permitidos).toEqual(["NAO_APRESENTADO", "APROVADO_POR_PUBLICACAO"]);
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
