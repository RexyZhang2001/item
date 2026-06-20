"""MCP 插件：Streamable HTTP / STDIO — RTMP 字符串入，三图依次出。

耀耀工厂「接入 MCP 插件」:
  传输方式: Streamable HTTP
  URL: http://<服务器IP>:8000/mcp
  认证: Bearer Token（与 MCP_BEARER_TOKEN 一致；未设置则可不填）

启动:
  bash scripts/run_mcp_http.sh
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP

from rtmp_pipeline import analyze_rtmp_stream

_mcp_host = os.environ.get("MCP_HTTP_HOST", "0.0.0.0")
_mcp_port = int(os.environ.get("MCP_HTTP_PORT", "8000"))
_bearer = os.environ.get("MCP_BEARER_TOKEN", "").strip()
_public_base = os.environ.get(
    "MCP_PUBLIC_URL",
    f"http://{_mcp_host if _mcp_host != '0.0.0.0' else '127.0.0.1'}:{_mcp_port}",
).rstrip("/")


class _StaticBearerVerifier:
    """与耀耀工厂表单 Bearer Token 字段对齐：固定密钥比对。"""

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
            "输入施工现场 RTMP/HLS/FLV 流地址（单个字符串），"
            "抽取当前帧并运行 YOLO 人机检测，"
            "按固定顺序返回三张 JPEG：原图、人员检测图、机械检测图。"
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


@mcp.tool()
def ping() -> str:
    """服务存活检测，不加载 YOLO。"""
    return "ok"


@mcp.tool()
def rtmp_triple_analyze(stream_url: str) -> str:
    """【主工具】输入 RTMP 流地址字符串，固定依次输出 3 张 JPEG 图。

    输入:
      stream_url: 单个字符串，视频流地址，如 rtmp://10.148.1.22/live/test

    输出（JSON 字符串，format=jpeg，image_count=3）:
      images[0] — 当前帧原图 (image.jpg)
      images[1] — 人员/PPE YOLO 叠加 (image-human.jpg)
      images[2] — 机械 YOLO 叠加 (image-machine.jpg)
      每项 mime 均为 image/jpeg，含 base64。
      顶层字段 image / image_human / image_machine 与 images 顺序一致，便于耀耀工厂编排。
    """
    result = analyze_rtmp_stream(stream_url.strip(), return_urls=False)
    return json.dumps(result, ensure_ascii=False)


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
