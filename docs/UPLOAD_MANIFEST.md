# 仓库上传清单（Batch 1 + Batch 2）

> 仓库：https://github.com/ZTX-666/item  
> 同事接手顺序：`COLLABORATION_HANDOFF.md` → 本文 → `docs/product/` 产品文档

---

## Batch 1（已上传）

| 路径 | 用途 |
| --- | --- |
| `chitung-frontend` | 正式前端工作台 |
| `chitung-center` | FastAPI 中台 + Skills |
| `agent-toolbox` | 129+ 工具网关 |
| `chitong-lingxun` | WhatsApp 桌面客户端 |
| `docmate-shanshan` | 闪闪文档编辑器 |
| `rtmp-tools` / `vlm-detection` / `scripts` | 视觉巡检 |
| `report-generators` | 报告生成 |
| `safety-policy-templates-20241025` | 159 表格模板 |
| `docs/COLLABORATION_HANDOFF.md` | 协作交接主文档 |

---

## Batch 2（建议追加）

### A. FinalAgentSuite 内未传模块

| 路径 | 用途 | 优先级 |
| --- | --- | --- |
| `whatsapp-archive` | WhatsApp 归档后端+Web UI | P0 |
| `frontend-ui-prototype` | UI 原型与交互规范 | P0 |
| `docs/product/*.md` | 产品/技术/飞书/视觉文档（已脱敏） | P0 |
| `docs/product/*.html` | 架构图、功能地图（设计参考） | P1 |
| `CODE_RELATIONSHIP_GRAPH*.md` | 代码关系图 | P0 |
| `PRODUCT_HANDOFF.md` / `FINAL_VERSIONS.md` | 产品形态与版本决策 | P1 |

### B. 从 `J:\China Oversea  Final` 复制到 `external/`

| 源路径 | 目标路径 | 用途 |
| --- | --- | --- |
| `02-depth-VLM-Pipeline` | `external/02-depth-VLM-Pipeline` | YOLO+Depth 增强流水线 |
| `01-PaddleOCRSharp/PaddleOCRSharp` | `external/paddle-ocr-sharp/PaddleOCRSharp` | 耀耀慧读 OCR 核心库 |
| `01-PaddleOCRSharp/PaddlePdfOcrApp` | `external/paddle-ocr-sharp/PaddlePdfOcrApp` | PDF OCR 示例 |
| `03-site-memorandum-standard` | `external/site-memorandum-standard` | 地盘 Memo/联系人 Skill |
| `ChinaOverseas Final/docx_translate` | `external/docx-translate` | Word 抽取/回填 |
| `open-source-references` | `open-source-references` | 开源参考（排除 mlruns/weights） |

### C. 本地自备，不上传

| 资源 | 原因 |
| --- | --- |
| `VLM Detection/weights/*.pt` | 体积大（~164MB），用下载说明代替 |
| `3311 AI/*.jpg` | 现场测试图，54 张；本地路径写入 `fixtures/README` |
| `patrol-output/` | 运行输出 |
| `publish4/`、`workbuddy/` | 打包产物/工具缓存 |
| 含真实 API Key 的 RTMP 迁移文档 | 已脱敏版在 `docs/product/` |
| `agent-toolbox/.env` | 密钥 |

---

## 同事完成软件的最小阅读路径

1. `docs/COLLABORATION_HANDOFF.md` — 启动与环境
2. `docs/product/赤瞳安全智能平台_完成度差距与开发路线_2026-06-20.md` — 差距与 P0
3. `docs/product/飞书机器人五阶段实施工具清单.md` — 飞书 MVP
4. `docs/product/赤瞳守护者_零上下文接手开发手册.md` — 视觉链路
5. `frontend-ui-prototype/` — UI 目标态
6. `CODE_RELATIONSHIP_GRAPH_2026-06-20.md` — 模块关系

---

## YOLO 权重（已纳入 Git LFS）

权重位于仓库内：

```text
vlm-detection/weights/worker/yolo26x_worker.pt      (~113 MB, Git LFS)
vlm-detection/weights/machinery/yolo26l_machinery.pt (~51 MB, Git LFS)
```

同事 clone 后需安装 Git LFS：

```powershell
git lfs install
git clone https://github.com/ZTX-666/item.git
```

本地来源（上传脚本自动复制）：

```text
J:\China Oversea  Final\VLM Detection\weights\
```
