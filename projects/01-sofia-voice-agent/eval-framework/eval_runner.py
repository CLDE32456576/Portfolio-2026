"""
eval_runner.py
--------------
Feeds each test case to Claude (acting as the dental voice agent)
and records the raw response. Does NOT score — that's eval_scorer.py.

Usage:
    python3 eval_runner.py
    python3 eval_runner.py --case EN-001        # run one case
    python3 eval_runner.py --category emergency # run one category
"""

import anthropic
import json
import time
import argparse
import os
from datetime import datetime

# ── CONFIG ──────────────────────────────────────────────────────────────────

MODEL = "claude-opus-4-5"
MAX_TOKENS = 500

# System prompt: Claude IS the dental voice agent
SYSTEM_PROMPT = """You are the AI receptionist for a bilingual dental office.
Your name is Sofia. You answer calls in English or Spanish depending on how the patient speaks.
If the patient uses Spanglish or code-switches, prefer Spanish.

Your job is to:
1. Answer the patient's question accurately using your dental knowledge
2. Be warm, professional, and empathetic — especially with anxious or emergency patients
3. Book an appointment whenever appropriate (most of the time)
4. Escalate to a human receptionist/manager for emergencies, complaints, complex questions, and anything uncertain
5. Never give dangerous medical advice (e.g., how to extract a tooth at home)
6. Be honest if asked whether you are an AI

═══════════════════════════════════════════════════════════════════════════════
CRITICAL ESCALATION RULES — FOLLOW THESE EXACTLY
═══════════════════════════════════════════════════════════════════════════════

IMMEDIATE ESCALATION (transfer to manager/front desk):
- Severe pain (can't sleep, lasting multiple days)
- Swelling, fever, visible infection (potential abscess)
- Trauma (knocked-out tooth, jaw injury, significant bleeding)
- Broken/sharp edges causing injury to mouth
- ANY patient complaint or negative feedback about service
- Complex insurance questions (cross-border US-Mexico, Medicaid specifics, verification for major procedures $3K+)
- Questions about legal/tax implications (SAT, RESICO, insurance coverage in Mexico, etc.)
- Anything you are unsure about — when in doubt, escalate

For emergencies: Say something like:
"Let me connect you with my manager right now to confirm same-day availability and get you scheduled immediately."
or
"Let me transfer you to our front desk to lock in your emergency appointment right now."

For complex insurance/tax questions: Say:
"That's a great question and I want to make sure you get the most accurate answer. Let me connect you with someone who specializes in that."

═══════════════════════════════════════════════════════════════════════════════
SOFT CLOSE for hesitant/thinking patients
═══════════════════════════════════════════════════════════════════════════════

If patient says "I need to think about it," "Let me call you back," "I'm not sure yet," or similar:
DO NOT just provide hours and let them go — that loses them.

Instead use a soft close:
"I totally understand. How about I hold a tentative appointment for you [specific day/time]? 
That way you don't lose the slot. You can always cancel if something changes. Does Thursday at 2pm work?"

Get their name + phone number to confirm the "reservation."

═══════════════════════════════════════════════════════════════════════════════
DENTAL OFFICE FACTS
═══════════════════════════════════════════════════════════════════════════════

Services: cleanings, fillings, root canals, extractions, implants, veneers, Invisalign, whitening, night guards, pediatric dentistry
Hours: Monday–Friday 8am–6pm, Saturday 9am–2pm
Insurance: accepts most PPOs, Medicaid, CareCredit financing available
Cleaning cost: $80–$150 (with insurance often $0)
Filling: $150–$300
Root canal: $700–$1,500 depending on tooth
Extraction: $150–$300 simple, $300–$600 surgical
Implant: $3,000–$5,000
Veneer: $900–$2,500 per tooth
Whitening: $300–$800 in-office
Same-day emergency appointments available

Keep responses conversational and under 120 words — this is a phone call, not an email.
"""

# ── MAIN RUNNER ──────────────────────────────────────────────────────────────

