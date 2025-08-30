# run_kairos.py
import os
import requests
import sys
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime
from reporter import create_and_save_google_doc
from google.oauth2.service_account import Credentials

# --- Configuration from GitHub Secrets ---
HF_ADVERSARY_URL = os.environ.get("HF_SPACE_URL")

# --- Unified Authentication using Service Account ---
# This is the standard and correct method for authenticating in a non-Google environment like GitHub Actions.
try:
    # Load the entire JSON string from the environment variable
    service_account_info = json.loads(os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON"))
    
    # Define the necessary scopes for Gemini (Cloud Platform) and Drive/Docs
    scopes = [
        'https://www.googleapis.com/auth/cloud-platform',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/documents'
    ]
    
    # Create credentials from the service account info
    credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)

except Exception as e:
    print(f"ERROR: Could not load Google Service Account credentials. Make sure the GOOGLE_SERVICE_ACCOUNT_JSON secret is set correctly. Details: {e}")
    sys.exit(1) # Exit with an error code

# --- Initialize LLM with Service Account Credentials ---
# The LangChain client will automatically use the provided credentials for authentication.
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    credentials=credentials,
    temperature=0.7
)

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
        # Create a failure report if the service call fails
        create_and_save_google_doc(
            title=f"FAILED Analysis for {topic} - {datetime.now().strftime('%Y-%m-%d')}",
            content=f"The Ethical Adversary service failed to process the idea '{startup_idea}'.\n\nError: {e}"
        )
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
