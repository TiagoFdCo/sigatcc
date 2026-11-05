import { useState, type ChangeEvent, type FormEvent } from "react";

import { ErroApi, api } from "../api/cliente";
import type { ErrosFormulario } from "../api/erros";
import type { TccDetalhe } from "../api/tipos";
import { Alerta } from "./Alerta";

type Props = {
  tcc: TccDetalhe;
  aoConcluir: (atualizado: TccDetalhe) => void;
  aoCancelar: () => void;
};

const CAMPOS = ["periodico", "issn_doi", "data_publicacao", "comprovante_arquivo_path", "link_artigo"];

/** C1: registra a publicacao e aprova o TCC por publicacao numa so operacao. */
export function FormularioPublicacao({ tcc, aoConcluir, aoCancelar }: Props) {
  const [periodico, setPeriodico] = useState("");
  const [issnDoi, setIssnDoi] = useState("");
  const [data, setData] = useState("");
  const [comprovante, setComprovante] = useState("");
  const [link, setLink] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erros, setErros] = useState<ErrosFormulario | null>(null);

  // Data local (nao UTC): a API recusa data futura
  const agora = new Date();
  const hoje = [
    agora.getFullYear(),
    String(agora.getMonth() + 1).padStart(2, "0"),
    String(agora.getDate()).padStart(2, "0"),
  ].join("-");

  const incompleto = !periodico.trim() || !issnDoi.trim() || !data || !comprovante.trim();
  const erroCampo = (campo: string) => erros?.campos[campo];
  // Erros de campos que nao estao no formulario (ex.: "tcc") vao no alerta
  const foraDoFormulario = Object.entries(erros?.campos ?? {})
    .filter(([campo]) => !CAMPOS.includes(campo))
    .map(([, mensagem]) => mensagem);

  async function confirmar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    if (incompleto) return;
    setEnviando(true);
    setErros(null);
    try {
      const atualizado = await api<TccDetalhe>(`/tccs/${tcc.id}/publicacao/`, {
        metodo: "POST",
        corpo: {
          periodico: periodico.trim(),
          issn_doi: issnDoi.trim(),
          data_publicacao: data,
          comprovante_arquivo_path: comprovante.trim(),
          link_artigo: link.trim() || null,
        },
      });
      aoConcluir(atualizado);
    } catch (e) {
      setErros(
        e instanceof ErroApi ? e.erros : { geral: ["Não foi possível registrar a publicação."], campos: {} },
      );
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form className="cartao cartao-destaque" onSubmit={confirmar} aria-labelledby="titulo-publicacao-form">
      <div className="pilha-pequena">
        <h2 id="titulo-publicacao-form">Registrar publicação</h2>
        <p className="texto-suave">
          Registra a publicação e aprova o TCC por publicação, sem banca. A mudança fica no histórico e na auditoria.
        </p>
      </div>

      {erros && (erros.geral.length > 0 || foraDoFormulario.length > 0) && (
        <Alerta>
          {[...erros.geral, ...foraDoFormulario].map((m) => (
            <div key={m}>{m}</div>
          ))}
        </Alerta>
      )}

      <div className="grade">
        <div className="campo">
          <label htmlFor="pub-periodico">
            Periódico ou evento <span className="obrigatorio">*</span>
          </label>
          <input
            id="pub-periodico"
            type="text"
            maxLength={300}
            value={periodico}
            aria-invalid={Boolean(erroCampo("periodico"))}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setPeriodico(e.target.value)}
          />
          {erroCampo("periodico") && <span className="campo-erro">{erroCampo("periodico")}</span>}
        </div>
        <div className="campo">
          <label htmlFor="pub-issn-doi">
            ISSN ou DOI <span className="obrigatorio">*</span>
          </label>
          <input
            id="pub-issn-doi"
            type="text"
            maxLength={100}
            value={issnDoi}
            aria-invalid={Boolean(erroCampo("issn_doi"))}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setIssnDoi(e.target.value)}
          />
          {erroCampo("issn_doi") && <span className="campo-erro">{erroCampo("issn_doi")}</span>}
        </div>
      </div>

      <div className="grade">
        <div className="campo">
          <label htmlFor="pub-data">
            Data de publicação <span className="obrigatorio">*</span>
          </label>
          <input
            id="pub-data"
            type="date"
            max={hoje}
            value={data}
            aria-invalid={Boolean(erroCampo("data_publicacao"))}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setData(e.target.value)}
          />
          {erroCampo("data_publicacao") ? (
            <span className="campo-erro">{erroCampo("data_publicacao")}</span>
          ) : (
            <span className="campo-ajuda">Não pode ser uma data futura.</span>
          )}
        </div>
        <div className="campo">
          <label htmlFor="pub-link">Link do artigo (opcional)</label>
          <input
            id="pub-link"
            type="url"
            placeholder="https://"
            value={link}
            aria-invalid={Boolean(erroCampo("link_artigo"))}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setLink(e.target.value)}
          />
          {erroCampo("link_artigo") && <span className="campo-erro">{erroCampo("link_artigo")}</span>}
        </div>
      </div>

      <div className="campo">
        <label htmlFor="pub-comprovante">
          Comprovante (link ou caminho do arquivo) <span className="obrigatorio">*</span>
        </label>
        <input
          id="pub-comprovante"
          type="text"
          maxLength={500}
          value={comprovante}
          aria-invalid={Boolean(erroCampo("comprovante_arquivo_path"))}
          onChange={(e: ChangeEvent<HTMLInputElement>) => setComprovante(e.target.value)}
        />
        {erroCampo("comprovante_arquivo_path") ? (
          <span className="campo-erro">{erroCampo("comprovante_arquivo_path")}</span>
        ) : (
          <span className="campo-ajuda">O envio de arquivo ainda não existe: informe onde o comprovante está guardado.</span>
        )}
      </div>

      <div className="acoes">
        <button type="button" className="botao-secundario" onClick={aoCancelar}>
          Cancelar
        </button>
        <button type="submit" className="botao" disabled={incompleto || enviando}>
          {enviando ? "Salvando…" : "Registrar e aprovar"}
        </button>
      </div>
    </form>
  );
}
