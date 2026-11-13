import { useParams } from "react-router-dom";

import { api } from "../api/cliente";
import type { AcessoExterno as Dados } from "../api/tipos";
import { Alerta } from "../componentes/Alerta";
import { Logo } from "../componentes/Logo";
import { useCarregar } from "../hooks/useCarregar";
import { MODALIDADES, descreverLocal, formatarDataHora, nomeDoCurso } from "../util/rotulos";

/**
 * C16 (PF19, RD32): página pública do membro externo. Pelo link do e-mail ele
 * lê o TCC e vê a banca, sem senha, até 48 h depois do início da defesa.
 */
export function AcessoExterno() {
  const { token = "" } = useParams<{ token: string }>();
  const { dados, erro, carregando } = useCarregar(() => api<Dados>(`/acesso-externo/${token}/`), [token]);

  return (
    <main className="conteudo pilha">
      <div className="marca">
        <Logo />
        SIGATCC
      </div>
      {carregando && <p className="carregando">Abrindo o TCC…</p>}
      {erro && <Alerta>{erro.status === 404 ? "Este link de acesso não é válido." : erro.message}</Alerta>}
      {dados && (
        <>
          <Alerta tom="info">
            Olá, {dados.membro_nome}. Este acesso vale até {formatarDataHora(dados.expira_em)} (48 horas depois do
            início da defesa).
          </Alerta>
          <div className="duas-colunas">
            <section className="cartao pilha coluna-principal" aria-labelledby="titulo-tcc">
              <div className="pilha-pequena">
                <span className="texto-rotulo">{MODALIDADES[dados.tcc.modalidade]}</span>
                <h1 id="titulo-tcc">{dados.tcc.titulo}</h1>
                {dados.tcc.subtitulo && <p className="texto-suave subtitulo">{dados.tcc.subtitulo}</p>}
              </div>
              <dl className="lista-dados">
                <div>
                  <dt>Autor</dt>
                  <dd>{dados.tcc.autor_nome}</dd>
                </div>
                <div>
                  <dt>Orientador</dt>
                  <dd>{dados.tcc.orientador_nome}</dd>
                </div>
                {dados.tcc.coorientador_nome && (
                  <div>
                    <dt>Coorientador</dt>
                    <dd>{dados.tcc.coorientador_nome}</dd>
                  </div>
                )}
                <div>
                  <dt>Curso</dt>
                  <dd>{nomeDoCurso(dados.tcc.curso_nome)}</dd>
                </div>
                <div>
                  <dt>Área</dt>
                  <dd>{dados.tcc.area_nome}</dd>
                </div>
              </dl>
              {dados.tcc.arquivo_tcc_path || dados.tcc.link_externo ? (
                <div className="acoes">
                  {dados.tcc.link_externo && (
                    <a href={dados.tcc.link_externo} target="_blank" rel="noreferrer" className="botao botao-contorno">
                      Abrir o trabalho
                    </a>
                  )}
                  {dados.tcc.arquivo_tcc_path && <span className="campo-ajuda">Arquivo: {dados.tcc.arquivo_tcc_path}</span>}
                </div>
              ) : (
                <p className="texto-suave">O orientador ainda não enviou o arquivo do trabalho.</p>
              )}
            </section>
            <aside className="cartao pilha-pequena coluna-lateral" aria-labelledby="titulo-defesa">
              <h2 id="titulo-defesa">Defesa</h2>
              <dl className="lista-dados">
                <div>
                  <dt>Início</dt>
                  <dd>{formatarDataHora(dados.banca.data_hora_inicio)}</dd>
                </div>
                <div>
                  <dt>Término</dt>
                  <dd>{formatarDataHora(dados.banca.data_hora_fim)}</dd>
                </div>
                <div>
                  <dt>{dados.banca.tipo_local === "REMOTO" ? "Link" : "Local"}</dt>
                  <dd>
                    {dados.banca.tipo_local === "REMOTO" && dados.banca.link_remoto ? (
                      <a href={dados.banca.link_remoto} target="_blank" rel="noreferrer">
                        {dados.banca.link_remoto}
                      </a>
                    ) : (
                      descreverLocal(dados.banca)
                    )}
                  </dd>
                </div>
              </dl>
              <h3>Banca</h3>
              <ul className="membros">
                {dados.banca.membros.map((m) => (
                  <li key={m.nome}>
                    <div className="pilha-pequena">
                      <strong>{m.nome}</strong>
                      <span className="campo-ajuda">
                        {m.tipo_membro === "TITULAR" ? "Titular" : "Suplente"}
                        {m.membro_externo ? " · membro externo" : ""}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            </aside>
          </div>
        </>
      )}
    </main>
  );
}
