import { describe, expect, it } from "vitest";

import { lerErros } from "./erros";

describe("lerErros", () => {
  it("lê o detail das respostas de permissão e login", () => {
    expect(lerErros({ detail: "E-mail, matrícula ou senha incorretos.", code: "credenciais_invalidas" })).toEqual({
      geral: ["E-mail, matrícula ou senha incorretos."],
      campos: {},
    });
  });

  it("separa erros por campo e pega a primeira mensagem de cada um", () => {
    const erros = lerErros({
      coorientador: ["O coorientador deve ser diferente do orientador."],
      titulo: ["Este campo é obrigatório.", "outra"],
    });
    expect(erros.campos).toEqual({
      coorientador: "O coorientador deve ser diferente do orientador.",
      titulo: "Este campo é obrigatório.",
    });
    expect(erros.geral).toEqual([]);
  });

  it("trata lista solta como erro geral (ValidationError sem campo)", () => {
    expect(lerErros(["TCC inativo não muda de situação."]).geral).toEqual(["TCC inativo não muda de situação."]);
  });

  it("junta non_field_errors ao geral", () => {
    expect(lerErros({ non_field_errors: ["Combinação inválida."] }).geral).toEqual(["Combinação inválida."]);
  });

  it("usa a mensagem padrão quando não há corpo", () => {
    expect(lerErros(null, "Sem conexão.").geral).toEqual(["Sem conexão."]);
    expect(lerErros({}).geral).toHaveLength(1);
  });

  it("ignora campos auxiliares do login bloqueado", () => {
    const erros = lerErros({
      detail: "Conta bloqueada por 15 minutos após 5 tentativas sem sucesso.",
      code: "conta_bloqueada",
      bloqueado_ate: "2026-10-25T21:15:00-04:00",
    });
    expect(erros.campos).toEqual({});
    expect(erros.geral).toHaveLength(1);
  });
});
