### ✨ Features (Technical Deep Dive)
##### Multi-Format Resume Ingestion & Parsing:

- The system ingests resumes in multiple formats, including .pdf, .docx, .png, and .jpg.

-It uses a hybrid parsing strategy: PyMuPDF for efficient text extraction from text-based PDFs, python-docx for Word documents, and Google's Tesseract-OCR engine (via pytesseract) for image-based documents.

=A specialized Gemini agent then receives the extracted raw text. This agent uses a few-shot prompt containing curated examples to reliably parse the text into a structured JSON object, which is validated against a strict Pydantic model.

##### Agentic Title Inference:

- To handle real-world resume ambiguity, the system uses a two-agent chain for project parsing.

- The primary Extractor Agent performs the initial parse. If it finds a project with a null title, a secondary, hyper-focused Title Synthesizer Agent is invoked.

- This second agent receives only the project's responsibilities and uses a constrained prompt to generate a concise, descriptive title, ensuring the final data is always complete.

##### Comprehensive JD Analysis:

- A dedicated JD Analyzer Agent is prompted to act as a senior technical recruiter, extracting key criteria like required/preferred skills, years of experience, and education into a ParsedJD Pydantic model.

- The API provides flexibility by exposing two distinct endpoints: /jds/upload-file (accepting multipart/form-data) and /jds/paste-text (accepting text/plain), which both funnel data to the same underlying agent.

##### Semantic Candidate Screening:

- The core Screening Agent receives the structured JSON from a parsed resume and a JD. It constructs a detailed prompt containing both JSON objects.

- It leverages Gemini's JSON Mode to guarantee a valid, structured JSON response containing a match_score, a qualitative summary, and lists of strengths and gaps, which is then validated by the ScreeningResult Pydantic model.

##### Stateful, Asynchronous Backend:

- Built with FastAPI, the API is fully asynchronous and leverages Pydantic for automatic request validation, serialization, and generation of OpenAPI (/docs) and ReDoc (/redoc) documentation.

- The system is stateful, using PyMongo to connect to a MongoDB instance. A singleton pattern is used for the database client to ensure efficient connection pooling.

- All parsed artifacts and screening results are persisted in separate collections and referenced via their unique MongoDB ObjectId, allowing for a robust, decoupled workflow.

