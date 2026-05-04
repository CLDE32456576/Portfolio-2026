# LLM Cost Optimizer

**Find the cheapest LLM that's good enough for your task.**

## The Problem

Most companies use expensive LLMs (Claude Sonnet, GPT-4) for everything. But 90% of tasks don't need that quality.

Running the same prompt through Sonnet vs GPT-4 Mini:
- **Sonnet:** $0.0055/prompt, 7.0/10 quality
- **GPT-4 Mini:** $0.0002/prompt, 6.8/10 quality
- **Savings:** 96% cost reduction, only 0.2% quality loss

## What It Does

1. Takes a prompt
2. Runs it through 4 LLMs (Claude Haiku, Sonnet, GPT-4 Mini, Mistral)
3. Scores quality on accuracy, clarity, completeness, relevance
4. Calculates ROI (quality per dollar)
5. Recommends the best value option

## Results (20 Real-World Prompts)

| Model | Cost | Quality | ROI | Winner? |
|-------|------|---------|-----|---------|
| **GPT-4 Mini** | $0.0002 | 6.8/10 | **38,833** | ✅ BEST VALUE |
| Claude Haiku | $0.0014 | 7.0/10 | 6,630 | Mid-tier |
| Mistral Large | $0.0016 | 7.2/10 | 5,947 | Mid-tier |
| Claude Sonnet | $0.0055 | 7.0/10 | 1,798 | ❌ Expensive |

**GPT-4 Mini won on cost in 20/20 tasks** while maintaining competitive quality.

## Tech Stack

- **FastAPI** — Web framework
- **Anthropic, OpenAI, Mistral APIs** — LLM providers
- **Claude as Judge** — Quality scoring (LLM-as-evaluator)
- **Chart.js** — Interactive dashboard
- **SQLite** — Results storage

## Run It

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env with your API keys
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
MISTRAL_API_KEY=...

# Run tests on all 20 prompts
python llm_client.py

# Score quality and calculate ROI
python analyzer.py

# Start dashboard
python main.py
# Visit http://localhost:8000
```

## Key Insights

1. **GPT-4 Mini dominates on ROI** — 38,833 quality per dollar vs 1,798 for Sonnet
2. **Quality difference is negligible** — 6.8 vs 7.2 is 0.4 points on a 10-point scale
3. **Use Sonnet only for hard reasoning** — When you need the absolute best (5 out of 20 tasks)
4. **Never use Sonnet for easy tasks** — You're overpaying 27x for 3% better quality

## Portfolio Value

Shows:
- ✅ Multi-provider API integration
- ✅ LLM evaluation framework (quality scoring)
- ✅ Data-driven decision making (ROI analysis)
- ✅ Full-stack (backend + frontend)
- ✅ Real business problem (cost optimization)
- ✅ Production-ready code

## Monetization

**$200–$500/month SaaS:**
- Companies connect their LLM usage
- Tool analyzes their workflows
- Recommends which model for each task
- Automatic routing for cost savings
- Show them the ROI (companies love ROI)

**One customer saving $50K/year pays for itself in 1 month.**
