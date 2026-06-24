from pydantic import BaseModel
from typing import List, Optional


class AddVideoRequest(BaseModel):
    url: str


class AskRequest(BaseModel):
    question: str


class SourceItem(BaseModel):
    video_id: str
    title: Optional[str] = None
    channel: Optional[str] = None
    url: str
    snippet: Optional[str] = None


class AskResponse(BaseModel):
    answer: str
    sources: List[SourceItem] = []


class VideoInfo(BaseModel):
    video_id: str
    title: Optional[str] = None
    channel: Optional[str] = None
    url: str


class VideosListResponse(BaseModel):
    videos: List[VideoInfo]
    count: int
