# Gyansetu - Teacher AI Platform (IIT Mandi)

Gyansetu (meaning "Bridge of Knowledge") is an enterprise-grade AI-powered pedagogical platform built for the IIT Mandi AI Engineer Assignment. It transforms raw educational materials (textbook chapters, lecture slides, PDFs, DOCX, PPTX, and plaintext) into structured, classroom-ready Teacher Knowledge Packages (TKPs).

Rather than relying on basic prompt wrappers, Gyansetu implements a stateful 10-stage LangGraph multi-agent pipeline, hybrid RAG retrieval (ChromaDB + Rank-BM25), two-tier SHA-256 prompt response caching, real-time SSE progress streaming, and a responsive Vue 3 SPA with persistent Dark/Light mode theme switching.

---

## Live Prototype and Deployment

- Live Web Service: https://gyansetu-626t.onrender.com
- Source Code Repository: https://github.com/SAM8402/Gyansetu
- Default Credentials: admin@gyansetu.ai / 12345678

---

## System Architecture

```
+--------------------------------------------------------------------------+
|                         Vue 3 SPA (Frontend)                             |
|   LoginPage / SignupPage -> UploadPage -> ProcessingPage -> ResultsPage  |
|   (Persistent Light/Dark Mode Theme Manager, Pinia Store, SSE Listener)  |
+------+--------------------------------------+----------------------------+
       | SSE Stream (Server-Sent Events)       | REST API (Bearer JWT)
       v                                      v
+--------------------------------------------------------------------------+
|                       FastAPI Backend (Async)                            |
|                                                                          |
|  +----------+   +-------------------------------------------+            |
|  | Routers  |   |         LangGraph Pipeline                |            |
|  | Auth     |   |                                           |            |
|  | Upload   |-->|  Doc Intel -> Edu Class -> Knowledge Ext  |            |
|  | Jobs     |   |       |                                   |            |
|  | Stream   |   |  Teaching Planner -> Content Gen (Paral.) |            |
|  +----------+   |       |                                   |            |
|                 |  Activity Gen -> Assessment Gen (Paral.)  |            |
|                 |       |                                   |            |
|                 |  Gap Analysis -> Validation -> Publishing |            |
|                 +────────────+------------------------------+            |
|                              |                                           |
|  +----------+   +------------+----------+   +----------------+           |
|  | Redis 7  |   | ChromaDB + BM25         |   | SQLite (async) |           |
|  | (Cache)  |   | (Hybrid RAG & Gemini)   |   | (Persistence)  |           |
|  +----------+   +-----------------------+   +----------------+           |
+--------------------------------------------------------------------------+
```

---

## 10-Stage LangGraph AI Pipeline

The core AI engine uses a LangGraph StateGraph to orchestrate 10 specialized pedagogical agents. Stages 5, 7, and 8 execute concurrently via asyncio.gather() to maximize throughput:

```
document_intelligence -> educational_classification -> knowledge_extraction -> teaching_planning
    -> [content_generation || assessment_generation || gap_analysis] (Parallel Branch)
    -> activity_generation -> tkp_assembly -> validation -> publishing -> END
```

### Stage Details

| Stage | Node Name | Responsible Service | Function and Outputs |
| :---: | :--- | :--- | :--- |
| **1** | `document_intelligence` | `DocumentIntelService` | Multi-format parser (PyMuPDF, python-docx, python-pptx) extracting text while preserving structural headings, tables, and equations offloaded to threadpool workers. |
| **2** | `educational_classification` | `EduClassifierService` | Classifies document domain, target grade level (Grade 1-12, Higher Ed), difficulty, topic, language, and curriculum board alignment (CBSE, ICSE, Common Core). |
| **3** | `knowledge_extraction` | `KnowledgeExtractorService` | Constructs a structured knowledge graph with learning objectives, core concepts, definitions, formulae, and prerequisite mappings. |
| **4** | `teaching_planning` | `TeachingPlannerService` | Converts knowledge into a multi-period lesson plan (e.g., 5 periods x 40 minutes) with entry/exit ticket strategies. |
| **5** | `content_generation` | `ContentGeneratorService` | Generates lecture notes, teacher scripts, blackboard diagrams, homework, and Mentor Moment motivational stories. |
| **6** | `activity_generation` | `ActivityGeneratorService` | Formulates classroom activities (experiments, role-plays, group discussions) with required materials, timing, and evaluation criteria. |
| **7** | `assessment_generation` | `AssessmentGeneratorService` | Generates MCQs, short/long answers, numerical problems, complete answer keys, and grading rubrics. |
| **8** | `gap_analysis` | `GapAnalyzerService` | Detects student misconceptions and provides diagnostic questions, severity levels, and remedial actions. |
| **9** | `validation` | `ValidatorService` | Automated schema validation, consistency checking across periods, and hallucination verification. |
| **10**| `publishing` | `PublisherService` | Packages final TeacherKnowledgePackage.json, persists to disk and SQLite database, and updates job completion state. |

