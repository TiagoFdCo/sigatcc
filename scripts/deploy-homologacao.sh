#!/usr/bin/env bash
# Publica a branch escolhida no servidor de homologacao (B11).
# Rode NO DROPLET, dentro da pasta do repositorio, com o .env de homologacao pronto.
#
# Uso: ./scripts/deploy-homologacao.sh [branch] [--demo]
#   branch   padrao: main
#   --demo   cria os dados de demonstracao (python manage.py popular_demo)

set -euo pipefail

BRANCH="main"
DEMO="nao"
for arg in "$@"; do
  case "$arg" in
    --demo) DEMO="sim" ;;
    *) BRANCH="$arg" ;;
  esac
done

if [ ! -f .env ]; then
  echo "Falta o arquivo .env (copie de .env.example e preencha a parte de homologacao)."
  exit 1
fi

# shellcheck disable=SC1091
set -a; . ./.env; set +a
for var in DJANGO_SECRET_KEY JWT_SIGNING_KEY DB_PASSWORD API_HOST APP_HOST ACME_EMAIL VITE_API_URL; do
  if [ -z "${!var:-}" ]; then
    echo "Variavel $var vazia no .env."
    exit 1
  fi
done
if [ "${DJANGO_DEBUG:-False}" != "False" ]; then
  echo "Em homologacao use DJANGO_DEBUG=False no .env."
  exit 1
fi

COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.homolog.yml --profile frontend)

echo "==> Atualizando o codigo ($BRANCH)"
git fetch origin
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

echo "==> Build das imagens"
"${COMPOSE[@]}" build

echo "==> Banco e migrations"
"${COMPOSE[@]}" up -d db
"${COMPOSE[@]}" run --rm backend python manage.py migrate --noinput

if [ "$DEMO" = "sim" ]; then
  echo "==> Dados de demonstracao"
  "${COMPOSE[@]}" run --rm backend python manage.py popular_demo
fi

echo "==> Subindo API, frontend e proxy"
"${COMPOSE[@]}" up -d --remove-orphans backend frontend caddy

echo "==> Conferindo a API"
for tentativa in 1 2 3 4 5 6; do
  if "${COMPOSE[@]}" exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/saude/')" 2>/dev/null; then
    echo "API no ar. Acesse https://$APP_HOST"
    exit 0
  fi
  echo "Aguardando a API ($tentativa/6)..."
  sleep 5
done
echo "A API nao respondeu. Veja: ${COMPOSE[*]} logs backend"
exit 1
