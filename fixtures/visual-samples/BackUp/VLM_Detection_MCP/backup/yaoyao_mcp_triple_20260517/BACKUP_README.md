# 耀耀工厂 MCP 三图插件备份（2026-05-17）

## 备份说明

本目录为 **算法更换前** 的快照：双 YOLO（人/PPE + 机械）+ RTMP 抽帧，固定输出 3 张 JPEG URL（`json_url` 模式），已在耀耀工厂联调通过。

**未包含**（仍使用项目原路径，未复制以节省空间）：

- `.venv/`（Python 虚拟环境）
- `weights/worker/yolo26x_worker.pt`、`weights/machinery/yolo26l_machinery.pt`（见 `config/weights_manifest.txt`）

## 目录结构

| 路径 | 内容 |
|------|------|
| `code/` | `mcp_vlm_server.py`、`mcp_artifacts.py`、`rtmp_pipeline.py`、`detect_core.py` 等 |
| `scripts/` | `run_mcp_http.sh`、`test_rtmp_triple.py`、`hiagent_parse_triple_urls.py` |
| `config/` | `.mcp_local.env`、`weights_manifest.txt` |
| `docs/` | 耀耀接入与交接文档 |
| `logs_snapshot/` | 备份时 `mcp_tool.log` / `mcp_http.log` 末尾 |

## 当时运行配置摘要

- MCP：`http://10.148.1.22:8000/mcp`，Streamable HTTP，Bearer 见 `config/.mcp_local.env`
- 图床：`http://10.148.1.22:8001`，`MCP_IMAGE_DELIVERY=json_url`
- 工具：`rtmp_triple_analyze`，输出 `content[0].json` 含 `image_url` / `image_human_url` / `image_machine_url`
- 三张图顺序：原图 → 人员/PPE → 机械

## 恢复方法

```bash
cd /root/VLM_Detection_MCP/VLM_Detection_MCP
BK=backup/yaoyao_mcp_triple_20260517

cp -a "$BK/code/"* .
cp -a "$BK/scripts/"* scripts/
cp -a "$BK/config/.mcp_local.env" .mcp_local.env

# 重启 MCP
pkill -f mcp_vlm_server.py || true
source .mcp_local.env && source .venv/bin/activate
bash scripts/run_mcp_http.sh
```

恢复后在耀耀工厂 **重新同步工具**。

## 压缩包

同级目录：`backup/yaoyao_mcp_triple_20260517.tar.gz`（便于下载带走）