---

## Production and Free-Tier Engineering Features

### 1. 512 MB RAM Free-Tier Optimization
The production deployment on Render is engineered to operate within strict 512 MB RAM memory constraints. By utilizing a slim requirements manifest (`requirements-render.txt`) that delegates embeddings to Google Gemini API, heavy machine learning libraries (PyTorch, Transformers) are omitted, reducing memory usage from 2 GB to under 150 MB.

### 2. Async Threadpool Non-Blocking Health Checks
CPU-bound document parsing (PyMuPDF layout extraction, table detection, and BM25 index creation) is wrapped in `asyncio.to_thread()` background worker pools. This keeps the primary Python event loop active at all times, ensuring `/api/health` probes respond in under 1 millisecond during heavy document processing.

### 3. Ultra-Fast Two-Tier Prompt Response Caching
SHA-256 hashing of prompt and model parameters is evaluated against a two-tier cache (In-Memory dictionary and optional Redis key-value store with 24-hour TTL). Identical queries or repeated document generation requests return instantly in 0.001 seconds.

### 4. Multi-Key and Multi-Model Rate-Limit Resilience
Implements automatic key rotation and fallback model chaining (Gemini 2.5 Flash -> Gemini 2.5 Flash Lite -> Gemini 2.0 Flash -> Gemini 2.0 Flash Lite -> Gemini 3.1 Flash Lite -> Gemini 2.5 Pro). Low retry overhead prevents SDK stalls during API rate limit occurrences.

### 5. Hybrid RAG (Dense Vector + Sparse BM25)
Combines ChromaDB vector embeddings with rank_bm25 keyword search to ensure accurate citation traceability (`source_reference`) for all extracted concepts.

### 6. Real-Time SSE Progress Streaming
Server-Sent Events publish granular progress updates to `/api/stream/{job_id}`. The Vue 3 frontend dynamically updates stage completion status and progress bars in real time.

### 7. Native Client-Side File Downloads
TKP JSON packages are served directly via database JSON storage and downloaded via client-side Blob generation, preventing authentication and file system expiration errors.

### 8. Single-Page Application (SPA) Fallback Routing
FastAPI includes a catch-all 404 handler that automatically serves `index.html` for client-side Vue Router history mode routes (`/dashboard`, `/upload`, `/results/:id`), preventing 404 errors on direct navigation or page refresh.

### 9. Automatic Database Initialization and Seeding
On startup, `init_db()` automatically applies idempotent schema migrations (`ALTER TABLE jobs ADD COLUMN result_json JSON`) and seeds default admin credentials (`admin@gyansetu.ai` / `12345678`).

---

## Teacher Knowledge Package (TKP) Schema

The final output is packaged into a standard, machine-readable JSON structure:

```json
{
  "metadata": {
    "document_title": "Kinematics_Motion.pdf",
    "subject": "Physics",
    "grade": "Grade 11",
    "difficulty": "intermediate",
    "topic": "Motion in One Dimension",
    "language": "English",
    "board_alignment": "CBSE",
    "total_periods": 5,
    "period_duration_minutes": 40,
    "generated_at": "2026-07-31T03:30:00Z"
  },
  "knowledge_base": {
    "learning_objectives": ["Understand displacement vs distance", "Apply equations of motion"],
    "core_concepts": [],
    "formulae": [],
    "misconceptions": []
  },
  "teaching_plan": {
    "periods": [
      {
        "period_number": 1,
        "title": "Introduction to Position, Velocity and Acceleration",
        "duration_minutes": 40,
        "entry_ticket": { "question": "What is the difference between speed and velocity?" },
        "teacher_script": "Welcome class...",
        "blackboard_notes": "...",
        "classroom_activities": [],
        "exit_ticket": { "question": "Define acceleration." }
      }
    ]
  },
  "assessments": {
    "mcqs": [],
    "short_answer": [],
    "numerical_problems": [],
    "answer_keys": []
  },
  "learning_gaps": [
    {
      "concept": "Acceleration under gravity",
      "misconception": "Heavier objects fall faster than lighter objects in vacuum",
      "remedial_action": "Demonstrate feather and coin drop experiment"
    }
  ],
  "validation_report": { "score": 1.0, "status": "VALIDATED" }
}
```

---

## Technology Stack

