/* ============================================================
   Glossary — definizioni in italiano semplice
   Pensato per chi non ha background marketing/finance
   ============================================================ */

window.PROXIMA = window.PROXIMA || {};

window.PROXIMA.Glossary = function Glossary() {
  const [open, setOpen] = React.useState(false);

  const entries = [
    { group: "Clienti e crescita", items: [
      ["Clienti totali attivi", "Quante persone stanno pagando la parcella Proxima in quel mese."],
      ["Nuovi clienti", "Persone che sono diventate clienti paganti in quel mese specifico."],
      ["Clienti persi (churn)", "Clienti che hanno disdetto il servizio. In un servizio sano il churn mensile è tra 0,5% e 2%."],
      ["Capacità massima / Max gestibili", "Numero massimo di nuovi clienti gestibili con le ore disponibili."],
    ]},
    { group: "Funnel (il percorso del cliente)", items: [
      ["Click", "Persone che hanno cliccato su un annuncio pubblicitario."],
      ["Visite al sito", "Persone arrivate al sito tramite traffico gratuito (Google organico, social, ecc.)."],
      ["Calcolatore costi", "Tool gratuito sul sito che mostra quanto la persona paga alla banca. Principale punto di ingresso."],
      ["Prenotazione di check-up", "Persona che ha prenotato una consulenza iniziale gratuita."],
      ["Check-up fatto", "Consulenza iniziale effettivamente svolta (alcune persone prenotano e non si presentano)."],
      ["Cliente pagante", "Persona che, dopo il check-up, sottoscrive e paga la parcella annuale."],
    ]},
    { group: "Ricavi", items: [
      ["Parcella media (ARPU)", "Quanto paga in media un cliente all'anno. Default: €490."],
      ["Ricavi del mese (MRR)", "Quanto si fattura in quel mese. Clienti totali × parcella annua ÷ 12."],
      ["Ricavi annui (ARR)", "Quanto si fatturerebbe in un anno se tutti i clienti attuali continuassero."],
      ["Ricavi accumulati", "Totale fatturato dall'inizio della strategia."],
    ]},
    { group: "Costi", items: [
      ["Costi di costituzione", "Spese una tantum per aprire la società (notaio, OCF, avvocato, assicurazione, ecc.). Si concentrano nei primi 6-7 mesi."],
      ["Costi operativi", "Spese mensili ricorrenti per far funzionare l'azienda (commercialista, ufficio, software, ecc.)."],
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
      ["CAC (Costo Acquisizione Cliente)", "Quanto spendi in pubblicità per ottenere un cliente pagante. Calcolato per ogni canale separatamente."],
      ["SEO", "Traffico gratuito da Google. Cresce lentamente ma è composto."],
      ["Social organici", "Post gratuiti su IG/TikTok/LinkedIn. Costruiscono audience senza budget."],
      ["Passaparola (referral)", "Clienti esistenti che portano altri clienti."],
      ["PR / Podcast / Eventi (Borrowed)", "Apparizioni su giornali, podcast, conferenze."],
    ]},
    { group: "Gestione automatica", items: [
      ["Utilizzo capacità", "Percentuale delle ore disponibili già impegnate dai clienti attuali. Sopra l'85% il modello assume nuovi consulenti."],
      ["Budget ads %", "Quando la capacità è satura, il budget pubblicitario viene ridotto automaticamente per non sprecare soldi in lead che non puoi servire."],
      ["Assunzioni dinamiche", "Il modello assume nuovi consulenti, back-office, content creator e junior automaticamente quando i clienti superano le soglie impostate."],
    ]},
    { group: "Scenari di rischio", items: [
      ["Scenario base", "Crescita moderata dei mercati, condizioni favorevoli."],
      ["Scenario recessione", "Mercati in calo del 15-25%, clienti più cauti ma più bisognosi di consulenza."],
      ["Scenario crisi", "Crollo dei mercati del 30-50%, massima difficoltà ma anche massima domanda di consulenza indipendente."],
    ]},
    { group: "Fasi della strategia", items: [
      ["Fase 1 — Fondazione (M-12 / M-10)", "Costituzione SRL, notaio, pratiche OCF."],
      ["Fase 2 — Qualificazioni (M-9 / M-7)", "Esame OCF, compliance, assicurazione RC."],
      ["Fase 3 — Pre-lancio (M-6 / M-4)", "Sito web, calcolatore, primi contenuti, setup campagne."],
      ["Fase 4 — Alpha (M-3 / M-1)", "Test con 10-15 clienti, prime campagne, lista d'attesa."],
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
