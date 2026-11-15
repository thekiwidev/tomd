"""Pure helpers for what tomd accepts: which dropped paths are convertible,
and which YouTube links name a single video. No UI imports — shared by the
desktop UI and the sidecar.
"""

import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Extensions MarkItDown can handle. Used to filter folder drops; a file
# dropped directly is always accepted so MarkItDown can have a go at it.
SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls", ".csv",
    ".json", ".xml", ".html", ".htm", ".txt", ".rtf", ".epub", ".msg",
    ".eml", ".wav", ".mp3", ".m4a", ".jpg", ".jpeg", ".png", ".webp",
    ".ipynb", ".zip",
}


def collect_paths(paths):
    """Expand dropped paths into a flat list of convertible file paths."""
    files = []
    for raw in paths:
        path = Path(raw)
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file() and child.suffix.lower() in SUPPORTED_EXTENSIONS:
                    files.append(child)
    return files


# The two shapes a person can actually end up with: the address bar gives
# youtube.com/watch?v=…, YouTube's own Share button gives youtu.be/… . Both
# name a single video, which is all a transcript can come from.
_WATCH_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com"}
_SHORT_HOSTS = {"youtu.be", "www.youtu.be"}

# YouTube video ids have been 11 characters of this alphabet for the life of
# the API. Checking it here turns a typo into a clear message instead of a
# conversion that fetches a 404 page and calls it a document.
_YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")

_COPY_HINT = "Open the video on YouTube and copy the link from the address bar."

# Paths that are recognisably YouTube but aren't a plain video page. Worth
# naming individually — "unsupported" explains far more than "invalid".
_UNSUPPORTED_PATHS = {
    "shorts": "Shorts links aren't supported yet.",
    "live": "Live stream links aren't supported yet.",
    "embed": "Embed links aren't supported.",
    "playlist": "That's a playlist, not a single video.",
    "channel": "That's a channel, not a video.",
    "user": "That's a channel, not a video.",
    "c": "That's a channel, not a video.",
    "results": "That's a search results page, not a video.",
    "feed": "That's a YouTube feed, not a video.",
}


def parse_youtube_url(url: str) -> tuple:
    """(video_id, error). Exactly one is set; both are None for empty input.

    youtu.be links — what YouTube's Share button produces — carry the id as the
    path rather than a `v` parameter, so they're converted rather than refused.
    """
    url = (url or "").strip()
    if not url:
        return None, None
    try:
        parsed = urlparse(url)
    except ValueError:
        return None, f"That isn't a valid link. {_COPY_HINT}"

    if parsed.scheme not in ("http", "https"):
        if not parsed.scheme and "youtu" in url:
            return None, "Include the full link, starting with https://"
        return None, f"That isn't a YouTube link. {_COPY_HINT}"

    host = parsed.netloc.lower().split(":")[0]
    parts = [p for p in parsed.path.split("/") if p]

    if host in _SHORT_HOSTS:
        candidate = parts[0] if parts else ""
    elif host in _WATCH_HOSTS:
        if parts and parts[0] in _UNSUPPORTED_PATHS:
            return None, f"{_UNSUPPORTED_PATHS[parts[0]]} {_COPY_HINT}"
        if parsed.path.rstrip("/") not in ("/watch", ""):
            return None, f"That isn't a video link. {_COPY_HINT}"
        values = parse_qs(parsed.query).get("v")
        candidate = values[0] if values else ""
    elif host.endswith(".youtube.com") or host == "youtube.com":
        # music.youtube.com, studio.youtube.com, and friends.
        return None, f"That YouTube address isn't a video page. {_COPY_HINT}"
    else:
        return None, f"That isn't a YouTube link. {_COPY_HINT}"

    if not candidate:
        return None, f"That link doesn't name a video. {_COPY_HINT}"
    if not _YOUTUBE_ID.match(candidate):
        return None, f"\"{candidate[:24]}\" isn't a valid video id. {_COPY_HINT}"
    return candidate, None


def youtube_video_id(url: str):
    """The video id in a supported YouTube URL, or None."""
    return parse_youtube_url(url)[0]


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")[:80].strip("-")


def canonical_youtube_url(video_id: str) -> str:
    """The one URL shape MarkItDown's YouTube converter recognises.

    Its `accepts()` requires the URL to start with exactly
    "https://www.youtube.com/watch?", and its transcript lookup reads the video
    id out of the `v` query parameter. A youtu.be, /shorts/ or /live/ link
    satisfies neither, and the failure is silent — the generic HTML converter
    picks the page up instead and returns YouTube's footer as the "document".
    """
    return f"https://www.youtube.com/watch?v={video_id}"


def slugify(text: str, fallback: str = "transcript") -> str:
    """'My Video: Part 2!' -> 'my-video-part-2'.

    Falls back when a title slugifies to nothing (all punctuation, or
    non-Latin script) — the video id makes a usable filename where the title
    doesn't.
    """
    return _slug(text) or _slug(fallback) or "transcript"


def unique_output(directory: Path, slug: str, taken=()) -> Path:
    """<slug>.md in `directory`, suffixed -2, -3… rather than overwriting.

    `taken` covers paths that are spoken for but not yet on disk: two different
    videos can share a title, and queued rows haven't written their file yet,
    so checking the filesystem alone would hand both the same name.
    """
    taken = set(taken)
    candidate = directory / f"{slug}.md"
    counter = 2
    while candidate.exists() or candidate in taken:
        candidate = directory / f"{slug}-{counter}.md"
        counter += 1
    return candidate
