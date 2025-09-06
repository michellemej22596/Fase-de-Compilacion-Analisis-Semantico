#!/usr/bin/env bash
set -euo pipefail

ok=0; bad=0
status=0

# Habilitar que los globs vacíos NO pasen como texto literal
shopt -s nullglob

# --- OK ---
ok_files=(tests/ok/*.cps)
if ((${#ok_files[@]}==0)); then
  echo "No hay tests en tests/ok/*.cps"
else
  for f in "${ok_files[@]}"; do
    if python Driver.py "$f" >/dev/null 2>&1; then
      ok=$((ok+1))
    else
      echo "Falló (debería pasar): $f"
      status=1
    fi
  done
fi

# --- BAD ---
bad_files=(tests/bad/*.cps)
if ((${#bad_files[@]}==0)); then
  echo "No hay tests en tests/bad/*.cps"
else
  for f in "${bad_files[@]}"; do
    if python Driver.py "$f" >/dev/null 2>&1; then
      echo "No falló (debería fallar): $f"
      status=1
    else
      bad=$((bad+1))
    fi
  done
fi

echo "Sintaxis OK: $ok  |  Errores detectados: $bad"
exit $status
