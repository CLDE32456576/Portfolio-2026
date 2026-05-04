"""
eval_scorer.py
--------------
Takes raw_results from eval_runner.py and scores each response
on 5 dimensions using Claude as judge (LLM-as-judge pattern).

Scores each response on:
  1. accuracy       — Did it answer the question correctly?
  2. tone           — Was it warm, professional, empathetic?
  3. spanish        — Did it use the right language? (Spanish cases only)
  4. escalation     — Did it escalate when it should? NOT escalate when it shouldn't?
  5. conversion     — Did it try to book an appointment (when appropriate)?

Each dimension: 1–10. Final score = weighted average.

Usage:
    python3 eval_scorer.py --input raw_results_full_20260501_123456.json
"""

import anthropic
import json
import time
import argparse
import os
from datetime import datetime

# ── CONFIG ───────────────────────────────────────────────────────────────────

SCORER_MODEL = "claude-opus-4-5"
MAX_TOKENS = 400

WEIGHTS = {
    "accuracy": 0.30,
    "tone": 0.20,
    "spanish": 0.20,
    "escalation": 0.15,
    "conversion": 0.15
}

# ── SCORER PROMPT ─────────────────────────────────────────────────────────────

def build_scorer_prompt(result: dict) -> str:
    expected = result["expected_behaviors"]
    return f"""You are evaluating a dental office AI receptionist called Sofia.

PATIENT INPUT:
"{result['input']}"

SOFIA'S RESPONSE:
"{result['agent_response']}"

CONTEXT:
- Language: {result['language']}
- Category: {result['category']}
- Should escalate to human: {result['escalation_trigger']}
- Conversion opportunity (should try to book): {result['conversion_opportunity']}
- Expected language match: {expected.get('language_match', 'N/A')}
- Notes: {result['notes']}

Score Sofia on these 5 dimensions (1–10 each). Respond ONLY with valid JSON, no explanation:

{{
  "accuracy": <1-10>,
  "accuracy_reason": "<one sentence>",
  "tone": <1-10>,
  "tone_reason": "<one sentence>",
  "spanish": <1-10>,
  "spanish_reason": "<one sentence — if English-only case, score 10 automatically>",
  "escalation": <1-10>,
  "escalation_reason": "<one sentence>",
  "conversion": <1-10>,
  "conversion_reason": "<one sentence>"
}}

Scoring guide:
- accuracy: 10=perfect answer, 7=mostly correct, 4=partial, 1=wrong or dangerous advice
- tone: 10=warm+professional+empathetic, 7=professional but cold, 4=robotic, 1=rude or inappropriate
- spanish: 10=perfect language match (or English-only case), 7=right language but unnatural, 4=wrong language, 1=ignored Spanish patient completely
- escalation: 10=perfect escalation decision, 1=escalated when shouldn't OR failed to escalate emergency
- conversion: 10=naturally offered appointment, 7=mentioned it, 4=missed opportunity, 1=failed to convert AND no excuse (skip if conversion_opportunity=false)
"""

# ── SCORE ONE RESULT ──────────────────────────────────────────────────────────

def score_result(client, result: dict) -> dict:
    """Score a single result using Claude as judge."""
    if result["status"] == "error" or not result["agent_response"]:
        return {**result, "scores": None, "weighted_score": None, "score_status": "skipped"}

    try:
        response = client.messages.create(
            model=SCORER_MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": build_scorer_prompt(result)}]
        )

        raw = response.content[0].text.strip()

        # Clean up any markdown code blocks
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        scores = json.loads(raw)

        # Calculate weighted score
        weighted = (
            scores["accuracy"] * WEIGHTS["accuracy"] +
            scores["tone"] * WEIGHTS["tone"] +
            scores["spanish"] * WEIGHTS["spanish"] +
            scores["escalation"] * WEIGHTS["escalation"] +
            scores["conversion"] * WEIGHTS["conversion"]
        )

        return {
            **result,
            "scores": scores,
            "weighted_score": round(weighted, 2),
            "score_status": "success"
        }

    except json.JSONDecodeError as e:
        return {**result, "scores": None, "weighted_score": None,
                "score_status": "parse_error", "score_error": str(e)}
    except Exception as e:
        return {**result, "scores": None, "weighted_score": None,
                "score_status": "error", "score_error": str(e)}


# ── REPORT GENERATOR ──────────────────────────────────────────────────────────

