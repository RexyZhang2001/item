@echo off
setlocal EnableDelayedExpansion
rem 根据当前项目根目录生成本地 .env（避免 J: 盘旧路径导致启动失败）
set "ROOT=%~1"
if "%ROOT%"=="" exit /b 1

set "TOOLBOX=%ROOT%\agent-toolbox"
set "CENTER=%ROOT%\chitung-center"

> "%TOOLBOX%\.env" (
  echo AGENT_TOOLBOX_HOST=127.0.0.1
  echo AGENT_TOOLBOX_PORT=8899
  echo AGENT_TOOLBOX_ROOT=%TOOLBOX%
  echo AGENT_TOOLBOX_WORKSPACE=%TOOLBOX%\workspace
  echo VLM_DETECTION_DIR=%ROOT%\vlm-detection
  echo RTMP_SNAPSHOT_SCRIPT=%ROOT%\rtmp-tools\rtmp_snapshot.py
  echo REPORT_SCRIPT=%ROOT%\report-generators\generate_community_doc.py
  echo SAFETY_POLICY_TEMPLATES_DIR=%ROOT%\safety-policy-templates-20241025
  echo SAFETY_DATABASE_PATH=%TOOLBOX%\workspace\safety_platform.db
  echo YAOYAO_WORK_DIR=%TOOLBOX%\workspace\yaoyao
  echo YAOYAO_MODEL_DIR=%ROOT%\models\yaoyao\rapidocr
)

> "%CENTER%\.env" (
  echo CHITUNG_CENTER_HOST=127.0.0.1
  echo CHITUNG_CENTER_PORT=8999
  echo AGENT_TOOLBOX_BASE_URL=http://127.0.0.1:8899
  echo LLM_BASE_URL=
  echo LLM_API_KEY=
  echo LLM_MODEL=
  echo LLM_EMBEDDING_BASE_URL=
  echo LLM_EMBEDDING_MODEL=
  echo CHITUNG_DATA_DIR=%CENTER%\data
  echo CHITUNG_SKILLS_DIR=%CENTER%\skills
  echo CHITUNG_WORKFLOWS_DIR=%CENTER%\workflows
  echo CHITUNG_AUDIT_LOG=%CENTER%\data\audit.jsonl
  echo RAG_CHROMA_DIR=%CENTER%\data\rag_chroma
  echo RAG_META_PATH=%CENTER%\data\rag_meta.json
  echo RAG_UPLOAD_DIR=%CENTER%\data\rag_uploads
  echo TABLE_MAPPING_SCRIPT_DIR=E:\China Oversea  Final\表格映射\auto-fill-script
  echo TABLE_MAPPING_NODE_BIN=node
  echo TABLE_MAPPING_TIMEOUT_SECONDS=180
)

mkdir "%TOOLBOX%\workspace" 2>nul
mkdir "%CENTER%\data" 2>nul
mkdir "%CENTER%\workflows" 2>nul
endlocal
