import os
import shutil
from typing import List, Optional
import pymupdf
from fastapi import FastAPI, UploadFile, File, Query, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from models import Fact, Reconciliation, IngestResponse
from parser import PDFParser
from extractor import FactExtractor
from reconciler import Reconciler
from store import StorageEngine
from schema_engine import SchemaEngine
from qa_engine import QAEngine

app = FastAPI(
    title="Veritas Fact Knowledge Layer API",
    description="Cross-Document Fact Ingestion, Layout Grounding, Dynamic Schema, and Reconciliation Engine",
    version="1.1.0"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

storage = StorageEngine("veritas.db")

UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class QueryRequest(BaseModel):
    query: str

class SettingsUpdate(BaseModel):
    api_key: str
    provider: str = "gemini"
    model: Optional[str] = None

ACTIVE_LLM_CONFIG = {
    "api_key": os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY") or "",
    "provider": "gemini" if os.getenv("GEMINI_API_KEY") else ("openai" if os.getenv("OPENAI_API_KEY") else "none"),
    "model": os.getenv("LLM_MODEL", "gemini-1.5-flash" if os.getenv("GEMINI_API_KEY") else "gpt-4o-mini")
}

@app.get("/api/settings")
def get_settings():
    return {
        "llm_enabled": bool(ACTIVE_LLM_CONFIG["api_key"]),
        "provider": ACTIVE_LLM_CONFIG["provider"],
        "model": ACTIVE_LLM_CONFIG["model"],
        "universal_engine_active": True
    }

@app.post("/api/settings/api-key")
def update_api_key(body: SettingsUpdate):
    ACTIVE_LLM_CONFIG["api_key"] = body.api_key.strip()
    ACTIVE_LLM_CONFIG["provider"] = body.provider.lower().strip()
    if body.model:
        ACTIVE_LLM_CONFIG["model"] = body.model.strip()
    elif body.provider.lower() == "gemini":
        ACTIVE_LLM_CONFIG["model"] = "gemini-1.5-flash"
    else:
        ACTIVE_LLM_CONFIG["model"] = "gpt-4o-mini"
        
    if body.provider.lower() == "gemini":
        os.environ["GEMINI_API_KEY"] = body.api_key.strip()
    else:
        os.environ["OPENAI_API_KEY"] = body.api_key.strip()
        
    return {"status": "success", "settings": get_settings()}

@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "veritas-engine"}

@app.get("/api/facts", response_model=List[Fact])
def get_facts(doc_id: Optional[str] = None):
    all_facts = storage.get_all_facts()
    if doc_id:
        return [f for f in all_facts if f.doc_id == doc_id]
    return all_facts

@app.get("/api/reconciliations", response_model=List[Reconciliation])
def get_reconciliations(type: Optional[str] = None):
    return storage.get_reconciliations(type)

@app.post("/api/documents", response_model=IngestResponse)
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF documents are supported.")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return _process_pdf_file(file_path, file.filename)

@app.post("/api/ingest-starter")
def ingest_starter_datasets(dataset: str = Query("all", description="Options: 'delhivery', 'india-macroeconomy', or 'all'")):
    local_base = os.path.join(os.path.dirname(__file__), "..", "starter-datasets")
    fallback_base = r"D:\starter-datasets"

    base_dir = local_base if os.path.exists(local_base) else fallback_base
    if not os.path.exists(base_dir):
        raise HTTPException(status_code=404, detail=f"Starter dataset directory not found at '{base_dir}'.")

    target_dirs = []
    if dataset in ["delhivery", "all"]:
        d_dir = os.path.join(base_dir, "delhivery")
        if os.path.exists(d_dir):
            target_dirs.append(d_dir)

    if dataset in ["india-macroeconomy", "all"]:
        m_dir = os.path.join(base_dir, "india-macroeconomy")
        if os.path.exists(m_dir):
            target_dirs.append(m_dir)

    total_facts = 0
    ingested_files = []

    for d in target_dirs:
        for fname in os.listdir(d):
            if fname.lower().endswith(".pdf"):
                full_path = os.path.join(d, fname)
                resp = _process_pdf_file(full_path, fname)
                total_facts += resp.facts_extracted
                ingested_files.append(fname)

    all_facts = storage.get_all_facts()
    all_recs = storage.get_reconciliations()

    return {
        "status": "success",
        "dataset_selected": dataset,
        "files_ingested": ingested_files,
        "total_facts_stored": len(all_facts),
        "total_reconciliations": len(all_recs)
    }

