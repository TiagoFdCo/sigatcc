import { Link } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

export function Inicio() {
  const { usuario } = useAuth();
  return (
    <div className="pilha">
      <h1>Olá, {usuario?.nome_completo.split(" ")[0]}</h1>
      <p className="texto-suave">Escolha por onde começar.</p>
      <div>
        <Link to="/tccs" className="botao">
          Ver TCCs
        </Link>
      </div>
    </div>
  );
}
