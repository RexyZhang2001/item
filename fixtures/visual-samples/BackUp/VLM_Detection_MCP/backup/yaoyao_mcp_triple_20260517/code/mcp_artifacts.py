"""三图落盘 + 项目内 HTTP 静态服务（8001，仅 output/mcp_artifacts）。"""
from __future__ import annotations

import os
import threading
import uuid
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARTIFACT_ROOT = Path(
    os.environ.get("ARTIFACT_ROOT", str(ROOT / "output" / "mcp_artifacts"))
).resolve()
PUBLIC_BASE = os.environ.get(
    "MCP_ARTIFACT_PUBLIC_BASE", "http://10.148.1.22:8001"
).rstrip("/")
HTTP_PORT = int(os.environ.get("MCP_ARTIFACT_HTTP_PORT", "8001"))

_server: ThreadingHTTPServer | None = None
_server_lock = threading.Lock()


class _ArtifactHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ARTIFACT_ROOT), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.end_headers()

    def log_message(self, fmt, *args):
        return


def ensure_artifact_http_server() -> None:
    global _server
    with _server_lock:
        if _server is not None:
            return
        ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
        _server = ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), _ArtifactHandler)
        threading.Thread(target=_server.serve_forever, daemon=True).start()


def publish_triple_jpeg(
    original: bytes,
    human: bytes,
    machine: bytes,
) -> tuple[str, str, str]:
    """保存三张 JPEG，返回 HTTP URL（顺序固定）。"""
    ensure_artifact_http_server()
    job_id = uuid.uuid4().hex
    job_dir = ARTIFACT_ROOT / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    names = ("image.jpg", "image-human.jpg", "image-machine.jpg")
    blobs = (original, human, machine)
    urls: list[str] = []
    for name, data in zip(names, blobs):
        path = job_dir / name
        path.write_bytes(data)
        urls.append(f"{PUBLIC_BASE}/{job_id}/{name}")
    return urls[0], urls[1], urls[2]
