#!/usr/bin/env bash
# ============================================================================
# Proxima Daily Briefing — Setup one-shot
# ============================================================================
# Crea la struttura di cartelle, installa dipendenze, copia esempi.
# Da eseguire UNA SOLA VOLTA.
#
# Uso: bash setup.sh
# ============================================================================

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Proxima Daily Briefing — Setup${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""

# --- 1. Check Python ---------------------------------------------------------
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 non trovato. Installalo prima.${NC}"
    exit 1
fi
PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo -e "${RED}Python 3.10+ richiesto (trovato $PY_VERSION).${NC}"
    exit 1
fi
echo -e "  ✓ Python $PY_VERSION"

# --- 2. Crea cartelle --------------------------------------------------------
PROXIMA_ROOT="${PROXIMA_ROOT:-$HOME/proxima}"
echo -e "  → Creo struttura in $PROXIMA_ROOT"
mkdir -p "$PROXIMA_ROOT"/{portafogli,briefings,logs,launch-strategy-180k}
mkdir -p "$PROXIMA_ROOT/data/screener_results"
echo -e "  ✓ Cartelle create"

# --- 3. Virtual env (raccomandato) -------------------------------------------
if [ ! -d "$PROXIMA_ROOT/.venv" ]; then
    echo -e "  → Creo virtualenv .venv"
    python3 -m venv "$PROXIMA_ROOT/.venv"
fi
# shellcheck disable=SC1091
source "$PROXIMA_ROOT/.venv/bin/activate"
echo -e "  ✓ Virtualenv attivo"

# --- 4. Install requirements -------------------------------------------------
echo -e "  → Installo dipendenze (può richiedere 1-2 minuti)..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo -e "  ✓ Dipendenze installate"

# --- 5. Copia file di lavoro -------------------------------------------------
CODE_DIR="$PROXIMA_ROOT/code"
mkdir -p "$CODE_DIR"
cp screener.py briefing_pipeline.py system_prompt.md newspaper_template.html requirements.txt "$CODE_DIR/"
echo -e "  ✓ Script copiati in $CODE_DIR"

# --- 6. Portafogli esempio ---------------------------------------------------
if [ ! -f "$PROXIMA_ROOT/portafogli/vale.csv" ]; then
    cp portafogli_examples/vale.csv "$PROXIMA_ROOT/portafogli/"
    echo -e "  ✓ Esempio vale.csv creato (DA EDITARE con le tue posizioni reali)"
fi
if [ ! -f "$PROXIMA_ROOT/portafogli/alex.csv" ]; then
    cp portafogli_examples/alex.csv "$PROXIMA_ROOT/portafogli/"
    echo -e "  ✓ Esempio alex.csv creato (DA EDITARE con le tue posizioni reali)"
fi

# --- 7. Check API key --------------------------------------------------------
echo ""
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    echo -e "${YELLOW}⚠  ANTHROPIC_API_KEY non impostata.${NC}"
    echo "   Aggiungi al tuo ~/.zshrc o ~/.bashrc:"
    echo -e "   ${GREEN}export ANTHROPIC_API_KEY='sk-ant-...'${NC}"
else
    echo -e "  ✓ ANTHROPIC_API_KEY impostata"
fi

# --- 8. Riepilogo finale -----------------------------------------------------
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Setup completato!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}PROSSIMI PASSI:${NC}"
echo ""
echo "1. Modifica i portafogli reali:"
echo -e "   ${GREEN}$EDITOR $PROXIMA_ROOT/portafogli/vale.csv${NC}"
echo -e "   ${GREEN}$EDITOR $PROXIMA_ROOT/portafogli/alex.csv${NC}"
echo ""
echo "2. (Opzionale) Carica il file delle azioni immediate:"
echo -e "   ${GREEN}cp 70-azioni-immediate.md $PROXIMA_ROOT/launch-strategy-180k/${NC}"
echo ""
echo "3. Test dry-run (senza chiamare l'API):"
echo -e "   ${GREEN}cd $CODE_DIR && python briefing_pipeline.py --user vale --dry-run${NC}"
echo ""
echo "4. Test reale (consuma ~€0.10 di API):"
echo -e "   ${GREEN}cd $CODE_DIR && python briefing_pipeline.py --user vale${NC}"
echo ""
echo "5. Quando funziona, aggiungi al cron (crontab -e):"
echo -e "   ${GREEN}30 6 * * * cd $CODE_DIR && $PROXIMA_ROOT/.venv/bin/python briefing_pipeline.py --user vale >> $PROXIMA_ROOT/logs/vale.log 2>&1${NC}"
echo -e "   ${GREEN}35 6 * * * cd $CODE_DIR && $PROXIMA_ROOT/.venv/bin/python briefing_pipeline.py --user alex >> $PROXIMA_ROOT/logs/alex.log 2>&1${NC}"
echo ""
echo -e "Output briefing salvati in: ${GREEN}$PROXIMA_ROOT/briefings/${NC}"
echo ""
