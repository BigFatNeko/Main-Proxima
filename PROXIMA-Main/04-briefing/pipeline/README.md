# Proxima MVF v3.0 — Stock Screener (v2, fully automated)

Pipeline daily completa per Proxima Briefing in Claude Code. **Zero file da fornire**, **zero touch human** dopo il setup iniziale.

---

## La nuova architettura

```
┌─────────────────────────────────────────────────┐
│  CRON 06:30 daily — Mac Mini / VPS sempre acceso│
└────────────────────┬────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────┐
│  briefing_pipeline.py --user vale               │
│                                                 │
│   1. screener.py                                │
│      auto-universe TradingView                  │  ←── nessun file input
│      → JSON con 30 candidati                    │
│                                                 │
│   2. legge portafogli locali (CSV)              │  ←── salvati una volta,
│      legge 70-azioni-immediate.md               │      mai più toccati
│      legge briefing precedenti                  │                       
│                                                 │
│   3. fetch market snapshot via yfinance         │
│      (S&P, FTSE MIB, Brent, EUR/USD, ...)       │
│                                                 │
│   4. call Claude API Sonnet 4.6                 │
│      (prompt caching: 90% sconto su contesto    │
│       stabile = ~€0.10/briefing)                │
│                                                 │
│   5. render HTML newspaper-style (Jinja2)       │
│      → ~/proxima/briefings/2026-MM-DD-vale.html │
│                                                 │
│   6. apre nel browser + notifica Telegram       │
└─────────────────────────────────────────────────┘
                     ▼
        Ti svegli, apri il browser, briefing pronto
```

**Zero interazione richiesta dopo setup iniziale**. Niente file da uploadare, niente CSV da passare, niente da copia-incollare.

---

## Cosa è cambiato vs v1

| v1 | v2 (questa) |
|---|---|
| Richiedeva `portafogli_alex_vale.txt` come watchlist | Universo auto-built da TradingView globale |
| Solo USA via finvizfinance | USA + Europa + Asia + Oceania (60+ mercati) |
| Output CSV/JSON da consumare manualmente | Integrato nella pipeline briefing |
| User-driven (manual run) | Cron-driven (06:30 automatico) |

---

## Setup iniziale (una sola volta)

```bash
# 1. Clona/crea cartella
mkdir -p ~/proxima && cd ~/proxima
git clone <questo-repo> code/

# 2. Dipendenze
cd code
pip install tradingview-screener yfinance pandas numpy jinja2 anthropic markdown requests

# 3. Crea portafogli locali (formato CSV, una sola volta)
mkdir -p ~/proxima/portafogli
cat > ~/proxima/portafogli/vale.csv <<EOF
ticker,shares,currency,acquired_at
INSW,5,USD,2025-08-15
ENI.MI,14,EUR,2025-03-12
MITT,37,USD,2025-09-01
... eccetera
CASH,988,EUR,
PAC,400,EUR,monthly
EOF

# 4. Env variables
export ANTHROPIC_API_KEY="sk-ant-..."
export BRIEFING_PORTFOLIO_DIR="~/proxima/portafogli"
export BRIEFING_OUTPUT_DIR="~/proxima/briefings"
export BRIEFING_TODO_FILE="~/proxima/launch-strategy-180k/70-azioni-immediate.md"

# Opzionale per Telegram:
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."

# 5. Test manuale (prima del cron)
python briefing_pipeline.py --user vale --mode daily

# 6. Cron job (crontab -e)
30 6 * * * cd ~/proxima/code && python briefing_pipeline.py --user vale >> ~/proxima/logs/vale.log 2>&1
35 6 * * * cd ~/proxima/code && python briefing_pipeline.py --user alex >> ~/proxima/logs/alex.log 2>&1
0  7 * * 6 cd ~/proxima/code && python briefing_pipeline.py --user vale --mode weekend
```

Dopo questo setup, ogni mattina alle 06:30 il briefing viene generato in automatico. Tu apri l'app, il file è già lì.

---

## Stack tecnico

| Layer | Tool | Costo | Note |
|---|---|---|---|
| Universe building globale | `tradingview-screener` | Gratis | 60+ mercati, no API key |
| Universe US fallback | `finvizfinance` | Gratis | Solo se TV fallisce |
| Fondamentali profondi | `yfinance` | Gratis | Per le 24 metriche MVF |
| Real-time market data | `yfinance` | Gratis | Per il market snapshot |
| LLM generation | Claude Sonnet 4.6 | ~€0.10/briefing | Con prompt caching attivo |
| Template HTML | Jinja2 | Gratis | Newspaper-style fisso |
| Delivery | webbrowser + Telegram | Gratis | Opzionali |

