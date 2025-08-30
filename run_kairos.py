# run_kairos.py
import os
import requests
import sys
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime
from reporter import create_and_save_google_doc

# --- Configuration from GitHub Secrets ---
HF_ADVERSARY_URL = os.environ.get("HF_ADVERSARY_URL")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- Initialize LLM ---
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=GEMINI_API_KEY, temperature=0.7)

# --- Agent Definitions ---
def ideation_agent(topic: str) -> str:
    print(f"---KAIROS: Running Ideation Agent for topic: {topic}---")
    prompt = f"You are a creative venture capitalist. Generate a single, interesting, and novel startup idea related to the topic of {topic}. The idea should be a short, one-sentence concept."
    idea = llm.invoke(prompt).content
    print(f"Generated idea: {idea}")
    return idea

def news_agent(topic: str) -> str:
    print(f"---KAIROS: Running News Agent for topic: {topic}---")
    prompt = f"You are a news analyst. Find the top 3 most significant news articles and developments from the past week on the topic of '{topic}' and write a concise, one-paragraph summary for a weekly intelligence briefing."
    news_summary = llm.invoke(prompt).content
    print(f"Generated news summary.")
    return news_summary

# --- Main Orchestration Logic ---
def run_cycle(topic: str):
    print(f"Starting Kairós cycle for topic: {topic}")
    
    # 1. Ideation
    startup_idea = ideation_agent(topic)
    
    # 2. Call Ethical Adversary Service
    print("---KAIROS: Calling Ethical Adversary Service---")
    try:
        response = requests.post(f"{HF_ADVERSARY_URL}/analyze", json={"product_idea": startup_idea}, timeout=600)
        response.raise_for_status()
        analysis_results = response.json()
    except Exception as e:
        print(f"Failed to get analysis from Ethical Adversary service. Error: {e}")
        return

    # 3. Report the Analysis
    report_title = f"Ethical Adversary Analysis: {startup_idea}"
    report_content = (
        f"Product Idea: {startup_idea}\n\n---\n\n"
        f"# Product Viability Report (Blue Team)\n\n{analysis_results.get('viability_report', 'N/A')}\n\n"
        f"---\n\n"
        f"# Risk Report (Red Team)\n\n{analysis_results.get('red_team_report', 'N/A')}\n\n"
        f"---\n\n"
        f"# Action Plan (Resolution)\n\n{analysis_results.get('action_plan', 'N/A')}"
    )
    create_and_save_google_doc(title=report_title, content=report_content)

    # 4. Gather and Report News
    news_summary = news_agent(topic)
    news_title = f"Weekly Intelligence Briefing: {topic} - {datetime.now().strftime('%Y-%m-%d')}"
    create_and_save_google_doc(title=news_title, content=news_summary)
    
    print("Kairós cycle completed successfully.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        topic_arg = sys.argv[1]
        run_cycle(topic_arg)
    else:
        print("No topic provided. Please run with an argument, e.g., 'python run_kairos.py Tech'")
