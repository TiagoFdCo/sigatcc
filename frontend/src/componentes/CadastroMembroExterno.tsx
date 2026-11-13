import { useState, type ChangeEvent, type FormEvent } from "react";

import { ErroApi, api } from "../api/cliente";
import type { UsuarioGeral } from "../api/tipos";
import { Alerta } from "./Alerta";

/**
 * C16 (PF60, RBN58): o Professor de TCC cadastra o membro externo direto na
 * tela de banca. Ele não tem senha: entra só pelo link do convite aceito.
 */
export function CadastroMembroExterno({ aoCadastrar }: { aoCadastrar: (u: UsuarioGeral) => void }) {
  const [aberto, setAberto] = useState(false);
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [instituicao, setInstituicao] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function enviar(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      const novo = await api<UsuarioGeral>("/membros-externos/", {
        metodo: "POST",
        corpo: { nome_completo: nome.trim(), email: email.trim(), instituicao_origem: instituicao.trim() },
      });
      aoCadastrar(novo);
      setNome("");
      setEmail("");
      setInstituicao("");
      setAberto(false);
    } catch (falha) {
      setErro(falha instanceof ErroApi ? falha.message : "Não foi possível cadastrar.");
    } finally {
      setEnviando(false);
    }
  }

  if (!aberto) {
    return (
      <div className="acoes">
        <button type="button" className="botao-secundario" onClick={() => setAberto(true)}>
          Cadastrar membro externo
        </button>
      </div>
    );
  }

  return (
    <form className="cartao pilha-pequena" onSubmit={enviar} aria-labelledby="titulo-externo">
      <h2 id="titulo-externo">Novo membro externo</h2>
      <p className="campo-ajuda">
        Ele recebe o convite por e-mail e, ao aceitar, um link de acesso ao TCC válido até 48 h depois da defesa.
      </p>
      <div className="grade">
        <div className="campo">
          <label htmlFor="externo-nome">
            Nome completo <span className="obrigatorio">*</span>
          </label>
          <input
            id="externo-nome"
            required
            maxLength={200}
            value={nome}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setNome(e.target.value)}
          />
        </div>
        <div className="campo">
          <label htmlFor="externo-email">
            E-mail <span className="obrigatorio">*</span>
          </label>
          <input
            id="externo-email"
            type="email"
            required
            value={email}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
          />
        </div>
        <div className="campo">
          <label htmlFor="externo-instituicao">
            Instituição de origem <span className="obrigatorio">*</span>
          </label>
          <input
            id="externo-instituicao"
            required
            maxLength={200}
            value={instituicao}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setInstituicao(e.target.value)}
          />
        </div>
      </div>
      {erro && <Alerta>{erro}</Alerta>}
      <div className="acoes">
        <button type="button" className="botao-secundario" onClick={() => setAberto(false)}>
          Cancelar
        </button>
        <button type="submit" className="botao" disabled={enviando}>
          {enviando ? "Cadastrando…" : "Cadastrar"}
        </button>
      </div>
    </form>
  );
}
