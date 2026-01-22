import json
import os
from typing import Dict, Any
from pydantic import BaseModel
from dotenv import load_dotenv
import requests

from ddgs import DDGS
from langchain_google_genai import ChatGoogleGenerativeAI

# Extra tools
from langchain_community.tools import WikipediaQueryRun, ArxivQueryRun
from langchain_community.utilities import WikipediaAPIWrapper, ArxivAPIWrapper

#-------------------- Load Environment-----------------------------
# ==============================
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY missing in .env file")

# LLM Setup ( Gemini API)
# ==============================
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.3
)

# Input Schema
# ==============================
class WorkflowInput(BaseModel):
    query: str

# Basic Web Search (DDGS)
# ==============================
def web_search(query: str) -> str:
    results = DDGS().text(query, max_results=5)
    if not results:
        return "No research data found."

    bodies = []
    for res in results:
        if "body" in res:
            bodies.append(res["body"])

    return "\n".join(bodies)

# Extra Tools (Safe Mode)
# ==============================

# Wikipedia
wiki_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=1500)
wiki_tool = WikipediaQueryRun(api_wrapper=wiki_wrapper)

# Arxiv
arxiv_wrapper = ArxivAPIWrapper(top_k_results=2, doc_content_chars_max=2000)
arxiv_tool = ArxivQueryRun(api_wrapper=arxiv_wrapper)

# Calculator
def calculator(expression: str) -> str:
    try:
        return str(eval(expression))
    except Exception:
        return "Invalid expression"

# Weather (Open-Meteo – free)
def get_weather(city: str) -> str:
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
        geo = requests.get(geo_url, timeout=10).json()

        if "results" not in geo:
            return "City not found."

        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]

        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        weather = requests.get(weather_url, timeout=10).json()

        temp = weather["current_weather"]["temperature"]
        wind = weather["current_weather"]["windspeed"]

        return f"Temperature: {temp}°C, Wind: {wind} km/h"

    except Exception as e:
        return f"Weather lookup failed: {e}"

# Multi-Agent Workflow
# ==============================

def run_multi_agent_workflow(workflow_input: WorkflowInput) -> Dict[str, Any]:
    query = workflow_input.query

    # -------- Agent 1: Researcher --------
    research_parts = []

    # DDGS (always)
    research_parts.append("Web Search:\n" + web_search(query))

    # Wikipedia (optional)
    try:
        research_parts.append("Wikipedia:\n" + wiki_tool.run(query))
    except:
        pass

    # Arxiv (optional)
    try:
        research_parts.append("Arxiv:\n" + arxiv_tool.run(query))
    except:
        pass

    research = "\n\n".join(research_parts)

    # -------- Agent 2: Summarizer --------
    summary_prompt = f"""
Convert the following research notes into structured JSON:

Research:
{research}

Return JSON EXACTLY like:
{{
   "executive_summary": "...",
   "action_items": ["...", "..."]
}}
"""

    summary_result = llm.invoke(summary_prompt)
    raw_summary = summary_result.content

    try:
        summary_json = json.loads(raw_summary)
    except:
        summary_json = {
            "executive_summary": raw_summary,
            "action_items": []
        }

    # -------- Agent 3: Email Writer --------
    email_prompt = f"""
Write a short professional business email based on this executive summary:

{summary_json['executive_summary']}

Return only the email body text.
"""

    email_result = llm.invoke(email_prompt)

    return {
        "raw_research": research,
        "raw_summary": summary_json,
        "final_email": email_result.content
    }

# ==============================
# CLI Test
# ==============================
if __name__ == "__main__":
    test = run_multi_agent_workflow(WorkflowInput(query="Latest AI trends in India"))
    print(json.dumps(test, indent=2))
