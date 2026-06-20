# VLM_Detection_MCP — 交付包（从这里开始）

> **唯一上传目录**：把整个 `VLM_Detection_MCP` 文件夹上传到 Linux  
> **服务器路径**：`/root/VLM_Detection_MCP`  
> **清理时**：`rm -rf /root/VLM_Detection_MCP`

---

## 一、这个文件夹里有什么

### 必传（MCP 插件核心）

| 文件/目录 | 作用 |
|-----------|------|
| `mcp_vlm_server.py` | MCP Streamable HTTP 服务入口 |
| `rtmp_pipeline.py` | RTMP 字符串 → 抽帧 → YOLO → **3 张 JPG** |
| `detect_core.py` | 双模型 YOLO 推理 |
| `stream_capture.py` | RTMP/HLS 拉流抽帧 |
| `artifact_storage.py` | 三图存储（可选 URL） |
| `config.yaml` | 模型路径与推理参数 |
| `weights/worker/yolo26x_worker.pt` | 工人/PPE 权重（约 113MB） |
| `weights/machinery/yolo26l_machinery.pt` | 机械权重（约 51MB） |
| `requirements.txt` + `requirements-mcp.txt` | Python 依赖 |
| `scripts/setup_linux.sh` | 服务器装 venv + 依赖 |
| `scripts/install_on_server.sh` | 服务器一键安装 |
| `scripts/run_mcp_http.sh` | 启动 MCP HTTP |
| `scripts/test_rtmp_triple.py` | 自检：RTMP → 3 张 jpg |
| `scripts/deploy_full_to_server.ps1` | **本机**一键上传+安装（需输密码） |

### 可选（REST / 本地测试）

| 文件 | 作用 |
|------|------|
| `hiagent_api.py` + `openapi.yaml` | 传统 HTTP 插件（8080 端口） |
| `test_stream_detect.py` | 本地/服务器流检测测试 |
| `deploy/vlm-mcp.service` | systemd 常驻示例 |

### 文档（含对话交接）

| 文件 | 内容 |
|------|------|
| **`对话与后续步骤_交接.md`** | **本次沟通摘要 + 待办清单（另一窗口必读）** |
| `YAoyao_MCP_STREAMABLE.md` | 耀耀工厂表单怎么填 |
| `MCP_PLUGIN.txt` | MCP 传输方式说明 |
| `DEPLOY.txt` | 部署要点 |
| `HANDOFF_交接说明.md` | 原项目权重来源说明 |

---

## 二、上传到 Linux（二选一）

### A. 本机 PowerShell（会提示输入 root 密码）

```powershell
powershell -ExecutionPolicy Bypass -File "E:\3311 AI\VLM_Detection_MCP\scripts\deploy_full_to_server.ps1"
```

### B. Cursor 已 Remote-SSH 连上 `company-linux`

1. `mkdir -p /root/VLM_Detection_MCP`
2. 把本文件夹 **整包拖入** `/root/VLM_Detection_MCP`
3. 远程终端：

```bash
chmod +x /root/VLM_Detection_MCP/scripts/*.sh
bash /root/VLM_Detection_MCP/scripts/install_on_server.sh
```

---

## 三、服务器启动 MCP（耀耀工厂用）

```bash
cd /root/VLM_Detection_MCP
export MCP_BEARER_TOKEN='自设强密钥'
export MCP_PUBLIC_URL=http://10.148.1.22:8000
bash scripts/run_mcp_http.sh
```

| 耀耀工厂字段 | 填写 |
|--------------|------|
| 传输方式 | **Streamable HTTP** |
| URL | `http://10.148.1.22:8000/mcp` |
| 认证 | Bearer Token = `MCP_BEARER_TOKEN` |
| 工具 | `rtmp_triple_analyze` |
| 输入 | `stream_url` 字符串，如 `rtmp://10.148.1.22/live/test` |
| 输出 | 固定 **3 张 JPEG**（见 `对话与后续步骤_交接.md`） |

---

## 四、自检命令

```bash
cd /root/VLM_Detection_MCP
source .venv/bin/activate
python scripts/test_rtmp_triple.py "rtmp://10.148.1.22/live/test"
ls -lh output/mcp_test/*.jpg
```

---

## 五、SSH 配置（本机 Windows）

`C:\Users\LENOVO\.ssh\config` 中：

```
Host company-linux
    HostName 10.148.1.22
    User root
    Port 22
```

**注意**：`company-linux` 只在 **Windows/Cursor 本机** 有效；在已登录的服务器 shell 里不要用 `ssh company-linux`。

---

**另一窗口继续沟通时**：请先打开 **`对话与后续步骤_交接.md`**。
