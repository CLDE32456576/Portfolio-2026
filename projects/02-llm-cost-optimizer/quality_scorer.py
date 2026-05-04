from anthropic import Anthropic
import json
from dotenv import load_dotenv

load_dotenv()

class QualityScorer:
    def __init__(self):
        self.client = Anthropic()
    
    def score_response(self, prompt: str, response: str, category: str = "general") -> dict:
        """
        Use Claude to score a response quality (1-10 scale)
        Criteria: accuracy, clarity, completeness, relevance
        """
        
        scoring_prompt = f"""You are an expert evaluator. Score this response OBJECTIVELY on the following criteria (1-10 scale, where 10 is perfect).

TASK CATEGORY: {category}
ORIGINAL PROMPT: {prompt[:300]}...

RESPONSE TO EVALUATE:
{response[:500]}...

Score on these criteria:
1. ACCURACY (1-10): How correct and factually accurate is the response?
2. CLARITY (1-10): How clear and easy to understand is the response?
3. COMPLETENESS (1-10): Does it fully address what was asked?
4. RELEVANCE (1-10): How directly does it answer the prompt?

IMPORTANT: Return ONLY valid JSON, nothing else. No markdown, no explanation.

Example format:
{{"accuracy": 9, "clarity": 8, "completeness": 9, "relevance": 9, "overall": 9}}

Now score this response:"""
        
        try:
            response_msg = self.client.messages.create(
                model="claude-opus-4-6",  # CHANGED FROM claude-3-5-haiku
                max_tokens=100,
                messages=[{"role": "user", "content": scoring_prompt}]
            )
            
            text = response_msg.content[0].text.strip()
            
            # Extract JSON
            start = text.find('{')
            end = text.rfind('}') + 1
            
            if start == -1 or end == 0:
                return {
                    "accuracy": 0,
                    "clarity": 0,
                    "completeness": 0,
                    "relevance": 0,
                    "overall": 0,
                    "error": "Could not parse JSON"
                }
            
            json_str = text[start:end]
            scores = json.loads(json_str)
            
            # Calculate overall if not provided
            if "overall" not in scores:
                scores["overall"] = round(
                    (scores.get("accuracy", 0) + scores.get("clarity", 0) + 
                     scores.get("completeness", 0) + scores.get("relevance", 0)) / 4
                )
            
            return scores
        
        except Exception as e:
            return {
                "accuracy": 0,
                "clarity": 0,
                "completeness": 0,
                "relevance": 0,
                "overall": 0,
                "error": str(e)
            }
    
    def compare_quality(self, prompt: str, responses: list, category: str = "general") -> list:
        """
        Score multiple responses and rank by quality
        responses: list of (model_name, response_text) tuples
        """
        scored = []
        
        for model_name, response_text in responses:
            print(f"    Scoring {model_name}...", end=" ", flush=True)
            scores = self.score_response(prompt, response_text, category)
            scored.append({
                "model": model_name,
                "scores": scores,
            })
            print("✅")
        
        # Sort by overall score
        scored.sort(key=lambda x: x["scores"].get("overall", 0), reverse=True)
        return scored