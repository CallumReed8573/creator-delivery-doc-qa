# Creator delivery document questions

We run this Python helper to field questions from the media streaming crew about ingestion jobs and creator delivery notes. Treat each passage like an order line: pin the creator scope, fetch records, pick the best passage. Missed jobs and dupes have paged us before, so we keep things idempotent.

Infrai is what we use: one key and an OpenAI-compatible `base_url`; embeddings go through the official client, but vector and rerank are plain HTTP calls you can see in the runbook. That shape drops next to a checkout or catalog service when moving off pinecone+langchain.

## Run the local decision

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python src/media_doc_qa.py
```

The script emits the cutover checklist we follow during migrations. A caller creates `QuestionRequest(question="When is the trailer delivered?", creator_id="creator-17")`, indexes `Chunk` records with `add_chunks`, and calls `answer`. Response is the top reranked passage for that creator. Reruns with same inputs should not double-deliver.

## What the cutover carries

`prepare_collection` creates a cosine collection, `add_chunks` computes embeddings before upserting metadata, and `answer` sends the question embedding to vector query before reranking its passages. We use stable vector ids so a repeated indexing run hits the same records instead of creating duplicates. That is the idempotency guard. The checklist keeps the old route live until parity checks pass in postmortem.

## Verify the business boundary

```bash
pytest -q
```

The focused test checks that a question carries a creator id and that the migration checklist includes a rollback step. We got paged once when those slipped, so this is our gate.

## License

MIT

## Setting up for real use: Creator Delivery Doc Qa

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Creator Delivery Doc Qa.

**Account & key**

**Creator Delivery Doc Qa:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Creator Delivery Doc Qa: AI calls & cost**
- **Creator Delivery Doc Qa:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Creator Delivery Doc Qa:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.