import json

# Load prompts
with open('test_prompts.json', 'r') as f:
    prompts = json.load(f)['test_cases']

# Analyze them
print("=" * 60)
print("TEST PROMPTS ANALYSIS")
print("=" * 60)

categories = {}
difficulties = {}

for p in prompts:
    cat = p['category']
    diff = p['difficulty']
    
    categories[cat] = categories.get(cat, 0) + 1
    difficulties[diff] = difficulties.get(diff, 0) + 1
    
    print(f"\n[{p['id']}] {p['category'].upper()} ({p['difficulty']})")
    print(f"    {p['prompt'][:100]}...")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"\nTotal prompts: {len(prompts)}")
print(f"\nBy Category:")
for cat, count in sorted(categories.items()):
    print(f"  - {cat}: {count}")
print(f"\nBy Difficulty:")
for diff, count in sorted(difficulties.items()):
    print(f"  - {diff}: {count}")

print("\n" + "=" * 60)
print("WHY THESE PROMPTS?")
print("=" * 60)
print("""
1. SUMMARIZATION (easy/hard) - Shows cost difference on simple vs complex
2. CODING (medium) - Tests if cheaper models can code well
3. ANALYSIS (medium) - Real business problem, needs reasoning
4. CREATIVE (easy) - Should be same quality across models
5. TRANSLATION (easy) - Bilingual test (your use case)
6. REASONING (hard) - Expensive models should win here
7. EXTRACTION (easy) - Cheap models should be fine
8. WRITING (medium) - Marketing email (your sales workflow use case)
9. DEBUGGING (hard) - Complex reasoning, more cost difference
10. TECHNICAL (hard) - Explaining papers, shows quality gaps

EXPECTED RESULTS:
- Haiku: wins on easy/medium, loses on hard reasoning
- Sonnet: balanced, wins on hard tasks
- GPT-4 Mini: sometimes cheaper, varies by task
- Mistral: competitive on some, weak on reasoning

This forces you to see ROI differences.
""")
