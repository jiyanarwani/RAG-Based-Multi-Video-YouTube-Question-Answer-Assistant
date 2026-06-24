# YouTube RAG Assistant (Python 3.14 Compatible)

A ChatGPT-style assistant that answers questions from YouTube video transcripts.
**Backend:** FastAPI + LangChain + **FAISS** + Gemini.
**Frontend:** Vanilla HTML/CSS/JS (ChatGPT-style UI).

## Why FAISS instead of ChromaDB?

ChromaDB pulls in `grpcio`, which has no prebuilt wheels for Python 3.14 on
Windows yet and fails with `ImportError: DLL load failed while importing cygrpc`.
This project uses **FAISS (`faiss-cpu`)**, which has Python 3.14 wheels and
zero gRPC dependencies.

## Project structure

```
yt-rag/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── rag.py               # FAISS RAG pipeline
│   ├── transcript_loader.py # YouTube transcripts + oEmbed metadata
│   ├── models.py            # Pydantic models
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
└── README.md
```

## Setup (Windows 11, Python 3.14, VS Code)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

Create `.env` from `.env.example` and add your Gemini API key:

```
GOOGLE_API_KEY=your_key_here
```

Get a free key at https://aistudio.google.com/app/apikey

## Run

```bash
cd backend
python -m uvicorn main:app --reload
```

Open http://localhost:8000

The backend serves the frontend on `/`, so a single command runs the whole app.

## API

| Method | Path                | Description              |
|--------|---------------------|--------------------------|
| GET    | /api/health         | Health check             |
| GET    | /api/videos         | List indexed videos      |
| POST   | /api/videos         | `{ "url": "..." }` add   |
| DELETE | /api/videos/{id}    | Remove a video           |
| POST   | /api/ask            | `{ "question": "..." }`  |
| POST   | /api/reset          | Clear index              |

## Notes

- FAISS index persists to `backend/faiss_store/`.
- Embeddings use `sentence-transformers/all-MiniLM-L6-v2` (downloaded on first run).
- First request downloads the embedding model (~90 MB).
