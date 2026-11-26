# ai4dev-wiki

Βοηθός Q&A πάνω στο υλικό του σεμιναρίου **AI for Developers** (Οικονομικό Πανεπιστήμιο Αθηνών).

Χτίζεται σταδιακά, ενότητα προς ενότητα του προγράμματος.

## Τι κάνει σήμερα

Υπηρεσία FastAPI που στέλνει μια ερώτηση σε οποιοδήποτε LLM — τοπικό ή cloud — και
επιστρέφει την απάντηση μαζί με **tokens, κόστος και χρόνο**.

```http
POST /api/v1/ask
{ "question": "Ποια είναι η πρωτεύουσα της Κρήτης;", "model": "ollama_chat/llama3.2:1b" }
```

```json
{
  "answer": "...",
  "model": "ollama_chat/llama3.2:1b",
  "tokens_in": 39,
  "tokens_out": 16,
  "cost_usd": 0.0,
  "seconds": 3.43
}
```

Το πεδίο `model` είναι προαιρετικό· χωρίς αυτό χρησιμοποιείται το `MODEL` του `.env`.

## Εγκατάσταση

```bash
uv sync
copy .env.example .env     # και συμπληρώστε το κλειδί σας
uv run fastapi dev main.py
```

Διαδραστική τεκμηρίωση: <http://localhost:8000/docs>

## Δομή

```
main.py           η εφαρμογή FastAPI
routers/          τα endpoints
schemas/          μοντέλα Pydantic για είσοδο και έξοδο
services/         επικοινωνία με τα μοντέλα, χωρίς γνώση HTTP
```

## Πορεία

- [x] Υπηρεσία με ένα endpoint, εναλλαγή μοντέλων, μέτρηση κόστους
- [ ] Σύγκριση πολλών μοντέλων παράλληλα
- [ ] Prompt engineering: system prompt, few-shot, δομημένη έξοδος
- [ ] Διαχείριση κατάστασης, timeouts, rate limits
- [ ] RAG πάνω στις διαφάνειες και τα repo του μαθήματος
- [ ] Agent με εργαλεία αναζήτησης και εκτέλεσης κώδικα

## Τεχνολογίες

uv · FastAPI · Pydantic · LiteLLM · Ollama
