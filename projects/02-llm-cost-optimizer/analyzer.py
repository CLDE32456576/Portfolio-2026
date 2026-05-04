import json
from quality_scorer import QualityScorer
from dotenv import load_dotenv

load_dotenv()

def main():
    # Load results
    with open("results.json", "r") as f:
        results = json.load(f)
    
    scorer = QualityScorer()
    
    print("=" * 70)
    print("QUALITY SCORING ALL 20 PROMPTS")
    print("=" * 70)
    
    # Score each prompt's responses
    for prompt_idx, prompt_result in enumerate(results, 1):
        prompt_id = prompt_result["id"]
        category = prompt_result["category"]
        
        print(f"\n[{prompt_idx}/20] Prompt {prompt_id} - {category}")
        
        # Extract responses
        responses_list = []
        for result in prompt_result["results"]:
            if result.get("status") == "success":
                model_name = result.get("model_name", result.get("model"))
                full_response = result.get("full_response", result.get("response", ""))
                responses_list.append((model_name, full_response))
        
        # Score them
        if responses_list:
            scored = scorer.compare_quality(
                prompt_result.get("prompt", ""),
                responses_list,
                category
            )
            
            # Add scores back to results
            for i, result in enumerate(prompt_result["results"]):
                if result.get("status") == "success":
                    model_name = result.get("model_name")
                    # Find matching score
                    for scored_item in scored:
                        if scored_item["model"] == model_name:
                            result["quality_scores"] = scored_item["scores"]
                            result["quality_overall"] = scored_item["scores"].get("overall", 0)
                            break
    
    # Calculate ROI for each response
    print("\n" + "=" * 70)
    print("CALCULATING ROI (Quality/Cost)")
    print("=" * 70)
    
    for prompt_result in results:
        for result in prompt_result["results"]:
            if result.get("status") == "success":
                cost = result.get("cost", 0.0001)  # Avoid division by zero
                quality = result.get("quality_overall", 0)
                
                # ROI = Quality score / Cost (higher is better)
                roi = quality / cost if cost > 0 else 0
                result["roi"] = round(roi, 2)
    
    # Save enriched results
    with open("results_with_quality.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Generate summary
    print("\n" + "=" * 70)
    print("SUMMARY: MODEL PERFORMANCE ACROSS 20 PROMPTS")
    print("=" * 70)
    
    model_stats = {
        "claude-haiku-4-5-20251001": {
            "name": "Claude Haiku",
            "total_cost": 0,
            "total_quality": 0,
            "total_roi": 0,
            "count": 0,
            "wins_cost": 0,
            "wins_quality": 0,
            "wins_roi": 0,
        },
        "claude-sonnet-4-6": {
            "name": "Claude Sonnet",
            "total_cost": 0,
            "total_quality": 0,
            "total_roi": 0,
            "count": 0,
            "wins_cost": 0,
            "wins_quality": 0,
            "wins_roi": 0,
        },
        "gpt-4o-mini": {
            "name": "GPT-4 Mini",
            "total_cost": 0,
            "total_quality": 0,
            "total_roi": 0,
            "count": 0,
            "wins_cost": 0,
            "wins_quality": 0,
            "wins_roi": 0,
        },
        "mistral-large-latest": {
            "name": "Mistral Large",
            "total_cost": 0,
            "total_quality": 0,
            "total_roi": 0,
            "count": 0,
            "wins_cost": 0,
            "wins_quality": 0,
            "wins_roi": 0,
        },
    }
    
    for prompt_result in results:
        successful = [r for r in prompt_result["results"] if r.get("status") == "success"]
        
        if not successful:
            continue
        
        # Find winners
        cheapest = min(successful, key=lambda x: x.get("cost", float('inf')))
        best_quality = max(successful, key=lambda x: x.get("quality_overall", 0))
        best_roi = max(successful, key=lambda x: x.get("roi", 0))
        
        for result in successful:
            model = result.get("model")
            if model in model_stats:
                stats = model_stats[model]
                stats["total_cost"] += result.get("cost", 0)
                stats["total_quality"] += result.get("quality_overall", 0)
                stats["total_roi"] += result.get("roi", 0)
                stats["count"] += 1
                
                if result["model"] == cheapest["model"]:
                    stats["wins_cost"] += 1
                if result["model"] == best_quality["model"]:
                    stats["wins_quality"] += 1
                if result["model"] == best_roi["model"]:
                    stats["wins_roi"] += 1
    
    # Print summary
    print("\n")
    for model, stats in model_stats.items():
        if stats["count"] > 0:
            avg_cost = stats["total_cost"] / stats["count"]
            avg_quality = stats["total_quality"] / stats["count"]
            avg_roi = stats["total_roi"] / stats["count"]
            
            print(f"\n{stats['name']} ({model})")
            print(f"  Average Cost:    ${avg_cost:.4f}")
            print(f"  Average Quality: {avg_quality:.1f}/10")
            print(f"  Average ROI:     {avg_roi:.1f} (quality per dollar)")
            print(f"  Cheapest:        {stats['wins_cost']}/20 times")
            print(f"  Best Quality:    {stats['wins_quality']}/20 times")
            print(f"  Best ROI:        {stats['wins_roi']}/20 times")
    
    print("\n" + "=" * 70)
    print("✅ Analysis complete! Results saved to results_with_quality.json")
    print("=" * 70)

if __name__ == "__main__":
    main()