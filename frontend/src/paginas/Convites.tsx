import { useState } from "react";
import { Link } from "react-router-dom";

import { ErroApi, api } from "../api/cliente";
import type { ConviteRecebido } from "../api/tipos";
import { Alerta } from "../componentes/Alerta";
import { useCarregar } from "../hooks/useCarregar";
import { STATUS_CONVITE, descreverLocal, formatarDataHora, papelDoConvite } from "../util/rotulos";

/** C6 (PF62, PF35): convites de banca e de audiência recebidos por quem está logado. */
export function Convites() {
  const { dados: convites, setDados, erro, carregando } = useCarregar(
    () => api<ConviteRecebido[]>("/convites/"),
    [],
  );
  const [ocupado, setOcupado] = useState<string | null>(null);
  const [erroAcao, setErroAcao] = useState<string | null>(null);

  async function responder(c: ConviteRecebido, resposta: "ACEITO" | "RECUSADO") {
    setOcupado(c.id);
    setErroAcao(null);
    try {
      const atualizado = await api<ConviteRecebido>(`/convites/${c.id}/responder/`, {
        metodo: "POST",
        corpo: { resposta },
      });
      setDados((atual) => (atual ?? []).map((x) => (x.id === c.id ? atualizado : x)));
    } catch (falha) {
      setErroAcao(falha instanceof ErroApi ? falha.message : "Não foi possível responder.");
    } finally {
      setOcupado(null);
    }
  }

  return (
    <div className="pilha">
      <div className="pilha-pequena">
        <h1>Convites</h1>
        <p className="texto-suave">Convites para compor bancas e para assistir a defesas. Responda antes da defesa.</p>
      </div>
      {erro && <Alerta>{erro.message}</Alerta>}
      {erroAcao && <Alerta>{erroAcao}</Alerta>}
      {carregando && <p className="carregando">Carregando…</p>}
      {!carregando && convites?.length === 0 && <div className="vazio">Você não recebeu convites.</div>}

      {(convites ?? []).map((c) => {
        const futura = new Date(c.banca.data_hora_inicio) > new Date();
        return (
          <article key={c.id} className="cartao pilha-pequena" aria-label={`Convite: ${c.tcc_titulo}`}>
            <div className="cabecalho-pagina">
              <div className="pilha-pequena">
                <h2>{c.tcc_titulo}</h2>
                <span className="campo-ajuda">
                  {papelDoConvite(c)} · {c.autor_nome}, orientação de {c.orientador_nome}
                </span>
              </div>
              <span className={`selo selo-convite-${c.status.toLowerCase()}`}>{STATUS_CONVITE[c.status]}</span>
            </div>
            <p>
              {formatarDataHora(c.banca.data_hora_inicio)} até {formatarDataHora(c.banca.data_hora_fim)} ·{" "}
              {c.banca.tipo_local === "REMOTO" && c.banca.link_remoto ? (
                <a href={c.banca.link_remoto} target="_blank" rel="noreferrer">
                  {c.banca.link_remoto}
                </a>
              ) : (
                descreverLocal(c.banca)
              )}
            </p>
            <div className="acoes">
              {c.tipo === "BANCA" && (
                <Link to={`/tccs/${c.tcc}`} className="link-botao">
                  Ver o TCC
                </Link>
              )}
              {c.status === "PENDENTE" && futura && (
                <>
                  <button
                    type="button"
                    className="botao-secundario"
                    disabled={ocupado === c.id}
                    onClick={() => responder(c, "RECUSADO")}
                  >
                    Recusar
                  </button>
                  <button type="button" className="botao" disabled={ocupado === c.id} onClick={() => responder(c, "ACEITO")}>
                    Aceitar
                  </button>
                </>
              )}
            </div>
          </article>
        );
      })}
    </div>
  );
}