@app.get("/api/documents/{doc_id}/pages/{page_num}/preview")
def render_page_preview(doc_id: str, page_num: int, bbox: Optional[str] = Query(None, description="x0,y0,x1,y1")):
    """
    Renders a high-resolution PNG image of the requested PDF page with the exact
    bounding box highlighted with an illuminated bounding rectangle.
    """
    # Find document
    file_path = _find_document_path(doc_id)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found.")

    doc = pymupdf.open(file_path)
    if not (1 <= page_num <= len(doc)):
        doc.close()
        raise HTTPException(status_code=400, detail=f"Page {page_num} out of bounds (1-{len(doc)}).")

    page = doc[page_num - 1]

    # Draw highlight if bbox provided
    if bbox:
        try:
            coords = [float(c.strip()) for c in bbox.split(",")]
            if len(coords) == 4:
                rect = pymupdf.Rect(coords[0], coords[1], coords[2], coords[3])
                # Draw illuminated highlight (orange border, translucent gold fill)
                page.draw_rect(rect, color=(0.95, 0.55, 0.1), fill=(1.0, 0.9, 0.2), fill_opacity=0.45, width=2.5)
        except Exception:
            pass

    pix = page.get_pixmap(dpi=120)
    png_bytes = pix.tobytes("png")
    doc.close()

    return Response(content=png_bytes, media_type="image/png")

@app.get("/api/schema")
def get_schema():
    """Returns the dynamically induced schema and canonical predicate taxonomy."""
    all_facts = storage.get_all_facts()
    return SchemaEngine.induce_schema(all_facts)

@app.post("/api/schema/induce")
def trigger_schema_induction():
    """Runs a fresh dynamic schema induction pass over the current knowledge store."""
    all_facts = storage.get_all_facts()
    return SchemaEngine.induce_schema(all_facts)

@app.post("/api/query")
def answer_query(body: QueryRequest):
    """Fact-Grounded Q&A over the structured knowledge layer with full citations."""
    all_facts = storage.get_all_facts()
    all_recs = storage.get_reconciliations()
    return QAEngine.answer_query(body.query, all_facts, all_recs)

def _find_document_path(doc_id: str) -> Optional[str]:
    # Check upload dir
    p = os.path.join(UPLOAD_DIR, doc_id)
    if os.path.exists(p):
        return p

    # Check starter datasets
    local_base = os.path.join(os.path.dirname(__file__), "..", "starter-datasets")
    for sub in ["delhivery", "india-macroeconomy"]:
        candidate = os.path.join(local_base, sub, doc_id)
        if os.path.exists(candidate):
            return candidate

    fallback_base = r"D:\starter-datasets"
    for sub in ["delhivery", "india-macroeconomy"]:
        candidate = os.path.join(fallback_base, sub, doc_id)
        if os.path.exists(candidate):
            return candidate

    return None

def _process_pdf_file(file_path: str, filename: str) -> IngestResponse:
    parser = PDFParser(file_path)
    total_pages = parser.total_pages
    doc_id = filename

    storage.save_document(doc_id, filename, total_pages)

    extractor = FactExtractor(parser, doc_id)
    new_facts = extractor.extract_all_facts()
    parser.close()

    storage.save_facts(new_facts)

    # Cross-document reconciliation against all known facts
    all_facts = storage.get_all_facts()
    reconciliations = Reconciler.reconcile_all(all_facts)
    storage.save_reconciliations(reconciliations)

    return IngestResponse(
        doc_id=doc_id,
        filename=filename,
        total_pages=total_pages,
        facts_extracted=len(new_facts),
        reconciliations_count=len(reconciliations),
        status="success"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
