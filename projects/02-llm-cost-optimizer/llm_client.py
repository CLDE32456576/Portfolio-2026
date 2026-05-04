from anthropic import Anthropic
from openai import OpenAI
from mistralai.client import Mistral
import os
import json
from datetime import datetime
import asyncio

class LLMClient:
    def __init__(self):
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.mistral = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
        
        # Pricing per 1M tokens (May 2026)
        self.pricing = {
            "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00, "name": "Claude Haiku 4.5"},
            "claude-sonnet-4-6": {"input": 3.00, "output": 15.00, "name": "Claude Sonnet 4.6"},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60, "name": "GPT-4 Mini"},
            "mistral-large-latest": {"input": 2.00, "output": 6.00, "name": "Mistral Large"},
        }
    
    def run_claude(self, prompt: str, model: str = "claude-haiku-4-5-20251001") -> dict:
        """Run prompt through Claude"""
        try:
            response = self.anthropic.messages.create(
                model=model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            
            pricing = self.pricing[model]
            cost = (input_tokens / 1_000_000 * pricing["input"]) + (output_tokens / 1_000_000 * pricing["output"])
            
            return {
                "model": model,
                "model_name": pricing["name"],
                "response": response.content[0].text[:200],  # First 200 chars
                "full_response": response.content[0].text,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "cost": round(cost, 4),
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "model": model,
                "model_name": self.pricing[model]["name"],
                "error": str(e),
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
    
    def run_openai(self, prompt: str, model: str = "gpt-4o-mini") -> dict:
        """Run prompt through OpenAI"""
        try:
            response = self.openai.chat.completions.create(
                model=model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            
            pricing = self.pricing[model]
            cost = (input_tokens / 1_000_000 * pricing["input"]) + (output_tokens / 1_000_000 * pricing["output"])
            
            return {
                "model": model,
                "model_name": pricing["name"],
                "response": response.choices[0].message.content[:200],
                "full_response": response.choices[0].message.content,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "cost": round(cost, 4),
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "model": model,
                "model_name": self.pricing[model]["name"],
                "error": str(e),
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
    
    def run_mistral(self, prompt: str, model: str = "mistral-large-latest") -> dict:
        """Run prompt through Mistral"""
        try:
            response = self.mistral.chat.complete(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            
            # Mistral doesn't always return token counts, estimate
            input_tokens = len(prompt.split()) * 1.3
            output_tokens = len(response.choices[0].message.content.split()) * 1.3
            
            pricing = self.pricing[model]
            cost = (input_tokens / 1_000_000 * pricing["input"]) + (output_tokens / 1_000_000 * pricing["output"])
            
            return {
                "model": model,
                "model_name": pricing["name"],
                "response": response.choices[0].message.content[:200],
                "full_response": response.choices[0].message.content,
                "input_tokens": int(input_tokens),
                "output_tokens": int(output_tokens),
                "total_tokens": int(input_tokens + output_tokens),
                "cost": round(cost, 4),
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "model": model,
                "model_name": self.pricing[model]["name"],
                "error": str(e),
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
    
    def compare_models(self, prompt: str, models: list = None) -> list:
        """Run prompt through all models"""
        if models is None:
            models = [
                "claude-haiku-4-5-20251001",
                "claude-sonnet-4-6",
                "gpt-4o-mini",
                "mistral-large-latest"
            ]
        
        results = []
        for model in models:
            print(f"  Testing {self.pricing[model]['name']}...", end=" ", flush=True)
            
            if "claude" in model:
                result = self.run_claude(prompt, model)
            elif "gpt" in model:
                result = self.run_openai(prompt, model)
            elif "mistral" in model:
                result = self.run_mistral(prompt, model)
            
            results.append(result)
            
            if result["status"] == "success":
                print(f"✅ ${result['cost']}")
            else:
                print(f"❌ Error")
        
        return results


# Test runner
if __name__ == "__main__":
    import json
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Load test prompts
    with open("test_prompts.json", "r") as f:
        test_data = json.load(f)
    
    prompts = test_data["test_cases"]
    client = LLMClient()
    
    print("=" * 70)
    print("LLM COST OPTIMIZER - RUNNING ALL 20 PROMPTS")
    print("=" * 70)
    
    results_by_prompt = []
    
    for i, prompt_data in enumerate(prompts, 1):
        prompt_id = prompt_data["id"]
        category = prompt_data["category"]
        difficulty = prompt_data["difficulty"]
        prompt = prompt_data["prompt"]
        
        print(f"\n[{prompt_id}/20] {category.upper()} ({difficulty})")
        print(f"  Prompt: {prompt[:60]}...")
        
        # Run through all models
        results = client.compare_models(prompt)
        
        # Sort by cost
        successful = [r for r in results if r["status"] == "success"]
        successful.sort(key=lambda x: x["cost"])
        
        # Store results
        results_by_prompt.append({
            "id": prompt_id,
            "category": category,
            "difficulty": difficulty,
            "prompt": prompt,
            "results": results
        })
        
        if successful:
            cheapest = successful[0]
            most_expensive = successful[-1]
            print(f"  Cheapest: {cheapest['model_name']} (${cheapest['cost']}, {cheapest['total_tokens']} tokens)")
            print(f"  Most expensive: {most_expensive['model_name']} (${most_expensive['cost']}, {most_expensive['total_tokens']} tokens)")
            print(f"  Savings: {round((1 - cheapest['cost']/most_expensive['cost']) * 100)}% vs most expensive")
    
    # Summary statistics
    print("\n" + "=" * 70)
    print("SUMMARY STATISTICS")
    print("=" * 70)
    
    model_stats = {
        "claude-haiku-4-5-20251001": {"total_cost": 0, "count": 0, "wins": 0},
        "claude-sonnet-4-6": {"total_cost": 0, "count": 0, "wins": 0},
        "gpt-4o-mini": {"total_cost": 0, "count": 0, "wins": 0},
        "mistral-large-latest": {"total_cost": 0, "count": 0, "wins": 0},
    }
    
    for prompt_result in results_by_prompt:
        results = prompt_result["results"]
        successful = [r for r in results if r["status"] == "success"]
        
        if successful:
            cheapest = min(successful, key=lambda x: x["cost"])
            model_stats[cheapest["model"]]["wins"] += 1
        
        for result in results:
            if result["status"] == "success":
                model_stats[result["model"]]["total_cost"] += result["cost"]
                model_stats[result["model"]]["count"] += 1
    
    print("\nPer-Model Stats (across all 20 prompts):")
    for model, stats in model_stats.items():
        if stats["count"] > 0:
            avg_cost = stats["total_cost"] / stats["count"]
            win_pct = (stats["wins"] / 20) * 100
            print(f"\n{model}:")
            print(f"  Average cost per prompt: ${avg_cost:.4f}")
            print(f"  Total cost (20 prompts): ${stats['total_cost']:.2f}")
            print(f"  Won (cheapest): {stats['wins']}/20 ({win_pct:.0f}%)")
    
    # Save results to file
    with open("results.json", "w") as f:
        json.dump(results_by_prompt, f, indent=2)
    
    print("\n" + "=" * 70)
    print("✅ Results saved to results.json")
    print("=" * 70)