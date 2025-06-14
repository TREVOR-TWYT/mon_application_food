#!/bin/sh

# Script pour attendre que Postgres soit prêt
set -e

host="$1"
shift
cmd="$@"

until pg_isready -h "$host" -p 5432 > /dev/null 2>&1; do
  >&2 echo "Postgres n'est pas encore prêt - attente..."
  sleep 2
done

>&2 echo "Postgres est prêt !"
exec $cmd
