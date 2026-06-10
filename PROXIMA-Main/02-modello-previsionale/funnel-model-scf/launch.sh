#!/bin/bash
cd "$(dirname "$0")"
echo "Avvio Proxima Funnel Model..."
python3 -m http.server 8000 &
SERVER_PID=$!
sleep 1
if command -v open &>/dev/null; then
  open http://localhost:8000
elif command -v xdg-open &>/dev/null; then
  xdg-open http://localhost:8000
else
  echo "Apri http://localhost:8000 nel browser"
fi
echo "Server attivo su http://localhost:8000 (PID $SERVER_PID)"
echo "Premi Ctrl+C per fermare."
wait $SERVER_PID
