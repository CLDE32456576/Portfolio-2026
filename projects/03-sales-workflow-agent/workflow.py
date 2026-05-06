from research_agent import ResearchAgent
from database import SalesDatabase
import json
from datetime import datetime

class SalesWorkflow:
    def __init__(self):
        self.researcher = ResearchAgent()
        self.db = SalesDatabase()
    
    def process_target(self, company_name: str, city: str = "", owner_name: str = "", 
                       email: str = "", phone: str = "") -> dict:
        """
        Complete workflow for one target:
        1. Add to database
        2. Research the company
        3. Generate personalized message
        4. Log the outreach
        5. Return everything for review
        """
        
        print(f"\n" + "="*70)
        print(f"PROCESSING: {company_name}")
        print("="*70)
        
        # Step 1: Add to database
        lead_id = self.db.add_lead(
            company_name=company_name,
            city=city,
            owner_name=owner_name,
            email=email,
            phone=phone
        )
        
        # Step 2: Research
        company_info = self.researcher.search_company(company_name, city)
        
        # Step 3: Generate message
        message = self.researcher.generate_message(company_info, owner_name or "Owner")
        
        # Step 4: Log outreach
        self.db.log_outreach(
            lead_id=lead_id,
            message_type="email",
            content=message,
            notes=json.dumps({
                "pain_points": company_info.get("pain_points", []),
                "industry": company_info.get("industry", ""),
                "website": company_info.get("website_domain", "")
            })
        )
        
        # Step 5: Mark as contacted
        self.db.update_lead_status(lead_id, "contacted")
        
        # Return everything
        result = {
            "lead_id": lead_id,
            "company_name": company_name,
            "owner_name": owner_name,
            "email": email,
            "phone": phone,
            "research": company_info,
            "message": message,
            "status": "ready_to_send"
        }
        
        return result
    
    def process_batch(self, targets: list) -> list:
        """
        Process multiple targets at once
        targets = [
            {"company_name": "...", "city": "...", "email": "...", "phone": "..."},
            ...
        ]
        """
        results = []
        
        for target in targets:
            try:
                result = self.process_target(
                    company_name=target.get("company_name"),
                    city=target.get("city", ""),
                    owner_name=target.get("owner_name", ""),
                    email=target.get("email", ""),
                    phone=target.get("phone", "")
                )
                results.append(result)
            except Exception as e:
                print(f"❌ Error processing {target.get('company_name')}: {str(e)}")
                results.append({
                    "company_name": target.get("company_name"),
                    "error": str(e)
                })
        
        return results
    
    def display_result(self, result: dict):
        """Pretty print a result for review"""
        if "error" in result:
            print(f"\n❌ Error: {result['error']}")
            return
        
        print(f"\n{'='*70}")
        print(f"REVIEW & SEND: {result['company_name']}")
        print(f"{'='*70}")
        print(f"\n📋 Lead Details:")
        print(f"  Company: {result['company_name']}")
        print(f"  Owner: {result['owner_name']}")
        print(f"  Email: {result['email']}")
        print(f"  Phone: {result['phone']}")
        
        print(f"\n🔍 Research:")
        research = result['research']
        print(f"  Industry: {research.get('industry', 'N/A')}")
        print(f"  Pain Points:")
        for pain in research.get('pain_points', [])[:3]:
            print(f"    - {pain}")
        
        print(f"\n📧 Generated Message:")
        print(f"  {result['message']}")
        
        print(f"\n{'='*70}")
        print(f"Status: {result['status']}")
        print(f"Lead ID: {result['lead_id']} (use this to track responses)")
        print(f"{'='*70}\n")
    
    def get_next_actions(self) -> dict:
        """
        AI-suggested next actions based on lead status
        """
        print("\n" + "="*70)
        print("SUGGESTED NEXT ACTIONS")
        print("="*70)
        
        leads = self.db.get_all_leads()
        
        contacted = [l for l in leads if l['status'] == 'contacted']
        replied = [l for l in leads if l['status'] == 'replied']
        customers = [l for l in leads if l['status'] == 'customer']
        
        print(f"\n📊 Current Status:")
        print(f"  Total leads: {len(leads)}")
        print(f"  Contacted: {len(contacted)}")
        print(f"  Replied: {len(replied)}")
        print(f"  Customers: {len(customers)}")
        
        print(f"\n📞 Action Items:")
        
        if replied:
            print(f"\n  ✅ FOLLOW UP NEEDED ({len(replied)} leads):")
            for lead in replied[:5]:
                print(f"     - {lead['company_name']} (replied, needs follow-up)")
                print(f"       Email: {lead['email']}")
        
        if contacted and not replied:
            print(f"\n  🔔 WAIT FOR RESPONSES ({len(contacted)} leads):")
            print(f"     Monitor these for replies over next 3-5 days")
        
        if len(leads) < 10:
            print(f"\n  📧 MORE OUTREACH NEEDED:")
            print(f"     Currently at {len(leads)} leads. Target: 15-20.")
            print(f"     Suggested: Add 5-10 more targets this week.")
        
        return {
            "total": len(leads),
            "contacted": len(contacted),
            "replied": len(replied),
            "customers": len(customers)
        }


# Test it
if __name__ == "__main__":
    workflow = SalesWorkflow()
    
    # Your tier 1 dental targets
    targets = [
        {
            "company_name": "AD Dental",
            "city": "Chula Vista, CA",
            "owner_name": "Dr. Ana Beatriz Dominguez",
            "email": "info@addental.com",
            "phone": "(619) 691-0121"
        },
        {
            "company_name": "Eastlake Implant & Laser",
            "city": "Chula Vista, CA",
            "owner_name": "Dr. Eduardo Diaz",
            "email": "info@eastlakeimplant.com",
            "phone": "(619) 216-0111"
        },
        {
            "company_name": "AZ Dental",
            "city": "Phoenix, AZ",
            "owner_name": "Dr. Brian Tong",
            "email": "info@azdentaloffice.com",
            "phone": "(602) 455-0505"
        }
    ]
    
    # Process all targets
    results = workflow.process_batch(targets)
    
    # Display each result
    for result in results:
        workflow.display_result(result)
    
    # Get next actions
    workflow.get_next_actions()