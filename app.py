from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os
import json
import io
import PyPDF2
import requests
import chromadb
import uuid
import shutil
from dotenv import load_dotenv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")

# Cleanup ChromaDB on startup (to ensure data is removed from previous sessions)
if os.path.exists(CHROMA_PATH):
    print(f"Cleaning up old ChromaDB data at {CHROMA_PATH}...")
    shutil.rmtree(CHROMA_PATH)

app = FastAPI()
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Ollama Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b") # Default model
OLLAMA_EMBED_MODEL = "nomic-embed-text:latest"

# ChromaDB Configuration (Persistent)
chroma_client = chromadb.PersistentClient(path=os.path.join(BASE_DIR, "chroma_db"))
# Collection for Blueprint Summaries
summary_collection = chroma_client.get_or_create_collection(name="blueprint_summaries")
# Collection for Strategic Sections
sections_collection = chroma_client.get_or_create_collection(name="blueprint_sections")

def get_ollama_embedding(text):
    payload = {
        "model": OLLAMA_EMBED_MODEL,
        "prompt": text,
        "options": {
            "num_thread": 8
        }
    }
    try:
        response = requests.post(f"{OLLAMA_URL}/api/embeddings", json=payload)
        response.raise_for_status()
        return response.json().get("embedding", [])
    except Exception as e:
        print(f"Embedding Error: {e}")
        return []

