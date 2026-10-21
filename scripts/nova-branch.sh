#!/usr/bin/env bash
# Cria uma branch no padrao feature/<ID-da-EAP>-<descricao>
# Uso: ./scripts/nova-branch.sh B5 login-docente

set -euo pipefail

if [ $# -ne 2 ]; then
  echo "Uso: $0 <ID-da-EAP> <descricao-curta-sem-espacos>"
  echo "Exemplo: $0 B5 login-docente"
  exit 1
fi

ID="$1"
DESCRICAO="$2"

git checkout main
git pull origin main
git checkout -b "feature/${ID}-${DESCRICAO}"

echo "Branch feature/${ID}-${DESCRICAO} criada a partir da main atualizada."