| Category | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.13 + FastAPI | High-performance asynchronous API server, SSE streaming, OpenAPI documentation. |
| **AI Pipeline Engine** | LangGraph 1.2 + LangChain 1.3 | Stateful multi-agent graph execution, parallel node invocation. |
| **Primary LLM** | Google Gemini API (2.5 Flash / 3.1 Flash Lite) | High-speed response generation and structured JSON extraction. |
| **RAG System** | ChromaDB + Rank-BM25 | Hybrid dense vector and sparse keyword search. |
| **Caching Layer** | Redis 7 + In-Memory Store | SHA-256 prompt response caching. |
| **Database** | SQLAlchemy 2.0 + Async SQLite (aiosqlite) | Asynchronous object-relational mapping for users and processing jobs. |
| **Frontend Framework** | Vue 3 + Pinia + Vue Router + Vite | Reactive single-page application with centralized state and routing. |
| **Styling** | Tailwind CSS v4 | Utility-first CSS with persistent class-based dark mode management. |
| **Authentication** | JWT (python-jose) + bcrypt | Secure access and refresh token authentication with password hashing. |
| **Containerization** | Docker + Docker Compose | Unified single-container and multi-container deployment models. |

---

## Quick Start Guide

### Prerequisites

- Python: 3.12 or 3.13
- Node.js: 20+
- Redis: 7.x (Optional; system defaults to built-in in-memory caching if Redis is absent)
- Google Gemini API Key: Free API key from Google AI Studio

---

### Local Installation and Setup

#### 1. Clone Repository and Configure Environment

```bash
git clone https://github.com/SAM8402/Gyansetu.git
cd Gyansetu

# Create local environment configuration
cp backend/.env.example backend/.env
```

Configure `backend/.env`:
```env
GOOGLE_API_KEY=AIzaSyYourActualGeminiApiKeyHere
GEMINI_MODEL=gemini-3.1-flash-lite
LLM_FALLBACK_CHAIN=gemini-2.5-flash,gemini-2.5-flash-lite,gemini-2.0-flash
DATABASE_URL=sqlite+aiosqlite:///./app.db
REDIS_URL=
```

#### 2. Start Backend API Server

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
python main.py
```
- Backend Base URL: http://localhost:8000
- Interactive API Documentation: http://localhost:8000/docs

#### 3. Start Frontend Development Server

In a second terminal window:

```bash
cd frontend
npm install
npm run dev
```
- Frontend Application URL: http://localhost:5173

---

### Docker Compose Deployment

To build and run the application locally using Docker Compose:

```bash
docker compose up -d --build
```

- Unified Web Application: http://localhost:8000

---

## Sample Test Datasets

Educational test documents are available in the `/samples` directory for testing upload and pipeline processing:

| File Path | Format | Subject / Topic | Target Level |
| :--- | :---: | :--- | :---: |
| `samples/sample_physics_lesson.pdf` | PDF | Physics (Kinematics and Motion) | Grade 11 |
| `samples/sample_physics_lesson.md` | Markdown | Physics (Kinematics and Motion) | Grade 11 |
| `samples/sample_chemistry_bonding.pdf` | PDF | Chemistry (Chemical Bonding) | Grade 10 |
| `samples/sample_math_calculus.pdf` | PDF | Mathematics (Differential Calculus) | Grade 12 |
| `samples/sample_biology_genetics.pdf` | PDF | Biology (Mendelian Genetics) | Grade 10 |

---

## REST API Reference

| Endpoint | Method | Auth Required | Description |
| :--- | :---: | :---: | :--- |
| `/api/auth/register` | `POST` | Public | Register a new user account. |
| `/api/auth/login` | `POST` | Public | Authenticate user credentials and return JWT tokens. |
| `/api/auth/refresh` | `POST` | Public | Refresh expired access tokens. |
| `/api/upload` | `POST` | JWT Bearer | Upload document (`.pdf`, `.docx`, `.pptx`, `.txt`) and start pipeline job. |
| `/api/stream/{job_id}` | `GET` | JWT Bearer | Real-time Server-Sent Events (SSE) progress stream. |
| `/api/jobs` | `GET` | JWT Bearer | List all processing jobs for the authenticated user. |
| `/api/jobs/{job_id}` | `GET` | JWT Bearer | Retrieve status, current stage, and metadata for a specific job. |
| `/api/jobs/{job_id}` | `DELETE` | JWT Bearer | Delete job record, uploaded file, and generated TKP output. |
| `/api/jobs/{job_id}/tkp` | `GET` | JWT Bearer | Download complete Teacher Knowledge Package JSON structure. |
| `/api/health` | `GET` | Public | System health check endpoint. |

---

## License

This project is licensed under the MIT License.
