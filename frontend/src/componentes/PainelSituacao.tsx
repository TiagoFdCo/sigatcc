import { useState, type ChangeEvent, type FormEvent } from "react";

import { ErroApi, api } from "../api/cliente";
import type { ErrosFormulario } from "../api/erros";
import type { MotivoNaoApresentacao, StatusTcc, TccDetalhe } from "../api/tipos";
import { MOTIVOS, STATUS, opcoesDeSituacao } from "../util/rotulos";
import { Alerta } from "./Alerta";

type Props = {
  tcc: TccDetalhe;
  aoConcluir: (atualizado: TccDetalhe) => void;
  aoCancelar: () => void;
};

/** B7b/B9b: mudanca de situacao com motivo obrigatorio para "Não apresentado". */
export function PainelSituacao({ tcc, aoConcluir, aoCancelar }: Props) {
  const [status, setStatus] = useState<StatusTcc | "">("");
  const [motivo, setMotivo] = useState<MotivoNaoApresentacao | "">("");
  const [motivoOutro, setMotivoOutro] = useState("");
  const [justificativa, setJustificativa] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erros, setErros] = useState<ErrosFormulario | null>(null);

  const opcoes = opcoesDeSituacao(tcc.status, tcc.modalidade);
  const pedeMotivo = status === "NAO_APRESENTADO";
  const pedeOutro = pedeMotivo && motivo === "OUTRO";
  const incompleto = !status || (pedeMotivo && !motivo) || (pedeOutro && !motivoOutro.trim());

  async function confirmar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    if (incompleto) return;
    setEnviando(true);
    setErros(null);
    try {
      const atualizado = await api<TccDetalhe>(`/tccs/${tcc.id}/situacao/`, {
        metodo: "POST",
        corpo: {
          status,
          motivo_nao_apresentacao: pedeMotivo ? motivo : null,
          motivo_outro: pedeOutro ? motivoOutro.trim() : null,
          justificativa: justificativa.trim() || null,
        },
      });
      aoConcluir(atualizado);
    } catch (e) {
      setErros(e instanceof ErroApi ? e.erros : { geral: ["Não foi possível mudar a situação."], campos: {} });
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form className="cartao cartao-destaque" onSubmit={confirmar} aria-labelledby="titulo-situacao">
      <div className="pilha-pequena">
        <h2 id="titulo-situacao">Mudar situação</h2>
        <p className="texto-suave">
          Situação atual: {STATUS[tcc.status]}. A mudança fica registrada no histórico e na auditoria.
        </p>
      </div>

      {erros && (
        <Alerta>
          {[...erros.geral, ...Object.values(erros.campos)].map((m) => (
            <div key={m}>{m}</div>
          ))}
        </Alerta>
      )}

      <fieldset className="pilha-pequena">
        <legend>Nova situação</legend>
        {opcoes.map((o) => (
          <label key={o.valor} className="opcao">
            <input
              type="radio"
              name="situacao"
              value={o.valor}
              checked={status === o.valor}
              disabled={!o.permitido}
              onChange={() => {
                setStatus(o.valor);
                setMotivo("");
              }}
            />
            <span className="opcao-texto">
              <span>{STATUS[o.valor]}</span>
              <span className="campo-ajuda">{o.dica}</span>
            </span>
          </label>
        ))}
      </fieldset>

      {pedeMotivo && (
        <div className="grade">
          <div className="campo">
            <label htmlFor="motivo">
              Motivo da não apresentação <span className="obrigatorio">*</span>
            </label>
            <select
              id="motivo"
              value={motivo}
              onChange={(e: ChangeEvent<HTMLSelectElement>) => setMotivo(e.target.value as MotivoNaoApresentacao | "")}
            >
              <option value="">Selecione</option>
              {Object.entries(MOTIVOS).map(([valor, rotulo]) => (
                <option key={valor} value={valor}>
                  {rotulo}
                </option>
              ))}
            </select>
          </div>
          {pedeOutro && (
            <div className="campo">
              <label htmlFor="motivo-outro">
                Descreva o motivo <span className="obrigatorio">*</span>
              </label>
              <input
                id="motivo-outro"
                type="text"
                value={motivoOutro}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setMotivoOutro(e.target.value)}
              />
            </div>
          )}
        </div>
      )}

      <div className="campo">
        <label htmlFor="justificativa">Justificativa (opcional)</label>
        <textarea
          id="justificativa"
          rows={3}
          value={justificativa}
          placeholder="Fica registrada no histórico de situação"
          onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setJustificativa(e.target.value)}
        />
      </div>

      <div className="acoes">
        <button type="button" className="botao-secundario" onClick={aoCancelar}>
          Cancelar
        </button>
        <button type="submit" className="botao" disabled={incompleto || enviando}>
          {enviando ? "Salvando…" : "Confirmar mudança"}
        </button>
      </div>
    </form>
  );
}
