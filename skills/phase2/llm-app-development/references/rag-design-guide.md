# RAG design guide

RAG (retrieval-augmented generation) connects an LLM to a knowledge source it was not trained on. The model answers questions using retrieved documents rather than relying on parametric memory. This guide covers the design decisions that determine whether RAG works well or produces expensive hallucinations.

---

## When RAG is the right choice

Use RAG when:
- The model needs up-to-date information (docs published after training cutoff, live device state, current policy)
- The knowledge is too large to fit in a context window (full product documentation, legal corpus)
- The answer must be attributable to a specific source document (compliance, audit)

Do not use RAG when:
- The knowledge fits in the context window and changes rarely — just put it in the prompt
- The task is classification or transformation with no external knowledge needed
- Retrieval quality cannot be measured and improved iteratively (skip RAG until it can be)

---

## Chunking strategies

Chunking determines what units go into your vector store. Bad chunking is the most common source of poor retrieval quality. It is not fixable by tuning the retrieval model — the quality of what you retrieve is bounded by what you put in.

### Strategy 1: Semantic chunking (recommended default)

Split on natural semantic boundaries: paragraph breaks, section headings, list item groups. A chunk should express one complete idea.

```python
import re

def chunk_by_paragraphs(text: str, min_tokens: int = 50, max_tokens: int = 400) -> list[str]:
    """
    Split text into paragraph chunks. Merge short paragraphs to meet min_tokens;
    split long paragraphs at sentence boundaries if they exceed max_tokens.
    """
    rough_paragraphs = re.split(r'\n{2,}', text.strip())
    chunks = []
    current = []
    current_tokens = 0

    for para in rough_paragraphs:
        para = para.strip()
        if not para:
            continue
        para_tokens = len(para.split()) * 1.3  # rough estimate

        if current_tokens + para_tokens > max_tokens and current:
            chunks.append("\n\n".join(current))
            current = []
            current_tokens = 0

        current.append(para)
        current_tokens += para_tokens

        if current_tokens >= min_tokens:
            chunks.append("\n\n".join(current))
            current = []
            current_tokens = 0

    if current:
        chunks.append("\n\n".join(current))

    return chunks
```

**When to use:** general documentation, knowledge bases, runbooks, policy documents.

### Strategy 2: Fixed-overlap chunking

Split into fixed-size windows with an overlap between adjacent chunks. Useful when semantic structure is absent (raw logs, transcripts, unstructured text).

```python
def chunk_with_overlap(text: str, chunk_size: int = 300, overlap: int = 50) -> list[str]:
    """
    Split text into token-approximate chunks with overlap.
    chunk_size and overlap are in rough token units (words / 0.75).
    """
    words = text.split()
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        chunk_words = words[i:i + chunk_size]
        if chunk_words:
            chunks.append(" ".join(chunk_words))
    return chunks
```

**When to use:** raw logs, transcripts, unstructured blobs where paragraph structure does not exist.

**Caution:** fixed-size chunking splits sentences. The overlap mitigates this but does not eliminate it. Always prefer semantic chunking when structure exists.

### Strategy 3: Hierarchical chunking

Store the document at two levels: whole sections for context, individual paragraphs for precision. Retrieve at the paragraph level; include the parent section summary as metadata.

**When to use:** long technical documents where questions may be either broad ("what does this module do") or narrow ("what is the retry backoff formula"). The hierarchical index serves both query types.

### What NOT to do

- Do not chunk at a fixed token count without overlap. A question about "the retry configuration" will fail if "retry" is at the end of one chunk and "configuration" is at the start of the next.
- Do not make chunks so small (< 50 tokens) that they lose context. A chunk that says "3 minutes." tells the model nothing.
- Do not make chunks so large (> 600 tokens) that one chunk covers multiple topics. The retrieval model will then surface the chunk for off-topic queries.

---

## Metadata to store with each chunk

Every chunk should carry metadata that can be used to filter before retrieval or to cite after retrieval.

