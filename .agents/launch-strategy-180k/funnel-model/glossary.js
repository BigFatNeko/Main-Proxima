/* ============================================================
   Glossary — definizioni in italiano semplice
   Pensato per chi non ha background marketing/finance
   ============================================================ */

window.PROXIMA = window.PROXIMA || {};

window.PROXIMA.Glossary = function Glossary() {
  const [open, setOpen] = React.useState(false);

  const entries = [
    {
      group: "Clienti e crescita",
      items: [
        ["Clienti totali attivi",
         "Quante persone stanno pagando la parcella Proxima in quel mese."],
        ["Nuovi clienti",
         "Persone che sono diventate clienti paganti in quel mese specifico."],
        ["Clienti persi (churn)",
         "Clienti che hanno disdetto il servizio in quel mese. In un servizio sano il churn mensile è tra 0,5% e 2%."],
        ["Capacità massima / Max gestibili",
         "Il numero massimo di nuovi clienti che il team riesce a seguire con le ore di lavoro disponibili. Se la domanda supera questo numero, si perdono opportunità."],
      ]
    },
    {
      group: "Funnel (il percorso del cliente)",
      items: [
        ["Click",
         "Persone che hanno cliccato su un annuncio pubblicitario."],
        ["Visite al sito",
         "Persone che sono arrivate al sito tramite traffico gratuito (Google organico, social, ecc.)."],
        ["Calcolatore costi",
         "Tool gratuito sul sito che mostra quanto la persona paga alla banca. È il principale punto di ingresso — se una persona lo usa, è molto più probabile che prenoti una consulenza."],
        ["Prenotazione di check-up",
         "Persona che ha prenotato una consulenza iniziale gratuita (il 'check-up finanziario')."],
        ["Check-up fatto",
         "Consulenza iniziale effettivamente svolta (alcune persone prenotano e poi non si presentano)."],
        ["Cliente pagante",
         "Persona che, dopo il check-up, sottoscrive e paga la parcella annuale."],
      ]
    },
    {
      group: "Ricavi",
      items: [
        ["Parcella media (ARPU)",
         "Quanto paga in media un cliente all'anno. Default Proxima: €490. Deriva dal mix di fasce di patrimonio (€250–€1.200/anno)."],
        ["Ricavi del mese (MRR)",
         "Quanto si fattura in quel singolo mese. Pari a: clienti totali × parcella annua ÷ 12."],
        ["Ricavi annui (ARR)",
         "Quanto si fatturerebbe in un anno se tutti i clienti attuali continuassero a pagare. Pari a: clienti totali × parcella annua."],
        ["Ricavi accumulati",
         "Totale di tutto quello che si è fatturato dall'inizio della strategia, mese dopo mese."],
        ["Mese di pareggio (break-even)",
         "Il primo mese in cui i ricavi accumulati superano i €180.000 investiti. È il momento in cui l'investimento iniziale è ripagato."],
      ]
    },
    {
      group: "Costi e acquisizione",
      items: [
        ["Costo per click (CPC)",
         "Quanto si paga Google, Meta o LinkedIn per ogni click sull'annuncio. Varia per canale: Google ~€1,80 · Meta ~€0,90 · LinkedIn ~€6."],
        ["Costo per acquisire 1 cliente (CAC)",
         "Quanto è costato in media ottenere un nuovo cliente pagante, considerando tutta la spesa pubblicitaria. Formula: spesa totale ÷ clienti acquisiti dal paid. Target Proxima: sotto €100."],
        ["Spesa accumulata",
         "Totale di tutto quello che è stato speso dall'inizio (pubblicità + costi fissi operativi)."],
      ]
    },
    {
      group: "Canali di acquisizione",
      items: [
        ["Google Ads / Meta Ads / LinkedIn Ads",
         "Pubblicità a pagamento. Paghi per ogni click. Porta traffico rapidamente ma costa."],
        ["SEO",
         "Traffico gratuito da Google (articoli del blog, pagine ottimizzate). Cresce lentamente ma è gratis e composto: ogni mese porta più del precedente."],
        ["Social organici",
         "Post gratuiti su Instagram, TikTok, LinkedIn. Costruiscono audience nel tempo senza budget."],
        ["Passaparola (referral)",
         "Clienti esistenti che portano amici/conoscenti. Parte dal 9° mese (serve tempo prima di avere clienti soddisfatti che parlino di noi)."],
        ["PR / Podcast / Eventi (Borrowed)",
         "Apparizioni su giornali, podcast, conferenze. Porta credibilità e visibilità grazie ad audience già costruite da altri."],
      ]
    },
    {
      group: "Fasi della strategia",
      items: [
        ["Fase 1 — Pre-lancio (mesi -6 a -4)",
         "Preparazione: sito, calcolatore, albo OCF, primi contenuti. Zero clienti."],
        ["Fase 2 — Alpha (mesi -3 a -1)",
         "Test con 10-15 clienti early adopter scontati del 20%, zero pubblicità a pagamento."],
        ["Fase 3 — Beta (mesi 0 a +2)",
         "Lista d'attesa pubblica, prime campagne paid in soft launch."],
        ["Fase 4 — Early Access (mesi +3 a +5)",
         "Apertura progressiva, pubblicità a pieno regime, PR pre-lancio."],
        ["Fase 5 — Lancio Pubblico (dal mese +6)",
         "Servizio aperto a tutti, scaling aggressivo, introduzione di LinkedIn Ads e passaparola."],
      ]
    },
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
