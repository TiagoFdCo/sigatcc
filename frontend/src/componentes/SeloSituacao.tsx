import type { StatusTcc } from "../api/tipos";
import { STATUS } from "../util/rotulos";

/** Selo com texto e cor (a cor nunca e a unica pista: RNF01). */
export function SeloSituacao({ status }: { status: StatusTcc }) {
  return <span className={`selo selo-${status.toLowerCase()}`}>{STATUS[status]}</span>;
}