```python
chunk_record = {
    "chunk_id": "doc-003-chunk-012",
    "source_document": "device-registry-api-guide.md",
    "section": "Authentication",
    "page": 4,                          # for PDFs
    "published_date": "2026-01-15",
    "content_hash": "sha256:abc123...",  # detect stale chunks after re-indexing
    "text": "API keys are rotated every 90 days...",
}
```

Filter on `published_date` or `section` at retrieval time to narrow the search space before vector similarity runs. This is faster than post-filtering and improves recall.

---

## Embedding model selection

### General-purpose models (good starting point)

| Model | Provider | Best for |
|-------|----------|----------|
| `text-embedding-3-small` | OpenAI | General English text; low cost |
| `text-embedding-3-large` | OpenAI | Higher accuracy for general text; 3× cost |
| `nomic-embed-text` | Nomic / local | Open-weight; self-hosted option |

Start with `text-embedding-3-small`. Measure recall@5 on a held-out set of your actual queries. If recall@5 < 0.75, evaluate a larger or domain-specific model before concluding that chunking or retrieval is the bottleneck.

### When to consider a domain-specific embedding model

Switch when your corpus has significant domain-specific vocabulary that general models do not handle well:
- Network protocols, device firmware, kernel documentation → technical embedding models
- Medical records, clinical notes → biomedical embedding models (PubMedBERT-based)
- Legal contracts, case law → legal embedding models

**How to decide:** run recall@5 on 50 representative queries using the general model. If recall@5 < 0.70 and you cannot fix it with better chunking, test a domain-specific model. Do not switch models based on intuition — measure first.

---

## Retrieval quality metrics

Measure these before connecting retrieval to the LLM. A weak retrieval step cannot be compensated by a stronger prompt.

### Recall@k

Does the correct chunk appear in the top-k results? The most important metric.

```python
def recall_at_k(queries: list[dict], retriever, k: int = 5) -> float:
    """
    queries: list of {"query": str, "relevant_chunk_id": str}
    retriever: callable that takes (query, k) and returns list of chunk dicts with "chunk_id"
    """
    hits = 0
    for q in queries:
        results = retriever(q["query"], k)
        retrieved_ids = {r["chunk_id"] for r in results}
        if q["relevant_chunk_id"] in retrieved_ids:
            hits += 1
    return hits / len(queries)
```

**Target:** recall@5 > 0.85 before connecting to the LLM.

If recall@5 < 0.85: first check chunking (are relevant chunks coherent?), then check the embedding model, then consider metadata filtering.

### MRR (mean reciprocal rank)

On average, how high in the result list does the correct chunk appear? Recall@k tells you if the chunk is found; MRR tells you how much irrelevant context the model must wade through.

```python
def mean_reciprocal_rank(queries: list[dict], retriever, k: int = 10) -> float:
    """
    Returns MRR across all queries. Higher is better. Range: (0, 1].
    """
    reciprocal_ranks = []
    for q in queries:
        results = retriever(q["query"], k)
        for rank, result in enumerate(results, start=1):
            if result["chunk_id"] == q["relevant_chunk_id"]:
                reciprocal_ranks.append(1.0 / rank)
                break
        else:
            reciprocal_ranks.append(0.0)
    return sum(reciprocal_ranks) / len(reciprocal_ranks)
```

**Target:** MRR > 0.6 before connecting to the LLM. MRR < 0.4 means relevant chunks are consistently buried — reranking is likely needed.

---

## Reranking

Retrieve a larger candidate set from the vector store (top-20), then rerank to top-3 before passing to the LLM. The vector retrieval step optimises for recall (cast wide); reranking optimises for precision (pick the best).

### Why reranking matters

Vector similarity retrieves semantically similar chunks, but "similar" is not the same as "relevant to this specific query." A question about "how to rotate API keys" might retrieve chunks about "API key creation", "key expiry policy", and "key rotation" — all similar, but only the last is the answer. A cross-encoder reranker scores each candidate against the query directly and is much more precise.

### Reranking options

