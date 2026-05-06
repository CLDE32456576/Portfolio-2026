from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from workflow import SalesWorkflow
from database import SalesDatabase
from dotenv import load_dotenv
from typing import List
import json

load_dotenv()

app = FastAPI(title="Sales Workflow Agent")
workflow = SalesWorkflow()
db = SalesDatabase()

# Serve static files (dashboard)
import os
if not os.path.exists("static"):
    os.makedirs("static")

# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/")
async def root():
    """Serve the dashboard"""
    return FileResponse("static/index.html")

@app.get("/api/stats")
async def get_stats():
    """Get current pipeline stats"""
    stats = db.get_dashboard_stats()
    return stats

@app.get("/api/leads")
async def get_leads(status: str = None):
    """Get all leads, optionally filtered by status"""
    leads = db.get_all_leads(status)
    return {"leads": leads, "count": len(leads)}

@app.get("/api/leads/{lead_id}")
async def get_lead_detail(lead_id: int):
    """Get details for one lead"""
    lead = db.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Get outreach history
    history = db.get_outreach_history(lead_id)
    
    return {
        "lead": lead,
        "outreach_history": history
    }

@app.post("/api/process")
async def process_target(company_name: str, city: str = "", owner_name: str = "", 
                        email: str = "", phone: str = ""):
    """
    Process one target company
    Example: /api/process?company_name=AD%20Dental&city=Chula%20Vista&owner_name=Dr.%20Ana&email=info@ad.com
    """
    try:
        result = workflow.process_target(
            company_name=company_name,
            city=city,
            owner_name=owner_name,
            email=email,
            phone=phone
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/process-batch")
async def process_batch(targets: List[dict] = Body(...)):
    """
    Process multiple targets at once
    Body: [{"company_name": "...", "city": "...", "email": "...", "phone": "..."}, ...]
    """
    try:
        results = workflow.process_batch(targets)
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/mark-sent/{lead_id}")
async def mark_sent(lead_id: int):
    """Mark a lead as 'sent' (message was sent to them)"""
    db.update_lead_status(lead_id, "sent")
    return {"status": "success", "lead_id": lead_id, "message": "Marked as sent"}

@app.post("/api/log-response/{lead_id}")
async def log_response(lead_id: int, response_type: str, content: str):
    """Log a response from a lead (they replied)"""
    db.log_response(lead_id, response_type, content)
    return {"status": "success", "lead_id": lead_id, "message": "Response logged"}

@app.post("/api/mark-customer/{lead_id}")
async def mark_customer(lead_id: int):
    """Mark a lead as a paying customer"""
    db.update_lead_status(lead_id, "customer")
    return {"status": "success", "lead_id": lead_id, "message": "Marked as customer!"}

@app.get("/api/next-actions")
async def next_actions():
    """Get suggested next actions"""
    stats = db.get_dashboard_stats()
    leads = db.get_all_leads()
    
    replied = [l for l in leads if l['status'] == 'replied']
    contacted = [l for l in leads if l['status'] == 'contacted']
    
    return {
        "stats": stats,
        "follow_ups_needed": [{"id": l['id'], "company": l['company_name'], "email": l['email']} for l in replied],
        "waiting_for_replies": len(contacted),
        "suggested_action": "Follow up with those who replied" if replied else "Wait for responses or add more targets"
    }

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)