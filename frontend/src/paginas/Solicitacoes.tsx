import { useState, type ChangeEvent } from "react";
import { Link } from "react-router-dom";

import { ErroApi, api } from "../api/cliente";
import type { SolicitacaoOrientacao, StatusSolicitacao } from "../api/tipos";
import { useAuth } from "../auth/AuthContext";
import { Alerta } from "../componentes/Alerta";
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
            {podeCadastrarTcc && (
              <div className="acoes">
                <Link to={`/tccs/novo?autor=${s.aluno}`} className="botao botao-contorno">
                  Cadastrar o TCC deste aluno
                </Link>
              </div>
            )}
          </article>
        );
      })}
    </div>
  );
}
