import { useState } from "react";
import { useSearchParams } from "react-router-dom";

import { ErroApi, api } from "../api/cliente";
import type { ConviteRecebido } from "../api/tipos";
import { Alerta } from "../componentes/Alerta";
import { Logo } from "../componentes/Logo";
import { useCarregar } from "../hooks/useCarregar";
import { STATUS_CONVITE, descreverLocal, formatarDataHora, papelDoConvite } from "../util/rotulos";

/**
 * C6 (PF35): página pública do link do e-mail. Quem foi convidado aceita ou
 * recusa sem login; é o caminho do membro externo, que não tem senha.
 */
export function ResponderConvite() {
  const [params] = useSearchParams();
  const c = params.get("c") ?? "";
  const { dados: convite, setDados, erro, carregando } = useCarregar(
    () => api<ConviteRecebido>("/convites/link/", { params: { c } }),
    [c],
  );
  const [enviando, setEnviando] = useState(false);
  const [erroAcao, setErroAcao] = useState<string | null>(null);

  async function responder(resposta: "ACEITO" | "RECUSADO") {
    setEnviando(true);
    setErroAcao(null);
    try {
      setDados(await api<ConviteRecebido>("/convites/link/", { metodo: "POST", corpo: { c, resposta } }));
    } catch (falha) {
      setErroAcao(falha instanceof ErroApi ? falha.message : "Não foi possível registrar a resposta.");
    } finally {
      setEnviando(false);
    }
  }

  const futura = convite ? new Date(convite.banca.data_hora_inicio) > new Date() : false;

  return (
    <main className="conteudo conteudo-estreito pilha">
      <div className="marca">
        <Logo />
        SIGATCC
      </div>
      {carregando && <p className="carregando">Carregando o convite…</p>}
      {erro && <Alerta>{erro.status === 400 || erro.status === 404 ? "Este link de convite não é válido." : erro.message}</Alerta>}
      {convite && (
        <section className="cartao pilha" aria-labelledby="titulo-convite">
          <div className="pilha-pequena">
            <span className="texto-rotulo">{papelDoConvite(convite)}</span>
            <h1 id="titulo-convite">{convite.tcc_titulo}</h1>
            <p className="texto-suave">
              Olá, {convite.convidado_nome}. TCC de {convite.autor_nome}, orientação de {convite.orientador_nome}.
            </p>
          </div>
          <dl className="lista-dados">
            <div>
              <dt>Início</dt>
              <dd>{formatarDataHora(convite.banca.data_hora_inicio)}</dd>
            </div>
            <div>
              <dt>Término</dt>
              <dd>{formatarDataHora(convite.banca.data_hora_fim)}</dd>
            </div>
            <div>
              <dt>{convite.banca.tipo_local === "REMOTO" ? "Link" : "Local"}</dt>
              <dd>{descreverLocal(convite.banca)}</dd>
            </div>
          </dl>
          {erroAcao && <Alerta>{erroAcao}</Alerta>}
          {convite.status === "PENDENTE" && futura ? (
            <div className="acoes">
              <button type="button" className="botao-secundario" disabled={enviando} onClick={() => responder("RECUSADO")}>
                Recusar
              </button>
              <button type="button" className="botao" disabled={enviando} onClick={() => responder("ACEITO")}>
                Aceitar convite
              </button>
            </div>
          ) : (
            <Alerta tom={convite.status === "RECUSADO" ? "info" : "sucesso"}>
              {convite.status === "PENDENTE"
                ? "A defesa já começou; o convite não pode mais ser respondido."
                : `${STATUS_CONVITE[convite.status]}. Obrigado pela resposta.`}
              {convite.status === "ACEITO" && convite.tipo === "BANCA" && convite.convidado_externo && (
                <> Enviamos para o seu e-mail o link de acesso ao TCC, válido até 48 horas depois da defesa.</>
              )}
            </Alerta>
          )}
        </section>
      )}
    </main>
  );
}