def call_ollama(prompt, format_json=False, model=None):
    selected_model = model if model else OLLAMA_MODEL
    payload = {
        "model": selected_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": 8192,  # Increase token limit for long plans
            "num_thread": 8,      # Increased usage for speed
            "num_ctx": 4096       # Balanced context for speed + depth
        }
    }
    if format_json:
        payload["format"] = "json"
    
    try:
        response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload)
        response.raise_for_status()
        raw_output = response.json().get("response", "")
        
        # Strip thinking tags if it's a reasoning model and it bled through
        if "<think>" in raw_output and "</think>" in raw_output:
             raw_output = raw_output.split("</think>")[-1].strip()
        
        return raw_output
    except Exception as e:
        print(f"Ollama Error: {e}")
        raise e

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyze")
async def analyze_onboarding(
    request: Request,
    resume: UploadFile = File(None),
    form_data: str = Form(...)
):
    try:
        answers = json.loads(form_data)
        resume_text = ""
        
        # 1. Extract Resume Text
        if resume:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(await resume.read()))
            for page in pdf_reader.pages:
                resume_text += page.extract_text()
        
        # 2. Unified Strategic Synthesis Prompt
        prompt = f"""
        Act as an elite Cognitive Psychologist, Executive Coach, and Data Strategist. 
        Your task is to generate a PREMIER "PlanWise Strategic Blueprint" based on the following raw data.
        
        DATA SOURCE 1: Resume Text
        {resume_text}
        
        DATA SOURCE 2: Onboarding Questionnaire
        {json.dumps(answers, indent=2)}
        
        TASK:
        Synthesize this data into a comprehensive, multidimensional strategy. You must expand on the raw answers using behavioral science to provide deep narrative insights.
        
        Return the result in this STRICT JSON structure:
        {{
            "executive_summary": "A high-level, master synthesis of the strategy and the individual's unique value proposition.",
            "sections": [
                {{
                    "title": "Section Title (e.g., identity, psychology, work_style, goals)",
                    "narrative": "A detailed, 2-3 paragraph professional narrative analysis of this dimension.",
                    "structured_data": {{ "key_metric": "value", "system": "description" }},
                    "insights": ["Specific strategic breakthrough 1", "Actionable advice 2"]
                }}
            ],
            "raw_blueprint": {{ ... populated version of original identity/life/psychology schema ... }}
        }}
        
        Provide sections for: Identity, Life Structure, Psychology, Education & Skills, Health & Lifestyle, Goals, and SWOT.
        Return ONLY valid JSON.
        """

        # 3. Call Ollama for Master Synthesis
        print("PlanWise Engine: Executing Unified Strategic Synthesis...")
        response_text = call_ollama(prompt, format_json=True)
        report_data = json.loads(response_text)
        
        # Generate a unique ID for this strategy session
        blueprint_id = str(uuid.uuid4())
        report_data["blueprint_id"] = blueprint_id

        # 4. Generate Neural Vector Embeddings & PERSIST to ChromaDB
        print(f"Vectorizing & Persisting Strategy {blueprint_id} to ChromaDB...")
        
        # A. Store Executive Summary
        summary_text = report_data.get("executive_summary", "")
        summary_vector = get_ollama_embedding(summary_text)
        
        summary_collection.add(
            ids=[f"summary_{blueprint_id}"],
            embeddings=[summary_vector],
            metadatas=[{"blueprint_id": blueprint_id, "type": "executive_summary"}],
            documents=[summary_text]
        )
        
        # B. Store Individual Sections (Parallelized for Speed)
        def process_section(idx, section):
            section_text = f"{section.get('title', '')}: {section.get('narrative', '')}"
            vector = get_ollama_embedding(section_text)
            
            sections_collection.add(
                ids=[f"section_{blueprint_id}_{idx}"],
                embeddings=[vector],
                metadatas=[{
                    "blueprint_id": blueprint_id, 
                    "title": section.get('title', ''),
                    "type": "strategic_section"
                }],
                documents=[section_text]
            )
            return {"title": section.get("title", ""), "vector": vector}

        sections = report_data.get("sections", [])
        with ThreadPoolExecutor(max_workers=5) as executor:
            sections_data = list(executor.map(lambda x: process_section(x[0], x[1]), enumerate(sections)))

        report_data["embeddings"] = {
            "summary_vector": summary_vector,
            "sections": sections_data
        }

        # 5. Add System Prompt for Chat
        report_data["chat_system_prompt"] = f"""
        You are PlanWise AI, the Elite Strategic Scheduler. You operate in two distinct modes: DISCOVERY and EXECUTION.
        
        CRITICAL OPERATING LOGIC:
        - If the user has NOT provided specific times, events, or commitments for TODAY, you are in DISCOVERY MODE. You MUST NOT provide a timetable.
        - If the user HAS provided even 1-2 specific commitments (meetings, chores, energy level), you are in EXECUTION MODE. You MUST provide the final timetable.
        
        DISCOVERY MODE MISSION:
        Ask exactly 3 hyper-personalized questions based on their Blueprint context:
        1. Professional Commitments (Meetings/Deadlines for today?)
        2. Personal Obligations (Chores/Family for today?)
        3. Current State & Goal (Feelings/Well-being & #1 objective for today?)
        
        CRITICAL KNOWLEDGE:
        Blueprint Summary: {report_data.get('executive_summary', '')}
        Strategic Sections: {json.dumps(report_data.get('sections', []), indent=2)}
        
        TONE: Elite, professional, and personalized.
        """
        

        return JSONResponse(content=report_data)

    except Exception as e:
        print(f"Error in unified analysis: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        message = data.get("message")
        system_prompt = data.get("system_prompt", "You are a helpful assistant.")
        history = data.get("history", [])
        blueprint_id = data.get("blueprint_id")
        
        # 1. Semantic Search for relevant context
        print(f"RAG: Searching context for chat: '{message}'...")
        query_vector = get_ollama_embedding(message)
        
        search_params = {
            "query_embeddings": [query_vector],
            "n_results": 4
        }
        if blueprint_id:
            search_params["where"] = {"blueprint_id": blueprint_id}
            
        search_results = sections_collection.query(**search_params)
        
        context_block = ""
        if search_results.get("documents") and len(search_results["documents"][0]) > 0:
            context_block = "\nRELEVANT STRATEGIC CONTEXT:\n"
            for doc in search_results["documents"][0]:
                context_block += f"- {doc}\n"

        # Format chat history for context
        history_block = ""
        if history:
            history_block = "\nCONVERSATION HISTORY:\n"
            for msg in history[-6:]: # Keep last 6 messages to save context space
                role = "User" if msg['role'] == 'user' else "PlanWise"
                history_block += f"{role}: {msg['content']}\n"
        
        # 2. Construct Augmented Prompt
        full_prompt = f"""
        {system_prompt}
        
        {context_block}
        
        {history_block}
        
        CURRENT USER MESSAGE: {message}
        
        DECISION GATE:
        - Review the CONVERSATION HISTORY. Have the 3 discovery questions been answered yet?
        - If NO (or if this is the start): Focus on the DISCOVERY MODE questions.
        - If YES (the user has provided their daily variables): Transition to EXECUTION MODE and provide the timetable.
        - Do not schedule household chores between 9am-5pm.
        
        FINAL STRATEGIC RESPONSE:
        """
        
        # Use DeepSeek for Chat reasoning
        response_text = call_ollama(full_prompt, model="deepseek-r1:8b")
        
        return JSONResponse(content={"reply": response_text})
    except Exception as e:
        print(f"Error in chat: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/search")
async def search_blueprint(request: Request):
    try:
        data = await request.json()
        query = data.get("query", "")
        n_results = data.get("n_results", 3)
        
        if not query:
            return JSONResponse(content={"error": "Missing query"}, status_code=400)
            
        print(f"Neural Search for: '{query}'...")
        query_vector = get_ollama_embedding(query)
        
        # Search the sections collection
        results = sections_collection.query(
            query_embeddings=[query_vector],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "id": results['ids'][0][i],
                "document": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "relevance_score": 1 - results['distances'][0][i]  # Distance to similarity approx
            })
            
        return JSONResponse(content={"results": formatted_results})
    except Exception as e:
        print(f"Error in search: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    print(f"PlanWise AI Server booting up...")
    print(f"Ollama URL: {OLLAMA_URL}")
    print(f"Ollama Model: {OLLAMA_MODEL}")
    uvicorn.run(app, host="0.0.0.0", port=8000)

@app.on_event("shutdown")
def shutdown_event():
    if os.path.exists(CHROMA_PATH):
        print(f"Cleaning up ChromaDB storage at {CHROMA_PATH}...")
        try:
            # Note: chroma_client should be closed if it has a close method,
            # or we rely on the process ending.
            shutil.rmtree(CHROMA_PATH)
        except Exception as e:
            print(f"Shutdown cleanup failed: {e}")
