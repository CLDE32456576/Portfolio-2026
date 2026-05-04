from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from llm_client import LLMClient
from quality_scorer import QualityScorer
from dotenv import load_dotenv
import asyncio

load_dotenv()

app = FastAPI(title="LLM Cost Optimizer")
llm_client = LLMClient()
quality_scorer = QualityScorer()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/dashboard")
async def dashboard():
    return FileResponse("static/index.html")

@app.post("/optimize")
async def optimize_prompt(prompt: str):
    """Run prompt through all models, score quality, return ROI comparison"""
    results = await asyncio.to_thread(llm_client.compare_models, prompt)
    
    # Score each
    for result in results:
        if result.get("status") == "success":
            scores = quality_scorer.score_response(
                prompt, 
                result.get("full_response", "")
            )
            result["quality_scores"] = scores
            result["quality_overall"] = scores.get("overall", 0)
            
            # ROI
            cost = result.get("cost", 0.0001)
            quality = result.get("quality_overall", 0)
            result["roi"] = round(quality / cost, 2) if cost > 0 else 0
    
    # Sort by ROI
    successful = [r for r in results if r.get("status") == "success"]
    successful.sort(key=lambda x: x.get("roi", 0), reverse=True)
    
    return {
        "prompt": prompt[:100] + "...",
        "results": successful,
        "recommendation": successful[0] if successful else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)