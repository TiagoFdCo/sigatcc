import { Link } from "react-router-dom";

import type { TccDetalhe } from "../api/tipos";
import { STATUS_CONVITE, formatarDataHora } from "../util/rotulos";

/** B9c: banca no detalhe do TCC (ou o caminho para cadastrar uma). */
export function CartaoBanca({ tcc, podeEditar }: { tcc: TccDetalhe; podeEditar: boolean }) {
  const banca = tcc.banca;
  const porPublicacao = tcc.modalidade === "PUBLICACAO_APROVADA";
  const podeCadastrar =
    podeEditar && !banca && !porPublicacao && tcc.ativo && tcc.status === "EM_DESENVOLVIMENTO";

  return (
    <section className="cartao" aria-labelledby="titulo-banca">
      <div className="cabecalho-pagina">
        <h2 id="titulo-banca">Banca</h2>
        {podeCadastrar && (
          <Link to={`/tccs/${tcc.id}/banca/nova`} className="botao botao-contorno">
            Cadastrar banca
          </Link>
        )}
      </div>

      {!banca && porPublicacao && (
        <p className="texto-suave">TCC na modalidade Publicação aprovada: conclui sem banca.</p>
      )}
      {!banca && !porPublicacao && (
        <div className="vazio">
          Nenhuma banca cadastrada. A banca precisa de 3 titulares, com o orientador entre eles, data futura e sala ou
          link.
        </div>
      )}

      {banca && (
        <>
          <dl className="lista-dados">
            <div>
              <dt>Data e horário</dt>
              <dd>{formatarDataHora(banca.data_hora)}</dd>
            </div>
            <div>
              <dt>{banca.tipo_local === "REMOTO" ? "Link (remota)" : "Sala (presencial)"}</dt>
              <dd>
                {banca.tipo_local === "REMOTO" ? (
                  <a href={banca.local} target="_blank" rel="noreferrer">
                    {banca.local}
                  </a>
                ) : (
                  banca.local
                )}
              </dd>
            </div>
          </dl>
          <ul className="membros">
            {banca.participacoes.map((p) => {
              const convite = banca.convites.find((c) => c.usuario === p.usuario && c.tipo === "BANCA");
              const orientador = p.usuario === tcc.orientador;
              return (
                <li key={p.usuario}>
                  <div className="pilha-pequena">
                    <strong>{p.usuario_nome}</strong>
                    <span className="campo-ajuda">
                      {p.tipo_membro === "TITULAR" ? "Titular" : "Suplente"}
                      {orientador ? " · orientador" : ""}
                      {p.tipo_usuario === "MEMBRO_EXTERNO" ? " · membro externo" : ""}
                    </span>
                  </div>
                  {convite && <span className={`selo selo-convite-${convite.status.toLowerCase()}`}>{STATUS_CONVITE[convite.status]}</span>}
                </li>
              );
            })}
          </ul>
        </>
      )}
    </section>
  );
}
