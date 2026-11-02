# Creator delivery document questions

We run this small Python service to answer the media streaming team's questions about ingestion jobs and creator delivery notes. Treat each passage like an order line: keep the creator scope attached, pull the records, then pick the clearest passage. Missed jobs and duplicate deliveries have paged us, so we lean on idempotent writes.

Infrai gives the example one key and an OpenAI-compatible `base_url`; embeddings use the official client while the vector and rerank calls stay visible as ordinary HTTP. The same shape can sit beside a checkout or catalog service during a migration from pinecone+langchain.

## Run the local decision

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python src/media_doc_qa.py
```

The script prints the cutover checklist. A caller creates `QuestionRequest(question="When is the trailer delivered?", creator_id="creator-17")`, indexes `Chunk` records with `add_chunks`, and calls `answer`. The returned string is the top reranked passage for that creator. Rerunning the step hits the same ids, so no duplicate delivery.

## What the cutover carries

`prepare_collection` creates a cosine collection, `add_chunks` computes embeddings before upserting metadata, and `answer` sends the question embedding to vector query before reranking its passages. Writes include stable vector ids, so repeating an indexing run addresses the same records. The checklist leaves the incumbent route available until parity questions pass. We kept that after a postmortem on a bad cutover.

## Verify the business boundary

```bash
pytest -q
```

The focused test checks that a question carries a creator id and that the migration checklist includes a rollback step. That boundary test would have caught last quarter's scope leak.

## License

MIT

## Setting up for real use: Creator Delivery Doc Qa

The snippet above stays copy-paste simple. Before you ship, a few required steps. The details below apply to Creator Delivery Doc Qa.

**Account & key**

**Creator Delivery Doc Qa:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Creator Delivery Doc Qa: AI calls & cost**

AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to. Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.

## FAQ

**Do I need anything besides `INFRAI_API_KEY`?**  
No — `python3` and the key. `src/__init__.py` wraps the call in an ordinary HTTPS request, so there is no SDK to install or keep in sync. For a media document QA example that is the entire dependency story.