# VLM-Detection 双模型检测 + HiAgent 插件 — 交接包说明

> 打包日期：2026-05-15  
> 用途：带到新环境与其他代码合并，统一部署为 HiAgent HTTP 插件上云。

---

## 一、今晚完成事项（摘要）

1. **筛选并下载两个高精度工地检测权重**（目标检测 bbox，非实例分割）
2. **搭建 `VLM-Detection` 推理项目**（仅检测，不训练）
3. **配置 conda 环境 `vlm_detection`**（本机勿用项目内 `.venv` 装 torch）
4. **实现 HiAgent HTTP 插件**：输入 1 张图 → 固定顺序输出 3 张图
5. **提供 Docker / OpenAPI / 部署文档**，便于明天合并上云

---

## 二、两个权重（必带）

| 用途 | 本地路径 | 原始来源 | 架构 |
|------|----------|----------|------|
| 工人 + PPE | `weights/worker/yolo26x_worker.pt` (~113MB) | [Construction-Hazard-Detection](https://huggingface.co/yihong1120/Construction-Hazard-Detection) `models/yolo26/pt/yolo26x.pt` | YOLO26x |
| 8 类施工机械 | `weights/machinery/yolo26l_machinery.pt` (~51MB) | [sitesense-weights](https://huggingface.co/Zaafan/sitesense-weights) `yolo26l_construction_v1.pt` | YOLO26-L |

**工人模型常用类别 ID**（`config.yaml` 中 `worker_classes` 已过滤）：

- 5 Person, 0 Hardhat, 2 NO-Hardhat, 7 Safety Vest, 4 NO-Safety Vest, 1 Mask, 3 NO-Mask

**机械模型类别**：excavator, dump_truck, bulldozer, wheel_loader, mobile_crane, tower_crane, roller_compactor, cement_mixer

若权重丢失，可用 HuggingFace 重新下载（见 `scripts/redownload_weights.py`）。

---

## 三、目录与文件说明

```
VLM-Detection/
├── HANDOFF_交接说明.md      ← 本文件
├── DEPLOY.txt               ← 上云步骤（简版）
├── USE.txt                  ← 日常使用
├── config.yaml              ← 权重路径、conf、类别
├── detect_core.py           ← 核心：双模型推理 + 三张图
├── detect.py                ← 命令行批量检测
├── hiagent_api.py           ← FastAPI（HiAgent 插件主体）
├── verify_weights.py        ← 检查权重是否可加载
├── openapi.yaml             ← 导入 HiAgent（改 servers.url）
├── requirements.txt         ← 推理依赖
├── requirements-api.txt     ← HTTP 服务额外依赖
├── setup_env.ps1            ← 创建 conda 环境
├── run_api.ps1              ← 本地启动 API
├── run_detect.ps1 / .bat    ← 本地批量检测
├── Dockerfile               ← 云部署镜像
├── weights/
│   ├── worker/yolo26x_worker.pt
│   └── machinery/yolo26l_machinery.pt
└── input/demo.jpg           ← 试跑样例（可选）
```

**不要复制**：`.venv/`（本机中文路径下 torch 易失败）、`weights/*_hf/`（HF 缓存副本，可删）。

---

## 四、实现路径（与领导要求一致）

**插件 = 云服务器上的 HTTPS HTTP 接口**

```
HiAgent 工作流
    │  POST /v1/detect/triple/json  (image_url 或 image_base64)
    ▼
你的云服务器 (hiagent_api.py + 两个 .pt)
    │  JSON: images[0]=原图, [1]=human, [2]=machine + detections
    ▼
HiAgent 后续 VLM 节点（行为/隐患分析）
```

- **权重只放服务器**，HiAgent 平台只登记 API 地址 + OpenAPI + API Key
- 单图建议 ≤ 5MB（平台常见限制）

---

## 五、新环境快速启动

### 5.1 环境（推荐 conda）

```powershell
cd <解压目录>\VLM-Detection
powershell -ExecutionPolicy Bypass -File setup_env.ps1
conda activate vlm_detection
python verify_weights.py
```

### 5.2 命令行检测

```powershell
python detect.py --source input\demo.jpg --triple --export-json
# 三张图在 output/triple/：*_01_original, *_02_human, *_03_machine
```

### 5.3 本地 API（合并前自测）

```powershell
powershell -File run_api.ps1
# 打开 http://127.0.0.1:8080/docs
```

### 5.4 Docker 上云

```bash
docker build -t vlm-detection-api .
docker run -d -p 8080:8080 -e HIAGENT_API_KEY=密钥 vlm-detection-api
# 前接 Nginx HTTPS，见 DEPLOY.txt
```

---

## 六、与另一套代码合并建议

1. **保留本包 `detect_core.py` + `config.yaml`** 作为双模型唯一入口，避免两套 YOLO 逻辑分叉。
2. **合并方式 A**：把 `hiagent_api.py` 的路由挂到对方现有 FastAPI `app`（`app.include_router` 或复制 `/v1/detect/triple` 两个端点）。
3. **合并方式 B**：本服务独立容器，对方通过内网 HTTP 调用（微服务，耦合最低）。
4. **权重路径**：合并后统一用环境变量 `VLM_CONFIG` 指向 `config.yaml`，或改 `config.yaml` 里 `models.worker` / `models.machinery` 为绝对路径。
5. **HiAgent**：只导入一份 `openapi.yaml`，`servers.url` 改为合并后的对外域名。

---

## 七、API 契约（合并时勿改顺序）

**POST** `/v1/detect/triple/json`

请求（二选一）：
```json
{ "image_url": "https://..." }
```
或
```json
{ "image_base64": "..." }
```

响应 `images` 数组**固定顺序**：
| 下标 | role | 含义 |
|------|------|------|
| 0 | original | 原图 |
| 1 | human | 原图 + 仅工人/PPE 框（绿色） |
| 2 | machine | 原图 + 仅机械框（橙色） |

另含 `detections.worker`、`detections.machinery`、`counts`。

---

## 八、已知问题

- 路径含中文（如 `E:\VLM检测`）时，pip `.venv` + PyTorch 可能 DLL 失败 → **用英文路径 + conda**。
- 本机 `E:\VLMDetection` 与 `e:\VLM-Detection\VLM-Detection` 可能各有一份副本，以本交接包为准。

---

## 九、联系人/延续开发

- 本地已验证：`verify_weights.py` 通过；API 返回 `original/human/machine` 顺序正确。
- 明天优先：与对方代码合并 → Docker 上云 → HiAgent 导入 OpenAPI 联调。
