# Engineering-document retrieval

V1 performs provenance-aware local lexical retrieval over extracted document text. PDF chunks retain page metadata when available. This keeps the offline demo and tests deterministic and avoids requiring an embedding API.

The retriever is deliberately isolated behind `EngineeringRetriever`. A vector/embedding backend can replace the scoring implementation without changing agent/report schemas.

BenchMind never labels retrieved text as a verified electrical fact automatically. Retrieval supplies evidence to downstream diagnosis; the claim type remains explicit.
