import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { ProvedorAuth } from "./auth/AuthContext";
import { RotaProtegida } from "./auth/RotaProtegida";
import { Layout } from "./componentes/Layout";
import { BancaFormulario } from "./paginas/BancaFormulario";
import { BuscarOrientador } from "./paginas/BuscarOrientador";
import { Convites } from "./paginas/Convites";
import { Login } from "./paginas/Login";
import { NaoEncontrada } from "./paginas/NaoEncontrada";
import { ResponderConvite } from "./paginas/ResponderConvite";
import { Solicitacoes } from "./paginas/Solicitacoes";
import { TccDetalhe } from "./paginas/TccDetalhe";
import { TccFormulario } from "./paginas/TccFormulario";
import { TccLista } from "./paginas/TccLista";

export function App() {
  return (
    <ProvedorAuth>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          {/* C6: rota publica do link do convite (o membro externo nao tem login) */}
          <Route path="/convites/responder" element={<ResponderConvite />} />
          <Route element={<RotaProtegida />}>
            <Route element={<Layout />}>
              <Route index element={<Navigate to="/tccs" replace />} />
              <Route path="/tccs" element={<TccLista />} />
              <Route path="/tccs/novo" element={<TccFormulario />} />
              <Route path="/tccs/:id" element={<TccDetalhe />} />
              <Route path="/tccs/:id/editar" element={<TccFormulario />} />
              <Route path="/tccs/:id/banca/nova" element={<BancaFormulario />} />
              <Route path="/orientadores" element={<BuscarOrientador />} />
              <Route path="/solicitacoes" element={<Solicitacoes />} />
              <Route path="/convites" element={<Convites />} />
              <Route path="*" element={<NaoEncontrada />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </ProvedorAuth>
  );
}
