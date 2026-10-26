import { useState, type ChangeEvent, type FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { ErroApi } from "../api/cliente";
import { useAuth } from "../auth/AuthContext";
import { Alerta } from "../componentes/Alerta";
import { Logo } from "../componentes/Logo";

function horaDoDesbloqueio(dados: unknown): string | null {
  const ate = (dados as { bloqueado_ate?: string } | null)?.bloqueado_ate;
  if (!ate) return null;
  return new Date(ate).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

/** B9a: login do docente, secretaria e administrador (RBN29). */
export function Login() {
  const { usuario, entrar } = useAuth();
  const navegar = useNavigate();
  const local = useLocation();
  const destino = (local.state as { de?: string } | null)?.de ?? "/";

  const [login, setLogin] = useState("");
  const [senha, setSenha] = useState("");
  const [senhaVisivel, setSenhaVisivel] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<{ tom: "erro" | "aviso"; texto: string } | null>(null);

  if (usuario) return <Navigate to={destino} replace />;

  async function aoEnviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      await entrar(login.trim(), senha);
      navegar(destino, { replace: true });
    } catch (e) {
      if (e instanceof ErroApi && e.status === 423) {
        const hora = horaDoDesbloqueio(e.dados);
        setErro({
          tom: "aviso",
          texto: `Conta bloqueada por 15 minutos após 5 tentativas sem sucesso.${hora ? ` Tente de novo às ${hora}.` : ""}`,
        });
      } else {
        setErro({ tom: "erro", texto: e instanceof Error ? e.message : "Não foi possível entrar." });
      }
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="login">
      <section className="login-painel">
        <div className="login-marca">
          <Logo cor="#FFFFFF" tamanho={36} />
          <span>SIGATCC</span>
        </div>
        <div className="login-chamada">
          <h1>Gestão acadêmica de TCC do NUCOMP</h1>
          <p>
            Cadastro de trabalhos, situação, bancas e orientação para Engenharia de Computação, Sistemas de
            Informação e Licenciatura em Computação.
          </p>
        </div>
        <p className="login-rodape">NUCOMP · Universidade do Estado do Amazonas</p>
      </section>

      <main className="login-area">
        <form className="login-cartao" onSubmit={aoEnviar} noValidate>
          <div className="pilha-pequena">
            <h2>Entrar</h2>
            <p className="texto-suave">Acesso para docentes, secretaria e administração.</p>
          </div>

          {erro && <Alerta tom={erro.tom}>{erro.texto}</Alerta>}

          <div className="campo">
            <label htmlFor="login">E-mail institucional ou matrícula</label>
            <input
              id="login"
              type="text"
              autoComplete="username"
              placeholder="nome@uea.edu.br"
              value={login}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setLogin(e.target.value)}
              required
            />
          </div>

          <div className="campo">
            <div className="campo-topo">
              <label htmlFor="senha">Senha</label>
              <button type="button" className="link-botao" onClick={() => setSenhaVisivel((v) => !v)}>
                {senhaVisivel ? "Ocultar" : "Mostrar"}
              </button>
            </div>
            <input
              id="senha"
              type={senhaVisivel ? "text" : "password"}
              autoComplete="current-password"
              value={senha}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setSenha(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="botao botao-largo" disabled={enviando || !login || !senha}>
            {enviando ? "Entrando…" : "Entrar"}
          </button>
        </form>
      </main>
    </div>
  );
}
