import { useState, type ChangeEvent, type FormEvent } from "react";

import { ErroApi, api } from "../api/cliente";
import type { RespostaReuniao, ResumoReuniao, TipoLocal } from "../api/tipos";
import { Alerta } from "./Alerta";

function paraCampos(iso: string | undefined) {
  if (!iso) return { data: "", hora: "" };
  const d = new Date(iso);
  const doisDigitos = (n: number) => String(n).padStart(2, "0");
  return {
    data: `${d.getFullYear()}-${doisDigitos(d.getMonth() + 1)}-${doisDigitos(d.getDate())}`,
    hora: `${doisDigitos(d.getHours())}:${doisDigitos(d.getMinutes())}`,
  };
}

/**
 * C3b (PF44): agenda ou remarca a reunião de alinhamento de uma solicitação
 * aceita. Conflito de agenda volta como alerta, sem impedir o agendamento.
 */
export function FormularioReuniao({
  solicitacaoId,
  atual,
  aoSalvar,
  aoCancelar,
}: {
  solicitacaoId: string;
  atual: ResumoReuniao | null;
  aoSalvar: (reuniao: ResumoReuniao, alertas: string[]) => void;
  aoCancelar: () => void;
}) {
  const inicial = paraCampos(atual?.data_hora);
  const [data, setData] = useState(inicial.data);
  const [hora, setHora] = useState(inicial.hora);
  const [tipoLocal, setTipoLocal] = useState<TipoLocal>(atual?.tipo_local ?? "PRESENCIAL");
  const [local, setLocal] = useState(atual?.local ?? "");
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function enviar(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      const resposta = await api<RespostaReuniao>(`/solicitacoes-orientacao/${solicitacaoId}/reuniao/`, {
        metodo: "POST",
        corpo: { data_hora: new Date(`${data}T${hora}`).toISOString(), tipo_local: tipoLocal, local: local.trim() },
      });
      const { id, data_hora, tipo_local, local: salvo } = resposta.reuniao;
      aoSalvar({ id, data_hora, tipo_local, local: salvo }, resposta.alertas);
    } catch (falha) {
      setErro(falha instanceof ErroApi ? falha.message : "Não foi possível agendar a reunião.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form className="pilha-pequena" onSubmit={enviar} aria-label="Agendar reunião de alinhamento">
      <div className="grade">
        <div className="campo">
          <label htmlFor={`data-${solicitacaoId}`}>
            Data <span className="obrigatorio">*</span>
          </label>
          <input
            id={`data-${solicitacaoId}`}
            type="date"
            required
            value={data}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setData(e.target.value)}
          />
        </div>
        <div className="campo">
          <label htmlFor={`hora-${solicitacaoId}`}>
            Hora <span className="obrigatorio">*</span>
          </label>
          <input
            id={`hora-${solicitacaoId}`}
            type="time"
            required
            value={hora}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setHora(e.target.value)}
          />
        </div>
        <div className="campo">
          <label htmlFor={`tipo-${solicitacaoId}`}>Tipo</label>
          <select
            id={`tipo-${solicitacaoId}`}
            value={tipoLocal}
            onChange={(e: ChangeEvent<HTMLSelectElement>) => setTipoLocal(e.target.value as TipoLocal)}
          >
            <option value="PRESENCIAL">Presencial</option>
            <option value="REMOTO">Remota</option>
          </select>
        </div>
      </div>
      <div className="campo">
        <label htmlFor={`local-${solicitacaoId}`}>
          {tipoLocal === "PRESENCIAL" ? "Local" : "Link da reunião"} <span className="obrigatorio">*</span>
        </label>
        <input
          id={`local-${solicitacaoId}`}
          type={tipoLocal === "PRESENCIAL" ? "text" : "url"}
          required
          maxLength={300}
          placeholder={tipoLocal === "PRESENCIAL" ? "Ex.: Sala 3, NUCOMP" : "https://"}
          value={local}
          onChange={(e: ChangeEvent<HTMLInputElement>) => setLocal(e.target.value)}
        />
      </div>
      {erro && <Alerta>{erro}</Alerta>}
      <div className="acoes">
        <button type="button" className="botao-secundario" onClick={aoCancelar}>
          Cancelar
        </button>
        <button type="submit" className="botao" disabled={enviando}>
          {enviando ? "Salvando…" : atual ? "Remarcar reunião" : "Agendar reunião"}
        </button>
      </div>
    </form>
  );
}
