import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { ProvedorAuth } from "./auth/AuthContext";
import { RotaProtegida } from "./auth/RotaProtegida";
import { Layout } from "./componentes/Layout";
import { BancaFormulario } from "./paginas/BancaFormulario";
import { Login } from "./paginas/Login";
import { NaoEncontrada } from "./paginas/NaoEncontrada";
import { TccDetalhe } from "./paginas/TccDetalhe";
import { TccFormulario } from "./paginas/TccFormulario";
import { TccLista } from "./paginas/TccLista";

export function App() {
  return (
    <ProvedorAuth>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<RotaProtegida />}>
            <Route element={<Layout />}>
              <Route index element={<Navigate to="/tccs" replace />} />
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
