import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from serpapi import GoogleSearch
from google import genai

app = FastAPI(title="IndicPulse AI", version="1.0.0")

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
        search_query = f"{query} in {location}"
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

@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>IndicPulse AI</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: #0f172a; color: #f8fafc; min-height: 100vh; display: flex; flex-direction: column; justify-content: space-between; align-items: center; padding: 28px 16px; }
        .header { text-align: center; }
        .header h1 { font-size: 26px; color: #38bdf8; font-weight: 700; letter-spacing: -0.5px; }
        .header p { font-size: 13px; color: #94a3b8; margin-top: 6px; }
        .tag { display: inline-block; background: rgba(56, 189, 248, 0.12); color: #38bdf8; padding: 4px 10px; border-radius: 999px; font-size: 11px; margin-top: 10px; font-weight: 600; border: 1px solid rgba(56, 189, 248, 0.25); }
        .main-card { width: 100%; max-width: 440px; background: #1e293b; border-radius: 20px; padding: 22px; border: 1px solid #334155; min-height: 240px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
        .query-label { font-size: 12px; font-weight: 600; text-transform: uppercase; color: #64748b; margin-bottom: 4px; }
        .query-text { font-size: 15px; color: #cbd5e1; margin-bottom: 16px; min-height: 22px; }
        .response-label { font-size: 12px; font-weight: 600; text-transform: uppercase; color: #38bdf8; margin-bottom: 4px; }
        .response-text { font-size: 15px; line-height: 1.6; color: #f1f5f9; }
        .status { font-size: 13px; color: #38bdf8; text-align: center; min-height: 20px; }
        .controls { display: flex; flex-direction: column; align-items: center; margin-bottom: 20px; }
        .mic-btn { width: 80px; height: 80px; border-radius: 50%; background: linear-gradient(135deg, #0284c7, #2563eb); border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 20px rgba(37, 99, 235, 0.4); transition: transform 0.2s, background 0.2s; -webkit-tap-highlight-color: transparent; }
        .mic-btn:active { transform: scale(0.95); }
        .mic-btn.active { background: linear-gradient(135deg, #ef4444, #dc2626); box-shadow: 0 0 25px rgba(239, 68, 68, 0.6); animation: pulse 1.4s infinite; }
        .mic-btn svg { width: 34px; height: 34px; fill: #ffffff; }
        .mic-caption { font-size: 13px; color: #94a3b8; margin-top: 12px; }
        @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.08); } 100% { transform: scale(1); } }
    </style>
</head>
<body>
    <div class="header">
        <h1>IndicPulse AI</h1>
        <p>Voice-First Hyperlocal Intelligence for Rural India</p>
        <span class="tag">FastAPI • SerpApi • Gemini</span>
    </div>

    <div class="main-card">
        <div>
            <div class="query-label">Input Query</div>
            <div class="query-text" id="queryDisplay">Tap mic to speak...</div>
        </div>
        <div>
            <div class="response-label">Assistant Response</div>
            <div class="response-text" id="responseDisplay">Ready. Tap the microphone to ask about local schemes, mandi prices, or notifications.</div>
        </div>
    </div>

    <div class="status" id="statusMessage"></div>

    <div class="controls">
        <button class="mic-btn" id="micButton" onclick="toggleSpeech()">
            <svg viewBox="0 0 24 24"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/><path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>
        </button>
        <div class="mic-caption" id="micCaption">Tap to Speak</div>
    </div>

    <script>
        const micButton = document.getElementById('micButton');
        const queryDisplay = document.getElementById('queryDisplay');
        const responseDisplay = document.getElementById('responseDisplay');
        const statusMessage = document.getElementById('statusMessage');
        let recognition;
        let isRecording = false;

        const SpeechAPI = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (SpeechAPI) {
            recognition = new SpeechAPI();
            recognition.lang = 'bn-IN';
            recognition.continuous = false;
            recognition.interimResults = false;

            recognition.onstart = () => {
                isRecording = true;
                micButton.classList.add('active');
                statusMessage.innerText = 'Listening to speech...';
            };

            recognition.onresult = async (event) => {
                const text = event.results[0][0].transcript;
                queryDisplay.innerText = text;
                statusMessage.innerText = 'Fetching SerpApi data & processing with Gemini...';
                await queryBackend(text);
            };

            recognition.onerror = () => {
                resetMic();
                statusMessage.innerText = 'Voice capture issue. Please try again.';
            };

            recognition.onend = () => {
                resetMic();
            };
        } else {
            statusMessage.innerText = 'Web Speech API not supported. Use Chrome.';
        }

        function toggleSpeech() {
            if (!recognition) return;
            if (isRecording) {
                recognition.stop();
            } else {
                recognition.start();
            }
        }

        function resetMic() {
            isRecording = false;
            micButton.classList.remove('active');
        }

        async function queryBackend(promptText) {
            try {
                const res = await fetch('/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: promptText, location: 'West Bengal, India', language: 'Bengali' })
                });
                const data = await res.json();
                responseDisplay.innerText = data.response;
                statusMessage.innerText = '';
                playAudio(data.response);
            } catch (err) {
                responseDisplay.innerText = 'Failed to fetch information.';
                statusMessage.innerText = '';
            }
        }

        function playAudio(text) {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'bn-IN';
                window.speechSynthesis.speak(utterance);
            }
        }
    </script>
</body>
</html>
    """

@app.post("/ask")
def ask(payload: QueryRequest):
    if not GEMINI_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured.")

    search_context = fetch_serp_data(payload.query, payload.location)

    try:
        client = genai.Client(api_key=GEMINI_KEY)
        system_instruction = f"""
You are IndicPulse AI, a hyperlocal voice assistant built for rural Indian citizens.
User Question: {payload.query}
Location: {payload.location}
Target Language: {payload.language}

Ground Truth Web Results from SerpApi:
\"\"\"
{search_context}
\"\"\"

Guidelines:
1. Answer accurately based on the SerpApi ground-truth results.
2. Formulate the response in natural, conversational {payload.language}.
3. Keep the tone concise and simple (2-3 sentences max) so that it can be easily understood over audio.
"""
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=system_instruction,
        )

        return {
            "query": payload.query,
            "response": response.text,
            "raw_context": search_context
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

