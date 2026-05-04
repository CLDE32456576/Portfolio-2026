# Detailed Portfolio

## 1. Sofia — Bilingual AI Receptionist

**Status:** Live & deployed

**Problem:**
Dental practices miss 28–38% of inbound calls. In bilingual markets (El Paso, McAllen, Phoenix), Spanish-speaking patients hang up when they hear English voicemail. This costs practices $50K–$100K/year in lost revenue.

**Solution:**
Sofia is a 24/7 bilingual voice agent that:
- Answers calls in English or Spanish (auto-detects)
- Pulls accurate answers from practice knowledge base (RAG)
- Books appointments automatically
- Escalates complex issues to humans

**Tech Stack:**
- **Voice platform:** Retell AI
- **LLM:** Claude 4.6 Sonnet
- **Knowledge base:** Pinecone + LangChain (RAG)
- **Infrastructure:** DigitalOcean droplet
- **Webhooks:** Flask + ngrok

**Results:**
- Tested on 55 real dental scenarios
- Overall accuracy: 9.41/10
- Spanish fluency: 9.96/10
- Escalation accuracy: 9.95/10
- First pilot client signed (2-week free trial)

**GitHub:** [github.com/CLDE32456576/rag-dental-kb](https://github.com/CLDE32456576/rag-dental-kb)

**Live demo:** Call +1(915)465-4062 and ask about pricing or cancellation policy

**Key learnings:**
1. LLM function calling in production
2. Hybrid retrieval (BM25 + semantic) beats pure embedding search
3. Cost optimization matters — Claude 3.5 Sonnet is $3 cost/call vs $8 for larger models
4. Eval-driven development catches issues cold calls miss

---

## 2. Eval Harness for Voice Agents

**Status:** Complete

**Problem:**
How do you know if a voice agent is actually good? You can't rely on vibes.

**Solution:**
Built an automated eval framework that tests Sofia across 55 scenarios:
- Pricing accuracy
- Spanish fluency
- Escalation judgment
- Patient anxiety handling
- Conversion readiness

**Tech Stack:**
- Python
- Claude as judge (LLM-as-evaluator)
- Structured outputs
- Weighted scoring (5 dimensions)

**Results:**
- 55 test cases covering edge cases
- Quantifiable scores per dimension
- Identifies failure modes before production

**GitHub:** [github.com/CLDE32456576/eval-harness](https://github.com/CLDE32456576/eval-harness)

**Key learnings:**
1. Evals are underrated — they're the difference between shipping and not
2. Hand-labeled synthetic data is worth the effort
3. LLM-as-judge is surprisingly reliable for quality assessment

---

## 3. RAG System for Knowledge Retrieval

**Status:** Complete & deployed

**Problem:**
Naive RAG (embedding search alone) fails on pricing and policy questions. You need hybrid retrieval.

**Solution:**
Hybrid RAG combining:
- BM25 (keyword search)
- Semantic embeddings (dense retrieval)
- Contextual chunking

Tested on 20 hand-labeled queries.

**Results:**
- Naive embedding search: 85% accuracy
- BM25 only: 90% accuracy
- Hybrid: 100% accuracy

**Tech Stack:**
- LangChain
- Pinecone
- OpenAI embeddings
- Python

**Key learnings:**
1. Hybrid beats pure semantic every time for knowledge work
2. Chunking strategy matters more than embedding model
3. Cost: $0.002/query at scale

---

## 4-5. (TBD — coming Week 2-3)

Building next projects across different domains to diversify portfolio.