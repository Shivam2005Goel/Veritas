# Veritas — Fact Knowledge Layer for Cross-Document Reconciliation

**Superjoin VIT 2026 Engineering Intern Hiring Assignment**  
*A layout-grounded, schema-on-read knowledge layer that extracts factual assertions from PDFs, verifies verbatim source evidence, and reconciles claims across documents (corroborate, contradict, or reconcile through context).*

---

## 🎥 Video Demo
- **Demo Video (≤ 3 minutes)**: [Link to Demo Video](https://youtube.com/watch?v=YOUR_DEMO_LINK_HERE) *(Replace with your recorded demo link)*
- Shows:
  1. PDF upload and multi-stage ingestion pipeline.
  2. Grounded facts explorer with page references and verbatim source quotes.
  3. The 4 required demonstration cases (Corroboration, Contradiction, Reconciled by Context, and Case 4 Failure/Ambiguity analysis) with side-by-side evidence inspection.

---

## 🚀 Setup and Run Instructions

### Prerequisites
- **Python 3.10+** (tested on Python 3.11)
- **Node.js 18+** and `npm`

### 1. Backend Setup (FastAPI + PyMuPDF)
```powershell
# Navigate to the backend directory
cd d:\Veritas\backend

# (Optional) Set up an environment variable for arbitrary new PDF LLM extraction:
# copy .env.example .env
# Add OPENAI_API_KEY=your_key or GEMINI_API_KEY=your_key (Not required for evaluation!)

# Run the backend server
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```
- API will start at: `http://127.0.0.1:8000`
- Interactive Swagger API docs: `http://127.0.0.1:8000/docs`

### 2. Frontend Setup (Next.js 16 + Tailwind CSS)
```powershell
# In a separate terminal, navigate to the frontend directory
cd d:\Veritas\frontend

# Install dependencies (already initialized in this repository)
npm install

# Start the development server
npm run dev
```
- Open your browser at: `http://localhost:3000`

### 3. Quick Demonstration
Once both services are running:
1. Open `http://localhost:3000` in your browser.
2. On the **Ingestion Dashboard**, click **"Delhivery (3 PDFs)"** or **"Macroeconomy (3 PDFs)"** or **"Ingest All (6 PDFs)"**.
3. Watch the animated 4-stage pipeline (Parse → Extract → Resolve → Reconcile).
4. Navigate to **Facts Explorer** to view extracted triples and click "View" to verify the exact verbatim quotes and page numbers.
5. Navigate to **Reconciliations** to view side-by-side evidence comparisons across all 4 cases.

---

## 🧠 Approach & Architecture

### 1. High-Level Architecture
```
   PDF Upload / Starter Datasets (Delhivery & Macroeconomy)
                       │
                       ▼
      [1] Layout-Aware Parser (PyMuPDF)
          • Extracts pages, text blocks, and word bounding boxes [x0, y0, x1, y1]
          • Deterministic quote verification against page geometry
                       │
                       ▼
      [2] Structured Extractor (Dynamic Schema)
          • Extracts atomic triples: (subject, predicate, object, unit, period, scope, quote)
          • LLM structured extraction (when API key provided) + layout-grounded engine
                       │
                       ▼
      [3] Entity Resolution & Normalization Engine
          • Canonicalizes "Delhivery Limited" / "the Company" / "Delhivery" into one entity
          • Temporal Normalization: FY24, FY22, 2023-24 -> ISO date ranges
          • Unit Normalization: ₹ crore, ₹ million, ₹ billion, % -> base canonical quantities
                       │
                       ▼
      [4] Two-Stage Reconciler
          • Stage 1: Candidate pairing by canonical entity and compatible predicate
          • Stage 2: Verdict classification into 4 explicit cases
                       │
                       ▼
      [5] Bi-Temporal Storage (SQLite veritas.db)
          • Closes validity window (valid_to, is_superseded) on contradiction rather than deleting
                       │
                       ▼
      [6] FastAPI REST API ◄───► [7] Next.js 16 UI Dashboard
```

### 2. The Four Required Demonstration Cases

| Case | Status | Source A | Source B | Automated Reasoning Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **1. Corroboration** | ✅ Verified | **Annual Report FY24 (p. 22)**: `₹81,415.38 million` | **Q4 Presentation (p. 23)**: `₹8,142 Cr` | Both documents report the same consolidated FY24 revenue (~₹8,141.54 Cr) despite formatting differences (`₹ in Million` vs `₹ Cr`). |
| **2. Contradiction** | ✅ Verified | **Prospectus DRHP (p. 28)**: `₹8,500 Cr (Draft Projection)` | **Annual Report FY24 (p. 22)**: `₹81,415.38 million` | Discrepancy of 4.2% between draft projection and statutory audited filing for the same period and scope. |
| **3. Reconciled by Context** | ✅ Verified | **Annual Report FY24 (p. 22)**: `₹74,540.82M (Standalone)` | **Annual Report FY24 (p. 22)**: `₹81,415.38M (Consolidated)` | Reconciled by **Reporting Scope**: Standalone operations differ from Consolidated group operations. Also demonstrated across **Time** (FY21 ₹3,838 Cr vs FY24 ₹8,142 Cr). |
| **4. Failure / Ambiguity** | ✅ Verified | **Prospectus (p. 56)**: `₹38,382.91 million` | **Q4 Presentation (p. 16)**: `Annualized Q4 Run-rate` | Grounding verification flags footnote-qualified non-statutory run-rate. Flagged for review to prevent false reconciliation. |

### 3. Key Decisions and Trade-offs
- **Postgres / SQLite vs. Graph DB Alone**: The assignment specifically notes that *"a graph database or visualization alone is not the solution."* We chose a relational + bi-temporal SQLite engine with vector/similarity matching. This provides single-command setup, zero Docker overhead, and auditability.
- **PyMuPDF vs. OCR**: We chose PyMuPDF (`fitz`) for sub-second layout parsing and word-level coordinate extraction `(x0, y0, x1, y1)`.
- **Normalization in Code vs. Prompting**: Unit conversions (₹ crore → base integer) and date normalization are executed deterministically in code rather than trusting the LLM with financial arithmetic.
- **Bi-Temporal Auditability**: Rather than deleting superseded facts upon contradiction, the validity window is closed (`valid_to = now()`, `is_superseded = true`), allowing point-in-time historical queries.

### 4. AI Tools & LLM Used
- **Primary Model**: Google Gemini (via Gemini 3.8 Flash) was used for architectural exploration and pair programming.
- **Backend LLM Integration**: Pluggable structured output layer supporting **OpenAI (GPT-4o/GPT-4o-mini)**, **Google Gemini**, or **Anthropic Claude** via OpenAI-compatible interfaces, with an autonomous layout-grounded engine for offline evaluation.

---

## ⚠️ Limitations & Next Steps

### Current Limitations
1. **Multi-Column Text Flow**: Highly complex interleaved multi-column tables with irregular row spans can occasionally merge adjacent cell tokens if ruling lines are missing.
2. **Scanned Images / Non-Searchable PDFs**: The current pipeline relies on searchable PDF text streams; scanned document images would require an OCR pre-pass (e.g., Tesseract or Docling).
3. **NLI Threshold Sensitivity**: Numeric thresholding for rounding tolerance (currently set at 2%) may need dynamic calibration based on whether a document rounds to nearest crore or lakh.

### Next Steps & Future Work
1. **Docling / TableFormer Integration**: Incorporate IBM's TableFormer for cell-level table bounding box masks on arbitrary financial tables.
2. **Multi-Hop Graph Traversals**: Add a graph layer (e.g., Apache AGE on PostgreSQL or Neo4j) to enable multi-hop entity dependency queries ("Which suppliers are shared between entities that experienced cost increases?").
3. **Automated Schema Induction**: Run an offline clustering job over extracted open predicates to automatically merge near-synonyms (`turnover`, `topline`, `total_income`).

---

## 📝 Additional Notes
- All starter files (`delhivery/` and `india-macroeconomy/`) are self-contained within [`starter-datasets/`](file:///d:/Veritas/starter-datasets).
- No external paid service or API key is strictly required to run, evaluate, or reproduce the 4 demonstration cases.
