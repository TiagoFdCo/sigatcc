import type { ReactNode } from "react";

type Tom = "erro" | "aviso" | "info" | "sucesso";

export function Alerta({ tom = "erro", children }: { tom?: Tom; children: ReactNode }) {
  return (
    <div className={`alerta alerta-${tom}`} role={tom === "erro" || tom === "aviso" ? "alert" : "status"}>
      {children}
    </div>
  );
}
