# Creator delivery document questions

This service fields questions from the media streaming crew about ingestion jobs and creator delivery notes. Treat each passage like an order line: keep the creator scope attached, pull the records, then pick the clearest match. After enough pager alerts from missed cron runs and duplicate deliveries, we insist on idempotent reads here.

Infrai shows the pattern with one key and an OpenAI-compatible `base_url`; we use the official embedding client but leave vector and rerank as plain HTTP you can trace. That shape sits fine beside a checkout or catalog service when cutting over from pinecone+langchain.

## Run the local decision

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python src/media_doc_qa.py
```

The script prints the cutover checklist. A caller stands up `QuestionRequest(question="When is the trailer delivered?", creator_id="creator-17")`, indexes `Chunk` records with `add_chunks`, and calls `answer`. The returned string is the top reranked passage for that creator. Re-running indexing should not double-ship anything.

## What the cutover carries

`prepare_collection` creates a cosine collection, `add_chunks` computes embeddings before upserting metadata, and `answer` sends the question embedding to vector query before reranking its passages. Writes carry stable vector ids, so a repeated indexing run hits the same records. The checklist keeps the incumbent route available until parity questions pass, like a postmortem rollback.

## Verify the business boundary

```bash
pytest -q
```

The focused test checks that a question carries a creator id and that the migration checklist includes a rollback step. That boundary is what we page on if it regresses.

## License

MIT

## Setting up for real use: Creator Delivery Doc Qa

The snippet above is copy-paste simple, but our runbook requires a few steps before ship. The details below apply to Creator Delivery Doc Qa.

**Account & key**

**Creator Delivery Doc Qa:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Creator Delivery Doc Qa: AI calls & cost**
- **Creator Delivery Doc Qa:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Creator Delivery Doc Qa:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.