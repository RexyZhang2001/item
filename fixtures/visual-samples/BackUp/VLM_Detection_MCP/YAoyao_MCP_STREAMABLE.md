# 耀耀工厂 · Streamable HTTP MCP 插件接入说明

## 功能约定

| 项目 | 说明 |
|------|------|
| **输入** | 单个字符串 `stream_url`，内容为 RTMP/HLS/FLV 地址，例如 `rtmp://10.148.1.22/live/test` |
| **输出** | 固定顺序 **3 张 JPG**（`mime: image/jpeg`，base64 编码） |
| 第 1 张 | `image.jpg` — 当前帧原图 |
| 第 2 张 | `image-human.jpg` — YOLO 人员/PPE 叠加 |
| 第 3 张 | `image-machine.jpg` — YOLO 机械叠加 |

MCP 工具名：**`rtmp_triple_analyze`**（参数仅 `stream_url`）。

---

## 一、上传到 Linux 云服务器（10.148.1.22）

在 **已 SSH 连上的 Cursor 远程窗口** 或本机 PowerShell：

```bash
# 本机上传整目录（在 Windows PowerShell，路径按你本机改）
scp -r "E:\3311 AI\Yolo Detection" root@10.148.1.22:/root/vlm-yolo
```

或在 Cursor 远程里：**文件 → 将文件夹拖到 `/root/vlm-yolo`**。

服务器上需包含：

- `weights/worker/*.pt`、`weights/machinery/*.pt`
- `config.yaml`、`detect_core.py`、`stream_capture.py`、`rtmp_pipeline.py`、`mcp_vlm_server.py`
- `requirements-mcp.txt`

---

## 二、服务器安装与启动

```bash
cd /root/vlm-yolo
bash scripts/setup_linux.sh mcp

# 设置 Bearer（与耀耀工厂表单 Token 一致，自行换成强随机串）
export MCP_BEARER_TOKEN='你的密钥'
export MCP_HTTP_HOST=0.0.0.0
export MCP_HTTP_PORT=8000
export MCP_PUBLIC_URL=http://10.148.1.22:8000

bash scripts/run_mcp_http.sh
```

后台常驻（可选 systemd）见 `deploy/vlm-mcp.service`。

本机自检：

```bash
curl -s http://127.0.0.1:8000/mcp
# 或带 Bearer（若已设置 MCP_BEARER_TOKEN）
curl -s -H "Authorization: Bearer 你的密钥" http://127.0.0.1:8000/mcp
```

---

## 三、耀耀工厂表单填写

| 字段 | 填写 |
|------|------|
| **插件名称** | VLM 视频流三图检测 |
| **插件描述** | 输入 RTMP 流地址，抽当前帧并 YOLO 检测，按序返回原图、人员图、机械图共三张 JPEG base64 |
| **传输方式** | **Streamable HTTP** |
| **URL** | `http://10.148.1.22:8000/mcp` |
| **认证类型** | Bearer Token |
| **Token** | 与服务器环境变量 `MCP_BEARER_TOKEN` **完全相同** |
| **开启** | 打开 |

若耀耀工厂与服务器不在同一内网，需用 **公网 IP/域名 + HTTPS**（Nginx 反代到 8000），URL 改为 `https://你的域名/mcp`。

---

## 四、工作流如何调用

1. 在智能体工作流中添加 **MCP 工具** 节点。  
2. 选择工具 **`rtmp_triple_analyze`**。  
3. 入参：`stream_url` = `rtmp://10.148.1.22/live/test`（或变量）。  
4. 解析返回 JSON 的 **`images` 数组**（长度 3，顺序固定），或顶层字段：
   - `image` / `image_human` / `image_machine`（均为 base64 字符串）

返回 JSON 结构示例：

```json
{
  "ok": true,
  "format": "jpeg",
  "image_count": 3,
  "images": [
    {"index": 1, "role": "image", "filename": "image.jpg", "mime": "image/jpeg", "base64": "..."},
    {"index": 2, "role": "image-human", "filename": "image-human.jpg", "mime": "image/jpeg", "base64": "..."},
    {"index": 3, "role": "image-machine", "filename": "image-machine.jpg", "mime": "image/jpeg", "base64": "..."}
  ],
  "image": "...",
  "image_human": "...",
  "image_machine": "..."
}
```

解码示例（任意节点）：`base64.b64decode(images[0]["base64"])` → 写入 `image.jpg` 即为第一张原图。

后续 **VLM 语义分析** 在耀耀工厂用大模型节点读这三张图即可（本服务只做抽帧+YOLO）。

---

## 五、与「HTTP 请求插件」的区别

| 方式 | 地址 | 适用 |
|------|------|------|
| **MCP Streamable HTTP** | `http://IP:8000/mcp` | 耀耀工厂「接入 MCP 插件」 |
| **REST（openapi）** | `http://IP:8080/v1/analyze/stream` | 工作流「HTTP 请求」节点 |

两套可并存：MCP 给智能体工具；REST 给传统编排。
