import sqlite3
import json
from datetime import datetime
import os

class SalesDatabase:
    def __init__(self, db_name: str = "sales.db"):
        self.db_name = db_name
        self.init_db()
    
    def init_db(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Leads table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY,
                company_name TEXT NOT NULL,
                city TEXT,
                owner_name TEXT,
                email TEXT UNIQUE,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'new'
            )
        ''')
        
        # Outreach table (track every message sent)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS outreach (
                id INTEGER PRIMARY KEY,
                lead_id INTEGER NOT NULL,
                message_type TEXT,
                content TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'sent',
                notes TEXT,
                FOREIGN KEY(lead_id) REFERENCES leads(id)
            )
        ''')
        
        # Responses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY,
                lead_id INTEGER NOT NULL,
                response_type TEXT,
                content TEXT,
                received_at TIMESTAMP,
                status TEXT DEFAULT 'new',
                FOREIGN KEY(lead_id) REFERENCES leads(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_lead(self, company_name: str, city: str = "", owner_name: str = "", 
                 email: str = "", phone: str = "") -> int:
        """Add a new lead"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO leads (company_name, city, owner_name, email, phone)
                VALUES (?, ?, ?, ?, ?)
            ''', (company_name, city, owner_name, email, phone))
            
            conn.commit()
            lead_id = cursor.lastrowid
            print(f"✅ Added lead: {company_name} (ID: {lead_id})")
            return lead_id
        
        except sqlite3.IntegrityError:
            print(f"⚠️ Lead already exists: {company_name}")
            cursor.execute('SELECT id FROM leads WHERE email = ?', (email,))
            return cursor.fetchone()[0]
        
        finally:
            conn.close()
    
    def log_outreach(self, lead_id: int, message_type: str, content: str, notes: str = ""):
        """Log an outreach attempt"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO outreach (lead_id, message_type, content, notes)
            VALUES (?, ?, ?, ?)
        ''', (lead_id, message_type, content, notes))
        
        conn.commit()
        conn.close()
        print(f"✅ Logged outreach for lead {lead_id}")
    
    def get_lead(self, lead_id: int) -> dict:
        """Get lead details"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM leads WHERE id = ?', (lead_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_all_leads(self, status: str = None) -> list:
        """Get all leads, optionally filtered by status"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if status:
            cursor.execute('SELECT * FROM leads WHERE status = ? ORDER BY created_at DESC', (status,))
        else:
            cursor.execute('SELECT * FROM leads ORDER BY created_at DESC')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_outreach_history(self, lead_id: int) -> list:
        """Get all outreach for a lead"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM outreach 
            WHERE lead_id = ? 
            ORDER BY sent_at DESC
        ''', (lead_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_lead_status(self, lead_id: int, status: str):
        """Update lead status (new, contacted, replied, customer, etc)"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE leads SET status = ? WHERE id = ?', (status, lead_id))
        conn.commit()
        conn.close()
        print(f"✅ Updated lead {lead_id} status to: {status}")
    
    def log_response(self, lead_id: int, response_type: str, content: str):
        """Log a response from a lead"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO responses (lead_id, response_type, content, received_at)
            VALUES (?, ?, ?, ?)
        ''', (lead_id, response_type, content, datetime.now()))
        
        conn.commit()
        conn.close()
        print(f"✅ Logged response for lead {lead_id}")
        
        # Update lead status to "replied"
        self.update_lead_status(lead_id, "replied")
    
    def get_dashboard_stats(self) -> dict:
        """Get summary stats for dashboard"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM leads')
        total_leads = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'replied'")
        replied = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'customer'")
        customers = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM outreach")
        total_outreach = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_leads": total_leads,
            "replied": replied,
            "customers": customers,
            "total_outreach": total_outreach,
            "reply_rate": round((replied / total_leads * 100) if total_leads > 0 else 0, 1)
        }


# Test it
if __name__ == "__main__":
    db = SalesDatabase()
    
    # Add a lead
    lead_id = db.add_lead(
        company_name="Eastlake Implant & Laser",
        city="Chula Vista, CA",
        owner_name="Dr. Eduardo Diaz",
        email="info@eastlakeimplant.com",
        phone="(619) 216-0111"
    )
    
    # Log outreach
    db.log_outreach(
        lead_id=lead_id,
        message_type="email",
        content="Subject: The implant consultations calling after hours...",
        notes="Personalized message about after-hours calls"
    )
    
    # Get stats
    stats = db.get_dashboard_stats()
    print(f"\n📊 Dashboard Stats: {stats}")
    
    # Get all leads
    leads = db.get_all_leads()
    print(f"\n📋 All Leads: {len(leads)} total")
    for lead in leads:
        print(f"  - {lead['company_name']} ({lead['status']})")