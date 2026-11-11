import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { ProvedorAuth, useAuth } from "./auth/AuthContext";
import { RotaProtegida } from "./auth/RotaProtegida";
import { Layout } from "./componentes/Layout";
import { BancaFormulario } from "./paginas/BancaFormulario";
import { Login } from "./paginas/Login";
import { NaoEncontrada } from "./paginas/NaoEncontrada";
import { PerfilAluno } from "./paginas/PerfilAluno";
import { TccDetalhe } from "./paginas/TccDetalhe";
import { TccFormulario } from "./paginas/TccFormulario";
import { TccLista } from "./paginas/TccLista";
import { rotaInicial } from "./util/rotas";

/** Pagina inicial depende do perfil: o aluno abre o proprio perfil (C2a). */
function Inicio() {
  const { usuario } = useAuth();
  return <Navigate to={rotaInicial(usuario?.tipo_usuario)} replace />;
}

export function App() {
  return (
    <ProvedorAuth>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<RotaProtegida />}>
            <Route element={<Layout />}>
              <Route index element={<Inicio />} />
              <Route path="/meu-perfil" element={<PerfilAluno />} />
              <Route path="/tccs" element={<TccLista />} />
              <Route path="/tccs/novo" element={<TccFormulario />} />
              <Route path="/tccs/:id" element={<TccDetalhe />} />
              <Route path="/tccs/:id/editar" element={<TccFormulario />} />
              <Route path="/tccs/:id/banca/nova" element={<BancaFormulario />} />
              <Route path="*" element={<NaoEncontrada />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </ProvedorAuth>
  );
}
