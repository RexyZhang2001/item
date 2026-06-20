# 赤瞳安全智能平台 — 项目框架图

> 三层架构：**前端桌面工作台 → chitung-center 中台（Agent 基座）→ agent-toolbox 工具箱**。
> 前端只调中台，中台负责意图理解 / Skill 注入 / LLM 网关 / 工作流编排 / 人工确认，
> 一切特权操作（视觉、文档、飞书、OCR…）统一经工具箱执行。

## 1. 总体架构

```mermaid
flowchart TD
    subgraph 入口层["入口层 Entry"]
        FE["chitung-frontend<br/>Electron + Vue 桌面工作台<br/>:5173"]
        FS_IN["飞书机器人<br/>Webhook 推送 / 事件回调"]
        CLI["Agent 客户端 / Cursor MCP"]
    end

    subgraph CENTER["chitung-center 中台（Agent 基座） :8999"]
        IR["意图路由<br/>intent_router"]
        ORCH["编排器<br/>orchestrator"]
        WF["工作流引擎<br/>workflow_engine（5 条）"]
        SK["Skill 服务<br/>skill_service + SKILL.md"]
        LLM["LLM 网关<br/>llm_gateway"]
        CONF["确认服务<br/>confirmation_service"]
        FADP["飞书适配器<br/>feishu_adapter"]
        AUDIT["审计<br/>audit.jsonl"]
    end

    subgraph TOOLBOX["agent-toolbox 工具箱 :8899（HTTP + MCP，79+ 工具）"]
        T_FEISHU["飞书工具<br/>发消息/卡片/事件解密(AES)"]
        T_VLM["视觉巡检<br/>YOLO + VLM hybrid"]
        T_RTMP["RTMP 截图"]
        T_FORM["智能表格<br/>模板检索/填充/DOCX"]
        T_DOC["DocMate<br/>read→generate→preview→apply"]
        T_RISK["外部风险<br/>天气/安全资讯"]
        T_YAO["耀耀 OCR<br/>结构化录入"]
        DB[("SQLite<br/>safety_platform.db")]
    end

    subgraph EXT["外部依赖 / 模型"]
        GLM["GLM-5.1<br/>open.bigmodel.cn"]
        FS_OUT["飞书开放平台<br/>OpenAPI"]
        HKO["香港天文台 + 官方安全资讯"]
        CAM["RTMP 摄像头 / YOLO 权重"]
        TPL["安全表格模板 159 份"]
    end

    FE -->|HTTP REST| IR
    FS_IN --> FADP
    CLI -->|MCP / HTTP| TOOLBOX

    IR --> ORCH
    ORCH --> WF
    ORCH --> SK
    SK --> LLM
    LLM --> GLM
    ORCH --> CONF
    FADP --> ORCH
    ORCH --> AUDIT

    WF -->|toolbox_client| TOOLBOX
    CONF --> TOOLBOX

    T_FEISHU --> FS_OUT
    T_VLM --> CAM
    T_RTMP --> CAM
    T_RISK --> HKO
    T_FORM --> TPL
    T_FORM --> DB
    T_VLM --> DB
    T_RISK --> DB
```

## 2. 一次"聊天 → 工作流 → Skill 增强 → 确认"的请求流

```mermaid
sequenceDiagram
    participant U as 用户/前端
    participant C as chitung-center
    participant G as GLM-5.1
    participant T as agent-toolbox
    participant F as 飞书

    U->>C: POST /api/chat/message（自然语言）
    C->>C: 意图路由 intent_router
    C->>T: 按意图执行工作流（调用工具）
    T-->>C: 结构化结果（草稿/卡片，未入库）
    C->>C: 按意图加载 SKILL.md
    C->>G: 注入 Skill 规则 + 工作流结果
    G-->>C: 遵循 Skill 的专业回复 + 要点 + 建议动作
    C-->>U: reply + cards + applied_skill（待人工确认）
    U->>C: 采纳/确认（card action）
    C->>T: 执行落库 / 生成正式文档
    C->>F: 可选：推送通知到飞书群
```

## 3. 组件与端口

| 组件 | 目录 | 端口 | 角色 |
| --- | --- | --- | --- |
| 桌面前端 | `chitung-frontend` | 5173 | Electron + Vue 工作台 |
| 中台（Agent 基座） | `chitung-center` | 8999 | 意图/编排/Skill/LLM/确认 |
| 工具箱 | `agent-toolbox` | 8899 | HTTP + MCP 工具网关 |
| 数据库 | `agent-toolbox/workspace` | — | SQLite |

## 4. 当前完成度

| 能力 | 状态 |
| --- | --- |
| Agent 中台 + 工具箱 | ✅ 运行 |
| 大模型 GLM-5.1 | ✅ 已接入 |
| 5 条核心工作流 | ✅ 可跑（简报/隐患/填表/检索/巡检）|
| Skill 注入编排 | ✅ 已接入 GLM，可追溯 `applied_skill` |
| 飞书推送（Webhook） | ✅ 已打通 |
| 飞书事件解密（接收） | ✅ 代码就绪，需公网回调地址 |
| 视觉巡检 E2E | ⚠️ 需 YOLO 权重 + 摄像头 |
| 桌面前端 GUI | ✅ 运行 |

> 关系图同时参见仓库根目录 `CODE_RELATIONSHIP_GRAPH.md` 与 `chitung-center/docs/ARCHITECTURE.md`。
