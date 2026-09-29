import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from serpapi import GoogleSearch
from google import genai

app = FastAPI(title="IndicPulse AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

class QueryRequest(BaseModel):
    query: str
    location: str = "West Bengal, India"
    language: str = "Bengali"

def fetch_serp_data(query: str, location: str) -> str:
    if not SERPAPI_KEY:
        return "SerpApi key not configured."
    try:
        search_query = f"{query} {location}"
        params = {
            "q": search_query,
            "api_key": SERPAPI_KEY,
            "engine": "google",
            "gl": "in",
            "hl": "en",
            "num": 5
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        
        snippets = []
        if "organic_results" in results:
            for item in results["organic_results"][:4]:
                snippet = item.get("snippet") or item.get("title")
                if snippet:
                    snippets.append(snippet)
        
        return "\n".join(snippets) if snippets else "No direct results found."
    except Exception as e:
        return f"SerpApi Error: {str(e)}"

@app.get("/")
def health():
    return {"status": "ok", "service": "IndicPulse AI Backend Live"}

@app.post("/ask")
def ask(payload: QueryRequest):
    if not GEMINI_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured.")

    search_context = fetch_serp_data(payload.query, payload.location)

    try:
        client = genai.Client(api_key=GEMINI_KEY)
        prompt = f"""
Tumi IndicPulse AI shohayak. Gramin manushder shohoj vashay totho dewa tomar kaj.

User Proshno: {payload.query}
User Location: {payload.location}
Bhasha: {payload.language}

Live SerpApi Search Context:
\"\"\"
{search_context}
\"\"\"

Nirdesh:
1. Uporer real-time tother upor vitti kore shohoj Bangla vashay 2-3 line-e sposto uttor dao.
2. Mandi rate ba Sarkari prokolper takar poriman thakle thikbhabe ullekh koro.
3. Kotha bolar vongi te shorol bhabe uttor dao jate shune shobai bujhte pare.
"""
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )

        return {
            "query": payload.query,
            "response": response.text,
            "raw_context": search_context
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

