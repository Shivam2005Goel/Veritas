import os
import shutil
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import Fact, Reconciliation, IngestResponse
from parser import PDFParser
from extractor import FactExtractor
from reconciler import Reconciler
from store import StorageEngine

app = FastAPI(
    title="Veritas Fact Knowledge Layer API",
    description="Cross-Document Fact Ingestion, Layout Grounding, and Reconciliation Engine",
    version="1.0.0"
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
    # Look in local project directory first, fallback to D:\starter-datasets
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
