"""MCP 插件：RTMP 入 → 固定 3 张 JPEG。

交付方式（MCP_IMAGE_DELIVERY）:
  json_url — 默认（耀耀工厂），落盘 + 8001 HTTP 直链，返回结构化字段（可直引 image_url 等）
  inline   — 3 个 MCP Image 块
  embedded — 3 个 EmbeddedResource blob
  url      — 3 个 resource_link
"""
from __future__ import annotations

import base64
import logging
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from pydantic import BaseModel, Field

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import BlobResourceContents, CallToolResult, EmbeddedResource, ImageContent, ResourceLink

from mcp_artifacts import publish_triple_jpeg
from rtmp_pipeline import _get_bundle, _jpeg_bytes, analyze_rtmp_stream_bgr

_log_dir = ROOT / "logs"
_log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=str(_log_dir / "mcp_tool.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
_logger = logging.getLogger("mcp_vlm")

_mcp_host = os.environ.get("MCP_HTTP_HOST", "0.0.0.0")
_mcp_port = int(os.environ.get("MCP_HTTP_PORT", "8000"))
_bearer = os.environ.get("MCP_BEARER_TOKEN", "").strip()
_public_base = os.environ.get(
    "MCP_PUBLIC_URL",
    f"http://{_mcp_host if _mcp_host != '0.0.0.0' else '127.0.0.1'}:{_mcp_port}",
).rstrip("/")

_IMAGE_ROLES = (
    ("image.jpg", "image", "当前帧原图"),
    ("image-human.jpg", "image-human", "人员/PPE 检测图"),
    ("image-machine.jpg", "image-machine", "机械检测图"),
)


class TripleAnalyzeResult(BaseModel):
    """结构化输出：耀耀可直接引用各字段，无需代码解析。"""

    ok: bool = True
    format: str = "jpeg"
    image_count: int = 3
    stream_url: str = ""
    image_url: str = Field(description="原图 HTTP 直链")
    image_human_url: str = Field(description="人员/PPE 检测图 HTTP 直链")
    image_machine_url: str = Field(description="机械检测图 HTTP 直链")
    worker_boxes: int = 0
    machinery_boxes: int = 0


class _StaticBearerVerifier:
    def __init__(self, expected: str) -> None:
        self._expected = expected

    async def verify_token(self, token: str) -> AccessToken | None:
        if token and token == self._expected:
            return AccessToken(token=token, client_id="yaoyao-factory", scopes=[])
        return None


def _build_mcp() -> FastMCP:
    kwargs: dict = {
        "name": "vlm-rtmp-yolo-triple",
        "instructions": (
            "输入 RTMP/HLS/FLV 流地址，抽取当前帧并 YOLO 检测，"
            "固定返回三张 JPEG 的 HTTP 直链（JSON 文本，供耀耀工厂工作流与视觉模型使用）。"
        ),
        "host": _mcp_host,
        "port": _mcp_port,
    }
    if _bearer:
        kwargs["auth"] = AuthSettings(
            issuer_url=_public_base,
            resource_server_url=f"{_public_base}/mcp",
        )
        kwargs["token_verifier"] = _StaticBearerVerifier(_bearer)
    return FastMCP(**kwargs)


mcp = _build_mcp()


def _preload_yolo() -> None:
    if os.environ.get("MCP_PRELOAD_YOLO", "1").strip() not in ("1", "true", "yes"):
        return
    _logger.info("preload YOLO start")
    t0 = time.time()
    _get_bundle()
    _logger.info("preload YOLO done in %.1fs", time.time() - t0)


def _delivery_mode() -> str:
    return os.environ.get("MCP_IMAGE_DELIVERY", "json_url").strip().lower()


def _b64(jpeg: bytes) -> str:
    return base64.b64encode(jpeg).decode("ascii")


def _build_triple_result_struct(
    j1: bytes, j2: bytes, j3: bytes, meta: dict, stream_url: str
) -> TripleAnalyzeResult:
    """耀耀工厂：落盘 + 结构化字段（image_url 等可直接引用）。"""
    u1, u2, u3 = publish_triple_jpeg(j1, j2, j3)
    counts = meta.get("counts") or {}
    return TripleAnalyzeResult(
        ok=True,
        stream_url=meta.get("stream_url") or stream_url[:200],
        image_url=u1,
        image_human_url=u2,
        image_machine_url=u3,
        worker_boxes=int(counts.get("worker", 0)),
        machinery_boxes=int(counts.get("machinery", 0)),
    )


def _build_triple_result(j1: bytes, j2: bytes, j3: bytes) -> CallToolResult:
    mode = _delivery_mode()
    blobs = (j1, j2, j3)

    if mode == "embedded":
        blocks = [
            EmbeddedResource(
                type="resource",
                resource=BlobResourceContents(
                    uri=f"vlm-detection://triple/{role}",
                    mimeType="image/jpeg",
                    blob=_b64(j),
                ),
                meta={"role": role, "index": idx},
            )
            for idx, (j, (_, role, _)) in enumerate(zip(blobs, _IMAGE_ROLES), start=1)
        ]
        return CallToolResult(content=blocks)

    if mode == "url":
        u1, u2, u3 = publish_triple_jpeg(j1, j2, j3)
        blocks = [
            ResourceLink(
                type="resource_link",
                uri=url,
                name=fname,
                mimeType="image/jpeg",
                meta={"role": role},
            )
            for url, (fname, role, _) in zip((u1, u2, u3), _IMAGE_ROLES)
        ]
        return CallToolResult(content=blocks)

    blocks = [
        ImageContent(
            type="image",
            data=_b64(j),
            mimeType="image/jpeg",
            meta={"role": role, "index": idx},
        )
        for idx, (j, (_, role, _)) in enumerate(zip(blobs, _IMAGE_ROLES), start=1)
    ]
    return CallToolResult(content=blocks)


_preload_yolo()


@mcp.tool()
def ping() -> str:
    """服务存活检测，不加载 YOLO。"""
    return "ok"


@mcp.tool()
def rtmp_triple_analyze(stream_url: str) -> TripleAnalyzeResult:
    """输入 RTMP 流地址，返回 3 张检测图 HTTP 直链（结构化字段）。

    可直接引用：image_url、image_human_url、image_machine_url。
    """
    url = stream_url.strip()
    if not url:
        raise ToolError("stream_url 为空")
    mode = _delivery_mode()
    _logger.info("rtmp_triple_analyze start url=%s delivery=%s", url[:120], mode)
    t0 = time.time()
    try:
        original, human_vis, machine_vis, meta = analyze_rtmp_stream_bgr(url)
    except RuntimeError as e:
        _logger.warning("rtmp_triple_analyze failed: %s", e)
        raise ToolError(str(e)) from e

    max_side = int(os.environ.get("MCP_IMAGE_MAX_SIDE", "640"))
    if 0 < max_side < 640:
        from stream_capture import preprocess_for_infer

        original = preprocess_for_infer(original, max_side=max_side)
        human_vis = preprocess_for_infer(human_vis, max_side=max_side)
        machine_vis = preprocess_for_infer(machine_vis, max_side=max_side)

    j1, j2, j3 = _jpeg_bytes(original), _jpeg_bytes(human_vis), _jpeg_bytes(machine_vis)

    if mode == "json_url":
        out = _build_triple_result_struct(j1, j2, j3, meta, url)
        _logger.info(
            "rtmp_triple_analyze done delivery=json_url elapsed=%.1fs urls=%s",
            time.time() - t0,
            out.image_url[:48],
        )
        return out

    result = _build_triple_result(j1, j2, j3)
    _logger.info(
        "rtmp_triple_analyze done delivery=%s elapsed=%.1fs bytes=%d,%d,%d",
        mode,
        time.time() - t0,
        len(j1),
        len(j2),
        len(j3),
    )
    return result


def main() -> None:
    transport = os.environ.get("MCP_TRANSPORT", "stdio").strip().lower()
    if transport in ("stdio", ""):
        mcp.run(transport="stdio")
        return
    if transport in ("streamable-http", "http"):
        mcp.run(transport="streamable-http")
        return
    if transport == "sse":
        mcp.run(transport="sse")
        return
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
