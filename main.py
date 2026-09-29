import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from serpapi import GoogleSearch
from groq import Groq

app = FastAPI(title="IndicPulse AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")
GROQ_KEY = os.getenv("GROQ_API_KEY")

class QueryRequest(BaseModel):
    query: str
    location: str = "India"
    language: str = "English"

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
            "num": 4
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        
        snippets = []
        if "organic_results" in results:
            for item in results["organic_results"][:3]:
                snippet = item.get("snippet") or item.get("title")
                if snippet:
                    snippets.append(snippet)
        
        return "\n".join(snippets) if snippets else "No direct snippets found."
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
        body { background: #0f172a; color: #f8fafc; min-height: 100vh; display: flex; flex-direction: column; justify-content: space-between; align-items: center; padding: 24px 16px; }
        .header { text-align: center; }
        .header h1 { font-size: 26px; color: #38bdf8; font-weight: 700; }
        .header p { font-size: 13px; color: #94a3b8; margin-top: 4px; }
        .tag { display: inline-block; background: rgba(56, 189, 248, 0.12); color: #38bdf8; padding: 3px 10px; border-radius: 999px; font-size: 11px; margin-top: 8px; font-weight: 600; border: 1px solid rgba(56, 189, 248, 0.25); }
        
        .lang-selector-container { margin: 14px 0; width: 100%; max-width: 440px; display: flex; align-items: center; justify-content: space-between; background: #1e293b; padding: 10px 16px; border-radius: 12px; border: 1px solid #334155; }
        .lang-label { font-size: 13px; color: #cbd5e1; font-weight: 500; }
        .lang-select { background: #0f172a; color: #38bdf8; border: 1px solid #475569; padding: 6px 12px; border-radius: 8px; font-size: 14px; font-weight: 600; outline: none; }

        .main-card { width: 100%; max-width: 440px; background: #1e293b; border-radius: 20px; padding: 20px; border: 1px solid #334155; min-height: 240px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
        .query-label { font-size: 12px; font-weight: 600; text-transform: uppercase; color: #64748b; margin-bottom: 4px; }
        .query-text { font-size: 15px; color: #cbd5e1; margin-bottom: 16px; min-height: 24px; }
        .response-label { font-size: 12px; font-weight: 600; text-transform: uppercase; color: #38bdf8; margin-bottom: 4px; }
        .response-text { font-size: 15px; line-height: 1.6; color: #f1f5f9; }
        .status { font-size: 13px; color: #38bdf8; text-align: center; min-height: 20px; margin: 10px 0; }
        
        .controls { display: flex; flex-direction: column; align-items: center; margin-bottom: 10px; }
        .mic-btn { width: 80px; height: 80px; border-radius: 50%; background: linear-gradient(135deg, #0284c7, #2563eb); border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 20px rgba(37, 99, 235, 0.4); transition: transform 0.2s, background 0.2s; -webkit-tap-highlight-color: transparent; }
        .mic-btn:active { transform: scale(0.95); }
        .mic-btn.active { background: linear-gradient(135deg, #ef4444, #dc2626); box-shadow: 0 0 25px rgba(239, 68, 68, 0.6); animation: pulse 1.4s infinite; }
        .mic-btn svg { width: 34px; height: 34px; fill: #ffffff; }
        .mic-caption { font-size: 13px; color: #94a3b8; margin-top: 10px; }
        @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.08); } 100% { transform: scale(1); } }
    </style>
</head>
<body>
    <div class="header">
        <h1>IndicPulse AI</h1>
        <p>Voice-First Hyperlocal Intelligence for Rural India</p>
        <span class="tag">FastAPI • SerpApi • AI Engine</span>
    </div>

    <div class="lang-selector-container">
        <span class="lang-label">Select Language:</span>
        <select class="lang-select" id="languageSelect">
            <option value="en-IN|English">English</option>
            <option value="bn-IN|Bengali" selected>বাংলা (Bengali)</option>
            <option value="hi-IN|Hindi">हिन्दी (Hindi)</option>
            <option value="mr-IN|Marathi">मরাठी (Marathi)</option>
            <option value="pa-IN|Punjabi">ਪੰਜਾਬੀ (Punjabi)</option>
            <option value="gu-IN|Gujarati">ગુજરાતી (Gujarati)</option>
            <option value="ta-IN|Tamil">தமிழ் (Tamil)</option>
            <option value="te-IN|Telugu">తెలుగు (Telugu)</option>
            <option value="kn-IN|Kannada">ಕನ್ನಡ (Kannada)</option>
            <option value="ml-IN|Malayalam">മലയാളം (Malayalam)</option>
        </select>
    </div>

    <div class="main-card">
        <div>
            <div class="query-label">Input Query</div>
            <div class="query-text" id="queryDisplay">Tap mic and ask your question...</div>
        </div>
        <div>
            <div class="response-label">Assistant Response</div>
            <div class="response-text" id="responseDisplay">Ready to assist. Select your language and speak into the microphone.</div>
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
        const languageSelect = document.getElementById('languageSelect');
        let recognition;
        let isRecording = false;

        const SpeechAPI = window.SpeechRecognition || window.webkitSpeechRecognition;

        function getSelectedLangCode() {
            return languageSelect.value.split('|')[0];
        }

        function getSelectedLangName() {
            return languageSelect.value.split('|')[1];
        }

        if (SpeechAPI) {
            recognition = new SpeechAPI();
            recognition.continuous = false;
            recognition.interimResults = false;

            recognition.onstart = () => {
                isRecording = true;
                micButton.classList.add('active');
                statusMessage.innerText = 'Listening in ' + getSelectedLangName() + '...';
            };

            recognition.onresult = async (event) => {
                const text = event.results[0][0].transcript;
                queryDisplay.innerText = text;
                statusMessage.innerText = 'Searching live SerpApi data & formulating response...';
                await queryBackend(text);
            };

            recognition.onerror = () => {
                resetMic();
                statusMessage.innerText = 'Voice capture issue. Please tap again.';
            };

            recognition.onend = () => {
                resetMic();
            };
        } else {
            statusMessage.innerText = 'Speech recognition not supported in this browser. Please use Chrome.';
        }

        function toggleSpeech() {
            if (!recognition) return;
            if (isRecording) {
                recognition.stop();
            } else {
                recognition.lang = getSelectedLangCode();
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
                    body: JSON.stringify({ 
                        query: promptText, 
                        location: 'India', 
                        language: getSelectedLangName() 
                    })
                });
                const data = await res.json();
                
                const reply = data.response || 'No response generated.';
                responseDisplay.innerText = reply;
                statusMessage.innerText = '';
                playAudio(reply, getSelectedLangCode());
            } catch (err) {
                responseDisplay.innerText = 'Backend connection error. Please try again.';
                statusMessage.innerText = '';
            }
        }

        function playAudio(text, langCode) {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = langCode;
                window.speechSynthesis.speak(utterance);
            }
        }
    </script>
</body>
</html>
    """

@app.post("/ask")
def ask(payload: QueryRequest):
    search_context = fetch_serp_data(payload.query, payload.location)

    # Candidate active models from Groq console
    candidate_models = [
        "openai/gpt-oss-20b",
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-120b",
        "llama-3.3-70b-versatile"
    ]

    if GROQ_KEY:
        try:
            client = Groq(api_key=GROQ_KEY)
            prompt = f"""
You are IndicPulse AI, a voice-first hyperlocal intelligence assistant built for rural and urban Indian citizens.
User Query: {payload.query}
Location: {payload.location}
Target Language: {payload.language}

Ground Truth Search Context from SerpApi:
{search_context}

Guidelines:
1. Respond EXCLUSIVELY in {payload.language} script and language.
2. Formulate a direct, simple, and concise response (maximum 2-3 sentences) suitable for clear speech audio playback.
3. Incorporate real-time information such as figures, rates, or dates directly from the search context if available.
"""
            for m in candidate_models:
                try:
                    completion = client.chat.completions.create(
                        model=m,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        max_tokens=250,
                    )
                    reply = completion.choices[0].message.content.strip()
                    if reply:
                        return {"query": payload.query, "response": reply}
                except Exception:
                    continue
        except Exception:
            pass

    # Reliable fallback: Return the verified SerpApi facts directly if LLMs fail
    fallback_text = f"প্রাপ্ত তথ্য অনুযায়ী: {search_context[:300]}" if search_context else "বর্তমানে এই তথ্যের আপডেট পাওয়া যায়নি।"
    return {
        "query": payload.query,
        "response": fallback_text
    }

