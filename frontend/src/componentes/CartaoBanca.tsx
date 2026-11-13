import { useState, type ChangeEvent } from "react";
import { Link } from "react-router-dom";

import { ErroApi, api } from "../api/cliente";
import type { Aluno, Banca, Convite, Docente, TccDetalhe } from "../api/tipos";
import { useCarregar } from "../hooks/useCarregar";
import { STATUS_CONVITE, descreverLocal, formatarDataHora } from "../util/rotulos";
import { Alerta } from "./Alerta";

type Pessoa = { id: string; nome: string };

/** B9c: banca no detalhe do TCC (ou o caminho para cadastrar uma). C6: convites. */
export function CartaoBanca({ tcc, podeEditar }: { tcc: TccDetalhe; podeEditar: boolean }) {
  const [banca, setBanca] = useState<Banca | null>(tcc.banca);
  const porPublicacao = tcc.modalidade === "PUBLICACAO_APROVADA";
  const podeCadastrar =
    podeEditar && !banca && !porPublicacao && tcc.ativo && tcc.status === "EM_DESENVOLVIMENTO";
  const defesaFutura = banca ? new Date(banca.data_hora_inicio) > new Date() : false;
  const gerenciaConvites = podeEditar && defesaFutura;

  const [aviso, setAviso] = useState<{ tom: "sucesso" | "erro"; texto: string } | null>(null);
  const [ocupado, setOcupado] = useState<string | null>(null);
  const [convidado, setConvidado] = useState("");

  // C6 (PF34): docentes e alunos que podem assistir (so para quem gerencia)
  const { dados: pessoas } = useCarregar<Pessoa[]>(async () => {
    if (!gerenciaConvites) return [];
    const [docentes, alunos] = await Promise.all([
      api<Docente[]>("/docentes/", { params: { ativo: "true" } }),
      api<Aluno[]>("/alunos/", { params: { ativo: "true" } }),
    ]);
    return [
      ...docentes.map((d) => ({ id: d.id, nome: `${d.nome_completo} (docente)` })),
      ...alunos.map((a) => ({ id: a.id, nome: `${a.nome_completo} (aluno)` })),
    ];
  }, [gerenciaConvites]);

  async function reenviar(convite: Convite) {
    setOcupado(convite.id);
    setAviso(null);
    try {
      const atualizado = await api<Convite>(`/convites/${convite.id}/reenviar/`, { metodo: "POST" });
      setBanca((b) => (b ? { ...b, convites: b.convites.map((c) => (c.id === convite.id ? atualizado : c)) } : b));
      setAviso({ tom: "sucesso", texto: `Convite reenviado para ${convite.usuario_nome}.` });
    } catch (falha) {
      setAviso({ tom: "erro", texto: falha instanceof ErroApi ? falha.message : "Não foi possível reenviar." });
    } finally {
      setOcupado(null);
    }
  }

  async function convidarAudiencia() {
    if (!banca || !convidado) return;
    setOcupado("audiencia");
    setAviso(null);
    try {
      const atualizada = await api<Banca>(`/bancas/${banca.id}/audiencia/`, {
        metodo: "POST",
        corpo: { usuarios: [convidado] },
      });
      setBanca(atualizada);
      setConvidado("");
      setAviso({ tom: "sucesso", texto: "Convite para a audiência enviado." });
    } catch (falha) {
      setAviso({ tom: "erro", texto: falha instanceof ErroApi ? falha.message : "Não foi possível convidar." });
    } finally {
      setOcupado(null);
    }
  }

  const audiencia = banca?.convites.filter((c) => c.tipo === "AUDIENCIA") ?? [];
  const jaNaDefesa = new Set([
    tcc.autor,
    ...(banca?.participacoes.map((p) => p.usuario) ?? []),
    ...(banca?.convites.map((c) => c.usuario) ?? []),
  ]);
  const disponiveis = (pessoas ?? []).filter((p) => !jaNaDefesa.has(p.id));

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
          Nenhuma banca cadastrada. A banca precisa de 3 titulares, com o orientador entre eles, data futura e bloco e
          sala ou link.
        </div>
      )}

      {banca && (
        <>
          <dl className="lista-dados">
            <div>
              <dt>Início</dt>
              <dd>{formatarDataHora(banca.data_hora_inicio)}</dd>
            </div>
            <div>
              <dt>Término (2 h de defesa)</dt>
              <dd>{formatarDataHora(banca.data_hora_fim)}</dd>
            </div>
            <div>
              <dt>{banca.tipo_local === "REMOTO" ? "Link (remota)" : "Local (presencial)"}</dt>
              <dd>
                {banca.tipo_local === "REMOTO" && banca.link_remoto ? (
                  <a href={banca.link_remoto} target="_blank" rel="noreferrer">
                    {banca.link_remoto}
                  </a>
                ) : (
                  descreverLocal(banca)
                )}
              </dd>
            </div>
          </dl>

          {aviso && <Alerta tom={aviso.tom}>{aviso.texto}</Alerta>}

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
                      {convite ? ` · convite enviado em ${formatarDataHora(convite.enviado_em)}` : ""}
                    </span>
                  </div>
                  <div className="acoes">
                    {convite && (
                      <span className={`selo selo-convite-${convite.status.toLowerCase()}`}>
                        {STATUS_CONVITE[convite.status]}
                      </span>
                    )}
                    {convite && gerenciaConvites && convite.status === "PENDENTE" && (
                      <button
                        type="button"
                        className="link-botao"
                        disabled={ocupado === convite.id}
                        onClick={() => reenviar(convite)}
                      >
                        Reenviar
                      </button>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>

          <h3>Audiência da defesa</h3>
          {audiencia.length === 0 && <p className="texto-suave">Ninguém foi convidado para assistir.</p>}
          {audiencia.length > 0 && (
            <ul className="membros">
              {audiencia.map((c) => (
                <li key={c.id}>
                  <div className="pilha-pequena">
                    <strong>{c.usuario_nome}</strong>
                    <span className="campo-ajuda">Enviado em {formatarDataHora(c.enviado_em)}</span>
                  </div>
                  <div className="acoes">
                    <span className={`selo selo-convite-${c.status.toLowerCase()}`}>{STATUS_CONVITE[c.status]}</span>
                    {gerenciaConvites && c.status === "PENDENTE" && (
                      <button
                        type="button"
                        className="link-botao"
                        disabled={ocupado === c.id}
                        onClick={() => reenviar(c)}
                      >
                        Reenviar
                      </button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
          {gerenciaConvites && (
            <div className="campo-flex">
              <div className="campo">
                <label htmlFor="convidar-audiencia">Convidar para assistir</label>
                <select
                  id="convidar-audiencia"
                  value={convidado}
                  onChange={(e: ChangeEvent<HTMLSelectElement>) => setConvidado(e.target.value)}
                >
                  <option value="">Escolha um docente ou aluno</option>
                  {disponiveis.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.nome}
                    </option>
                  ))}
                </select>
              </div>
              <button
                type="button"
                className="botao botao-contorno"
                disabled={!convidado || ocupado === "audiencia"}
                onClick={convidarAudiencia}
              >
                Enviar convite
              </button>
            </div>
          )}
        </>
      )}
    </section>
  );
}
