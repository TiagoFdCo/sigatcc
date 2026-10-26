export function Logo({ cor = "currentColor", tamanho = 28 }: { cor?: string; tamanho?: number }) {
  return (
    <svg width={tamanho} height={tamanho} viewBox="0 0 36 36" fill="none" aria-hidden="true">
      <rect x="1" y="1" width="34" height="34" rx="8" stroke={cor} strokeWidth="2.5" />
      <path d="M10 13h16M10 18h16M10 23h10" stroke={cor} strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}
