# Study notes

How to talk about Tether in an interview without pretending the graph is larger than it is.

## Chunking vs RFC structure

Ingest uses `RecursiveCharacterTextSplitter` at **800 / 120** with separators `\n\n`, `\n`, `. `, ` `. RFCs are numbered sections, not essays. Overlap helps a heading stay with the next paragraph. It also splits mid-section and can orphan a table or ASCII diagram.

What to say: “I chose character chunks because the corpus is plain RFC text with uneven section lengths. The tradeoff is retrieval that sometimes returns a fragment without its section title. A later improvement is section-aware splits on `^[0-9]+\.` lines, not a different product.”

Metadata `chunk_id = {rfc}:{index}` is what citations hang on. Source ids (`rfc791`, …) are what gold retrieval checks.

## Embeddings vs BM25

Today retrieve is **dense only** (`similarity_search`). BM25 would help exact tokens: `IHL`, `SYN`, port `443`, field widths. Dense helps paraphrase (“how long does a packet live” → TTL). Hybrid (BM25 + dense, then fuse) is optional later; skipping it keeps the demo one failure mode: embedding quality.

Embeddings must match the model that built the index. Rebuild after changing `EMBEDDING_MODEL`. Default: same FastRouter/OpenAI gateway as chat. Override with `EMBEDDING_BASE_URL` if you need OpenAI embeddings while chat stays on FastRouter.

## CRAG / Self-RAG in *this* graph

Classic CRAG: retrieve, grade relevance, if weak then transform the query (or web search) and retrieve again, then generate.

This repo:

1. Retrieve `k` chunks for `query` (starts as the user question).
2. LLM grades each chunk relevant / not.
3. If any relevant → generate with **only** those passages.
4. If none and `rewrite_count < REWRITE_MAX` → rewrite to one sentence, increment count, retrieve again.
5. If none and budget spent → refuse node.

It is **not** full Self-RAG (no per-token retrieve tokens, no critique-then-regenerate loop). It is **not** web-CRAG (no Tavily). Rewrite budget is **1** by default, so you get at most two retrieve passes. That is small enough to explain on a whiteboard.

Generate also refuses if the model says `REFUSE`, emits no `[n]`, citation ids do not match numbered passages, or a long sentence has no citation. That is a faithfulness gate on the way out, not a second graph.

## Metrics

Gold lives in `backend/evals/gold.json`.

| Metric | What it measures | How Tether scores it |
|---|---|---|
| Retrieval hit | Right RFC in the top-k | `must_sources` ⊆ retrieved `source` metadata |
| Citation precision | Every `[n]` maps to a returned citation object | `parse_citation_ids` vs citation ids; eval wants **1.0** plus `decision == answer` |
| Faithfulness | Answer claims supported by passages | `sentences_without_citations` refuses long uncited sentences even when some `[n]` exist |
| Refusal accuracy | Out-of-corpus questions do not get fake footnotes | Gold `refuse` rows must `decision == refuse` |

Say: “citation filter is precision on ids; sentence-level faithfulness refuses leftover claims.”

## Failure modes

- **Bad grades.** A relevant chunk marked false → rewrite or refuse on a question the corpus could answer. A junk chunk marked true → generate from the wrong passage.
- **Rewrite loops.** Budget 1 prevents infinite rewrite. A bad rewrite can retrieve worse chunks than the original question.
- **Uncited sentences.** Model cites `[1]` once then adds extra facts. `finalize_generate` refuses with `uncited_sentences`. Short fragments under 24 characters are ignored.
- **Citation mismatch.** Model invents `[9]` → empty `filter_citations` → refuse. Good.
- **FastRouter embedding mismatch.** If ingest 401s, the embedding gateway or key is wrong. Default is the same FastRouter/OpenAI endpoint as chat. Override with `EMBEDDING_BASE_URL` / `EMBEDDING_API_KEY` if you need OpenAI vectors while chat stays on FastRouter.
- **Empty index.** Health `index_ready: false`; Ask **409**. Ingest deletes collection `tether_rfc` and re-adds chunks.
- **Stale settings.** `get_settings` is cached; `.env` edits need an API restart.

`GRADE_RELEVANCE_THRESHOLD` (default 0.5) cuts LLM grade scores. Below the cutoff the chunk is treated as irrelevant, which can trigger rewrite then refuse. A sloppy high score still sends junk into generate.

## Talking about the trace in an interview

The composer shows retrieve / grade / rewrite / decision, plus a muted **Reason** when the graph refuses (`graded_irrelevant`, `uncited_sentences`, …).

Walk a grounded question: retrieve 6 → some relevant → rewrite skipped → answer + footnotes. Walk World Cup: retrieve still returns *something* (nearest neighbors), grades should mark them irrelevant, rewrite once, still irrelevant, refuse, **no footnotes**. If grades are sloppy, you might see a rewrite then still refuse — that is the budget doing its job.

Open the folio while you talk: empty → loading line → either serif answer with `[n]` or a refused block with the “no footnotes” hint. That is the product, not the graph diagram.
