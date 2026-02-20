import mimetypes
import os
from typing import Callable, Any


class MimeRouter:
    """
    detects MIME types of input files and routes them to appropriate loaders.
    Currently a mock for multimodal support, but functional for text/json.
    """

    def __init__(self):
        mimetypes.init()
        self.loaders = {
            "text/plain": self.load_text,
            "text/markdown": self.load_text,
            "application/json": self.load_json,
            # Future multimodal stubs
            "image/png": self.load_image_mock,
            "image/jpeg": self.load_image_mock,
            "audio/mpeg": self.load_audio_mock,
            "video/mp4": self.load_video_mock,
            "application/pdf": self.load_pdf_mock,
        }

    def route(self, filepath: str) -> Any:
        """Determines loader for file and executes it."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        mime_type, _ = mimetypes.guess_type(filepath)
        if not mime_type:
            # Fallback for common text files without extension or unknown
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    f.read(1024)
                mime_type = "text/plain"
            except UnicodeDecodeError:
                mime_type = "application/octet-stream"

        loader = self.loaders.get(mime_type)
        if loader:
            return loader(filepath)
        else:
            return f"[Unsupported MIME type: {mime_type}]"

    def load_text(self, filepath: str) -> str:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    def load_json(self, filepath: str) -> dict:
        import json

        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_image_mock(self, filepath: str) -> str:
        return f"[IMAGE CONTENT MOCK: {os.path.basename(filepath)}]"

    def load_audio_mock(self, filepath: str) -> str:
        return f"[AUDIO CONTENT MOCK: {os.path.basename(filepath)}]"

    def load_video_mock(self, filepath: str) -> str:
        return f"[VIDEO CONTENT MOCK: {os.path.basename(filepath)}]"

    def load_pdf_mock(self, filepath: str) -> str:
        return f"[PDF CONTENT MOCK: {os.path.basename(filepath)}]"