def generate_report(scored_results: list, metadata: dict) -> dict:
    """Generate aggregate metrics from scored results."""
    scored = [r for r in scored_results if r.get("score_status") == "success"]

    if not scored:
        return {"error": "No successfully scored results"}

    # Overall averages
    def avg(key):
        vals = [r["scores"][key] for r in scored if r.get("scores")]
        return round(sum(vals) / len(vals), 2) if vals else 0

    # By category
    categories = {}
    for r in scored:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r["weighted_score"])

    cat_averages = {
        cat: round(sum(scores) / len(scores), 2)
        for cat, scores in categories.items()
    }

    # By language
    languages = {}
    for r in scored:
        lang = r["language"]
        if lang not in languages:
            languages[lang] = []
        languages[lang].append(r["weighted_score"])

    lang_averages = {
        lang: round(sum(scores) / len(scores), 2)
        for lang, scores in languages.items()
    }

    # Lowest scoring cases (need improvement)
    worst = sorted(
        [r for r in scored if r.get("weighted_score")],
        key=lambda x: x["weighted_score"]
    )[:5]

    # Escalation accuracy
    escalation_cases = [r for r in scored if r["escalation_trigger"]]
    escalation_avg = avg("escalation") if escalation_cases else "N/A"

    # Conversion effectiveness
    conversion_cases = [r for r in scored if r["conversion_opportunity"]]
    conversion_scores = [r["scores"]["conversion"] for r in conversion_cases if r.get("scores")]
    conversion_avg = round(sum(conversion_scores) / len(conversion_scores), 2) if conversion_scores else 0

    # Spanish accuracy
    spanish_cases = [r for r in scored if r["language"] in ["spanish", "bilingual"]]
    spanish_scores = [r["scores"]["spanish"] for r in spanish_cases if r.get("scores")]
    spanish_avg = round(sum(spanish_scores) / len(spanish_scores), 2) if spanish_scores else 0

    overall_avg = round(
        sum(r["weighted_score"] for r in scored) / len(scored), 2
    )

    return {
        "summary": {
            "total_cases": metadata["total_cases"],
            "scored_cases": len(scored),
            "overall_weighted_score": overall_avg,
            "overall_grade": grade(overall_avg),
            "dimension_averages": {
                "accuracy": avg("accuracy"),
                "tone": avg("tone"),
                "spanish_language": spanish_avg,
                "escalation": escalation_avg,
                "conversion": conversion_avg
            }
        },
        "by_category": cat_averages,
        "by_language": lang_averages,
        "weakest_5_cases": [
            {
                "id": r["id"],
                "score": r["weighted_score"],
                "category": r["category"],
                "language": r["language"],
                "input": r["input"][:60] + "...",
                "response_preview": (r["agent_response"] or "")[:80] + "..."
            }
            for r in worst
        ],
        "escalation_accuracy": escalation_avg,
        "conversion_rate": conversion_avg,
        "spanish_accuracy": spanish_avg,
        "weights_used": WEIGHTS
    }


def grade(score: float) -> str:
    if score >= 9.0: return "A+ — Production ready"
    if score >= 8.0: return "A  — Ship with minor improvements"
    if score >= 7.0: return "B  — Good, needs tuning in weak areas"
    if score >= 6.0: return "C  — Functional but not client-ready"
    return "D  — Needs significant work before shipping"


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Dental Voice Agent Eval Scorer")
    parser.add_argument("--input", type=str, required=True,
                        help="Path to raw_results JSON from eval_runner.py")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)

    raw_results = data["results"]
    metadata = data["metadata"]
    total = len(raw_results)

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    print(f"\n{'='*55}")
    print(f"  EVAL SCORER — scoring {total} responses")
    print(f"  Judge model: {SCORER_MODEL}")
    print(f"{'='*55}\n")

    scored_results = []
    for i, result in enumerate(raw_results, 1):
        if result["status"] == "error":
            print(f"[{i:02d}/{total}] {result['id']} — SKIPPED (runner error)")
            scored_results.append({**result, "scores": None,
                                   "weighted_score": None, "score_status": "skipped"})
            continue

        print(f"[{i:02d}/{total}] Scoring {result['id']}...", end=" ")
        scored = score_result(client, result)

        if scored.get("weighted_score"):
            ws = scored["weighted_score"]
            bar = "█" * int(ws) + "░" * (10 - int(ws))
            print(f"{ws:.1f}/10 [{bar}]")
        else:
            print(f"ERROR: {scored.get('score_error', 'unknown')}")

        scored_results.append(scored)

        if i < total:
            time.sleep(0.5)

    # Generate report
    report = generate_report(scored_results, metadata)

    # Save full scored output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"scored_results_{timestamp}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {**metadata, "scorer_model": SCORER_MODEL,
                         "scored_at": timestamp},
            "report": report,
            "scored_results": scored_results
        }, f, ensure_ascii=False, indent=2)

    # Print summary to terminal
    s = report["summary"]
    print(f"\n{'='*55}")
    print(f"  EVAL RESULTS")
    print(f"{'='*55}")
    print(f"  Overall score:   {s['overall_weighted_score']}/10 — {s['overall_grade']}")
    print(f"\n  Dimension breakdown:")
    for dim, score in s["dimension_averages"].items():
        bar = "█" * int(float(score)) + "░" * (10 - int(float(score))) if score != "N/A" else "N/A"
        print(f"    {dim:<22} {score}  [{bar}]")
    print(f"\n  By category:")
    for cat, score in sorted(report["by_category"].items(), key=lambda x: x[1]):
        print(f"    {cat:<22} {score}")
    print(f"\n  By language:")
    for lang, score in report["by_language"].items():
        print(f"    {lang:<22} {score}")
    print(f"\n  5 weakest cases to fix:")
    for case in report["weakest_5_cases"]:
        print(f"    [{case['score']}] {case['id']}: {case['input']}")
    print(f"\n  Full results saved → {output_file}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
