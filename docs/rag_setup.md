# TipTune RAG setup

## What this service does

`src/rag_api.py` retrieves relevant sections from `knowledge_base/` and sends
only those sections plus the visitor's question to an OpenRouter model. It never
sends an API key to the browser.

It also reads the existing `datasets/*.jsonl` conversations and treats every
user/assistant exchange as a retrievable support Q&A source. The response lists
the retrieved headings, making it possible to see whether an answer came from
the public knowledge base or a dataset example.

The initial retriever is deliberately small and keyword-based. It is sufficient
for the current small FAQ and makes each retrieved source easy to inspect. Move
to embeddings and a vector database only when the knowledge base becomes large
or retrieval quality needs it.

## Configure

1. Copy `.env.example` to `.env`.
2. Set `OPENROUTER_API_KEY` to a server-only OpenRouter key.
3. Set `OPENROUTER_MODEL` to one specific model available in your OpenRouter
   account. Avoid `openrouter/free` for a public production chatbot because the
   routed model can change and free capacity is limited.
4. Review every statement in `knowledge_base/tiptune_support.md`. Add product
   facts only when verified, with a source and review date.
5. Review the dataset answers periodically, especially payment, payout, and
   pricing answers. RAG makes them available immediately; changing or removing
   a JSONL entry changes what can be retrieved without another fine-tune.

## Run locally

```powershell
pip install -r requirements.txt
uvicorn src.rag_api:app --reload --port 8000
```

Then test from a second terminal:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/chat `
  -ContentType 'application/json' `
  -Body '{"message":"How do attendees join an event?"}'
```

The endpoint returns both the answer and the knowledge-base headings used as
sources. Your website should call this backend endpoint, never OpenRouter
directly.

The service explicitly asks the model to return only a customer-facing answer
and disables reasoning in the OpenRouter request. If a selected free model still
returns analysis instead of an answer, switch models; do not expose that output
to website visitors.
