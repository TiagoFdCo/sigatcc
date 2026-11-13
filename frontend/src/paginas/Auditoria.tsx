import { useState, type ChangeEvent } from "react";

import { api } from "../api/cliente";
import type { LogAcesso, LogAuditoria, Pagina } from "../api/tipos";
import { Alerta } from "../componentes/Alerta";
import { useCarregar } from "../hooks/useCarregar";
import { formatarDataHora } from "../util/rotulos";

const POR_PAGINA = 50;
const ENTIDADES = ["TCC", "BANCA", "PUBLICACAO", "DOCENTE", "ALUNO", "USUARIO", "AREA_CONHECIMENTO", "SOLICITACAO_ORIENTACAO"];

type Aba = "alteracoes" | "acessos";

/** C7 (8.3, RNF08): o administrador consulta quem mudou o quê e quem entrou no sistema. */
export function Auditoria() {
  const [aba, setAba] = useState<Aba>("alteracoes");
  const [entidade, setEntidade] = useState("");
  const [de, setDe] = useState("");
  const [ate, setAte] = useState("");
  const [offset, setOffset] = useState(0);

  const filtros = { de, ate, limit: String(POR_PAGINA), offset: String(offset) };
  const { dados: alteracoes, erro: erroAlt, carregando: carregandoAlt } = useCarregar<Pagina<LogAuditoria> | null>(
    () => (aba === "alteracoes" ? api<Pagina<LogAuditoria>>("/auditoria/", { params: { ...filtros, entidade } }) : Promise.resolve(null)),
    [aba, entidade, de, ate, offset],
  );
  const { dados: acessos, erro: erroAc, carregando: carregandoAc } = useCarregar<Pagina<LogAcesso> | null>(
    () => (aba === "acessos" ? api<Pagina<LogAcesso>>("/acessos/", { params: filtros }) : Promise.resolve(null)),
    [aba, de, ate, offset],
  );

  const pagina = aba === "alteracoes" ? alteracoes : acessos;
  const erro = aba === "alteracoes" ? erroAlt : erroAc;
  const carregando = aba === "alteracoes" ? carregandoAlt : carregandoAc;

  function mudar(setter: (v: string) => void) {
    return (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      setter(e.target.value);
      setOffset(0);
    };
  }

  const total = pagina?.count ?? 0;
  const primeiro = total === 0 ? 0 : offset + 1;
  const ultimo = Math.min(offset + POR_PAGINA, total);

  return (
    <div className="pilha">
      <div className="pilha-pequena">
        <h1>Auditoria</h1>
        <p className="texto-suave">
          Registro somente de leitura. Nada aqui pode ser editado ou apagado, nem pelo administrador.
        </p>
      </div>

      <div className="acoes" role="tablist" aria-label="Tipo de registro">
        {(["alteracoes", "acessos"] as const).map((valor) => (
          <button
            key={valor}
            type="button"
            role="tab"
            aria-selected={aba === valor}
            className={aba === valor ? "botao" : "botao-secundario"}
            onClick={() => {
              setAba(valor);
              setOffset(0);
            }}
          >
            {valor === "alteracoes" ? "Alterações" : "Acessos"}
          </button>
        ))}
      </div>

      <form className="cartao filtros" onSubmit={(e) => e.preventDefault()} aria-label="Filtros">
        {aba === "alteracoes" && (
          <div className="campo">
            <label htmlFor="entidade">Tipo de registro</label>
            <select id="entidade" value={entidade} onChange={mudar(setEntidade)}>
              <option value="">Todos</option>
              {ENTIDADES.map((e) => (
                <option key={e} value={e}>
                  {e}
                </option>
              ))}
            </select>
          </div>
        )}
        <div className="campo">
          <label htmlFor="de">De</label>
          <input id="de" type="date" value={de} onChange={mudar(setDe)} />
        </div>
        <div className="campo">
          <label htmlFor="ate">Até</label>
          <input id="ate" type="date" value={ate} onChange={mudar(setAte)} />
        </div>
      </form>

      {erro && <Alerta>{erro.status === 403 ? "Só o administrador consulta a auditoria." : erro.message}</Alerta>}
      {carregando && <p className="carregando">Carregando…</p>}
      {!carregando && !erro && total === 0 && <div className="vazio">Nenhum registro para esses filtros.</div>}

      {!erro && total > 0 && (
        <div className="tabela-caixa">
          {aba === "alteracoes" ? (
            <table className="tabela">
              <thead>
                <tr>
                  <th>Quando</th>
                  <th>Quem</th>
                  <th>Registro</th>
                  <th>Campo</th>
                  <th>Antes</th>
                  <th>Depois</th>
                </tr>
              </thead>
              <tbody>
                {(alteracoes?.results ?? []).map((l) => (
                  <tr key={l.id}>
                    <td>{formatarDataHora(l.data_hora)}</td>
                    <td>{l.responsavel_nome}</td>
                    <td>
                      {l.entidade}
                      <br />
                      <span className="campo-ajuda">{l.registro_id.slice(0, 8)}</span>
                    </td>
                    <td>{l.campo}</td>
                    <td>{l.valor_anterior ?? "—"}</td>
                    <td>{l.valor_novo ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <table className="tabela">
              <thead>
                <tr>
                  <th>Quando</th>
                  <th>Quem</th>
                  <th>IP</th>
                </tr>
              </thead>
              <tbody>
                {(acessos?.results ?? []).map((l) => (
                  <tr key={l.id}>
                    <td>{formatarDataHora(l.data_hora)}</td>
                    <td>{l.usuario_nome}</td>
                    <td>{l.ip}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {total > 0 && (
        <div className="acoes">
          <span className="texto-suave">
            {primeiro}–{ultimo} de {total}
          </span>
          <button type="button" className="botao-secundario" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - POR_PAGINA))}>
            Anterior
          </button>
          <button type="button" className="botao-secundario" disabled={!pagina?.next} onClick={() => setOffset(offset + POR_PAGINA)}>
            Próxima
          </button>
        </div>
      )}
    </div>
  );
}
