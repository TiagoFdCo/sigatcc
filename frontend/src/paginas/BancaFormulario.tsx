import { useState, type ChangeEvent, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { ErroApi, api } from "../api/cliente";
import type { ErrosFormulario } from "../api/erros";
import type { Docente, TccDetalhe, TipoLocal, UsuarioGeral } from "../api/tipos";
import { Alerta } from "../componentes/Alerta";
import { useCarregar } from "../hooks/useCarregar";
import { nomeDoCurso } from "../util/rotulos";

type Membro = { id: string; rotulo: string };

const ROTULOS: Record<string, string> = {
  titulares: "Titulares",
  suplentes: "Suplentes",
  membros: "Membros",
  data_hora: "Data e horário",
  tipo_local: "Tipo de local",
  local: "Sala ou link",
  tcc: "TCC",
};

/** B9c: cadastro de banca (RBN09 a RBN12). O envio dos convites e da E2. */
export function BancaFormulario() {
  const { id = "" } = useParams<{ id: string }>();
  const navegar = useNavigate();

  const { dados: tcc, erro: erroTcc } = useCarregar(() => api<TccDetalhe>(`/tccs/${id}/`), [id]);
  const { dados: membros, erro: erroMembros } = useCarregar<Membro[]>(async () => {
    const [docentes, externos] = await Promise.all([
      api<Docente[]>("/docentes/", { params: { ativo: "true" } }),
      api<UsuarioGeral[]>("/usuarios/", { params: { tipo: "MEMBRO_EXTERNO", ativo: "true" } }),
    ]);
    return [
      ...docentes.map((d) => ({ id: d.id, rotulo: `${d.nome_completo} · docente` })),
      ...externos.map((u) => ({
        id: u.id,
        rotulo: `${u.nome_completo} · externo${u.instituicao_origem ? ` (${u.instituicao_origem})` : ""}`,
      })),
    ];
  }, []);

  const [titular2, setTitular2] = useState("");
  const [titular3, setTitular3] = useState("");
  const [suplentes, setSuplentes] = useState<string[]>([]);
  const [data, setData] = useState("");
  const [hora, setHora] = useState("");
  const [tipoLocal, setTipoLocal] = useState<TipoLocal>("PRESENCIAL");
  const [local, setLocal] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erros, setErros] = useState<ErrosFormulario | null>(null);

  const orientador = tcc?.orientador ?? "";
  const escolhidos = new Set([orientador, titular2, titular3, ...suplentes].filter(Boolean));
  const disponiveis = (atual: string) =>
    (membros ?? []).filter((m) => m.id !== orientador && (m.id === atual || !escolhidos.has(m.id)));

  const incompleto = !titular2 || !titular3 || !data || !hora || !local.trim() || suplentes.some((s) => !s);

  async function salvar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    if (!tcc || incompleto) return;
    setEnviando(true);
    setErros(null);
    try {
      await api("/bancas/", {
        metodo: "POST",
        corpo: {
          tcc: tcc.id,
          titulares: [orientador, titular2, titular3],
          suplentes,
          // data e hora digitadas no fuso do navegador, enviadas com fuso (ISO)
          data_hora: new Date(`${data}T${hora}`).toISOString(),
          tipo_local: tipoLocal,
          local: local.trim(),
        },
      });
      navegar(`/tccs/${tcc.id}`);
    } catch (e) {
      setErros(e instanceof ErroApi ? e.erros : { geral: ["Não foi possível salvar a banca."], campos: {} });
      window.scrollTo({ top: 0, behavior: "smooth" });
    } finally {
      setEnviando(false);
    }
  }

  const agora = new Date();
  const hoje = [
    agora.getFullYear(),
    String(agora.getMonth() + 1).padStart(2, "0"),
    String(agora.getDate()).padStart(2, "0"),
  ].join("-");
  const erroCarga = erroTcc ?? erroMembros;

  return (
    <div className="pilha conteudo-estreito">
      <nav aria-label="Trilha" className="trilha">
        <Link to="/tccs">TCCs</Link> <span aria-hidden="true">/</span> <Link to={`/tccs/${id}`}>Detalhe</Link>{" "}
        <span aria-hidden="true">/</span> Cadastrar banca
      </nav>
      <div className="pilha-pequena">
        <h1>Cadastrar banca</h1>
        <p className="texto-suave">
          Exatamente 3 titulares, com o orientador entre eles. Suplentes só avaliam quando substituem um titular
          ausente.
        </p>
      </div>

      {erroCarga && <Alerta>{erroCarga.message}</Alerta>}
      {erros && (
        <Alerta>
          {erros.geral.map((m) => (
            <div key={m}>{m}</div>
          ))}
          {Object.entries(erros.campos).map(([campo, msg]) => (
            <div key={campo}>
              {ROTULOS[campo] ?? campo}: {msg}
            </div>
          ))}
        </Alerta>
      )}

      {tcc && (
        <section aria-label="TCC" className="resumo-tcc">
          <strong>{tcc.titulo}</strong>
          <span>
            <span className="texto-rotulo">Autor:</span> {tcc.autor_nome}
          </span>
          <span>
            <span className="texto-rotulo">Orientador:</span> {tcc.orientador_nome}
          </span>
          <span>
            <span className="texto-rotulo">Curso:</span> {nomeDoCurso(tcc.curso_nome)}
          </span>
        </section>
      )}

      {tcc?.banca && (
        <Alerta tom="info">
          Este TCC já tem banca. <Link to={`/tccs/${tcc.id}`}>Ver no detalhe</Link>
        </Alerta>
      )}

      <form className="pilha" onSubmit={salvar} noValidate>
        <section className="cartao">
          <div className="cabecalho-pagina">
            <h2>Titulares</h2>
            <span className="campo-ajuda">3 de 3</span>
          </div>
          <div className="membro-linha membro-fixo">
            <span className="numero">1</span>
            <div className="pilha-pequena">
              <strong>{tcc?.orientador_nome ?? "Orientador"}</strong>
              <span className="campo-ajuda">Orientador do TCC · titular obrigatório</span>
            </div>
          </div>
          {[
            { n: 2, valor: titular2, mudar: setTitular2 },
            { n: 3, valor: titular3, mudar: setTitular3 },
          ].map(({ n, valor, mudar }) => (
            <div key={n} className="membro-linha">
              <span className="numero numero-claro">{n}</span>
              <div className="campo campo-flex">
                <label htmlFor={`titular${n}`} className="so-leitor">
                  Titular {n}
                </label>
                <select
                  id={`titular${n}`}
                  value={valor}
                  onChange={(e: ChangeEvent<HTMLSelectElement>) => mudar(e.target.value)}
                >
                  <option value="">Selecione docente ou membro externo</option>
                  {disponiveis(valor).map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.rotulo}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          ))}
        </section>

        <section className="cartao">
          <div className="cabecalho-pagina">
            <h2>
              Suplentes <span className="texto-suave">(opcional)</span>
            </h2>
            <button type="button" className="botao-secundario" onClick={() => setSuplentes((s) => [...s, ""])}>
              Adicionar suplente
            </button>
          </div>
          {suplentes.length === 0 && <p className="texto-suave">Nenhum suplente. Quem for titular não pode ser suplente.</p>}
          {suplentes.map((valor, i) => (
            <div key={i} className="membro-linha">
              <div className="campo campo-flex">
                <label htmlFor={`suplente${i}`} className="so-leitor">
                  Suplente {i + 1}
                </label>
                <select
                  id={`suplente${i}`}
                  value={valor}
                  onChange={(e: ChangeEvent<HTMLSelectElement>) =>
                    setSuplentes((s) => s.map((x, j) => (j === i ? e.target.value : x)))
                  }
                >
                  <option value="">Selecione docente ou membro externo</option>
                  {disponiveis(valor).map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.rotulo}
                    </option>
                  ))}
                </select>
              </div>
              <button
                type="button"
                className="botao-icone"
                aria-label={`Remover suplente ${i + 1}`}
                onClick={() => setSuplentes((s) => s.filter((_, j) => j !== i))}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
                </svg>
              </button>
            </div>
          ))}
        </section>

        <section className="cartao">
          <h2>Data e local da defesa</h2>
          <div className="grade">
            <div className="campo">
              <label htmlFor="data">
                Data <span className="obrigatorio">*</span>
              </label>
              <input
                id="data"
                type="date"
                min={hoje}
                value={data}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setData(e.target.value)}
              />
              <span className="campo-ajuda">Precisa ser uma data futura.</span>
            </div>
            <div className="campo">
              <label htmlFor="hora">
                Horário de início <span className="obrigatorio">*</span>
              </label>
              <input id="hora" type="time" value={hora} onChange={(e: ChangeEvent<HTMLInputElement>) => setHora(e.target.value)} />
            </div>
          </div>
          <fieldset>
            <legend>
              Tipo de local <span className="obrigatorio">*</span>
            </legend>
            <div className="segmentado">
              {(["PRESENCIAL", "REMOTO"] as TipoLocal[]).map((t) => (
                <button
                  key={t}
                  type="button"
                  aria-pressed={tipoLocal === t}
                  onClick={() => {
                    setTipoLocal(t);
                    setLocal("");
                  }}
                >
                  {t === "PRESENCIAL" ? "Presencial" : "Remoto"}
                </button>
              ))}
            </div>
          </fieldset>
          <div className="campo campo-medio">
            <label htmlFor="local">
              {tipoLocal === "PRESENCIAL" ? "Sala" : "Link da sala virtual"} <span className="obrigatorio">*</span>
            </label>
            <input
              id="local"
              type={tipoLocal === "PRESENCIAL" ? "text" : "url"}
              placeholder={tipoLocal === "PRESENCIAL" ? "Ex.: Sala 10, bloco NUCOMP" : "https://"}
              value={local}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setLocal(e.target.value)}
            />
            {tipoLocal === "REMOTO" && <span className="campo-ajuda">Endereço completo, começando com https://</span>}
          </div>
        </section>

        <Alerta tom="info">
          Ao salvar, cada membro da banca, exceto o orientador, recebe um convite pendente. Membros externos ganham
          acesso temporário quando aceitam o convite.
        </Alerta>

        <div className="acoes">
          <Link to={`/tccs/${id}`} className="botao-secundario">
            Cancelar
          </Link>
          <button type="submit" className="botao" disabled={incompleto || enviando || !tcc || Boolean(tcc?.banca)}>
            {enviando ? "Salvando…" : "Salvar banca"}
          </button>
        </div>
      </form>
    </div>
  );
}
