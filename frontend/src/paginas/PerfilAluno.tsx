import { useState, type FormEvent } from "react";
import { Link, Navigate } from "react-router-dom";

import { ErroApi, api } from "../api/cliente";
import type { ErrosFormulario } from "../api/erros";
import type { Area, PerfilAluno as Perfil } from "../api/tipos";
import { useAuth } from "../auth/AuthContext";
import { Alerta } from "../componentes/Alerta";
import { SeloSituacao } from "../componentes/SeloSituacao";
import { useCarregar } from "../hooks/useCarregar";
import { MODALIDADES, nomeDoCurso } from "../util/rotulos";

type Props = {
  perfil: Perfil;
  areas: Area[];
  aoSalvar: (atualizado: Perfil) => void;
};

/** Marca as areas de conhecimento de interesse e salva (PATCH /alunos/meu-perfil/). */
function AreasDeInteresse({ perfil, areas, aoSalvar }: Props) {
  const salvas = perfil.areas_interesse.map((a) => a.id);
  const [escolhidas, setEscolhidas] = useState<string[]>(salvas);
  const [salvando, setSalvando] = useState(false);
  const [salvo, setSalvo] = useState(false);
  const [erros, setErros] = useState<ErrosFormulario | null>(null);

  const mudou = escolhidas.length !== salvas.length || escolhidas.some((id) => !salvas.includes(id));

  function alternar(id: string) {
    setSalvo(false);
    setEscolhidas((atuais) => (atuais.includes(id) ? atuais.filter((x) => x !== id) : [...atuais, id]));
  }

  async function salvar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    if (!mudou) return;
    setSalvando(true);
    setSalvo(false);
    setErros(null);
    try {
      const atualizado = await api<Perfil>("/alunos/meu-perfil/", {
        metodo: "PATCH",
        corpo: { areas_interesse: escolhidas },
      });
      aoSalvar(atualizado);
      setSalvo(true);
    } catch (e) {
      setErros(e instanceof ErroApi ? e.erros : { geral: ["Não foi possível salvar."], campos: {} });
    } finally {
      setSalvando(false);
    }
  }

  const mensagens = erros ? [...erros.geral, ...Object.values(erros.campos)] : [];

  return (
    <form className="cartao pilha" onSubmit={salvar} aria-labelledby="titulo-areas">
      <div className="pilha-pequena">
        <h2 id="titulo-areas">Áreas de interesse</h2>
        <p className="texto-suave">Marque as áreas de conhecimento em que você quer desenvolver o TCC.</p>
      </div>

      {mensagens.length > 0 && (
        <Alerta>
          {mensagens.map((m) => (
            <div key={m}>{m}</div>
          ))}
        </Alerta>
      )}
      {salvo && <Alerta tom="sucesso">Áreas de interesse salvas.</Alerta>}

      {areas.length === 0 ? (
        <p className="texto-suave">Ainda não há áreas cadastradas.</p>
      ) : (
        <fieldset className="grade">
          <legend className="visualmente-oculto">Áreas de conhecimento</legend>
          {areas.map((area) => (
            <label key={area.id} className="opcao">
              <input type="checkbox" checked={escolhidas.includes(area.id)} onChange={() => alternar(area.id)} />
              <span className="opcao-texto">{area.nome}</span>
            </label>
          ))}
        </fieldset>
      )}

      <div className="acoes">
        <button type="submit" className="botao" disabled={!mudou || salvando}>
          {salvando ? "Salvando…" : "Salvar áreas"}
        </button>
      </div>
    </form>
  );
}

/** C2a: "Meu perfil" do aluno: os proprios dados, as areas de interesse e o TCC. */
export function PerfilAluno() {
  const { usuario } = useAuth();
  const { dados, setDados, erro, carregando } = useCarregar(async () => {
    const [perfil, areas] = await Promise.all([api<Perfil>("/alunos/meu-perfil/"), api<Area[]>("/areas/")]);
    return { perfil, areas };
  }, []);

  if (usuario && usuario.tipo_usuario !== "ALUNO") return <Navigate to="/" replace />;
  if (carregando) return <p className="carregando">Carregando…</p>;
  if (erro || !dados) return <Alerta>{erro?.message ?? "Erro ao carregar o perfil."}</Alerta>;

  const { perfil, areas } = dados;
  const tcc = perfil.meu_tcc;
  const dadosAluno: [string, string][] = [
    ["Nome", perfil.nome_completo],
    ["E-mail", perfil.email],
    ["Matrícula", perfil.matricula],
    ["CPF", perfil.cpf ?? "—"],
    ["Curso", nomeDoCurso(perfil.curso_nome)],
    ["Cadastro", perfil.cadastro_confirmado ? "Confirmado" : "Aguardando confirmação"],
  ];

  return (
    <div className="pilha">
      <div className="cabecalho-pagina">
        <div className="pilha-pequena">
          <h1>Meu perfil</h1>
          <p className="texto-suave">Seus dados no SIGATCC, suas áreas de interesse e o seu TCC.</p>
        </div>
      </div>

      <div className="duas-colunas">
        <div className="coluna-principal">
          <section className="cartao" aria-labelledby="titulo-dados">
            <h2 id="titulo-dados">Meus dados</h2>
            <dl className="lista-dados">
              {dadosAluno.map(([rotulo, valor]) => (
                <div key={rotulo}>
                  <dt>{rotulo}</dt>
                  <dd>{valor}</dd>
                </div>
              ))}
            </dl>
            <p className="campo-ajuda">Para corrigir esses dados, procure a secretaria ou a administração.</p>
          </section>

          <AreasDeInteresse
            perfil={perfil}
            areas={areas}
            aoSalvar={(atualizado) => setDados({ perfil: atualizado, areas })}
          />
        </div>

        <aside className="cartao coluna-lateral" aria-labelledby="titulo-meu-tcc">
          <h2 id="titulo-meu-tcc">Meu TCC</h2>
          {tcc ? (
            <div className="pilha-pequena">
              <div>
                <SeloSituacao status={tcc.status} />
              </div>
              <Link to={`/tccs/${tcc.id}`}>
                <strong>{tcc.titulo}</strong>
              </Link>
              <span className="campo-ajuda">Orientador: {tcc.orientador_nome}</span>
              <span className="campo-ajuda">{MODALIDADES[tcc.modalidade]}</span>
            </div>
          ) : (
            <p className="texto-suave">
              Você ainda não tem um TCC cadastrado. O cadastro é feito pelo orientador ou pela administração.
            </p>
          )}
        </aside>
      </div>
    </div>
  );
}
