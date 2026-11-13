import { useState, type ChangeEvent, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { ErroApi, api } from "../api/cliente";
import type { Area, Orientador, SolicitacaoOrientacao } from "../api/tipos";
import { Alerta } from "../componentes/Alerta";
import { useCarregar } from "../hooks/useCarregar";
import { DEPARTAMENTOS } from "../util/rotulos";

/** C3a (PF63, PF41): o aluno busca orientador por área e envia a solicitação. */
export function BuscarOrientador() {
  const [busca, setBusca] = useState("");
  const [filtro, setFiltro] = useState({ busca: "", area: "" });
  const [escolhido, setEscolhido] = useState<Orientador | null>(null);
  const [mensagem, setMensagem] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erroEnvio, setErroEnvio] = useState<string | null>(null);
  const [enviadoPara, setEnviadoPara] = useState<string | null>(null);

  const { dados: areas } = useCarregar(() => api<Area[]>("/areas/"), []);
  const {
    dados: orientadores,
    erro,
    carregando,
  } = useCarregar(() => api<Orientador[]>("/orientadores/", { params: filtro }), [filtro.busca, filtro.area]);

  async function enviar(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!escolhido) return;
    setEnviando(true);
    setErroEnvio(null);
    try {
      await api<SolicitacaoOrientacao>("/solicitacoes-orientacao/", {
        metodo: "POST",
        corpo: { docente: escolhido.id, mensagem: mensagem.trim() || null },
      });
      setEnviadoPara(escolhido.nome_completo);
      setEscolhido(null);
      setMensagem("");
    } catch (falha) {
      setErroEnvio(falha instanceof ErroApi ? falha.message : "Não foi possível enviar a solicitação.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="pilha">
      <div className="cabecalho-pagina">
        <div className="pilha-pequena">
          <h1>Buscar orientador</h1>
          <p className="texto-suave">
            Procure docentes por área de interesse e envie sua solicitação de orientação.
          </p>
        </div>
        <Link to="/solicitacoes" className="botao botao-contorno">
          Minhas solicitações
        </Link>
      </div>

      <form
        role="search"
        className="cartao filtros"
        onSubmit={(e: FormEvent<HTMLFormElement>) => {
          e.preventDefault();
          setFiltro((f) => ({ ...f, busca: busca.trim() }));
        }}
      >
        <div className="campo filtro-busca">
          <label htmlFor="busca">Nome do docente</label>
          <input
            id="busca"
            type="search"
            value={busca}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setBusca(e.target.value)}
            onBlur={() => setFiltro((f) => ({ ...f, busca: busca.trim() }))}
          />
        </div>
        <div className="campo">
          <label htmlFor="area">Área de interesse</label>
          <select
            id="area"
            value={filtro.area}
            onChange={(e: ChangeEvent<HTMLSelectElement>) => setFiltro((f) => ({ ...f, area: e.target.value }))}
          >
            <option value="">Todas</option>
            {(areas ?? []).map((a) => (
              <option key={a.id} value={a.id}>
                {a.nome}
              </option>
            ))}
          </select>
        </div>
      </form>

      {enviadoPara && (
        <Alerta tom="sucesso">
          Solicitação enviada para {enviadoPara}. Acompanhe a resposta em <Link to="/solicitacoes">Minhas solicitações</Link>.
        </Alerta>
      )}
      {erro && <Alerta>{erro.message}</Alerta>}

      {escolhido && (
        <form className="cartao cartao-destaque pilha" onSubmit={enviar} aria-labelledby="titulo-solicitar">
          <h2 id="titulo-solicitar">Solicitar orientação a {escolhido.nome_completo}</h2>
          <div className="campo">
            <label htmlFor="mensagem">Mensagem (opcional)</label>
            <textarea
              id="mensagem"
              rows={4}
              maxLength={2000}
              placeholder="Conte em poucas linhas o tema que você quer pesquisar."
              value={mensagem}
              onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setMensagem(e.target.value)}
            />
          </div>
          {erroEnvio && <Alerta>{erroEnvio}</Alerta>}
          <div className="acoes">
            <button type="button" className="botao-secundario" onClick={() => setEscolhido(null)}>
              Cancelar
            </button>
            <button type="submit" className="botao" disabled={enviando}>
              {enviando ? "Enviando…" : "Enviar solicitação"}
            </button>
          </div>
        </form>
      )}

      {carregando && <p className="carregando">Carregando…</p>}
      {!carregando && orientadores?.length === 0 && (
        <div className="vazio">Nenhum docente encontrado com esses filtros.</div>
      )}

      <div className="grade">
        {(orientadores ?? []).map((o) => (
          <article key={o.id} className="cartao pilha-pequena" aria-label={o.nome_completo}>
            <h2>{o.nome_completo}</h2>
            <span className="campo-ajuda">
              {DEPARTAMENTOS[o.departamento] ?? o.departamento} · {o.qtd_orientacoes}{" "}
              {o.qtd_orientacoes === 1 ? "orientando" : "orientandos"}
            </span>
            <p className="texto-suave">
              {o.areas_interesse.length > 0
                ? o.areas_interesse.map((a) => a.nome).join(", ")
                : "Sem áreas de interesse cadastradas"}
            </p>
            <div className="acoes">
              {o.aceita_orientacoes ? (
                <button
                  type="button"
                  className="botao botao-contorno"
                  onClick={() => {
                    setEscolhido(o);
                    setEnviadoPara(null);
                    setErroEnvio(null);
                  }}
                >
                  Solicitar orientação
                </button>
              ) : (
                <span className="selo">Não aceita novas orientações</span>
              )}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
