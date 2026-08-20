import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.linter import T24CodeLinter
from app.templates_engine import T24TemplateEngine
from app.ai_service import T24AIService
from app.memory_store import T24MemoryStore

app = FastAPI(
    title="Temenos T24 / TAFJ Developer Tool & Master Agent",
    description="Enterprise API and IDE Suite with Continuous Learning for Temenos T24, TAFJ, and jBASE Infobasic Engineering.",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

memory_store = T24MemoryStore()
linter_engine = T24CodeLinter()
template_engine = T24TemplateEngine()
ai_service = T24AIService(memory_store=memory_store)

class LintRequest(BaseModel):
    code: str

class GenerateTemplateRequest(BaseModel):
    template_id: str
    params: Dict[str, str]

class ChatRequest(BaseModel):
    prompt: str
    history: Optional[List[Dict[str, str]]] = None

class LearnSampleRequest(BaseModel):
    title: str
    category: str
    code: str
    tags: Optional[str] = ""
    notes: Optional[str] = ""

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "T24 TAFJ Master Developer Tool with Learning Memory",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.1.0"
    }

@app.post("/api/lint")
def lint_code(req: LintRequest):
    if not req.code or not req.code.strip():
        raise HTTPException(status_code=400, detail="Source code cannot be empty.")
    return linter_engine.lint(req.code)

@app.get("/api/templates")
def list_templates():
    return {"templates": template_engine.list_templates()}

@app.post("/api/templates/generate")
def generate_template(req: GenerateTemplateRequest):
    try:
        generated_code = template_engine.generate(req.template_id, req.params)
        return {"code": generated_code}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/chat")
async def chat(req: ChatRequest):
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
    response_text = await ai_service.generate_response(req.prompt, req.history)
    return {"response": response_text}

# --- Pattern Learning & Memory Endpoints ---
@app.post("/api/learn")
def learn_code_sample(req: LearnSampleRequest):
    if not req.code or not req.code.strip():
        raise HTTPException(status_code=400, detail="Sample code cannot be empty.")
    if not req.title or not req.title.strip():
        raise HTTPException(status_code=400, detail="Sample title is required.")
    
    result = memory_store.add_sample(
        title=req.title,
        category=req.category,
        code=req.code,
        tags=req.tags or "",
        notes=req.notes or ""
    )
    return {
        "status": "success",
        "message": f"Successfully ingested and learned from '{req.title}'!",
        "sample": result
    }

@app.get("/api/learned-samples")
def list_learned_samples():
    return {"samples": memory_store.list_samples()}

@app.delete("/api/learned-samples/{sample_id}")
def delete_learned_sample(sample_id: int):
    deleted = memory_store.delete_sample(sample_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Sample not found.")
    return {"status": "success", "message": f"Sample {sample_id} deleted."}

@app.get("/api/knowledge")
def get_knowledge_base():
    return {
        "delimiters": [
            {"name": "Field Marker", "symbol": "^", "ascii": "254", "constant": "@FM", "use": "Separates table fields"},
            {"name": "Value Marker", "symbol": "]", "ascii": "253", "constant": "@VM", "use": "Separates multi-values"},
            {"name": "Sub-Value Marker", "symbol": "\\", "ascii": "252", "constant": "@SM", "use": "Separates sub-values"},
            {"name": "Text Marker", "symbol": "_", "ascii": "251", "constant": "@TM", "use": "Delimits text blocks"}
        ],
        "common_variables": [
            {"var": "ID.NEW", "description": "Current record key in memory"},
            {"var": "R.NEW", "description": "Dynamic array holding current in-flight record data"},
            {"var": "R.OLD", "description": "Snapshot of record prior to user modifications"},
            {"var": "APPLICATION", "description": "Active executing application name (e.g. ACCOUNT)"},
            {"var": "V$FUNCTION", "description": "Active function mode (I, A, D, R, C, S, V)"},
            {"var": "TODAY", "description": "System bank date in YYYYMMDD format"},
            {"var": "ID.COMPANY", "description": "9-character ID of active company/branch"}
        ]
    }

# Mount static frontend directory
static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_path):
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
