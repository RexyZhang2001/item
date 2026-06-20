# VLM_Detection_MCP

RTMP 流 → 抽帧 → YOLO 人机检测 → **固定 3 张 JPG**（MCP Streamable HTTP，供耀耀工厂接入）。

**请先阅读：`00_从这里开始_README.md` 与 `对话与后续步骤_交接.md`**

## 目录说明

| 路径 | 说明 |
|------|------|
| `mcp_vlm_server.py` | MCP 服务入口 |
| `rtmp_pipeline.py` | 抽流 + 三图 JPEG 逻辑 |
| `detect_core.py` / `stream_capture.py` | YOLO 与拉流 |
| `weights/` | `worker/yolo26x_worker.pt`（~113MB）、`machinery/yolo26l_machinery.pt`（~51MB） |
| `scripts/` | 安装、启动、自检 |
| `deploy/` | systemd 示例 |
| `YAoyao_MCP_STREAMABLE.md` | 耀耀工厂表单说明 |

## 上传到 Linux（10.148.1.22）

**推荐路径：** `/root/VLM_Detection_MCP`

### 方式 A：Cursor 已 Remote-SSH 连上服务器

1. 在服务器终端：`mkdir -p /root/VLM_Detection_MCP`
2. 本机把文件夹 `E:\3311 AI\VLM_Detection_MCP` **整个拖进** 远程 `/root/VLM_Detection_MCP`
3. 确认 `weights/` 下两个 `.pt` 已随文件夹一起上传（本机已包含）

### 方式 B：本机 PowerShell

```powershell
cd "E:\3311 AI\VLM_Detection_MCP\scripts"
.\upload_to_server.ps1
```

## 服务器启动

```bash
cd /root/VLM_Detection_MCP
bash scripts/setup_linux.sh mcp
export MCP_BEARER_TOKEN='你的密钥'
export MCP_PUBLIC_URL=http://10.148.1.22:8000
bash scripts/run_mcp_http.sh
```

MCP URL：`http://10.148.1.22:8000/mcp`  
工具：`rtmp_triple_analyze`，参数：`stream_url`（RTMP 字符串）。

## 清理

删除整个目录即可：`rm -rf /root/VLM_Detection_MCP`
