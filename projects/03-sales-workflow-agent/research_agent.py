from anthropic import Anthropic
import httpx
import json
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

class ResearchAgent:
    def __init__(self):
        self.client = Anthropic()
        self.model = "claude-opus-4-7"
    
    def search_company(self, company_name: str, city: str = "") -> dict:
        """
        Research a company: find website, owner, pain points
        """
        print(f"\n🔍 Researching {company_name}...")
        
        search_prompt = f"""You are a sales researcher. Find information about this company:
        
Company: {company_name}
Location: {city if city else "USA"}

Return ONLY valid JSON with this structure:
{{
  "company_name": "...",
  "likely_owner_titles": ["Practice Owner", "Office Manager", ...],
  "industry": "dental/medical/professional services",
  "pain_points": [
    "Missed phone calls cost revenue",
    "Spanish-speaking patients underserved",
    "After-hours calls go to voicemail"
  ],
  "typical_hours": "9am-5pm M-F",
  "website_domain": "example.com",
  "notes": "Additional context"
}}

Think step by step:
1. What industry is this company in?
2. Who makes decisions? (owner, manager, etc)
3. What problems do they face?
4. When are they busiest?
5. What's their online presence?

Return only JSON, no other text."""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": search_prompt}]
            )
            
            text = response.content[0].text.strip()
            
            
            start = text.find('{')
            end = text.rfind('}') + 1
            json_str = text[start:end]
            
            research = json.loads(json_str)
            print(f"  ✅ Found: {research.get('company_name')}")
            print(f"     Pain points: {', '.join(research.get('pain_points', [])[:2])}")
            
            return research
        
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            return {
                "company_name": company_name,
                "pain_points": [],
                "error": str(e)
            }
    
    def generate_message(self, company_info: dict, recipient_title: str = "Owner") -> str:
        """
        Write a personalized cold message based on company research
        """
        print(f"  ✍️ Writing personalized message...")
        
        pain_points = company_info.get("pain_points", [])
        company_name = company_info.get("company_name", "")
        
        message_prompt = f"""Write a short, personalized cold outreach email for a sales pitch.

Company: {company_name}
Recipient: {recipient_title}
Their pain points:
{chr(10).join(f"- {p}" for p in pain_points[:3])}

The pitch: Bilingual AI receptionist that handles phone calls 24/7, books appointments, 
answers pricing questions. English + Spanish. $3,500 setup, $1,500/month.

Write an email that:
1. Opens with ONE specific pain point from their business (not generic)
2. Shows you understand their situation
3. Offers a free 2-week pilot
4. Has a specific CTA (call number or reply)
5. Is SHORT (under 100 words)

Return ONLY the email text, no JSON, no preamble."""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                messages=[{"role": "user", "content": message_prompt}]
            )
            
            message = response.content[0].text.strip()
            print(f"  ✅ Message generated ({len(message)} chars)")
            return message
        
        except Exception as e:
            print(f"  ❌ Error generating message: {str(e)}")
            return ""


if __name__ == "__main__":
    agent = ResearchAgent()
    
    company = agent.search_company("Eastlake Implant & Laser", "Chula Vista, CA")
    
    if company.get("company_name"):
        message = agent.generate_message(company, "Practice Owner")
        print(f"\n📧 Generated Message:\n{message}")