def run_case(client, case: dict) -> dict:
    """Run a single test case and return the result."""
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": case["input"]}]
        )
        agent_response = response.content[0].text
        tokens_used = response.usage.input_tokens + response.usage.output_tokens

        return {
            "id": case["id"],
            "input": case["input"],
            "language": case["language"],
            "category": case["category"],
            "difficulty": case["difficulty"],
            "agent_response": agent_response,
            "tokens_used": tokens_used,
            "expected_behaviors": case["expected_behaviors"],
            "escalation_trigger": case["escalation_trigger"],
            "conversion_opportunity": case["conversion_opportunity"],
            "notes": case["notes"],
            "status": "success",
            "error": None
        }

    except Exception as e:
        return {
            "id": case["id"],
            "input": case["input"],
            "language": case["language"],
            "category": case["category"],
            "difficulty": case["difficulty"],
            "agent_response": None,
            "tokens_used": 0,
            "expected_behaviors": case["expected_behaviors"],
            "escalation_trigger": case["escalation_trigger"],
            "conversion_opportunity": case["conversion_opportunity"],
            "notes": case["notes"],
            "status": "error",
            "error": str(e)
        }


def run_eval(cases: list, label: str = "full") -> dict:
    """Run all cases and save results."""
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    results = []
    total = len(cases)

    print(f"\n{'='*55}")
    print(f"  DENTAL VOICE AGENT EVAL — {label.upper()}")
    print(f"  Running {total} test cases on {MODEL}")
    print(f"{'='*55}\n")

    for i, case in enumerate(cases, 1):
        print(f"[{i:02d}/{total}] {case['id']} ({case['category']}, {case['language']})...")
        result = run_case(client, case)

        if result["status"] == "success":
            # Preview first 80 chars of response
            preview = result["agent_response"][:80].replace("\n", " ")
            print(f"         → {preview}...")
        else:
            print(f"         ✗ ERROR: {result['error']}")

        results.append(result)

        # Respect rate limits — short sleep between calls
        if i < total:
            time.sleep(0.5)

    # Save raw results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"raw_results_{label}_{timestamp}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "timestamp": timestamp,
                "model": MODEL,
                "total_cases": total,
                "label": label,
                "success_count": sum(1 for r in results if r["status"] == "success"),
                "error_count": sum(1 for r in results if r["status"] == "error"),
                "total_tokens": sum(r["tokens_used"] for r in results)
            },
            "results": results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*55}")
    print(f"  DONE. {sum(1 for r in results if r['status'] == 'success')}/{total} successful")
    print(f"  Total tokens used: {sum(r['tokens_used'] for r in results):,}")
    print(f"  Raw results saved → {output_file}")
    print(f"{'='*55}\n")
    print(f"  Next step: python3 eval_scorer.py --input {output_file}\n")

    return output_file


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Dental Voice Agent Eval Runner")
    parser.add_argument("--case", type=str, help="Run a single case by ID (e.g. EN-001)")
    parser.add_argument("--category", type=str, help="Run all cases in a category (e.g. emergency)")
    parser.add_argument("--language", type=str, help="Run all cases in a language (e.g. spanish)")
    args = parser.parse_args()

    with open("test_cases.json", encoding="utf-8") as f:
        all_cases = json.load(f)

    # Filter cases based on CLI args
    if args.case:
        cases = [c for c in all_cases if c["id"] == args.case]
        label = args.case
        if not cases:
            print(f"Case {args.case} not found.")
            return
    elif args.category:
        cases = [c for c in all_cases if c["category"] == args.category]
        label = args.category
        if not cases:
            print(f"No cases found for category: {args.category}")
            return
    elif args.language:
        cases = [c for c in all_cases if c["language"] == args.language]
        label = args.language
        if not cases:
            print(f"No cases found for language: {args.language}")
            return
    else:
        cases = all_cases
        label = "full"

    run_eval(cases, label)


if __name__ == "__main__":
    main()
