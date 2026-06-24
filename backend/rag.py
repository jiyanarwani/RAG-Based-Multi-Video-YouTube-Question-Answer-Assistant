import os
import pickle
from pathlib import Path
from typing import List, Dict, Optional

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI

from transcript_loader import (
    extract_video_id,
    fetch_transcript_text,
    fetch_video_metadata,
)
from models import SourceItem, VideoInfo

BASE_DIR = Path(__file__).resolve().parent
STORE_DIR = BASE_DIR / "faiss_store"
STORE_DIR.mkdir(exist_ok=True)
INDEX_PATH = STORE_DIR / "index"
META_PATH = STORE_DIR / "videos.pkl"

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_embeddings: Optional[HuggingFaceEmbeddings] = None
_vectorstore: Optional[FAISS] = None
_videos: Dict[str, VideoInfo] = {}


def _get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    return _embeddings


def _save_meta():
    with open(META_PATH, "wb") as f:
        pickle.dump({k: v.model_dump() for k, v in _videos.items()}, f)


def _load_meta():
    global _videos
    if META_PATH.exists():
        with open(META_PATH, "rb") as f:
            raw = pickle.load(f)
        _videos = {k: VideoInfo(**v) for k, v in raw.items()}


def _load_store() -> Optional[FAISS]:
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore
    if (INDEX_PATH.with_suffix(".faiss")).exists() or (STORE_DIR / "index.faiss").exists():
        try:
            _vectorstore = FAISS.load_local(
                str(STORE_DIR),
                _get_embeddings(),
                index_name="index",
                allow_dangerous_deserialization=True,
            )
        except Exception:
            _vectorstore = None
    return _vectorstore


def _save_store():
    if _vectorstore is not None:
        _vectorstore.save_local(str(STORE_DIR), index_name="index")


# Initialize on import
_load_meta()
_load_store()


def add_video(url: str) -> VideoInfo:
    global _vectorstore
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError("Invalid YouTube URL or video id.")

    if video_id in _videos:
        return _videos[video_id]

    transcript = fetch_transcript_text(video_id)
    if not transcript.strip():
        raise ValueError("Empty transcript.")

    title, channel = fetch_video_metadata(video_id)
    canonical_url = f"https://www.youtube.com/watch?v={video_id}"

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_text(transcript)
    docs = [
        Document(
            page_content=c,
            metadata={
                "video_id": video_id,
                "title": title or "",
                "channel": channel or "",
                "url": canonical_url,
            },
        )
        for c in chunks
    ]

    emb = _get_embeddings()
    if _vectorstore is None:
        _vectorstore = FAISS.from_documents(docs, emb)
    else:
        _vectorstore.add_documents(docs)
    _save_store()

    info = VideoInfo(video_id=video_id, title=title, channel=channel, url=canonical_url)
    _videos[video_id] = info
    _save_meta()
    return info


def list_videos() -> List[VideoInfo]:
    return list(_videos.values())


def delete_video(video_id: str) -> bool:
    global _vectorstore
    if video_id not in _videos:
        return False

    # FAISS lacks per-id deletes pre-rebuild. Rebuild from remaining docs.
    remaining_docs: List[Document] = []
    if _vectorstore is not None:
        try:
            docstore = _vectorstore.docstore._dict  # type: ignore[attr-defined]
            for d in docstore.values():
                if d.metadata.get("video_id") != video_id:
                    remaining_docs.append(d)
        except Exception:
            remaining_docs = []

    del _videos[video_id]
    _save_meta()

    if remaining_docs:
        _vectorstore = FAISS.from_documents(remaining_docs, _get_embeddings())
        _save_store()
    else:
        _vectorstore = None
        for p in STORE_DIR.glob("index.*"):
            try:
                p.unlink()
            except Exception:
                pass
    return True


def reset_all():
    global _vectorstore, _videos
    _vectorstore = None
    _videos = {}
    if META_PATH.exists():
        META_PATH.unlink()
    for p in STORE_DIR.glob("index.*"):
        try:
            p.unlink()
        except Exception:
            pass


PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     """
You are a helpful assistant answering questions only from the provided YouTube transcripts.

When answering:
- Refer to videos by their actual title.
- Never say "Video 1", "Video 2", "Video 3", etc.
- If information comes from multiple videos, explicitly mention the video titles.
- If the answer is not present in the transcripts, say you don't know.
"""),
    ("human", "Context:\n{context}\n\nQuestion: {question}")
])


def _format_context(docs: List[Document]) -> str:
    parts = []

    for d in docs:
        t = d.metadata.get("title") or d.metadata.get("video_id")
        ch = d.metadata.get("channel") or ""

        parts.append(
            f"VIDEO TITLE: {t}\n"
            f"CHANNEL: {ch}\n"
            f"CONTENT:\n{d.page_content}"
        )

    return "\n\n".join(parts)


def answer_question(question: str, k: int = 4):
    if _vectorstore is None or not _videos:
        return "No videos indexed yet. Add a YouTube URL first.", []

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set. Add it to backend/.env")

    retriever = _vectorstore.as_retriever(search_kwargs={"k": k})
    docs = retriever.invoke(question)

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2, api_key=api_key)
    chain = PROMPT | llm | StrOutputParser()
    answer = chain.invoke({"context": _format_context(docs), "question": question})

    seen = set()
    sources: List[SourceItem] = []
    for d in docs:
        vid = d.metadata.get("video_id")
        if not vid or vid in seen:
            continue
        seen.add(vid)
        sources.append(SourceItem(
            video_id=vid,
            title=d.metadata.get("title") or None,
            channel=d.metadata.get("channel") or None,
            url=d.metadata.get("url") or f"https://www.youtube.com/watch?v={vid}",
            snippet=(d.page_content[:200] + "…") if len(d.page_content) > 200 else d.page_content,
        ))
    return answer, sources
