/* ============================================================
   Glossary SCF — definizioni in italiano semplice
   Pensato per chi non ha background marketing/finance
   ============================================================ */

window.PROXIMA = window.PROXIMA || {};

window.PROXIMA.Glossary = function Glossary() {
  const [open, setOpen] = React.useState(false);

  const entries = [
    { group: "L'offerta a fasce (decisione 10/06/2026)", items: [
      ["Check-up (gratuito)", "Report personalizzato generato via IA: la fotografia dei propri risparmi. È il punto d'ingresso del funnel: gratuito, digitale, senza appuntamento."],
      ["Fascia App (€1-5/mese)", "Abbonamento base: insights, personalizzazione, educazione finanziaria dentro l'app."],
      ["Fascia Monitor (€5-20/mese)", "Revisione e monitoraggio periodico del portafoglio reale del cliente, con raccomandazioni. Decide sempre il cliente: la SCF non gestisce."],
      ["Fascia Live (€50-150/mese)", "Consulenza approfondita con call dedicate. È l'unica fascia vincolata dalle ore del team."],
      ["Mix dei nuovi abbonati", "Come si ripartiscono i nuovi paganti tra le tre fasce. La % Live è derivata: 100% − App − Monitor."],
    ]},
    { group: "Clienti e crescita", items: [
      ["Utenti gratuiti", "Persone che hanno fatto il Check-up ma non si sono (ancora) abbonate. Sono il serbatoio da cui arrivano abbonati nel tempo."],
      ["Abbonati attivi", "Persone che stanno pagando un abbonamento Proxima in quel mese, su qualsiasi fascia."],
      ["Clienti assistiti", "Abbonati Monitor + Live: quelli che richiedono lavoro umano ricorrente. Le assunzioni a soglia scattano su questo numero."],
      ["Nuovi abbonati", "Persone che si sono abbonate in quel mese: una parte dai nuovi Check-up, una parte dalla base gratuita accumulata."],
      ["Persi (churn)", "Abbonati che disdicono. Ogni fascia ha il suo tasso: l'App ha churn alto (è economica), il Live basso (relazione forte)."],
    ]},
    { group: "Funnel (il percorso del cliente)", items: [
      ["Click", "Persone che hanno cliccato su un annuncio pubblicitario."],
      ["Visite al sito", "Persone arrivate al sito tramite traffico gratuito (Google organico, social, ecc.)."],
      ["Pagina Check-up", "La pagina del sito che propone il report gratuito. Principale punto di ingresso."],
      ["Iscrizione al Check-up", "Persona che lascia i propri dati e riceve il report IA gratuito. Diventa utente gratuito."],
      ["% Check-up → abbonati", "Quanti nuovi utenti del Check-up si abbonano nello stesso mese. È la leva più sensibile del modello: da validare sul campo."],
    ]},
    { group: "Ricavi", items: [
      ["Ricavi del mese (MRR)", "Somma degli abbonamenti del mese: App×prezzo + Monitor×prezzo + Live×prezzo."],
      ["Ricavi annui (ARR)", "MRR × 12: quanto si fatturerebbe in un anno se tutti gli abbonati attuali continuassero."],
      ["ARPU blended", "Ricavo medio annuo per abbonato, dato dal mix delle fasce. Con i default è molto più basso della vecchia parcella €490: servono molti più clienti."],
      ["Ricavi accumulati", "Totale fatturato dall'inizio della strategia."],
    ]},
    { group: "Costi", items: [
      ["Costi di costituzione", "Spese una tantum per aprire la società (notaio, OCF, avvocato, assicurazione, sviluppo app, ecc.). Si concentrano nei primi 9 mesi."],
      ["Costi operativi", "Spese mensili ricorrenti per far funzionare l'azienda (commercialista, ufficio, software, ecc.)."],
      ["Costi app e IA", "Hosting dell'app + costo IA per ogni report Check-up generato. Crescono con gli utenti gratuiti: il gratis non è gratis per noi."],
      ["Costi del personale", "Compensi dei fondatori, stipendi di dipendenti e collaboratori."],
      ["Costi di marketing", "Budget pubblicitario speso su Google, Meta, LinkedIn Ads."],
      ["Costi totali", "Somma di tutti i costi del mese."],
    ]},
    { group: "Cash flow", items: [
      ["Cash rimanente", "Quanto resta dei €180.000 iniziali dopo aver pagato tutti i costi e ricevuto i ricavi. Se arriva a zero, l'azienda non può più operare."],
      ["Burn netto", "Quanto si \"brucia\" ogni mese. Burn = costi totali − ricavi. Se positivo, si stanno perdendo soldi. Se negativo, si sta guadagnando."],
      ["Pareggio operativo (break-even operativo)", "Il mese in cui i ricavi mensili coprono i costi mensili. Da quel mese in poi l'azienda si autosostiene."],
      ["Pareggio investimento (break-even cumulato)", "Il mese in cui i ricavi totali accumulati superano i costi totali accumulati. L'investimento iniziale è ripagato."],
      ["Riserva minima", "Il punto più basso che il cash raggiunge. Se scende sotto €15.000-30.000, è critico."],
    ]},
    { group: "Canali di acquisizione", items: [
      ["Google Ads / Meta Ads / LinkedIn Ads", "Pubblicità a pagamento. Porta traffico ma costa."],
      ["CAC (Costo Acquisizione Cliente)", "Quanto spendi in pubblicità per ottenere un abbonato pagante. Va confrontato col valore della fascia: un CAC da €80 è ottimo per un Live, insostenibile per un App."],
      ["SEO", "Traffico gratuito da Google. Cresce lentamente ma è composto."],
      ["Social organici", "Post gratuiti su IG/TikTok/LinkedIn. Costruiscono audience senza budget."],
      ["Passaparola (referral)", "Abbonati esistenti che portano altre persone al Check-up."],
      ["PR / Podcast / Eventi (Borrowed)", "Apparizioni su giornali, podcast, conferenze."],
    ]},
    { group: "Capacità e gestione automatica", items: [
      ["Slot Live %", "Percentuale delle ore disponibili per onboarding di nuovi clienti Live già occupate dalla domanda. Solo la fascia Live consuma ore del team: App e Monitor scalano col software."],
      ["Budget ads %", "Quando gli slot Live sono saturi (>85%), il budget pubblicitario viene ridotto automaticamente per non sprecare soldi in domanda che non puoi servire."],
      ["Assunzioni dinamiche", "Il modello assume consulenti quando gli slot Live superano l'85%, e back-office, content creator e junior quando i clienti assistiti superano le soglie impostate."],
      ["AUM monitorato", "Patrimonio complessivo dei clienti Monitor+Live. Non genera ricavi (la SCF incassa solo abbonamenti): è un KPI di credibilità e responsabilità."],
    ]},
    { group: "Scenari di rischio", items: [
      ["Scenario base", "Crescita moderata dei mercati, condizioni favorevoli."],
      ["Scenario recessione", "Mercati in calo del 15-25%, clienti più cauti ma più bisognosi di consulenza."],
      ["Scenario crisi", "Crollo dei mercati del 30-50%, massima difficoltà ma anche massima domanda di consulenza indipendente."],
    ]},
    { group: "Fasi della strategia", items: [
      ["Fase 1 — Fondazione (M-12 / M-10)", "Costituzione SRL, notaio, pratiche OCF."],
      ["Fase 2 — Qualificazioni (M-9 / M-7)", "Esame OCF, compliance, assicurazione RC. Parte lo sviluppo dell'app."],
      ["Fase 3 — Pre-lancio (M-6 / M-4)", "Sito web, pagina Check-up, primi contenuti, setup campagne."],
      ["Fase 4 — Alpha (M-3 / M-1)", "Test del Check-up con i primi utenti, lista d'attesa."],
      ["Fase 5 — Beta (M0 / M+2)", "Lancio pubblico, prime campagne paid."],
      ["Fase 6 — Early Access (M+3 / M+5)", "Scaling, pubblicità a pieno regime."],
      ["Fase 7 — Lancio Pubblico (dal M+6)", "Tutti i canali attivi, scaling aggressivo."],
    ]},
    { group: "Agenti di marketing", items: [
      ["Agenti attivi", "Quanti dei 35 ruoli/workflow di marketing sono operativi in quel mese. Si attivano progressivamente: 10 in Fase 1, fino a 35 in Fase 6+."],
    ]},
  ];

  return (
    <div className="section">
      <div className="panel" style={{ marginBottom: 0 }}>
        <div className="panel-header" onClick={() => setOpen(!open)}>
          <h3>📖 Glossario — cosa significano i termini usati</h3>
          <span className="chev">{open ? "▼" : "▶"}</span>
        </div>
        {open && (
          <div className="panel-body" style={{ padding: "16px 20px" }}>
            <div style={{ display: "grid", gap: 20 }}>
              {entries.map((g) => (
                <div key={g.group}>
                  <div className="uppercase gold" style={{ marginBottom: 8 }}>
                    {g.group}
                  </div>
                  <div style={{ display: "grid", gap: 8 }}>
                    {g.items.map(([term, def]) => (
                      <div key={term} style={{ display: "grid", gridTemplateColumns: "220px 1fr", gap: 12, alignItems: "baseline" }}>
                        <div style={{ fontWeight: 600, fontSize: 13, color: "var(--text)" }}>
                          {term}
                        </div>
                        <div className="text-dim" style={{ fontSize: 13, lineHeight: 1.5 }}>
                          {def}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
