import { describe, expect, it } from "vitest";

import { rotaInicial } from "./rotas";

describe("rotaInicial", () => {
  it("manda o aluno para o próprio perfil", () => {
    expect(rotaInicial("ALUNO")).toBe("/meu-perfil");
  });

  it("manda os demais perfis para a lista de TCCs", () => {
    for (const tipo of ["DOCENTE", "ADMINISTRADOR", "SECRETARIA", "MEMBRO_EXTERNO"] as const) {
      expect(rotaInicial(tipo)).toBe("/tccs");
    }
  });

  it("sem usuário cai na lista de TCCs (a rota protegida cuida do login)", () => {
    expect(rotaInicial(null)).toBe("/tccs");
    expect(rotaInicial(undefined)).toBe("/tccs");
  });
});
