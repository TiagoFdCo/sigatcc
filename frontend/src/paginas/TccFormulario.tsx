import { useEffect, useState, type ChangeEvent, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { ErroApi, api } from "../api/cliente";
import type { ErrosFormulario } from "../api/erros";
import type { Aluno, Area, Docente, Modalidade, Tcc, Visibilidade } from "../api/tipos";
import { Alerta } from "../componentes/Alerta";
import { useCarregar } from "../hooks/useCarregar";
import { MODALIDADES, VISIBILIDADES, nomeDoCurso } from "../util/rotulos";

type Formulario = {
  autor: string;
  titulo: string;
  subtitulo: string;
  area_conhecimento: string;
  orientador: string;
  coorientador: string;
  modalidade: Modalidade;
  visibilidade: Visibilidade;
};

const VAZIO: Formulario = {
  autor: "",
  titulo: "",
  subtitulo: "",
  area_conhecimento: "",
  orientador: "",
  coorientador: "",
  modalidade: "DEFESA_EM_BANCA",
  visibilidade: "RESTRITO",
};

const ROTULOS: Record<string, string> = {
  autor: "Autor",
  titulo: "Título",
  subtitulo: "Subtítulo",
  area_conhecimento: "Área de conhecimento",
  orientador: "Orientador",
  coorientador: "Coorientador",
  modalidade: "Modalidade",
  visibilidade: "Visibilidade",
};

type Opcoes = { alunos: Aluno[]; docentes: Docente[]; areas: Area[] };

/** B9b: cadastro (RBN01 a RBN06, RBN33) e edicao (RBN07) de TCC. */
export function TccFormulario() {
  const { id } = useParams<{ id: string }>();
  const edicao = Boolean(id);
  const navegar = useNavigate();

  const [form, setForm] = useState<Formulario>(VAZIO);
  const [erros, setErros] = useState<ErrosFormulario | null>(null);
  const [enviando, setEnviando] = useState(false);

  const { dados: opcoes, erro: erroOpcoes } = useCarregar<Opcoes>(async () => {
    const [alunos, docentes, areas] = await Promise.all([
      api<Aluno[]>("/alunos/", { params: { ativo: "true" } }),
      api<Docente[]>("/docentes/", { params: { ativo: "true" } }),
      api<Area[]>("/areas/"),
    ]);
    return { alunos, docentes, areas };
  }, []);

  const { dados: existente, erro: erroTcc } = useCarregar<Tcc | null>(
    () => (id ? api<Tcc>(`/tccs/${id}/`) : Promise.resolve(null)),
    [id],
  );

  useEffect(() => {
    if (!existente) return;
    setForm({
      autor: existente.autor,
      titulo: existente.titulo,
      subtitulo: existente.subtitulo ?? "",
      area_conhecimento: existente.area_conhecimento,
      orientador: existente.orientador,
      coorientador: existente.coorientador ?? "",
      modalidade: existente.modalidade,
      visibilidade: existente.visibilidade,
    });
  }, [existente]);

  function mudar<K extends keyof Formulario>(campo: K, valor: Formulario[K]) {
    setForm((atual) => ({ ...atual, [campo]: valor }));
  }

  const alunoEscolhido = opcoes?.alunos.find((a) => a.id === form.autor);
  const cursoDoAluno = alunoEscolhido
    ? nomeDoCurso(alunoEscolhido.curso_nome)
    : existente
      ? nomeDoCurso(existente.curso_nome)
      : "Preenchido pelo cadastro do aluno";
  const erroCampo = (campo: keyof Formulario) => erros?.campos[campo];

  async function salvar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setEnviando(true);
    setErros(null);
    const corpo = {
      ...form,
      subtitulo: form.subtitulo.trim() || null,
      coorientador: form.coorientador || null,
    };
    try {
      const salvo = edicao
        ? await api<Tcc>(`/tccs/${id}/`, { metodo: "PATCH", corpo })
        : await api<Tcc>("/tccs/", { metodo: "POST", corpo });
      navegar(`/tccs/${salvo.id}`);
    } catch (e) {
      setErros(e instanceof ErroApi ? e.erros : { geral: ["Não foi possível salvar."], campos: {} });
      window.scrollTo({ top: 0, behavior: "smooth" });
    } finally {
      setEnviando(false);
    }
  }

  const camposComErro = Object.keys(erros?.campos ?? {});
  const docentes = opcoes?.docentes ?? [];

  return (
    <div className="pilha conteudo-estreito">
      <nav aria-label="Trilha" className="trilha">
        <Link to="/tccs">TCCs</Link> <span aria-hidden="true">/</span> {edicao ? "Editar TCC" : "Novo TCC"}
      </nav>
      <div className="pilha-pequena">
        <h1>{edicao ? "Editar TCC" : "Novo TCC"}</h1>
        <p className="texto-suave">
          Campos com <span className="obrigatorio">*</span> são obrigatórios.
          {!edicao && " O TCC começa na situação Em desenvolvimento."}
        </p>
      </div>

      {(erroOpcoes || erroTcc) && <Alerta>{(erroOpcoes ?? erroTcc)?.message}</Alerta>}
      {erros && (
        <Alerta>
          {erros.geral.map((m) => (
            <div key={m}>{m}</div>
          ))}
          {camposComErro.length > 0 && (
            <div>
              Corrija: {camposComErro.map((c) => ROTULOS[c] ?? c).join(", ")}.
            </div>
          )}
        </Alerta>
      )}

      <form className="pilha" onSubmit={salvar} noValidate>
        <section className="cartao">
          <h2>Aluno e curso</h2>
          <div className="grade">
            <div className="campo">
              <label htmlFor="autor">
                Autor <span className="obrigatorio">*</span>
              </label>
              <select
                id="autor"
                value={form.autor}
                disabled={edicao}
                aria-invalid={Boolean(erroCampo("autor"))}
                onChange={(e: ChangeEvent<HTMLSelectElement>) => mudar("autor", e.target.value)}
              >
                <option value="">Selecione um aluno cadastrado</option>
                {(opcoes?.alunos ?? []).map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.nome_completo} · {a.matricula}
                  </option>
                ))}
                {edicao && existente && !opcoes?.alunos.some((a) => a.id === existente.autor) && (
                  <option value={existente.autor}>{existente.autor_nome}</option>
                )}
              </select>
              {erroCampo("autor") && <span className="campo-erro">{erroCampo("autor")}</span>}
              {edicao && <span className="campo-ajuda">O autor não muda depois do cadastro.</span>}
            </div>
            <div className="campo">
              <span className="rotulo">Curso</span>
              <div className="campo-fixo">{cursoDoAluno}</div>
            </div>
          </div>
        </section>

        <section className="cartao">
          <h2>Trabalho</h2>
          <div className="campo">
            <div className="campo-topo">
              <label htmlFor="titulo">
                Título <span className="obrigatorio">*</span>
              </label>
              <span className="campo-ajuda">{form.titulo.length}/300</span>
            </div>
            <input
              id="titulo"
              type="text"
              maxLength={300}
              value={form.titulo}
              aria-invalid={Boolean(erroCampo("titulo"))}
              onChange={(e: ChangeEvent<HTMLInputElement>) => mudar("titulo", e.target.value)}
            />
            {erroCampo("titulo") && <span className="campo-erro">{erroCampo("titulo")}</span>}
          </div>
          <div className="campo">
            <label htmlFor="subtitulo">Subtítulo</label>
            <input
              id="subtitulo"
              type="text"
              maxLength={300}
              value={form.subtitulo}
              onChange={(e: ChangeEvent<HTMLInputElement>) => mudar("subtitulo", e.target.value)}
            />
          </div>
          <div className="campo campo-medio">
            <label htmlFor="area">
              Área de conhecimento <span className="obrigatorio">*</span>
            </label>
            <select
              id="area"
              value={form.area_conhecimento}
              aria-invalid={Boolean(erroCampo("area_conhecimento"))}
              onChange={(e: ChangeEvent<HTMLSelectElement>) => mudar("area_conhecimento", e.target.value)}
            >
              <option value="">Selecione</option>
              {(opcoes?.areas ?? []).map((a) => (
                <option key={a.id} value={a.id}>
                  {a.nome}
                </option>
              ))}
            </select>
            {erroCampo("area_conhecimento") && (
              <span className="campo-erro">{erroCampo("area_conhecimento")}</span>
            )}
          </div>
        </section>

        <section className="cartao">
          <h2>Orientação</h2>
          <div className="grade">
            <div className="campo">
              <label htmlFor="orientador">
                Orientador <span className="obrigatorio">*</span>
              </label>
              <select
                id="orientador"
                value={form.orientador}
                aria-invalid={Boolean(erroCampo("orientador"))}
                onChange={(e: ChangeEvent<HTMLSelectElement>) => mudar("orientador", e.target.value)}
              >
                <option value="">Selecione um docente ativo</option>
                {docentes.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.nome_completo}
                  </option>
                ))}
              </select>
              {erroCampo("orientador") && <span className="campo-erro">{erroCampo("orientador")}</span>}
            </div>
            <div className="campo">
              <label htmlFor="coorientador">Coorientador</label>
              <select
                id="coorientador"
                value={form.coorientador}
                aria-invalid={Boolean(erroCampo("coorientador"))}
                onChange={(e: ChangeEvent<HTMLSelectElement>) => mudar("coorientador", e.target.value)}
              >
                <option value="">Nenhum</option>
                {docentes
                  .filter((d) => d.id !== form.orientador)
                  .map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.nome_completo}
                    </option>
                  ))}
              </select>
              {erroCampo("coorientador") ? (
                <span className="campo-erro">{erroCampo("coorientador")}</span>
              ) : (
                <span className="campo-ajuda">Opcional. Deve ser outro docente.</span>
              )}
            </div>
          </div>
        </section>

        <section className="cartao">
          <h2>Conclusão e visibilidade</h2>
          <fieldset>
            <legend>
              Modalidade de conclusão <span className="obrigatorio">*</span>
            </legend>
            <div className="grade">
              {(Object.keys(MODALIDADES) as Modalidade[]).map((m) => (
                <label key={m} className="opcao">
                  <input
                    type="radio"
                    name="modalidade"
                    value={m}
                    checked={form.modalidade === m}
                    onChange={() => mudar("modalidade", m)}
                  />
                  <span className="opcao-texto">
                    <span>{MODALIDADES[m]}</span>
                    <span className="campo-ajuda">
                      {m === "DEFESA_EM_BANCA" ? "Exige banca com 3 titulares." : "Conclui por artigo publicado, sem banca."}
                    </span>
                  </span>
                </label>
              ))}
            </div>
          </fieldset>
          <fieldset>
            <legend>Visibilidade na consulta pública</legend>
            <div className="pilha-pequena">
              {(Object.keys(VISIBILIDADES) as Visibilidade[]).map((v) => (
                <label key={v} className="opcao">
                  <input
                    type="radio"
                    name="visibilidade"
                    value={v}
                    checked={form.visibilidade === v}
                    onChange={() => mudar("visibilidade", v)}
                  />
                  <span>{VISIBILIDADES[v]}</span>
                </label>
              ))}
            </div>
          </fieldset>
        </section>

        <div className="acoes">
          <Link to={edicao ? `/tccs/${id}` : "/tccs"} className="botao-secundario">
            Cancelar
          </Link>
          <button type="submit" className="botao" disabled={enviando || !opcoes}>
            {enviando ? "Salvando…" : edicao ? "Salvar alterações" : "Salvar TCC"}
          </button>
        </div>
      </form>
    </div>
  );
}
