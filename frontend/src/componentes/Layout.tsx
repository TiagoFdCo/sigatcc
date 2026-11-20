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

// Mesma regra do backend (PainelDeGestao): aluno e membro externo nao veem os indicadores.
const PERFIS_DO_PAINEL: string[] = ["DOCENTE", "SECRETARIA", "ADMINISTRADOR"];

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
            {usuario?.tipo_usuario === "ALUNO" ? (
              <NavLink to="/meu-perfil" className="menu-item">
                Meu perfil
              </NavLink>
            ) : (
              <NavLink to="/tccs" className="menu-item">
                TCCs
              </NavLink>
            )}
            {usuario && PERFIS_DO_PAINEL.includes(usuario.tipo_usuario) && (
              <NavLink to="/indicadores" className="menu-item">
                Indicadores
              </NavLink>
            )}
            {usuario?.tipo_usuario === "ALUNO" && (
              <NavLink to="/orientadores" className="menu-item">
                Buscar orientador
              </NavLink>
            )}
            {(usuario?.tipo_usuario === "ALUNO" || usuario?.tipo_usuario === "DOCENTE") && (
              <>
                <NavLink to="/solicitacoes" className="menu-item">
                  Solicitações
                </NavLink>
                <NavLink to="/convites" className="menu-item">
                  Convites
                </NavLink>
              </>
            )}
            {usuario?.tipo_usuario === "ADMINISTRADOR" && (
              <NavLink to="/auditoria" className="menu-item">
                Auditoria
              </NavLink>
            )}
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
