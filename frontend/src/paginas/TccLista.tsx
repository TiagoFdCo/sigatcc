import { useState, type ChangeEvent, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { api } from "../api/cliente";
import type { Curso, Tcc } from "../api/tipos";
import { useAuth } from "../auth/AuthContext";
import { Alerta } from "../componentes/Alerta";
import { SeloSituacao } from "../componentes/SeloSituacao";
import { useCarregar } from "../hooks/useCarregar";
import { MODALIDADES, STATUS, nomeDoCurso } from "../util/rotulos";

const FILTROS = ["busca", "curso", "status", "modalidade"] as const;
type Filtro = (typeof FILTROS)[number];

/** B9b: listagem de TCCs ativos com busca e filtros (filtros ficam na URL). */
export function TccLista() {
  const { podeEditar } = useAuth();
  const [params, setParams] = useSearchParams();
  const [busca, setBusca] = useState(params.get("busca") ?? "");

  const filtros = Object.fromEntries(FILTROS.map((f) => [f, params.get(f) ?? ""])) as Record<Filtro, string>;
  const chave = params.toString();

  const { dados: tccs, erro, carregando } = useCarregar(
    () => api<Tcc[]>("/tccs/", { params: { ...filtros, ativo: "true" } }),
    [chave],
  );
  const { dados: cursos } = useCarregar(() => api<Curso[]>("/cursos/"), []);

  function mudarFiltro(nome: Filtro, valor: string) {
    const novos = new URLSearchParams(params);
    if (valor) novos.set(nome, valor);
    else novos.delete(nome);
    setParams(novos, { replace: true });
  }

  return (
    <div className="pilha">
      <div className="cabecalho-pagina">
        <div className="pilha-pequena">
          <h1>TCCs</h1>
          <p className="texto-suave">Trabalhos ativos do NUCOMP nos três cursos.</p>
        </div>
        {podeEditar && (
          <Link to="/tccs/novo" className="botao">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" />
            </svg>
            Novo TCC
          </Link>
        )}
      </div>

      <form
        role="search"
        className="cartao filtros"
        onSubmit={(e: FormEvent<HTMLFormElement>) => {
          e.preventDefault();
          mudarFiltro("busca", busca.trim());
        }}
      >
        <div className="campo filtro-busca">
          <label htmlFor="busca">Buscar</label>
          <input
            id="busca"
            type="search"
            placeholder="Título, autor ou orientador"
            value={busca}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setBusca(e.target.value)}
            onBlur={() => mudarFiltro("busca", busca.trim())}
          />
        </div>
        <div className="campo">
          <label htmlFor="curso">Curso</label>
          <select
            id="curso"
            value={filtros.curso}
            onChange={(e: ChangeEvent<HTMLSelectElement>) => mudarFiltro("curso", e.target.value)}
          >
            <option value="">Todos</option>
            {(cursos ?? []).map((c) => (
              <option key={c.id} value={c.id}>
                {nomeDoCurso(c.nome)}
              </option>
            ))}
          </select>
        </div>
        <div className="campo">
          <label htmlFor="status">Situação</label>
          <select
            id="status"
            value={filtros.status}
            onChange={(e: ChangeEvent<HTMLSelectElement>) => mudarFiltro("status", e.target.value)}
          >
            <option value="">Todas</option>
            {Object.entries(STATUS).map(([valor, rotulo]) => (
              <option key={valor} value={valor}>
                {rotulo}
              </option>
            ))}
          </select>
        </div>
        <div className="campo">
          <label htmlFor="modalidade">Modalidade</label>
          <select
            id="modalidade"
            value={filtros.modalidade}
            onChange={(e: ChangeEvent<HTMLSelectElement>) => mudarFiltro("modalidade", e.target.value)}
          >
            <option value="">Todas</option>
            {Object.entries(MODALIDADES).map(([valor, rotulo]) => (
              <option key={valor} value={valor}>
                {rotulo}
              </option>
            ))}
          </select>
        </div>
      </form>

      {erro && <Alerta>{erro.message}</Alerta>}

      <div className="tabela-caixa">
        <table className="tabela">
          <thead>
            <tr>
              <th scope="col">Título</th>
              <th scope="col">Autor</th>
              <th scope="col">Curso</th>
              <th scope="col">Orientador</th>
              <th scope="col">Modalidade</th>
              <th scope="col">Situação</th>
            </tr>
          </thead>
          <tbody>
            {carregando && (
              <tr>
                <td colSpan={6} className="tabela-vazia">
                  Carregando…
                </td>
              </tr>
            )}
            {!carregando && tccs?.length === 0 && (
              <tr>
                <td colSpan={6} className="tabela-vazia">
                  Nenhum TCC encontrado com esses filtros.
                </td>
              </tr>
            )}
            {!carregando &&
              tccs?.map((t) => (
                <tr key={t.id}>
                  <td className="tabela-titulo">
                    <Link to={`/tccs/${t.id}`}>{t.titulo}</Link>
                  </td>
                  <td>{t.autor_nome}</td>
                  <td className="texto-suave">{nomeDoCurso(t.curso_nome)}</td>
                  <td>{t.orientador_nome}</td>
                  <td className="texto-suave">{MODALIDADES[t.modalidade]}</td>
                  <td>
                    <SeloSituacao status={t.status} />
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
      {!carregando && tccs && tccs.length > 0 && (
        <p className="texto-suave">
          {tccs.length} {tccs.length === 1 ? "TCC" : "TCCs"}
        </p>
      )}
    </div>
  );
}
