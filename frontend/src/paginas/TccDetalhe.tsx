import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../api/cliente";
import type { TccDetalhe as Detalhe } from "../api/tipos";
import { useAuth } from "../auth/AuthContext";
import { Alerta } from "../componentes/Alerta";
import { CartaoBanca } from "../componentes/CartaoBanca";
import { FormularioPublicacao } from "../componentes/FormularioPublicacao";
import { PainelSituacao } from "../componentes/PainelSituacao";
import { SeloSituacao } from "../componentes/SeloSituacao";
import { useCarregar } from "../hooks/useCarregar";
import {
  MODALIDADES,
  MOTIVOS,
  STATUS,
  VISIBILIDADES,
  formatarData,
  formatarDataHora,
  formatarDataPura,
  nomeDoCurso,
} from "../util/rotulos";

/** B9b: detalhe do TCC, historico e mudanca de situacao (B7b); B9c: banca; C1: publicacao. */
export function TccDetalhe() {
  const { id = "" } = useParams<{ id: string }>();
  const { podeEditar } = useAuth();
  const { dados: tcc, setDados, erro, carregando } = useCarregar(() => api<Detalhe>(`/tccs/${id}/`), [id]);
  const [mudando, setMudando] = useState(false);
  const [registrando, setRegistrando] = useState(false);
  const [aviso, setAviso] = useState<string | null>(null);

  if (carregando) return <p className="carregando">Carregando…</p>;
  if (erro || !tcc) {
    return (
      <div className="pilha">
        <Alerta>{erro?.status === 404 ? "TCC não encontrado." : (erro?.message ?? "Erro ao carregar.")}</Alerta>
        <div>
          <Link to="/tccs" className="botao-secundario">
            Voltar para a lista
          </Link>
        </div>
      </div>
    );
  }

  // C17: o perfil precisa poder editar e o TCC precisa estar no escopo dele
  const podeEditarEste = podeEditar && tcc.pode_editar;
  const podeMudar = podeEditarEste && tcc.ativo && tcc.status === "EM_DESENVOLVIMENTO";
  const podeRegistrarPublicacao = podeMudar && tcc.modalidade === "PUBLICACAO_APROVADA";
  const publicacao = tcc.publicacao;

  const dadosTrabalho: [string, string][] = [
    ["Autor", `${tcc.autor_nome} · ${tcc.autor_matricula}`],
    ["Curso", nomeDoCurso(tcc.curso_nome)],
    ["Área de conhecimento", tcc.area_nome],
    ["Orientador", tcc.orientador_nome],
    ["Coorientador", tcc.coorientador_nome ?? "—"],
    ["Modalidade de conclusão", MODALIDADES[tcc.modalidade]],
    ["Visibilidade", VISIBILIDADES[tcc.visibilidade]],
    ["Cadastrado em", formatarData(tcc.data_cadastro)],
  ];
  if (tcc.motivo_nao_apresentacao) {
    const motivo = MOTIVOS[tcc.motivo_nao_apresentacao];
    dadosTrabalho.push(["Motivo da não apresentação", tcc.motivo_outro ? `${motivo}: ${tcc.motivo_outro}` : motivo]);
  }

  return (
    <div className="pilha">
      <nav aria-label="Trilha" className="trilha">
        <Link to="/tccs">TCCs</Link> <span aria-hidden="true">/</span> Detalhe
      </nav>

      {aviso && <Alerta tom="sucesso">{aviso}</Alerta>}

      <div className="cabecalho-pagina">
        <div className="pilha-pequena detalhe-titulo">
          <div>
            <SeloSituacao status={tcc.status} />
          </div>
          <h1>{tcc.titulo}</h1>
          {tcc.subtitulo && <p className="texto-suave subtitulo">{tcc.subtitulo}</p>}
        </div>
        {podeEditarEste && (
          <div className="acoes">
            <Link to={`/tccs/${tcc.id}/editar`} className="botao-secundario">
              Editar
            </Link>
            {podeRegistrarPublicacao && !registrando && (
              <button
                type="button"
                className="botao"
                onClick={() => {
                  setMudando(false);
                  setRegistrando(true);
                }}
              >
                Registrar publicação
              </button>
            )}
            {podeMudar && !mudando && (
              <button
                type="button"
                className={podeRegistrarPublicacao ? "botao-secundario" : "botao"}
                onClick={() => {
                  setRegistrando(false);
                  setMudando(true);
                }}
              >
                Mudar situação
              </button>
            )}
          </div>
        )}
      </div>

      {registrando && (
        <FormularioPublicacao
          tcc={tcc}
          aoCancelar={() => setRegistrando(false)}
          aoConcluir={(atualizado) => {
            setDados(atualizado);
            setRegistrando(false);
            setAviso("Publicação registrada. O TCC foi aprovado por publicação.");
          }}
        />
      )}

      {mudando && (
        <PainelSituacao
          tcc={tcc}
          aoCancelar={() => setMudando(false)}
          aoConcluir={(atualizado) => {
            setDados(atualizado);
            setMudando(false);
            setAviso(`Situação alterada para ${STATUS[atualizado.status]}.`);
          }}
        />
      )}

      <div className="duas-colunas">
        <div className="coluna-principal">
          <section className="cartao">
            <h2>Dados do trabalho</h2>
            <dl className="lista-dados">
              {dadosTrabalho.map(([rotulo, valor]) => (
                <div key={rotulo}>
                  <dt>{rotulo}</dt>
                  <dd>{valor}</dd>
                </div>
              ))}
            </dl>
          </section>
          {publicacao && (
            <section className="cartao" aria-labelledby="titulo-publicacao">
              <h2 id="titulo-publicacao">Publicação</h2>
              <dl className="lista-dados">
                <div>
                  <dt>Periódico ou evento</dt>
                  <dd>{publicacao.periodico}</dd>
                </div>
                <div>
                  <dt>ISSN ou DOI</dt>
                  <dd>{publicacao.issn_doi}</dd>
                </div>
                <div>
                  <dt>Data de publicação</dt>
                  <dd>{formatarDataPura(publicacao.data_publicacao)}</dd>
                </div>
                {publicacao.comprovante_arquivo_path && (
                  <div>
                    <dt>Comprovante</dt>
                    <dd>{publicacao.comprovante_arquivo_path}</dd>
                  </div>
                )}
                {publicacao.link_artigo && (
                  <div>
                    <dt>Link do artigo</dt>
                    <dd>
                      <a href={publicacao.link_artigo} target="_blank" rel="noreferrer">
                        {publicacao.link_artigo}
                      </a>
                    </dd>
                  </div>
                )}
              </dl>
            </section>
          )}
          <CartaoBanca tcc={tcc} podeEditar={podeEditarEste} />
        </div>

        <aside className="cartao coluna-lateral">
          <h2>Histórico de situação</h2>
          <ol className="linha-do-tempo">
            {tcc.historico.map((h) => (
              <li key={`${h.status}-${h.data_alteracao}`}>
                <span className="ponto" aria-hidden="true" />
                <div className="pilha-pequena">
                  <strong>{STATUS[h.status]}</strong>
                  <span className="campo-ajuda">
                    {formatarDataHora(h.data_alteracao)} · {h.alterado_por_nome}
                  </span>
                  {h.justificativa && <span>{MOTIVOS[h.justificativa as keyof typeof MOTIVOS] ?? h.justificativa}</span>}
                </div>
              </li>
            ))}
          </ol>
        </aside>
      </div>
    </div>
  );
}
