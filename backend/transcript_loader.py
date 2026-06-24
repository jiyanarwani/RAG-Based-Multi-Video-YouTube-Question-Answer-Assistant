import re
import requests
from typing import Optional, Tuple, List
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound


YOUTUBE_ID_RE = re.compile(
    r"(?:v=|youtu\.be/|/embed/|/shorts/)([A-Za-z0-9_-]{11})"
)


def extract_video_id(url: str) -> Optional[str]:
    if not url:
        return None
    url = url.strip()
    if len(url) == 11 and re.match(r"^[A-Za-z0-9_-]{11}$", url):
        return url
    m = YOUTUBE_ID_RE.search(url)
    return m.group(1) if m else None


def fetch_video_metadata(video_id: str) -> Tuple[Optional[str], Optional[str]]:
    """Use YouTube oEmbed to fetch title + channel name."""
    try:
        r = requests.get(
            "https://www.youtube.com/oembed",
            params={"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"},
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            return data.get("title"), data.get("author_name")
    except Exception:
        pass
    return None, None


def fetch_transcript_text(video_id: str, languages: Optional[List[str]] = None) -> str:
    languages = languages or ["en", "en-US", "en-GB"]

    try:
        api = YouTubeTranscriptApi()

        transcript = api.fetch(video_id, languages=languages)

        return " ".join(
            snippet.text.strip()
            for snippet in transcript
            if snippet.text
        )

    except Exception as e:
        raise ValueError(f"Failed to fetch transcript: {e}")