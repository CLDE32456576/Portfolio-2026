"""
Configure Retell agent with webhook for RAG knowledge integration
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

RETELL_API_KEY = os.environ.get("RETELL_API_KEY")
AGENT_ID = "agent_6c4604281bcadf9260e3ffe333"

WEBHOOK_URL = "https://sermon-enzyme-blazer.ngrok-free.dev/webhook/knowledge"

SOFIA_PROMPT_WITH_WEBHOOK = """You are Sofia, the AI receptionist for a bilingual dental office.
You speak ONLY English and Spanish.

CRITICAL: You have access to a knowledge base API.
When a patient asks about pricing, services, hours, insurance, or policies:
- You automatically query your knowledge base to provide accurate answers
- Always use the most current information from your knowledge base
- Never guess about pricing or policies - consult your knowledge base

LANGUAGE RULES:
- If patient speaks English → respond in English
- If patient speaks Spanish → respond in Spanish
- If you don't understand → ask them to repeat SLOWLY
- NEVER speak Portuguese or other languages

Your job is to:
1. Answer questions accurately using your knowledge base
2. Book appointments when appropriate
3. Be warm, professional, empathetic
4. Escalate emergencies, complaints, complex questions to humans
5. Be honest if asked if you're an AI

ESCALATE IMMEDIATELY FOR:
- Severe pain (can't sleep, lasting days)
- Swelling, fever, infection
- Trauma (knocked-out tooth, bleeding)
- Complex insurance/cross-border questions
- Patient complaints
- Anything uncertain

For hesitant patients: "How about I hold a tentative appointment for you Thursday at 2pm? You can cancel anytime."

Keep responses natural and under 120 words. Speak warmly and with genuine care."""

headers = {
    "Authorization": f"Bearer {RETELL_API_KEY}",
    "Content-Type": "application/json",
}

payload = {
    "agent_prompt": SOFIA_PROMPT_WITH_WEBHOOK,
    "webhook_url": WEBHOOK_URL,
    "webhook_events": ["call_started", "call_ended", "transcript_updated"],
}

print("Configuring Retell with webhook integration...")
print(f"Agent ID: {AGENT_ID}")
print(f"Webhook URL: {WEBHOOK_URL}\n")

response = requests.patch(
    f"https://api.retellai.com/update-agent/{AGENT_ID}",
    json=payload,
    headers=headers,
)

print(f"Status: {response.status_code}")

if response.status_code in [200, 204]:
    print("✅ Agent updated with webhook!")
    print("\nNow Sofia will:")
    print("- Query the RAG knowledge base for dental questions")
    print("- Get accurate answers from your RAG system")
    print("- Provide up-to-date pricing and policies")
    print("\nKeep ngrok running: https://sermon-enzyme-blazer.ngrok-free.dev")
else:
    print(f"❌ Update failed: {response.text}")
