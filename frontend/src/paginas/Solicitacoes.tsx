import { useState, type ChangeEvent } from "react";
import { Link } from "react-router-dom";

import { ErroApi, api } from "../api/cliente";
import type { Reuniao, SolicitacaoOrientacao, StatusSolicitacao } from "../api/tipos";
import { useAuth } from "../auth/AuthContext";
import { Alerta } from "../componentes/Alerta";
import { FormularioReuniao } from "../componentes/FormularioReuniao";
import { useCarregar } from "../hooks/useCarregar";
import { STATUS_SOLICITACAO, formatarDataHora, nomeDoCurso } from "../util/rotulos";

const SELO: Record<StatusSolicitacao, string> = {
  PENDENTE: "selo-convite-pendente",
  ACEITA: "selo-convite-aceito",
  RECUSADA: "selo-convite-recusado",
};

/**
 * C3a (PF42, PF43): o aluno acompanha as solicitações que enviou; o docente
 * responde as que recebeu (uma vez só) e, depois do aceite, cadastra o TCC.
 */
export function Solicitacoes() {
  const { usuario } = useAuth();
  const ehAluno = usuario?.tipo_usuario === "ALUNO";
  const ehDocente = usuario?.tipo_usuario === "DOCENTE";

  const { dados: lista, setDados, erro, carregando } = useCarregar(
    () => api<SolicitacaoOrientacao[]>("/solicitacoes-orientacao/"),
    [],
  );
  const [recusando, setRecusando] = useState<string | null>(null);
  const [motivo, setMotivo] = useState("");
  const [enviando, setEnviando] = useState<string | null>(null);
  const [erroAcao, setErroAcao] = useState<string | null>(null);
  // C3b: reuniao de alinhamento
  const { dados: proximas, recarregar: recarregarReunioes } = useCarregar(
    () => api<Reuniao[]>("/reunioes/", { params: { futuras: "true" } }),
    [],
  );
  const [agendando, setAgendando] = useState<string | null>(null);
  const [alertas, setAlertas] = useState<{ id: string; textos: string[] } | null>(null);

  async function responder(s: SolicitacaoOrientacao, status: "ACEITA" | "RECUSADA") {
    setEnviando(s.id);
    setErroAcao(null);
    try {
      const atualizada = await api<SolicitacaoOrientacao>(`/solicitacoes-orientacao/${s.id}/responder/`, {
        metodo: "POST",
        corpo: { status, motivo_recusa: status === "RECUSADA" ? motivo.trim() || null : null },
      });
      setDados((atual) => (atual ?? []).map((x) => (x.id === s.id ? atualizada : x)));
      setRecusando(null);
      setMotivo("");
    } catch (falha) {
      setErroAcao(falha instanceof ErroApi ? falha.message : "Não foi possível responder.");
    } finally {
      setEnviando(null);
    }
  }

  return (
    <div className="pilha">
      <div className="cabecalho-pagina">
        <div className="pilha-pequena">
          <h1>{ehAluno ? "Minhas solicitações" : "Solicitações de orientação"}</h1>
          <p className="texto-suave">
            {ehAluno
              ? "Acompanhe as respostas dos docentes. Com uma solicitação aceita, o orientador cadastra o seu TCC."
              : "Responda cada solicitação uma vez. O aceite libera o cadastro do TCC com você como orientador."}
          </p>
        </div>
        {ehAluno && (
          <Link to="/orientadores" className="botao">
            Buscar orientador
          </Link>
        )}
      </div>

      {proximas && proximas.length > 0 && (
        <section className="cartao pilha-pequena" aria-labelledby="titulo-reunioes">
          <h2 id="titulo-reunioes">Próximas reuniões de alinhamento</h2>
          <ul className="membros">
            {proximas.map((r) => (
              <li key={r.id}>
                <div className="pilha-pequena">
                  <strong>{ehAluno ? r.docente_nome : r.aluno_nome}</strong>
                  <span className="campo-ajuda">
                    {formatarDataHora(r.data_hora)} · {r.tipo_local === "REMOTO" ? "Remota" : "Presencial"} · {r.local}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      {erro && <Alerta>{erro.message}</Alerta>}
      {erroAcao && <Alerta>{erroAcao}</Alerta>}
      {carregando && <p className="carregando">Carregando…</p>}
      {!carregando && lista?.length === 0 && (
        <div className="vazio">
          {ehAluno ? "Você ainda não enviou solicitações." : "Nenhuma solicitação recebida."}
        </div>
      )}

      {(lista ?? []).map((s) => {
        const podeResponder = ehDocente && s.docente === usuario?.id && s.status === "PENDENTE";
        const podeCadastrarTcc = ehDocente && s.docente === usuario?.id && s.status === "ACEITA";
        const participa = usuario?.id === s.aluno || usuario?.id === s.docente;
        const podeAgendar = participa && s.status === "ACEITA";
        return (
          <article key={s.id} className="cartao pilha-pequena" aria-label={`Solicitação de ${s.aluno_nome}`}>
            <div className="cabecalho-pagina">
              <div className="pilha-pequena">
                <h2>{ehAluno ? s.docente_nome : s.aluno_nome}</h2>
                <span className="campo-ajuda">
                  {ehAluno ? "Docente procurado" : `${nomeDoCurso(s.aluno_curso)} · ${s.aluno_email}`}
                  {!ehAluno && !ehDocente ? ` · para ${s.docente_nome}` : ""}
                  {" · enviada em "}
                  {formatarDataHora(s.enviada_em)}
                </span>
              </div>
              <span className={`selo ${SELO[s.status]}`}>{STATUS_SOLICITACAO[s.status]}</span>
            </div>

            {s.mensagem && <p>{s.mensagem}</p>}
            {s.status === "RECUSADA" && s.motivo_recusa && (
              <p className="texto-suave">Motivo da recusa: {s.motivo_recusa}</p>
            )}
            {s.respondida_em && <span className="campo-ajuda">Respondida em {formatarDataHora(s.respondida_em)}</span>}

            {podeResponder && recusando !== s.id && (
              <div className="acoes">
                <button type="button" className="botao-secundario" onClick={() => setRecusando(s.id)}>
                  Recusar
                </button>
                <button type="button" className="botao" disabled={enviando === s.id} onClick={() => responder(s, "ACEITA")}>
                  Aceitar orientação
                </button>
              </div>
            )}
            {podeResponder && recusando === s.id && (
              <div className="pilha-pequena">
                <div className="campo">
                  <label htmlFor={`motivo-${s.id}`}>Motivo da recusa (opcional)</label>
                  <textarea
                    id={`motivo-${s.id}`}
                    rows={2}
                    maxLength={2000}
                    value={motivo}
                    onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setMotivo(e.target.value)}
                  />
                </div>
                <div className="acoes">
                  <button type="button" className="botao-secundario" onClick={() => setRecusando(null)}>
                    Voltar
                  </button>
                  <button
                    type="button"
                    className="botao"
                    disabled={enviando === s.id}
                    onClick={() => responder(s, "RECUSADA")}
                  >
                    Confirmar recusa
                  </button>
                </div>
              </div>
            )}
            {s.reuniao && (
              <p>
                <strong>Reunião de alinhamento:</strong> {formatarDataHora(s.reuniao.data_hora)} ·{" "}
                {s.reuniao.tipo_local === "REMOTO" ? (
                  <a href={s.reuniao.local} target="_blank" rel="noreferrer">
                    {s.reuniao.local}
                  </a>
                ) : (
                  s.reuniao.local
                )}
              </p>
            )}
            {alertas?.id === s.id && alertas.textos.length > 0 && (
              <Alerta tom="aviso">
                Reunião salva, mas atenção à agenda: {alertas.textos.join(" ")}
              </Alerta>
            )}
            {podeAgendar && agendando === s.id && (
              <FormularioReuniao
                solicitacaoId={s.id}
                atual={s.reuniao}
                aoCancelar={() => setAgendando(null)}
                aoSalvar={(reuniao, textos) => {
                  setDados((atual) => (atual ?? []).map((x) => (x.id === s.id ? { ...x, reuniao } : x)));
                  setAlertas({ id: s.id, textos });
                  setAgendando(null);
                  recarregarReunioes();
                }}
              />
            )}
            {(podeCadastrarTcc || (podeAgendar && agendando !== s.id)) && (
              <div className="acoes">
                {podeAgendar && agendando !== s.id && (
                  <button type="button" className="botao-secundario" onClick={() => setAgendando(s.id)}>
                    {s.reuniao ? "Remarcar reunião" : "Agendar reunião de alinhamento"}
                  </button>
                )}
                {podeCadastrarTcc && (
                  <Link to={`/tccs/novo?autor=${s.aluno}`} className="botao botao-contorno">
                    Cadastrar o TCC deste aluno
                  </Link>
                )}
              </div>
            )}
          </article>
        );
      })}
    </div>
  );
}