**Costo totale stimato**: ~€6-12/mese per 2 utenti × daily briefing.

---

## Mapping con il prompt MVF v3.0

### Sezione 3B — 24 metriche del valore intrinseco

| Metrica MVF | In Python? | Note |
|---|:---:|---|
| Gross Margin | ✅ | da financials |
| EBITDA Margin | ✅ | da financials |
| Operating Margin | ✅ | da financials |
| Net Margin | ✅ | da financials |
| FCF Margin | ✅ | da cashflow |
| ROIC | ✅ | NOPAT/(Equity+Debt), approssimato |
| ROE | ✅ | da info |
| ROA | ✅ | da info |
| D/E | ✅ | da balance sheet |
| D/A | ✅ | da balance sheet |
| Altman-Z | ✅ | 5-factor classico (skip banche/REIT) |
| SBC/Revenue | ✅ | da cashflow |
| CapEx/Revenue | ✅ | da cashflow |
| CapEx/D&A | ✅ | da cashflow |
| R&D/Revenue | ✅ | da financials |
| Insider Trading | ❌ | richiede SEC Form 4, fragile |
| Dividend Yield | ✅ | da info |
| Payout Ratio | ✅ | da info |
| Dividend Growth 5y | ✅ | CAGR da serie storica |
| Buyback Yield | ✅ | da delta shares outstanding (proxy) |
| Price CAGR | ✅ | da history 5y |
| Tax Rate | ✅ | Tax Provision / Pretax Income |
| MOAT Economico | ❌ | esclusivo Morningstar, qualitativo |
| Earnings Quality | ✅ | Accruals Ratio + CCR |

### Sezione 8 — Red flag automatici

Tutti i red flag **quantitativi** sono codificati. Esclusi solo quelli qualitativi (auditor change, CFO turnover, pension underfunding, insider selling non motivato).

### Sezioni 7, 9, 10 — Valutazione

Restano a Claude in seconda passata sui top candidati dello screener. Il Python fa il setaccio iniziale, Claude fa l'analisi MVF completa solo sui ~5-10 più promettenti.

---

## Risparmio token reale (stima)

```
Briefing daily senza screener:
  Claude deve "cercare candidati" via web_search       → ~20 tool calls
  + analizzare grosse pagine                            → ~50k input token
  + ragionamento qualitativo                            → ~8k output token
  Costo: ~€0.50/briefing × 2 utenti × 30 giorni = €30/mese

Briefing daily CON screener:
  Python ha già fatto il lavoro quantitativo
  Claude riceve 30 candidati pre-filtrati come tabella  → ~5k input token (cached)
  + ragionamento qualitativo solo sui top 3-5           → ~5k output token
  Costo: ~€0.10/briefing × 2 utenti × 30 giorni = €6/mese

Risparmio: 80%+
```

---

## File del repo

```
proxima_screener/
├── screener.py             ← MVF filters + auto-universe TradingView
├── briefing_pipeline.py    ← Orchestratore end-to-end
├── README.md               ← Questo file
└── (template HTML Jinja2)  ← Da aggiungere quando il widget definitivo è OK
```

---

## Differenza claude.ai (oggi) vs Claude Code (target)

| Cosa | claude.ai | Claude Code |
|---|---|---|
| Trigger | "Buongiorno, sono Vale." nel chat | Cron 06:30 (zero touch) |
| Universe | qualitativo via web_search | quantitativo via TradingView |
| Fondamentali | web_search su singole news | yfinance batch su 30 ticker |
| Output | inline chat (widget HTML) | file HTML + Telegram |
| Costo | incluso nell'abbonamento Claude | ~€6-12/mese API |
| Latenza | 30-60 sec | tutto pronto al risveglio |

**Migrazione consigliata**: 2-3 settimane in claude.ai per stabilizzare prompt e template, poi un sabato di setup per spostare tutto in Claude Code.

---

## Punti aperti (da definire prima di andare in produzione)

1. **Template HTML Jinja2 newspaper**: lo costruiamo a partire dal widget HTML che abbiamo iterato. Non in questo deliverable.
2. **Portafogli locali CSV**: formato fisso (`ticker,shares,currency,acquired_at`). Posso aiutare a popolarli partendo dagli screenshot del broker.
3. **70-azioni-immediate.md**: quando lo carichi, lo metti in `~/proxima/launch-strategy-180k/` e il pipeline lo legge in automatico.
4. **TradingView ticker mapping**: ho coperto 25 exchange. Se trovate un titolo che non viene mappato (log dice "skipped"), aggiungiamo il prefix.
