import os
from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from models import (
    AddVideoRequest, AskRequest, AskResponse,
    VideosListResponse, VideoInfo,
)
import rag

load_dotenv()

app = FastAPI(title="YouTube RAG Assistant", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "google_api_key_set": bool(os.environ.get("GOOGLE_API_KEY"))}


@app.get("/api/videos", response_model=VideosListResponse)
def get_videos():
    vids = rag.list_videos()
    return VideosListResponse(videos=vids, count=len(vids))


@app.post("/api/videos", response_model=VideoInfo)
def post_video(req: AddVideoRequest):
    try:
        return rag.add_video(req.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add video: {e}")


@app.delete("/api/videos/{video_id}")
def delete_video(video_id: str):
    ok = rag.delete_video(video_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Video not found")
    return {"deleted": video_id}


@app.post("/api/reset")
def reset():
    rag.reset_all()
    return {"status": "reset"}


@app.post("/api/ask", response_model=AskResponse)
def ask(req: AskRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question is empty.")
    try:
        answer, sources = rag.answer_question(req.question)
        return AskResponse(answer=answer, sources=sources)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error answering: {e}")


# Serve frontend
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def index():
        return FileResponse(str(FRONTEND_DIR / "index.html"))
