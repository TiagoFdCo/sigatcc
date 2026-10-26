import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "./AuthContext";

/** Sem sessao, manda para o login e volta para a pagina pedida depois. */
export function RotaProtegida() {
  const { usuario, carregando } = useAuth();
  const local = useLocation();

  if (carregando) {
    return (
      <p className="carregando" role="status">
        Carregando…
      </p>
    );
  }
  if (!usuario) {
    return <Navigate to="/login" replace state={{ de: local.pathname + local.search }} />;
  }
  return <Outlet />;
}
