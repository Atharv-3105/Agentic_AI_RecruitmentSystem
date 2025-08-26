## ✨ Features (Technical Deep Dive)
#### Multi-Format Resume Ingestion & Parsing:

- The system ingests resumes in multiple formats, including .pdf, .docx, .png, and .jpg.

- It uses a hybrid parsing strategy: PyMuPDF for efficient text extraction from text-based PDFs, python-docx for Word documents, and Google's Tesseract-OCR engine (via pytesseract) for image-based documents.

- A specialized Gemini agent then receives the extracted raw text. This agent uses a few-shot prompt containing curated examples to reliably parse the text into a structured JSON object, which is validated against a strict Pydantic model.

#### Agentic Title Inference:

- To handle real-world resume ambiguity, the system uses a two-agent chain for project parsing.

- The primary Extractor Agent performs the initial parse. If it finds a project with a null title, a secondary, hyper-focused Title Synthesizer Agent is invoked.

- This second agent receives only the project's responsibilities and uses a constrained prompt to generate a concise, descriptive title, ensuring the final data is always complete.

#### Comprehensive JD Analysis:

- A dedicated JD Analyzer Agent is prompted to act as a senior technical recruiter, extracting key criteria like required/preferred skills, years of experience, and education into a ParsedJD Pydantic model.

- Provides two flexible endpoints for submitting a JD: file upload (.txt) or raw text paste.

- The API provides flexibility by exposing two distinct endpoints: /jds/upload-file (accepting multipart/form-data) and /jds/paste-text (accepting text/plain), which both funnel data to the same underlying agent.

#### Semantic Candidate Screening:

- The core Screening Agent receives the structured JSON from a parsed resume and a JD. It constructs a detailed prompt containing both JSON objects.

- The core engine compares the structured resume against the structured JD.

- Generates a quantitative match score (0-100).
  
- It leverages Gemini's JSON Mode to guarantee a valid, structured JSON response containing a match_score, a qualitative summary, and lists of strengths and gaps, which is then validated by the ScreeningResult Pydantic model.

#### Stateful, Asynchronous Backend:

- Built with FastAPI, the API is fully asynchronous and leverages Pydantic for automatic request validation, serialization, and generation of OpenAPI (/docs) and ReDoc (/redoc) documentation.

- The system is stateful, using PyMongo to connect to a MongoDB instance. A singleton pattern is used for the database client to ensure efficient connection pooling.

- All parsed artifacts and screening results are persisted in separate collections and referenced via their unique MongoDB ObjectId, allowing for a robust, decoupled workflow.
---
## 📋 API Workflow
#### The primary workflow is managed through the API:

- Upload Resume: POST /v1/resumes with a resume file to parse it and get a resume_id.

- Upload JD: POST /v1/jds/upload-file or /v1/jds/paste-text to parse a job description and get a jd_id.

- Screen Candidate: POST /v1/screen with the resume_id and jd_id to perform the analysis and get a screening_id.

- Get Report: GET /v1/reports/{screening_id} to retrieve the final, human-readable report.

---

## 🏗️ System Architecture
- The application is built on a decoupled frontend-backend architecture, ensuring scalability and separation of concerns.

+------------------------+        +--------------------------+        +---------------------+
|   Frontend             |        |      Backend API         |        |     AI & Data       |
|  (Streamlit)           |        |       (FastAPI)          |        |       (Google AI)   |
+------------------------+        +--------------------------+        +---------------------+
| - File Uploads         |        | - /v1/resumes (POST)     |        | - Gemini LLM        |
| - Screening Dashboard  |  <-->  | - /v1/jds/... (POST)     |  <-->  | - Embedding Models  |
| - Report Viewer        |        | - /v1/screen (POST)      |        +---------------------+
+------------------------+        | - /v1/reports/{id} (GET) |                  ^
                                  +--------------------------+                  |
                                               |                                |
                                               v                                |
                                  +--------------------------+                  |
                                  |     Agent Orchestrator   |------------------+
                                  +--------------------------+
                                               |
                                               v
                                  +--------------------------+
                                  |    Database (MongoDB)    |
                                  +--------------------------+