| Option | Cost | Accuracy | When to use |
|--------|------|----------|-------------|
| Cross-encoder model (local) | Low (CPU) | High | Self-hosted; latency budget > 200ms |
| Cohere Rerank API | Per-call | High | Managed; no model hosting |
| LLM-as-reranker | High (LLM tokens) | Very high | Only when precision is critical and cost is acceptable |
| BM25 hybrid re-score | Zero | Medium | Good baseline; combine BM25 + vector similarity scores |

```python
# Hybrid retrieval: combine vector similarity score with BM25 term frequency score
def hybrid_score(vector_score: float, bm25_score: float, alpha: float = 0.6) -> float:
    """
    alpha controls the weight of vector vs BM25.
    alpha=1.0 is pure vector; alpha=0.0 is pure BM25.
    Start at alpha=0.6 and tune on your retrieval quality metric.
    """
    return alpha * vector_score + (1 - alpha) * bm25_score
```

### Recommended reranking pipeline

```
Query
  → vector retrieval (top-20 candidates)
  → metadata filter (date, section, document type as applicable)
  → cross-encoder rerank (top-20 → top-3)
  → LLM with top-3 chunks in context
```

---

## Context construction

After retrieval and reranking, you have 3–5 chunks to pass to the LLM. How you construct the context prompt matters.

### Include source attribution in the context

```
CONTEXT DOCUMENTS
-----------------
[1] Source: device-registry-api-guide.md, Section: Authentication, 2026-01-15
    API keys are rotated every 90 days. The rotation endpoint is POST /api-keys/{id}/rotate.
    Rotation returns a new key immediately; the old key is valid for 24 hours.

[2] Source: device-registry-api-guide.md, Section: Key Management, 2026-01-15
    Keys can be revoked immediately via DELETE /api-keys/{id}. Revocation is immediate
    and cannot be undone.

QUESTION
--------
How do I rotate an API key without service interruption?
```

Including source attribution lets the model cite the document in its answer — important for trust and debugging.

### Constrain the model to the context

Add this instruction to every RAG prompt:

```
Answer the question using only the provided context documents.
If the answer is not in the documents, say: "I don't have enough information
to answer this from the available documentation."

Do not generate information that is not present in the context.
```

This constraint is the primary defence against hallucination in RAG. Test it explicitly in your eval dataset — include cases where the correct answer is "I don't know."

---

## Failure modes

| Failure | Signal | Cause | Fix |
|---------|--------|-------|-----|
| Retrieved chunks are irrelevant | Low MRR; LLM answers the wrong question | Chunking too coarse, embedding model mismatch | Re-chunk semantically; test a different embedding model |
| Model ignores the context and uses parametric memory | Answer contradicts the retrieved document | Constraint instruction too weak | Strengthen the constraint prompt; add examples of "I don't know" |
| Context overflow | Answers truncate or miss instructions near end of prompt | Too many or too large chunks | Reduce top-k; rerank more aggressively; summarise chunks before passing |
| Stale chunks | Model answers with outdated information | Re-indexing not triggered on document update | Add content_hash to chunks; compare on each document ingest; re-embed on change |
| Sparse retrieval (no good chunks found) | Recall@5 = 0 for certain query types | Vocabulary gap between queries and documents | Add query expansion (rewrite the query to multiple variants before retrieval); evaluate hybrid BM25+vector |

---

## Production indexing pipeline

```
Document source (S3, database, filesystem)
  → parse (PDF, HTML, markdown, plain text)
  → clean (strip navigation, boilerplate, headers/footers)
  → chunk (semantic or fixed-overlap, per document type)
  → embed (embedding model API or local)
  → upsert to vector store (with metadata + content_hash)
  → log: document_id, chunk_count, embedding_model_version, timestamp
```

Re-index when:
- A source document is updated (compare `content_hash`)
- The embedding model is upgraded (re-embed all chunks — scores are not comparable across models)
- Chunking strategy changes (re-chunk and re-embed all documents)

Never incrementally patch a partial index after a strategy change. Re-build the full index.
