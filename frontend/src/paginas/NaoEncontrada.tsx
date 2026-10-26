import { Link } from "react-router-dom";

export function NaoEncontrada() {
  return (
    <div className="pilha">
      <h1>Página não encontrada</h1>
      <p className="texto-suave">O endereço não existe ou você não tem acesso a ele.</p>
      <div>
        <Link to="/" className="botao botao-secundario">
          Voltar ao início
        </Link>
      </div>
    </div>
  );
}
