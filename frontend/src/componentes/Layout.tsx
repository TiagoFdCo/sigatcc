import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import { Logo } from "./Logo";

const PERFIS: Record<string, string> = {
  ADMINISTRADOR: "Administrador",
  DOCENTE: "Docente",
  SECRETARIA: "Secretaria de Curso",
  ALUNO: "Aluno",
  MEMBRO_EXTERNO: "Membro externo",
};

export function Layout() {
  const { usuario, sair } = useAuth();
  const navegar = useNavigate();

  const perfil = usuario?.professor_tcc
    ? "Professor de TCC"
    : (PERFIS[usuario?.tipo_usuario ?? ""] ?? "");

  async function aoSair() {
    await sair();
    navegar("/login", { replace: true });
  }

  return (
    <div className="app">
      <header className="topo">
        <div className="topo-conteudo">
          <NavLink to="/" className="marca">
            <Logo />
            SIGATCC
          </NavLink>
          <nav aria-label="Principal" className="menu">
            <NavLink to="/tccs" className="menu-item">
              TCCs
            </NavLink>
          </nav>
          <div className="usuario">
            <span>
              {usuario?.nome_completo} · {perfil}
            </span>
            <button type="button" className="link-botao" onClick={aoSair}>
              Sair
            </button>
          </div>
        </div>
      </header>
      <main className="conteudo">
        <Outlet />
      </main>
    </div>
  );
}
