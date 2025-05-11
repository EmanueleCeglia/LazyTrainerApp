| Ordine | Agent              | Input principale                  | Output                      | Persistenza |
| ------ | ------------------ | --------------------------------- | --------------------------- | ----------- |
| ①      | Needs-Analyzer     | Questionario                      | `user_profile` JSON         | breve       |
| ②      | SQL-Filter         | `user_profile`                    | raw exercises               | none        |
| ③      | Exercise-Selector  | raw exercises + `user_profile`    | short-list exercises        | none        |
| ④      | Protocol-Generator | short-list + goal                 | list `(exercise, protocol)` | short       |
| ⑤      | Program-Composer   | lista protocolli + `user_profile` | workout draft               | medium      |
| ⑥      | QA-Checker         | workout draft                     | ok / revision request       | ephemeral   |
| ⑦      | Summary Agent      | workout final                     | human-friendly sheet        | long-term   |


1. Raffinare la pipeline logica
Analisi esigenza utente

Trasforma le risposte al questionario in un JSON strutturato: obiettivo primario, eventuali secondari, giorni/tempo a disposizione, livello, attrezzatura, limitazioni.

Recupero esercizi (Agent già esistente)

Mantieni l’attuale agente “SQL-Filter” come primo step della pipeline.

Selezione esercizi

Nuovo Exercise-Selector Agent che:
• bilancia i movement pattern (push/pull, horizontal/vertical).
• impone limiti di volume (es. 5–8 esercizi totali).
• tiene conto del livello (scarta varianti troppo avanzate).
• può introdurre un leggero randomness controllato per varietà.

Generazione metodi d’allenamento (Protocol-Generator Agent)

Conoscenza enciclopedica di protocolli:
• Straight sets 3×10–12
• Piramidale (ascendente, discendente)
• Superset push/pull
• EMOM, AMRAP, ecc.

Regole di mappatura:
– linka pattern + obiettivo (ipertrofia, forza, endurance) → protocolli adatti.
– fornisce 1-2 opzioni per esercizio con parametri (serie, reps, RIR/rest).

Composizione scheda (Program-Composer Agent)

Riceve lista di coppie (esercizio, protocollo) e:
• ordina (compound prima degli isolamenti, tirate/spinte alternate, high-skill a inizio seduta).
• calcola durata stimata e verifica che rientri nel tempo disponibile.
• aggiunge riscaldamento/cool-down template se non presente.

Output: oggetto “workout” con metadati (giorno, equipment, link video, note progressione).

Validazione qualitativa (QA-Checker Agent)

Controlli automatici:
• nessun gruppo muscolare trascurato.
• volume/tonnellaggio entro range raccomandati.
• recupero ≥ 48 h per stesso gruppo nella programmazione multi-giorno.

Se fallisce, richiede un nuovo draft al Composer.

Post-processing & spiegazione

Summary Agent traduce il workout in linguaggio naturale (“scheda” leggibile dall’utente) e genera eventuali raccomandazioni (focus sulla tecnica, cue, progressione settimanale).