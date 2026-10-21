#!/usr/bin/env bash
# B4: gera a migration inicial (0001) a partir dos models, instala as migrations
# 0002 (cursos) e 0003 (logs so de acrescimo) e aplica tudo no banco local.
# Uso (na raiz do repositorio): ./scripts/b4-migrations.sh
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "Crie o .env antes: cp .env.example .env"
  exit 1
fi

docker compose up -d db

if ls backend/core/migrations/0001_*.py >/dev/null 2>&1; then
  echo "0001 ja existe; pulando makemigrations."
else
  docker compose run --rm backend python manage.py makemigrations core
fi

# Copia sem sobrescrever o que ja existe
cp -n backend/core/migrations_extra/*.py backend/core/migrations/

docker compose run --rm backend python manage.py migrate
echo "Pronto. Confira com: docker compose exec db psql -U \$DB_USER -d \$DB_NAME -c '\\dt'"
